
import os
import redis

# Initialize Redis client
redis_client = redis.Redis( host=os.getenv("LOCAL_DB_HOST", "localhost"),
    port=int(os.getenv("LOCAL_DB_PORT", "6379")),     
    db=int(os.getenv("LOCAL_DB_NUMBER", "0")), 
                           decode_responses=True)
print("Redis client initialized successfully.")