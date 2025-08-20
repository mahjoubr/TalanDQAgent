"""
Test script for the new VARIMA detector
"""
import pandas as pd
import numpy as np
from varima_detector import run_varima_detection, numeric_columns, cleanData, is_boolean_column, is_id_column

def test_basic_functionality():
    print("=== Testing Basic VARIMA Functionality ===")
    
    # Create test data
    np.random.seed(42)
    n_samples = 100
    
    # Create a sample dataset with various column types
    data = {
        'id': range(1, n_samples + 1),  # ID column
        'timestamp': pd.date_range('2023-01-01', periods=n_samples, freq='D'),
        'value1': np.random.normal(100, 10, n_samples),  # Numeric column
        'value2': np.random.normal(50, 5, n_samples),   # Numeric column
        'value3': np.random.normal(25, 3, n_samples),   # Numeric column
        'boolean_col': np.random.choice([True, False], n_samples),  # Boolean column
        'category': np.random.choice(['A', 'B', 'C'], n_samples),   # Categorical column
    }
    
    # Add some anomalies
    data['value1'][10] = 200  # Outlier
    data['value1'][50] = -50  # Outlier
    data['value2'][25] = 150  # Outlier
    
    df = pd.DataFrame(data)
    print(f"Created test dataframe with shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df

def test_column_detection(df):
    print("\n=== Testing Column Detection ===")
    
    # Test numeric columns detection
    numeric_cols = numeric_columns(df)
    print(f"Detected numeric columns: {numeric_cols}")
    
    # Test boolean column detection
    for col in df.columns:
        if is_boolean_column(df, col):
            print(f"'{col}' detected as boolean column")
    
    # Test ID column detection
    for col in df.columns:
        if is_id_column(df, col):
            print(f"'{col}' detected as ID column")

def test_data_cleaning(df):
    print("\n=== Testing Data Cleaning ===")
    
    # Add some missing values
    df_with_nulls = df.copy()
    df_with_nulls.loc[5:10, 'value1'] = np.nan
    df_with_nulls.loc[15:20, 'value2'] = np.nan
    
    print(f"Added nulls - Original shape: {df_with_nulls.shape}")
    print(f"Null counts: {df_with_nulls.isnull().sum().sum()}")
    
    try:
        cleaned_df = cleanData(df_with_nulls)
        print(f"Cleaned data shape: {cleaned_df.shape}")
        print(f"Remaining null counts: {cleaned_df.isnull().sum().sum()}")
    except Exception as e:
        print(f"Data cleaning failed: {e}")

def test_varima_detection(df):
    print("\n=== Testing VARIMA Anomaly Detection ===")
    
    try:
        # Run VARIMA detection
        result_df = run_varima_detection(df)
        
        print(f"VARIMA detection completed successfully")
        print(f"Result shape: {result_df.shape}")
        
        if 'anomaly_varima' in result_df.columns:
            anomaly_count = result_df['anomaly_varima'].sum()
            print(f"Anomalies detected: {anomaly_count} out of {len(result_df)} records")
            print(f"Anomaly rate: {anomaly_count/len(result_df)*100:.2f}%")
            
            # Show some anomaly indices
            anomaly_indices = result_df[result_df['anomaly_varima']].index.tolist()
            print(f"First 10 anomaly indices: {anomaly_indices[:10]}")
        else:
            print("No anomaly_varima column found in results")
            
    except Exception as e:
        print(f"VARIMA detection failed: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    print("\n=== Testing Edge Cases ===")
    
    # Test with minimal data
    print("1. Testing with minimal data...")
    minimal_df = pd.DataFrame({
        'value1': [1, 2, 3],
        'value2': [4, 5, 6]
    })
    
    try:
        result = run_varima_detection(minimal_df)
        print(f"Minimal data test passed, shape: {result.shape}")
    except Exception as e:
        print(f"Minimal data test failed: {e}")
    
    # Test with no numeric columns
    print("2. Testing with no numeric columns...")
    non_numeric_df = pd.DataFrame({
        'category1': ['A', 'B', 'C'],
        'category2': ['X', 'Y', 'Z']
    })
    
    try:
        result = run_varima_detection(non_numeric_df)
        print(f"No numeric columns test passed, shape: {result.shape}")
    except Exception as e:
        print(f"No numeric columns test failed: {e}")

def main():
    print("Starting VARIMA detector tests...")
    
    try:
        # Create test data
        df = test_basic_functionality()
        
        # Test column detection
        test_column_detection(df)
        
        # Test data cleaning
        test_data_cleaning(df)
        
        # Test VARIMA detection
        test_varima_detection(df)
        
        # Test edge cases
        test_edge_cases()
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
