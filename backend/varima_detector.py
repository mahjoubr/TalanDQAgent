import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.stattools import adfuller
import warnings
warnings.filterwarnings('ignore')

def numeric_columns(df):
    """Get numeric columns from dataframe"""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def date_column_by_variance(df):
    """Find date column by checking variance patterns"""
    date_cols = []
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower() or 'time' in col.lower():
            date_cols.append(col)
    return date_cols[0] if date_cols else None

class VarimaCleaner:
    """VARIMA-based data cleaning and anomaly detection"""
    
    def __init__(self, threshold=2.0, max_components=5):
        self.threshold = threshold
        self.max_components = max_components
        self.scaler = StandardScaler()
        self.pca = None
        self.var_model = None
        self.is_fitted = False
        
    def fit(self, data):
        """Fit the VARIMA model to the data"""
        if len(data) < 10:
            raise ValueError("Need at least 10 observations to fit VARIMA model")
            
        # Standardize the data
        data_scaled = self.scaler.fit_transform(data)
        
        # Apply PCA for dimensionality reduction
        n_components = min(self.max_components, data.shape[1], len(data) // 3)
        self.pca = PCA(n_components=n_components)
        data_pca = self.pca.fit_transform(data_scaled)
        
        # Convert to DataFrame for VAR model
        data_df = pd.DataFrame(data_pca, columns=[f'PC{i+1}' for i in range(n_components)])
        
        # Check stationarity and difference if needed
        stationary_data = self._make_stationary(data_df)
        
        # Fit VAR model
        self.var_model = VAR(stationary_data)
        var_results = self.var_model.fit(maxlags=min(5, len(stationary_data) // 4))
        self.var_fitted = var_results
        
        self.is_fitted = True
        return self
    
    def _make_stationary(self, data):
        """Make time series stationary"""
        stationary_data = data.copy()
        
        for col in data.columns:
            # Check stationarity using Augmented Dickey-Fuller test
            try:
                adf_result = adfuller(data[col].dropna())
                if adf_result[1] > 0.05:  # Not stationary
                    # Apply first difference
                    stationary_data[col] = data[col].diff().fillna(0)
            except:
                # If ADF test fails, just use the original data
                pass
                
        return stationary_data
    
    def detect_anomalies(self, data):
        """Detect anomalies using fitted VARIMA model"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before detecting anomalies")
            
        # Transform data using fitted scaler and PCA
        data_scaled = self.scaler.transform(data)
        data_pca = self.pca.transform(data_scaled)
        
        # Convert to DataFrame
        data_df = pd.DataFrame(data_pca, columns=[f'PC{i+1}' for i in range(data_pca.shape[1])])
        
        # Make stationary
        stationary_data = self._make_stationary(data_df)
        
        # Get residuals from VAR model
        try:
            forecast = self.var_fitted.forecast(stationary_data.values, steps=1)
            residuals = stationary_data.iloc[-1:].values - forecast
            
            # Calculate Mahalanobis distance for anomaly detection
            residuals_flat = residuals.flatten()
            mahal_dist = np.sqrt(np.sum(residuals_flat ** 2))
            
            # Detect anomalies based on threshold
            is_anomaly = mahal_dist > self.threshold
            
            return is_anomaly, mahal_dist
        except:
            # If forecasting fails, use simple statistical approach
            return self._statistical_anomaly_detection(data_pca)
    
    def _statistical_anomaly_detection(self, data_pca):
        """Fallback statistical anomaly detection"""
        # Calculate z-scores for each component
        z_scores = np.abs(stats.zscore(data_pca, axis=0, nan_policy='omit'))
        
        # Consider it an anomaly if any component has z-score > threshold
        max_z_score = np.max(z_scores, axis=1)
        is_anomaly = max_z_score > self.threshold
        
        return is_anomaly, max_z_score

def run_varima_detection(df, threshold=2.0, max_components=5):
    """Run VARIMA anomaly detection on a DataFrame"""
    try:
        # Get numeric columns
        num_cols = numeric_columns(df)
        if len(num_cols) < 2:
            raise ValueError("Need at least 2 numeric columns for VARIMA analysis")
        
        # Extract numeric data
        numeric_data = df[num_cols].fillna(df[num_cols].mean())
        
        # Initialize VARIMA cleaner
        varima_cleaner = VarimaCleaner(threshold=threshold, max_components=max_components)
        
        # Split data for training and testing
        train_size = int(0.8 * len(numeric_data))
        train_data = numeric_data.iloc[:train_size]
        test_data = numeric_data.iloc[train_size:]
        
        if len(train_data) < 10:
            raise ValueError("Insufficient training data")
        
        # Fit the model
        varima_cleaner.fit(train_data)
        
        # Detect anomalies in the full dataset
        anomalies = []
        anomaly_scores = []
        
        # Process data in chunks to avoid memory issues
        chunk_size = 100
        for i in range(0, len(numeric_data), chunk_size):
            chunk = numeric_data.iloc[i:i+chunk_size]
            
            for j in range(len(chunk)):
                single_point = chunk.iloc[j:j+1]
                try:
                    is_anomaly, score = varima_cleaner.detect_anomalies(single_point)
                    anomalies.append(is_anomaly)
                    anomaly_scores.append(score if isinstance(score, (int, float)) else score[0])
                except:
                    # If detection fails for a point, mark as normal
                    anomalies.append(False)
                    anomaly_scores.append(0.0)
        
        # Create result DataFrame
        result_df = df.copy()
        result_df['anomaly_varima'] = anomalies
        result_df['anomaly_score'] = anomaly_scores
        
        return result_df
        
    except Exception as e:
        print(f"VARIMA detection failed: {str(e)}")
        # Return original DataFrame with no anomalies detected
        result_df = df.copy()
        result_df['anomaly_varima'] = False
        result_df['anomaly_score'] = 0.0
        return result_df

def detect_varima_anomalies(df, threshold=2.0):
    """Simplified VARIMA anomaly detection"""
    return run_varima_detection(df, threshold=threshold)

def cleanData(df):
    """Clean data by removing detected anomalies"""
    result_df = run_varima_detection(df)
    
    # Remove anomalies
    clean_df = result_df[result_df['anomaly_varima'] == False].copy()
    
    # Drop the anomaly columns
    clean_df = clean_df.drop(['anomaly_varima', 'anomaly_score'], axis=1)
    
    return clean_df
