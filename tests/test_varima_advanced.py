import pandas as pd
import numpy as np
from varima_detector import detect_varima_anomalies
import datetime

def test_varima_with_proper_data():
    """Test VARIMA with data that has proper numeric columns for analysis"""
    print("=== Testing VARIMA with Proper Numeric Data ===")
    
    # Create data with clear numeric patterns for VARIMA analysis
    np.random.seed(42)
    n = 200
    
    # Generate time series data with some patterns
    dates = pd.date_range(start='2023-01-01', periods=n, freq='H')
    
    # Create correlated numeric time series
    trend = np.linspace(0, 10, n)
    seasonal = 3 * np.sin(2 * np.pi * np.arange(n) / 24)  # Daily seasonality
    noise = np.random.normal(0, 0.5, n)
    
    value1 = trend + seasonal + noise
    value2 = 0.8 * value1 + np.random.normal(0, 0.3, n)  # Correlated with value1
    value3 = trend * 0.5 + np.random.normal(0, 0.4, n)   # Partially correlated
    
    # Add some anomalies
    anomaly_indices = [50, 75, 120, 150]
    for idx in anomaly_indices:
        value1[idx] += np.random.normal(5, 1)  # Positive anomalies
        value2[idx] += np.random.normal(-4, 1)  # Negative anomalies
        value3[idx] += np.random.normal(6, 1)   # Positive anomalies
    
    df = pd.DataFrame({
        'timestamp': dates,
        'sales_amount': value1,
        'order_count': value2,
        'customer_visits': value3,
        'store_id': ['store_' + str(i % 10) for i in range(n)],  # This should be detected as ID
        'is_weekend': np.random.choice([True, False], n),  # Boolean column
        'category': np.random.choice(['A', 'B', 'C'], n)  # Categorical
    })
    
    print(f"Created test dataframe with shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    
    # Run VARIMA detection
    result = detect_varima_anomalies(df)
    
    print(f"\nVARIMA detection result shape: {result.shape}")
    
    if 'anomaly_score' in result.columns:
        anomalies = result[result['anomaly_score'] > 0].shape[0]
        print(f"Anomalies detected: {anomalies} out of {len(result)} records")
        print(f"Anomaly rate: {anomalies/len(result)*100:.2f}%")
        
        # Show top anomalies
        top_anomalies = result.nlargest(5, 'anomaly_score')[['timestamp', 'sales_amount', 'order_count', 'customer_visits', 'anomaly_score']]
        print(f"\nTop 5 anomalies:")
        print(top_anomalies.to_string(index=False))
    else:
        print("No anomaly_score column found in result")
    
    return result

def test_varima_performance():
    """Test VARIMA performance with different data sizes"""
    print("\n=== Testing VARIMA Performance ===")
    
    sizes = [50, 100, 500]
    
    for size in sizes:
        print(f"\nTesting with {size} records...")
        
        # Generate synthetic data
        dates = pd.date_range(start='2023-01-01', periods=size, freq='H')
        
        df = pd.DataFrame({
            'timestamp': dates,
            'metric1': np.random.randn(size).cumsum() + 100,
            'metric2': np.random.randn(size).cumsum() + 50,
            'metric3': np.random.randn(size) * 10 + 75,
            'id_col': range(size)
        })
        
        import time
        start_time = time.time()
        result = detect_varima_anomalies(df)
        end_time = time.time()
        
        print(f"Processed {size} records in {end_time - start_time:.2f} seconds")
        print(f"Result shape: {result.shape}")

if __name__ == "__main__":
    print("Starting Advanced VARIMA Tests...\n")
    
    try:
        # Test with proper numeric data
        result1 = test_varima_with_proper_data()
        
        # Test performance
        test_varima_performance()
        
        print("\n=== Advanced VARIMA Tests Completed Successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
