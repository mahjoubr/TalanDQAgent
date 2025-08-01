#!/usr/bin/env python3

"""
Simple test script to verify the store connection endpoint logic works
"""

import json
from datetime import datetime

# Mock Redis client for testing
class MockRedisClient:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ex=None):
        self.data[key] = value
        print(f"Redis SET: {key} = {value}")

# Mock the DbStoreRequest
class DbStoreRequest:
    def __init__(self, email, connectionString):
        self.email = email
        self.connectionString = connectionString

def test_store_connection_logic():
    # Initialize mock redis
    redis_client = MockRedisClient()
    
    # Test data
    data = DbStoreRequest("test@example.com", "postgresql://test:test@localhost:5432/testdb")
    
    try:
        # Create a key for the user's connection strings
        redis_key = f"user_connections:{data.email}"
        
        # Get existing connections for this user (if any)
        existing_connections = redis_client.get(redis_key)
        
        if existing_connections:
            # Parse existing JSON data
            connections_data = json.loads(existing_connections)
        else:
            # Initialize new connections data structure
            connections_data = {
                "email": data.email,
                "connections": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Create new connection entry
        new_connection = {
            "connection_string": data.connectionString,
            "created_at": datetime.now().isoformat(),
            "connection_id": f"conn_{len(connections_data['connections']) + 1}_{int(datetime.now().timestamp())}"
        }
        
        # Add new connection to the list
        connections_data["connections"].append(new_connection)
        connections_data["updated_at"] = datetime.now().isoformat()
        
        print(f"Storing connection string for {connections_data}")
        
        # Store updated data in Redis
        redis_client.set(
            redis_key, 
            json.dumps(connections_data),
            ex=86400 * 30  # Expire after 30 days (optional)
        )

        print(f"Stored connection string for {data.email}: {data.connectionString}")

        result = {
            "success": True, 
            "message": "Connection string stored successfully",
            "connection_id": new_connection["connection_id"],
            "total_connections": len(connections_data["connections"])
        }
        
        print("SUCCESS:", result)
        return result
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }

if __name__ == "__main__":
    print("Testing store connection logic...")
    result = test_store_connection_logic()
    print("Final result:", result)
