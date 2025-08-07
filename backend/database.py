"""
Database connection and management utilities
"""
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
import pymysql
import pyodbc
from typing import Dict, Any, List
from fastapi import HTTPException
import uuid
import json

from models import DatabaseConnection
from redis_client import redis_client


def clean_numeric(value):
    """Clean numeric values for JSON serialization"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        if pd.isna(value) or not pd.isfinite(value):
            return None
        return float(value)
    return value


def create_connection_string(db_type: str, connection: DatabaseConnection) -> str:
    """Create database connection string based on database type"""
    if db_type == "postgresql":
        return f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
    elif db_type == "sqlserver":
        return f"mssql+pyodbc://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported database type: {db_type}")


def test_database_connection(connection: DatabaseConnection) -> Dict[str, Any]:
    """Test database connection and return connection info"""
    try:
        connection_string = create_connection_string(connection.db_type, connection)
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        # Get table count
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        connection_id = str(uuid.uuid4())
        
        # Store connection info in Redis
        connection_info = {
            "id": connection_id,
            "type": "database",
            "db_type": connection.db_type,
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "username": connection.username,
            "password": connection.password,  # In production, encrypt this
            "table_count": len(tables),
            "tables": tables[:10],  # Store first 10 table names
            "status": "connected"
        }
        
        redis_client.setex(f"connection:{connection_id}", 3600, json.dumps(connection_info))
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": f"Successfully connected to {connection.db_type} database",
            "database_name": connection.database,
            "table_count": len(tables),
            "tables": tables[:10]
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def get_connection_info(connection_id: str) -> Dict[str, Any]:
    """Get connection information from Redis"""
    try:
        connection_data = redis_client.get(f"connection:{connection_id}")
        if not connection_data:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        return json.loads(connection_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid connection data")


def get_database_engine(connection_id: str):
    """Get SQLAlchemy engine for a connection"""
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] != "database":
        raise HTTPException(status_code=400, detail="Not a database connection")
    
    connection_string = create_connection_string(
        connection_info["db_type"], 
        DatabaseConnection(
            host=connection_info["host"],
            port=connection_info["port"],
            username=connection_info["username"],
            password=connection_info["password"],
            database=connection_info["database"],
            db_type=connection_info["db_type"]
        )
    )
    
    return create_engine(connection_string)


def get_table_list(connection_id: str) -> List[str]:
    """Get list of tables for a database connection"""
    try:
        engine = get_database_engine(connection_id)
        inspector = inspect(engine)
        return inspector.get_table_names()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


def get_table_data(connection_id: str, table_name: str, limit: int = 1000) -> pd.DataFrame:
    """Get data from a specific table"""
    try:
        engine = get_database_engine(connection_id)
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return pd.read_sql(query, engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table data: {str(e)}")


def disconnect_database(connection_id: str) -> Dict[str, Any]:
    """Disconnect database and clean up resources"""
    try:
        # Remove from Redis
        redis_client.delete(f"connection:{connection_id}")
        
        # Clean up any cached analysis results
        redis_client.delete(f"analysis:{connection_id}")
        redis_client.delete(f"varima:{connection_id}")
        
        return {"success": True, "message": "Database disconnected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")
