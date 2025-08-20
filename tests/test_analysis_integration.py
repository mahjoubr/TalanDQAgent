import sys
import os
sys.path.append(os.getcwd())

from analysis import calculate_quality_metrics
from varima_detector import detect_varima_anomalies
from redis_client import redis_client
import pandas as pd
import numpy as np
import uuid
import json

def test_analysis_integration():
    """Test the analysis module integration with new VARIMA detector"""
    print("=== Testing Analysis Module Integration ===")
    
    # Create test data
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start='2023-01-01', periods=n, freq='H')
    trend = np.linspace(0, 10, n)
    seasonal = 3 * np.sin(2 * np.pi * np.arange(n) / 24)
    noise = np.random.normal(0, 0.5, n)
    
    value1 = trend + seasonal + noise
    value2 = 0.8 * value1 + np.random.normal(0, 0.3, n)
    value3 = trend * 0.5 + np.random.normal(0, 0.4, n)
    
    # Add anomalies
    anomaly_indices = [50, 75, 120, 150]
    for idx in anomaly_indices:
        value1[idx] += np.random.normal(5, 1)
        value2[idx] += np.random.normal(-4, 1)
        value3[idx] += np.random.normal(6, 1)
    
    test_df = pd.DataFrame({
        'timestamp': dates,
        'sales_revenue': value1,
        'order_count': value2,
        'customer_visits': value3,
        'store_id': ['store_' + str(i % 5) for i in range(n)],
        'is_weekend': np.random.choice([True, False], n),
        'category': np.random.choice(['A', 'B', 'C'], n)
    })
    
    print(f"✓ Test data created: {test_df.shape}")
    
    # Test quality metrics calculation
    print("\n1. Testing quality metrics...")
    try:
        quality_metrics = calculate_quality_metrics(test_df)
        print(f"✓ Quality metrics calculated successfully")
        print(f"  - Overall quality score: {quality_metrics['quality_score']:.2f}")
        print(f"  - Completeness: {quality_metrics['completeness']:.2f}%")
        print(f"  - Total columns: {quality_metrics['total_columns']}")
    except Exception as e:
        print(f"✗ Quality metrics failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test VARIMA anomaly detection directly
    print("\n2. Testing VARIMA anomaly detection...")
    try:
        varima_result = detect_varima_anomalies(test_df)
        print(f"✓ VARIMA analysis completed successfully")
        print(f"  - Result shape: {varima_result.shape}")
        print(f"  - Result columns: {list(varima_result.columns)}")
        
        if 'anomaly' in varima_result.columns:
            anomaly_count = varima_result['anomaly'].sum()
            anomaly_rate = (anomaly_count / len(varima_result)) * 100
            print(f"  - Anomalies detected: {anomaly_count}")
            print(f"  - Anomaly rate: {anomaly_rate:.2f}%")
            
            if anomaly_count > 0:
                print(f"✓ Successfully detected {anomaly_count} anomalies")
                # Show which records were flagged
                anomaly_indices = varima_result[varima_result['anomaly']].index.tolist()
                print(f"  - Anomaly indices: {anomaly_indices[:10]}...")  # Show first 10
            else:
                print("⚠ No anomalies detected")
        else:
            print("✗ No anomaly column found in result")
            
    except Exception as e:
        print(f"✗ VARIMA analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Redis connection (used for caching)
    print("\n3. Testing Redis integration...")
    try:
        test_key = f"test:{uuid.uuid4().hex[:8]}"
        test_data = {"test": True, "timestamp": pd.Timestamp.now().isoformat()}
        redis_client.setex(test_key, 60, json.dumps(test_data))
        
        retrieved = redis_client.get(test_key)
        if retrieved:
            parsed = json.loads(retrieved)
            print("✓ Redis caching working correctly")
            redis_client.delete(test_key)
        else:
            print("✗ Redis retrieval failed")
    except Exception as e:
        print(f"✗ Redis integration failed: {e}")
    
    print("\n=== Analysis Integration Test Complete ===")

if __name__ == "__main__":
    test_analysis_integration()
