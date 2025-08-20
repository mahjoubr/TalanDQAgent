import requests
import pandas as pd
import numpy as np

def debug_upload():
    """Debug the file upload endpoint response"""
    
    # Create simple test file
    test_df = pd.DataFrame({
        'sales': [100, 200, 150, 300, 250],
        'orders': [10, 20, 15, 30, 25],
        'visitors': [50, 100, 75, 150, 125]
    })
    
    test_file = 'debug_test.csv'
    test_df.to_csv(test_file, index=False)
    
    print("Testing file upload response format...")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/csv')}
            response = requests.post(
                "http://localhost:8000/api/connect/file",
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Raw Response: {response.text}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"JSON Response: {json_data}")
                print(f"Response Keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
            except:
                print("Could not parse as JSON")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        import os
        os.remove(test_file)
    except:
        pass

if __name__ == "__main__":
    debug_upload()
