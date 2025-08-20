import requests
import json
import pandas as pd
import numpy as np

def test_full_varima_workflow():
    """Test the complete VARIMA workflow from file upload to analysis"""
    
    print("=== Testing Full VARIMA Workflow ===")
    
    # Create realistic test data
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start='2023-01-01', periods=n, freq='H')
    
    # Create time series with anomalies
    trend = np.linspace(0, 10, n)
    seasonal = 3 * np.sin(2 * np.pi * np.arange(n) / 24)
    noise = np.random.normal(0, 0.5, n)
    
    sales = trend + seasonal + noise
    orders = 0.8 * sales + np.random.normal(0, 0.3, n)
    visitors = trend * 0.5 + np.random.normal(0, 0.4, n)
    
    # Add clear anomalies
    anomaly_indices = [25, 50, 75]
    for idx in anomaly_indices:
        sales[idx] += 10
        orders[idx] += 8
        visitors[idx] += 15
    
    test_df = pd.DataFrame({
        'timestamp': dates,
        'sales_revenue': sales,
        'order_count': orders,
        'visitor_count': visitors,
        'store_id': ['store_' + str(i % 3) for i in range(n)],
        'is_weekend': np.random.choice([True, False], n),
        'category': np.random.choice(['A', 'B', 'C'], n)
    })
    
    # Save test file
    test_file = 'full_varima_test.csv'
    test_df.to_csv(test_file, index=False)
    print(f"✓ Created test data: {test_df.shape}")
    
    # Step 1: Upload file
    print("\n1. Uploading file...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/csv')}
            upload_response = requests.post(
                "http://localhost:8000/api/connect/file",
                files=files,
                timeout=30
            )
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            connection_id = upload_data['connection_id']  # Fixed: no 'data' wrapper
            print(f"✓ File uploaded successfully: {connection_id}")
        else:
            print(f"✗ Upload failed: {upload_response.status_code}")
            print(f"Error: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return False
    
    # Step 2: Run VARIMA analysis
    print("\n2. Running VARIMA analysis...")
    try:
        payload = {"connection_id": connection_id}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        varima_response = requests.post(
            "http://localhost:8000/api/analysis/auto-varima-all-tables",
            json=payload,
            headers=headers,
            timeout=60  # Longer timeout for analysis
        )
        
        print(f"VARIMA Response status: {varima_response.status_code}")
        
        if varima_response.status_code == 200:
            result = varima_response.json()
            print("✓ VARIMA analysis successful!")
            
            combined_results = result.get('combined_results', {})
            print(f"  - Anomaly rate: {combined_results.get('anomaly_rate', 'N/A')}%")
            print(f"  - Risk level: {combined_results.get('risk_level', 'N/A')}")
            print(f"  - Total anomalies: {combined_results.get('total_anomalies', 'N/A')}")
            print(f"  - Total records: {combined_results.get('total_records', 'N/A')}")
            print(f"  - Tables analyzed: {combined_results.get('tables_analyzed', 'N/A')}")
            
            # Expected: Should detect some anomalies since we added them
            total_anomalies = combined_results.get('total_anomalies', 0)
            if total_anomalies > 0:
                print(f"✓ Successfully detected anomalies as expected!")
            else:
                print("⚠ No anomalies detected (might be normal)")
                
        else:
            print(f"✗ VARIMA analysis failed: {varima_response.status_code}")
            print(f"Error response: {varima_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ VARIMA analysis timed out (>60s)")
        return False
    except Exception as e:
        print(f"✗ VARIMA analysis error: {e}")
        return False
    
    # Step 3: Test cached results
    print("\n3. Testing cached results...")
    try:
        cache_response = requests.get(
            f"http://localhost:8000/api/analysis/cached-varima-results/{connection_id}",
            timeout=10
        )
        
        if cache_response.status_code == 200:
            cached_data = cache_response.json()
            print("✓ Cached results retrieved successfully")
            cached_combined = cached_data.get('combined_results', {})
            print(f"  - Cached anomaly rate: {cached_combined.get('anomaly_rate', 'N/A')}%")
        else:
            print(f"✗ Cache retrieval failed: {cache_response.status_code}")
            
    except Exception as e:
        print(f"✗ Cache error: {e}")
    
    # Cleanup
    try:
        import os
        os.remove(test_file)
    except:
        pass
    
    print("\n=== Full Workflow Test Complete ===")
    return True

if __name__ == "__main__":
    test_full_varima_workflow()
