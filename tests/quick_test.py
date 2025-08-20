import requests
import json
import pandas as pd
import numpy as np

def quick_test():
    """Quick test of the VARIMA endpoint"""
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:8001/")
        print(f"Server running: {response.json()}")
    except Exception as e:
        print(f"Server not accessible: {e}")
        return
    
    # Create test data
    np.random.seed(42)
    test_df = pd.DataFrame({
        'sales': np.random.randn(50).cumsum() + 1000,
        'orders': np.random.randn(50).cumsum() + 500,
        'visitors': np.random.randn(50) * 20 + 200,
    })
    
    # Save and upload
    test_df.to_csv("quick_test.csv", index=False)
    
    with open("quick_test.csv", 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        upload_response = requests.post("http://localhost:8001/api/connect/file", files=files)
    
    if upload_response.status_code != 200:
        print(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
        return
    
    connection_id = upload_response.json()['data']['connection_id']
    print(f"Connection ID: {connection_id}")
    
    # Test VARIMA endpoint
    payload = {"connection_id": connection_id}
    try:
        varima_response = requests.post(
            "http://localhost:8001/api/analysis/auto-varima-all-tables",
            json=payload,
            timeout=30
        )
        
        print(f"VARIMA Response: {varima_response.status_code}")
        if varima_response.status_code == 200:
            result = varima_response.json()
            print(f"Success! Anomaly rate: {result.get('combined_results', {}).get('anomaly_rate', 'N/A')}%")
        else:
            print(f"Error: {varima_response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Cleanup
    import os
    try:
        os.remove("quick_test.csv")
    except:
        pass

if __name__ == "__main__":
    quick_test()
