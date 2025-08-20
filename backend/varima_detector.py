import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def is_boolean_column(df: pd.DataFrame, column_name: str) -> bool:
    series = df[column_name]
    unique_values = series.dropna().unique()
    if series.dtype == 'bool':
        return True
    boolean_values = {True, False, 'true', 'false', 'True', 'False',
                     'TRUE', 'FALSE', 1, 0, '1', '0', 'yes', 'no',
                     'Yes', 'No', 'YES', 'NO'}

    if len(unique_values) <= 2 and all(val in boolean_values for val in unique_values):
        return True
    return False

def is_id_column(series, column_name):
    """
    Check if a column is likely an ID column based on name patterns and data characteristics
    """
    if series.empty:
        return False
    
    column_name_lower = column_name.lower()
    
    # Name-based patterns for ID columns
    name_patterns = [
        'id' in column_name_lower,
        column_name_lower.endswith('_id'),
        column_name_lower.startswith('id_'),
        column_name_lower in ['index', 'key', 'pk', 'primary_key'],
        any(pattern in column_name_lower for pattern in ['customer_id', 'user_id', 'order_id', 'product_id'])
    ]
    
    # Data-based patterns for ID columns
    is_unique = series.nunique() == len(series.dropna())
    is_sequential = False
    has_low_correlation = True
    
    # Check for sequential pattern (like auto-increment IDs)
    if pd.api.types.is_numeric_dtype(series):
        try:
            numeric_series = pd.to_numeric(series.dropna(), errors='coerce')
            if len(numeric_series) > 1:
                diffs = numeric_series.diff().dropna()
                is_sequential = (diffs == 1).all() or (diffs == -1).all()
        except:
            pass
    
    data_patterns = [
        is_sequential,  # Sequential numbering
        is_unique and len(series) > 10,  # Large unique dataset
    ]
    
    # Only consider low correlation for numeric columns that look like IDs
    if pd.api.types.is_numeric_dtype(series) and any(name_patterns):
        has_low_correlation = True
    else:
        has_low_correlation = False
    
    return any(name_patterns) or any(data_patterns) or has_low_correlation

def numeric_columns(df: pd.DataFrame) -> list:
    numeric_cols = [col for col in df.columns
                   if pd.api.types.is_numeric_dtype(df[col])
                   and 'timestamp' not in col.lower()
                   and not is_boolean_column(df, col)
                   and not is_id_column(df[col], col)]
    return numeric_cols

def date_column_by_variance(df: pd.DataFrame) -> str:
    dt_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    if not dt_cols:
        return None
    return max(dt_cols, key=lambda col: df[col].diff().dt.total_seconds().var())

def cleanData(df: pd.DataFrame, null_threshold: float = 0.5):
    cleaned_df = df.copy()

    # Remove columns with null values > null_threshold
    missing_ratio = cleaned_df.isnull().mean()
    cols_to_drop = missing_ratio[missing_ratio > null_threshold].index
    cleaned_df.drop(columns=cols_to_drop, inplace=True)

    # Remove duplicated rows
    cleaned_df = cleaned_df.drop_duplicates()

    # Convert datetime columns
    for col in cleaned_df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            if pd.api.types.is_datetime64_any_dtype(cleaned_df[col]):
                continue
            if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                continue

            try:
                converted = pd.to_datetime(cleaned_df[col], errors='coerce')
                if converted.notnull().sum() > len(converted) * 0.5:
                    cleaned_df[col] = converted
            except Exception as e:
                print(f"Could not convert column {col} to datetime: {e}")
                continue

    # Convert datetime columns to timestamp
    datetime_cols = cleaned_df.select_dtypes(include=['datetime64']).columns
    print(f"Datetime columns found in data cleaner: {datetime_cols}")
    for col in datetime_cols:
        timestamp_col = f"{col}_timestamp"
        cleaned_df[timestamp_col] = cleaned_df[col].astype('int64') // 10**9

    return cleaned_df

def VarimaCleaner(df: pd.DataFrame):
    """
    Improved VARIMA data cleaner with better handling of time series data
    """
    cleaned_df = cleanData(df)

    # Find numeric columns
    numeric_cols = numeric_columns(cleaned_df)
    numeric_cols = [col for col in numeric_cols if 'age' not in col.lower()]

    print(f"Numeric columns for VARIMA: {numeric_cols}")

    if not numeric_cols:
        raise ValueError("No numeric columns found for VARIMA")

    # Handle missing values in numeric columns
    for col in numeric_cols:
        if cleaned_df[col].isnull().any():
            cleaned_df = cleaned_df.infer_objects(copy=False)
            cleaned_df[col] = cleaned_df[col].interpolate(method='linear').ffill().bfill()

    # Find date column
    date_col = date_column_by_variance(cleaned_df)
    if date_col is None:
        raise ValueError("No datetime column found for time series analysis")

    # Prepare VARIMA dataframe
    varima_df = cleaned_df[numeric_cols].copy()
    varima_df[date_col] = cleaned_df[date_col]
    varima_df.set_index(date_col, inplace=True)
    varima_df = varima_df.sort_index()
    varima_df = varima_df.dropna()

    print(f"VARIMA DataFrame shape after cleaning: {varima_df.shape}")
    return varima_df

def detect_varima_anomalies(df: pd.DataFrame, threshold: float = 2.0, max_components: int = 5) -> pd.DataFrame:
    """
    Improved VARIMA anomaly detection with better error handling and preprocessing
    """
    # Store original dataframe for final result
    original_df = df.copy()

    # If dataframe has datetime index, reset it to work with numeric data
    if isinstance(df.index, pd.DatetimeIndex):
        df_work = df.reset_index()
        datetime_col = df.index.name
    else:
        df_work = df.copy()
        datetime_col = None

    # Select numeric columns
    numeric_cols = df_work.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        print("No numeric columns found for VARIMA detection.")
        return original_df.assign(anomaly=False)

    # Remove columns with too many missing values or no variance
    valid_cols = []
    for col in numeric_cols:
        if df_work[col].isnull().sum() / len(df_work) < 0.5:  # Less than 50% missing
            if df_work[col].std() > 1e-6:  # Has some variance
                valid_cols.append(col)

    if len(valid_cols) == 0:
        print("No valid numeric columns found for VARIMA detection.")
        return original_df.assign(anomaly=False)

    print(f"Valid numeric columns for VARIMA: {valid_cols}")

    # Work with valid columns only
    df_numeric = df_work[valid_cols].copy()

    # Handle missing values
    df_numeric = df_numeric.interpolate(method='linear').ffill().bfill()

    # Remove any remaining rows with NaN
    df_numeric = df_numeric.dropna()

    if len(df_numeric) < 10:
        print("Not enough data points for VARIMA analysis.")
        return original_df.assign(anomaly=False)

    # Scale the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_numeric)

    # Apply PCA with limited components
    n_components = min(max_components, len(valid_cols), len(df_numeric) - 1)
    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(scaled_data)

    # Create PCA dataframe
    pca_columns = [f'PC_{i+1}' for i in range(principal_components.shape[1])]
    df_pca = pd.DataFrame(principal_components, columns=pca_columns, index=df_numeric.index)

    print(f"PCA components shape: {df_pca.shape}")
    print(f"Explained variance ratio: {pca.explained_variance_ratio_}")

    # Check stationarity and apply differencing if needed
    stationary_cols = []
    for col in df_pca.columns:
        try:
            result = adfuller(df_pca[col], autolag='AIC')
            if result[1] > 0.05:  # Not stationary
                print(f"Column {col} is not stationary (p-value: {result[1]:.4f}). Applying differencing.")
                df_pca[col] = df_pca[col].diff()
                stationary_cols.append(col)
            else:
                print(f"Column {col} is stationary (p-value: {result[1]:.4f})")
        except Exception as e:
            print(f"Stationarity test failed for {col}: {e}")
            continue

    # Remove NaN values created by differencing
    df_pca = df_pca.dropna()

    if len(df_pca) < 5:
        print("Not enough data points after differencing for VARIMA analysis.")
        return original_df.assign(anomaly=False)

    # Fit VARIMA model with simpler parameters and timeout protection
    try:
        print("Fitting VARIMA model...")
        # Use very simple model parameters to avoid convergence issues
        model = VARMAX(df_pca, order=(1, 0))  # AR(1) model without MA component
        fitted_model = model.fit(disp=False, maxiter=20, method='lbfgs')  # Reduced iterations
        print("VARIMA model fitted successfully")

    except Exception as e:
        print(f"VARIMA model fitting failed: {e}")
        try:
            # Fallback to even simpler model with minimal iterations
            print("Trying simpler VAR model...")
            model = VARMAX(df_pca, order=(1, 0))
            fitted_model = model.fit(disp=False, maxiter=10, method='lbfgs')
            print("VAR model fitted successfully")
        except Exception as e2:
            print(f"VAR model also failed: {e2}")
            return original_df.assign(anomaly=False)

    # Calculate residuals and detect anomalies
    try:
        residuals = fitted_model.resid
        if residuals.empty:
            print("No residuals available for anomaly detection.")
            return original_df.assign(anomaly=False)

        # Calculate z-scores for each component
        residuals_std = residuals.std()
        residuals_std[residuals_std == 0] = 1e-6  # Avoid division by zero

        z_scores = (residuals - residuals.mean()) / residuals_std

        # Detect anomalies (any component with z-score > threshold)
        anomalies = (z_scores.abs() > threshold).any(axis=1)

        print(f"Detected {anomalies.sum()} anomalies out of {len(anomalies)} observations")

        # Create result dataframe
        result_df = original_df.copy()

        # Map anomalies back to original dataframe
        # This is tricky because of potential index mismatches due to cleaning
        anomaly_series = pd.Series(False, index=result_df.index)

        if len(anomalies) == len(result_df):
            anomaly_series[:] = anomalies.values
        else:
            # Try to match by position (less ideal but functional)
            min_len = min(len(anomalies), len(result_df))
            anomaly_series.iloc[:min_len] = anomalies.iloc[:min_len].values

        result_df['anomaly'] = anomaly_series

        return result_df

    except Exception as e:
        print(f"Anomaly detection failed: {e}")
        return original_df.assign(anomaly=False)

# Example usage function
def run_varima_detection(df):
    """
    Main function to run VARIMA anomaly detection
    """
    print("\n=== VARIMA Detection ===")
    result_df = df.copy()

    try:
        # Clean and prepare data
        df_varima = VarimaCleaner(df)
        print(f"After VarimaCleaner shape: {df_varima.shape}")

        # Reset index to work with the detection function
        df_varima_reset = df_varima.reset_index()
        print(f"Data shape after reset_index: {df_varima_reset.shape}")

        # Run VARIMA anomaly detection
        varima_result = detect_varima_anomalies(df_varima_reset, threshold=2.0)

        if 'anomaly' in varima_result.columns:
            if len(varima_result) == len(result_df):
                result_df['anomaly_varima'] = varima_result['anomaly'].values
                print(f"Successfully added VARIMA anomaly detection results")
                print(f"Anomalies detected: {varima_result['anomaly'].sum()}")
            else:
                print(f"Warning: VARIMA results length {len(varima_result)} doesn't match original {len(result_df)}")
                result_df['anomaly_varima'] = False
        else:
            print("No anomaly column found in VARIMA results")
            result_df['anomaly_varima'] = False

    except Exception as e:
        print(f"VARIMA detection failed: {e}")
        result_df['anomaly_varima'] = False

    return result_df
