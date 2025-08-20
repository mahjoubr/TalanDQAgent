import requests
import pandas as pd
import numpy as np
import json

def test_varima_api_integration():
    """Test the VARIMA API integration"""
    print("=== Testing VARIMA API Integration ===")
    
    # Test API root endpoint
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✓ API Server running: {response.json()}")
    except Exception as e:
        print(f"✗ API Server not accessible: {e}")
        return
    
    # Create test data file for analysis
    print("\n1. Creating test data...")
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start='2023-01-01', periods=n, freq='H')
    trend = np.linspace(0, 10, n)
    seasonal = 3 * np.sin(2 * np.pi * np.arange(n) / 24)
    noise = np.random.normal(0, 0.5, n)
    
    # Create correlated time series data
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
    
    # Save test file
    test_file_path = "c:/Users/Refka/Downloads/power-bi-dashboard-setup (2)/backend/test_api_data.csv"
    test_df.to_csv(test_file_path, index=False)
    print(f"✓ Test data saved: {test_df.shape}")
    
    # Test file upload
    print("\n2. Testing file upload...")
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_data.csv', f, 'text/csv')}
            response = requests.post("http://localhost:8000/api/connect/file", files=files)
            
        if response.status_code == 200:
            upload_result = response.json()
            connection_id = upload_result['data']['connection_id']
            print(f"✓ File uploaded successfully: {connection_id}")
        else:
            print(f"✗ File upload failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ File upload error: {e}")
        return
    
    # Test VARIMA analysis
    print("\n3. Testing VARIMA analysis endpoint...")
    try:
        payload = {"connection_id": connection_id}
        response = requests.post(
            "http://localhost:8000/api/analysis/auto-varima-all-tables",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            varima_result = response.json()
            print(f"✓ VARIMA analysis successful")
            print(f"  - Anomaly rate: {varima_result['combined_results']['anomaly_rate']}%")
            print(f"  - Risk level: {varima_result['combined_results']['risk_level']}")
            print(f"  - Total anomalies: {varima_result['combined_results']['total_anomalies']}")
            print(f"  - Total records: {varima_result['combined_results']['total_records']}")
            
            # Test cached results
            print("\n4. Testing cached VARIMA results...")
            cache_response = requests.get(f"http://localhost:8000/api/analysis/cached-varima-results/{connection_id}")
            
            if cache_response.status_code == 200:
                cached_result = cache_response.json()
                print("✓ Cached results retrieved successfully")
                print(f"  - Cached anomaly rate: {cached_result['combined_results']['anomaly_rate']}%")
            else:
                print(f"✗ Cached results failed: {cache_response.status_code}")
            
        else:
            print(f"✗ VARIMA analysis failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"✗ VARIMA analysis error: {e}")
    
    print("\n=== API Integration Test Complete ===")

if __name__ == "__main__":
    test_varima_api_integration()
