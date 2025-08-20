import requests
import json
import sys

def test_live_endpoint():
    """Test the live VARIMA endpoint with the servers running"""
    
    print("=== Testing Live VARIMA Endpoint ===")
    
    # Test server connectivity
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✓ Backend server accessible: {response.json()}")
    except Exception as e:
        print(f"✗ Backend server error: {e}")
        return False
    
    # Test a simple endpoint first
    try:
        test_response = requests.get("http://localhost:8000/api/test-store", timeout=5)
        print(f"✓ Test endpoint works: {test_response.json()}")
    except Exception as e:
        print(f"✗ Test endpoint error: {e}")
        return False
    
    # Test with a non-existent connection ID to see if the endpoint responds
    print("\n1. Testing endpoint with invalid connection ID...")
    try:
        payload = {"connection_id": "test-connection-123"}
        response = requests.post(
            "http://localhost:8000/api/analysis/auto-varima-all-tables",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code in [400, 404, 422]:
            # These are expected errors for invalid connection ID
            print("✓ Endpoint is responding (with expected error for invalid ID)")
            try:
                error_data = response.json()
                print(f"Error response: {error_data}")
            except:
                print(f"Error text: {response.text}")
        elif response.status_code == 500:
            print("⚠ Server error occurred")
            print(f"Error: {response.text}")
        else:
            print(f"Unexpected response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out - endpoint might be hanging")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error - server might not be running")
        return False
    except Exception as e:
        print(f"✗ Request error: {e}")
        return False
    
    print("\n=== Endpoint Test Complete ===")
    return True

if __name__ == "__main__":
    success = test_live_endpoint()
    sys.exit(0 if success else 1)
