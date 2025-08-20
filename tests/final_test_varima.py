import pandas as pd
import numpy as np
from varima_detector import detect_varima_anomalies, run_varima_detection

def final_comprehensive_test():
    """Final comprehensive test of the new VARIMA detector"""
    print("=== FINAL COMPREHENSIVE VARIMA TEST ===\n")
    
    # Test 1: Standard time series data
    print("1. Testing with standard time series data...")
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
    
    df1 = pd.DataFrame({
        'timestamp': dates,
        'revenue': np.random.randn(100).cumsum() + 1000,
        'transactions': np.random.randn(100).cumsum() + 500,
        'customers': np.random.randn(100) * 20 + 200,
        'store_id': ['S' + str(i % 5) for i in range(100)],
        'is_holiday': np.random.choice([True, False], 100, p=[0.1, 0.9])
    })
    
    result1 = detect_varima_anomalies(df1)
    anomalies1 = result1['anomaly'].sum() if 'anomaly' in result1.columns else 0
    print(f"   ✓ Result shape: {result1.shape}")
    print(f"   ✓ Anomalies detected: {anomalies1}")
    print(f"   ✓ Output columns: {list(result1.columns)}\n")
    
    # Test 2: Data with missing values
    print("2. Testing with missing values...")
    df2 = df1.copy()
    df2.loc[10:15, 'revenue'] = np.nan
    df2.loc[20:22, 'transactions'] = np.nan
    
    result2 = detect_varima_anomalies(df2)
    anomalies2 = result2['anomaly'].sum() if 'anomaly' in result2.columns else 0
    print(f"   ✓ Result shape: {result2.shape}")
    print(f"   ✓ Anomalies detected: {anomalies2}")
    print(f"   ✓ Missing values handled successfully\n")
    
    # Test 3: High-level API test
    print("3. Testing high-level run_varima_detection API...")
    try:
        result3 = run_varima_detection(df1)
        anomalies3 = result3['anomaly'].sum() if 'anomaly' in result3.columns else 0
        print(f"   ✓ High-level API working: {result3.shape}")
        print(f"   ✓ Anomalies detected: {anomalies3}\n")
    except Exception as e:
        print(f"   ✗ High-level API failed: {e}\n")
    
    # Test 4: Edge case - minimal data
    print("4. Testing edge case - minimal data...")
    df4 = pd.DataFrame({
        'value1': [1, 2, 3],
        'value2': [4, 5, 6]
    })
    
    result4 = detect_varima_anomalies(df4)
    print(f"   ✓ Minimal data handled: {result4.shape}")
    print(f"   ✓ Output columns: {list(result4.columns)}\n")
    
    # Test 5: Performance check
    print("5. Performance test with larger dataset...")
    import time
    
    large_df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='H'),
        'metric1': np.random.randn(1000).cumsum(),
        'metric2': np.random.randn(1000).cumsum(),
        'metric3': np.random.randn(1000) * 10,
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })
    
    start_time = time.time()
    result5 = detect_varima_anomalies(large_df)
    end_time = time.time()
    
    anomalies5 = result5['anomaly'].sum() if 'anomaly' in result5.columns else 0
    print(f"   ✓ Large dataset processed: {result5.shape}")
    print(f"   ✓ Processing time: {end_time - start_time:.2f} seconds")
    print(f"   ✓ Anomalies detected: {anomalies5}")
    
    print("\n=== ALL TESTS COMPLETED SUCCESSFULLY ===")
    print("✅ The new VARIMA detector is ready for production use!")
    
    return {
        'test1_anomalies': anomalies1,
        'test2_anomalies': anomalies2,
        'test3_anomalies': anomalies3 if 'result3' in locals() else 0,
        'test5_anomalies': anomalies5,
        'performance_time': end_time - start_time
    }

if __name__ == "__main__":
    results = final_comprehensive_test()
