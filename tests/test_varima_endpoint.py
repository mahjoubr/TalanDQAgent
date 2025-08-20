import requests
import json

def test_varima_endpoint():
    """Test the auto-varima-all-tables endpoint that's failing"""
    print("=== Testing VARIMA API Endpoint ===")
    
    # Test basic API connectivity
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✓ API Server accessible: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ API Server not accessible: {e}")
        return
    
    # Test the failing endpoint with a mock connection ID
    print("\n1. Testing auto-varima-all-tables endpoint...")
    try:
        # First create some test data and get a connection ID
        import pandas as pd
        import numpy as np
        
        # Create test CSV file
        np.random.seed(42)
        n = 100
        dates = pd.date_range(start='2023-01-01', periods=n, freq='H')
        
        test_df = pd.DataFrame({
            'timestamp': dates,
            'sales': np.random.randn(n).cumsum() + 1000,
            'orders': np.random.randn(n).cumsum() + 500,
            'visitors': np.random.randn(n) * 20 + 200,
            'category': np.random.choice(['A', 'B', 'C'], n)
        })
        
        test_file_path = "test_varima_api.csv"
        test_df.to_csv(test_file_path, index=False)
        
        # Upload the file to get a connection ID
        print("  - Uploading test file...")
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_data.csv', f, 'text/csv')}
            upload_response = requests.post("http://localhost:8000/api/connect/file", files=files)
        
        if upload_response.status_code == 200:
            connection_data = upload_response.json()
            connection_id = connection_data['data']['connection_id']
            print(f"  ✓ File uploaded, connection ID: {connection_id}")
            
            # Now test the VARIMA endpoint
            print("  - Testing VARIMA analysis...")
            payload = {"connection_id": connection_id}
            headers = {"Content-Type": "application/json"}
            
            varima_response = requests.post(
                "http://localhost:8000/api/analysis/auto-varima-all-tables",
                json=payload,
                headers=headers,
                timeout=60  # 60 second timeout
            )
            
            print(f"  Response status: {varima_response.status_code}")
            print(f"  Response headers: {dict(varima_response.headers)}")
            
            if varima_response.status_code == 200:
                result = varima_response.json()
                print("  ✓ VARIMA endpoint working successfully!")
                print(f"    - Anomaly rate: {result.get('combined_results', {}).get('anomaly_rate', 'N/A')}%")
                print(f"    - Risk level: {result.get('combined_results', {}).get('risk_level', 'N/A')}")
                print(f"    - Total anomalies: {result.get('combined_results', {}).get('total_anomalies', 'N/A')}")
            else:
                print(f"  ✗ VARIMA endpoint failed: {varima_response.status_code}")
                print(f"    Response text: {varima_response.text}")
                
        else:
            print(f"  ✗ File upload failed: {upload_response.status_code}")
            print(f"    Response: {upload_response.text}")
            
        # Cleanup
        import os
        try:
            os.remove(test_file_path)
        except:
            pass
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_varima_endpoint()
