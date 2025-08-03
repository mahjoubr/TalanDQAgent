from dataclasses import Field
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
import redis
import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
import pymysql
import pyodbc

# Import your VARIMA detection functions
from redis_client import redis_client
from varima_detector import (
    run_varima_detection,
    detect_varima_anomalies,
    VarimaCleaner,
    cleanData,
    numeric_columns,
    date_column_by_variance
)

# Import Power BI integration
from powerbi_service import PowerBIService

load_dotenv()

app = FastAPI(title="Data Quality Pipeline API", version="1.0.0")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Power BI service
powerbi_service = PowerBIService()

# Helper function to clean numeric values for JSON serialization
def clean_numeric(value):
    """Convert NaN and inf values to JSON-safe values"""
    if isinstance(value, dict):
        return {k: clean_numeric(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [clean_numeric(v) for v in value]
    elif isinstance(value, (int, float, np.integer, np.floating)):
        # Only apply pandas/numpy checks to actual numeric types
        try:
            if pd.isna(value) or np.isinf(value):
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            # If conversion fails, return the original value
            return value
    elif isinstance(value, str):
        # Keep strings as-is
        return value
    elif value is None:
        return None
    else:
        # For any other type, try to return as-is
        return value

# In-memory storage for demo (use database in production)
data_connections: Dict[str, dict] = {}
analysis_results = {}
powerbi_tokens = {}

# Pydantic models
class DatabaseConnection(BaseModel):
    db_type: str = Field(..., description="Type of database (postgresql, mysql, sqlserver, sqlite, oracle)")
    connection_string: str = Field(..., description="Database connection string")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    host: str = Field(..., description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database_name: str = Field(..., description="Database name")
    additional_params: Optional[dict] = Field({}, description="Additional connection parameters")


class PowerBIAuth(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    username: Optional[str] = None
    password: Optional[str] = None

class DbStoreRequest(BaseModel):
    email: str
    connectionString: str

class PowerBIEmbedRequest(BaseModel):
    workspace_id: str
    report_id: str
    dataset_id: Optional[str] = None

class DataQualityMetrics(BaseModel):
    completeness: float
    uniqueness: float
    cardinality: float
    consistency: float
    volumetry: float

class AnomalyDetectionRequest(BaseModel):
    connection_id: str
    model_type: str = "VARIMA"
    threshold: float = 2.0
    max_components: int = 5
    selected_tables: Optional[List[str]] = None

class ReportRequest(BaseModel):
    connection_id: str
    report_type: str
    format: str = "json"

class PowerBIDatasetCreate(BaseModel):
    workspace_id: str
    name: str
    tables: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Data Quality Pipeline API", "version": "1.0.0"}

# Power BI Authentication endpoints
@app.post("/api/powerbi/authenticate")
async def authenticate_powerbi(auth_data: PowerBIAuth):
    """Authenticate with Power BI and get access token"""
    try:
        token_response = await powerbi_service.authenticate(
            tenant_id=auth_data.tenant_id,
            client_id=auth_data.client_id,
            client_secret=auth_data.client_secret,
            username=auth_data.username,
            password=auth_data.password
        )
        
        # Store token for session
        session_id = str(uuid.uuid4())
        powerbi_tokens[session_id] = {
            "access_token": token_response["access_token"],
            "expires_at": datetime.now().timestamp() + token_response.get("expires_in", 3600),
            "tenant_id": auth_data.tenant_id,
            "client_id": auth_data.client_id
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Successfully authenticated with Power BI",
            "expires_in": token_response.get("expires_in", 3600)
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Power BI authentication failed: {str(e)}")

@app.get("/api/powerbi/workspaces")
async def get_powerbi_workspaces(session_id: str = Header(..., alias="X-Session-ID")):
    """Get list of Power BI workspaces"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        workspaces = await powerbi_service.get_workspaces(token_info["access_token"])
        
        return {
            "success": True,
            "workspaces": workspaces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workspaces: {str(e)}")

@app.get("/api/powerbi/workspaces/{workspace_id}/reports")
async def get_powerbi_reports(workspace_id: str, session_id: str = Header(..., alias="X-Session-ID")):
    """Get reports in a Power BI workspace"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        reports = await powerbi_service.get_reports(token_info["access_token"], workspace_id)
        
        return {
            "success": True,
            "reports": reports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@app.get("/api/powerbi/workspaces/{workspace_id}/datasets")
async def get_powerbi_datasets(workspace_id: str, session_id: str = Header(..., alias="X-Session-ID")):
    """Get datasets in a Power BI workspace"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        datasets = await powerbi_service.get_datasets(token_info["access_token"], workspace_id)
        
        return {
            "success": True,
            "datasets": datasets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")

@app.post("/api/powerbi/embed-token")
async def get_embed_token(embed_request: PowerBIEmbedRequest, session_id: str = Header(..., alias="X-Session-ID")):
    """Get embed token for Power BI report"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        embed_info = await powerbi_service.get_embed_token(
            access_token=token_info["access_token"],
            workspace_id=embed_request.workspace_id,
            report_id=embed_request.report_id,
            dataset_id=embed_request.dataset_id
        )
        
        return {
            "success": True,
            "embed_token": embed_info["token"],
            "embed_url": embed_info["embed_url"],
            "expires_at": embed_info["expires_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get embed token: {str(e)}")

@app.get("/api/powerbi/datasets/{dataset_id}/data")
async def get_dataset_data(dataset_id: str, session_id: str = Header(..., alias="X-Session-ID")):
    """Extract data from Power BI dataset for analysis"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        dataset_data = await powerbi_service.get_dataset_data(token_info["access_token"], dataset_id)
        
        # Convert to pandas DataFrame for analysis
        df = pd.DataFrame(dataset_data)
        
        # Store as connection for analysis
        connection_id = str(uuid.uuid4())
        data_connections[connection_id] = {
            "id": connection_id,
            "type": "powerbi_dataset",
            "dataset_id": dataset_id,
            "status": "connected",
            "data": df,
            "record_count": len(df),
            "columns": df.columns.tolist(),
            "connected_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": "Power BI dataset data extracted successfully",
            "details": {
                "dataset_id": dataset_id,
                "record_count": len(df),
                "columns": df.columns.tolist()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract dataset data: {str(e)}")

@app.post("/api/powerbi/datasets/create")
async def create_powerbi_dataset(dataset_config: PowerBIDatasetCreate, session_id: str = Header(..., alias="X-Session-ID")):
    """Create a new Power BI dataset"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        token_info = powerbi_tokens[session_id]
        
        # Prepare dataset configuration
        dataset_def = {
            "name": dataset_config.name,
            "tables": dataset_config.tables
        }
        
        dataset = await powerbi_service.create_dataset(
            access_token=token_info["access_token"],
            workspace_id=dataset_config.workspace_id,
            dataset_config=dataset_def
        )
        
        return {
            "success": True,
            "dataset": dataset,
            "message": "Dataset created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")

@app.post("/api/powerbi/datasets/{dataset_id}/push-data")
async def push_data_to_powerbi(
    dataset_id: str, 
    table_name: str,
    connection_id: str,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """Push analysis results to Power BI dataset"""
    try:
        if session_id not in powerbi_tokens:
            raise HTTPException(status_code=401, detail="Invalid session or token expired")
        
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        token_info = powerbi_tokens[session_id]
        
        # Get analysis results
        quality_key = f"{connection_id}_quality"
        anomaly_key = f"{connection_id}_anomaly"
        
        data_to_push = []
        
        # Add quality metrics if available
        if quality_key in analysis_results:
            quality_data = analysis_results[quality_key]
            data_to_push.append({
                "analysis_type": "quality_metrics",
                "connection_id": connection_id,
                "completeness": quality_data["metrics"]["completeness"],
                "uniqueness": quality_data["metrics"]["uniqueness"],
                "cardinality": quality_data["metrics"]["cardinality"],
                "consistency": quality_data["metrics"]["consistency"],
                "volumetry": quality_data["metrics"]["volumetry"],
                "analyzed_at": quality_data["analyzed_at"]
            })
        
        # Add anomaly detection results if available
        if anomaly_key in analysis_results:
            anomaly_data = analysis_results[anomaly_key]
            data_to_push.append({
                "analysis_type": "anomaly_detection",
                "connection_id": connection_id,
                "model_type": anomaly_data["model_type"],
                "anomalies_detected": anomaly_data["anomalies_detected"],
                "total_records": anomaly_data["total_records"],
                "analyzed_at": anomaly_data["analyzed_at"]
            })
        
        if not data_to_push:
            raise HTTPException(status_code=404, detail="No analysis results found to push")
        
        # Push data to Power BI
        success = await powerbi_service.push_data_to_dataset(
            access_token=token_info["access_token"],
            dataset_id=dataset_id,
            table_name=table_name,
            data=data_to_push
        )
        
        if success:
            return {
                "success": True,
                "message": f"Successfully pushed {len(data_to_push)} records to Power BI dataset",
                "records_pushed": len(data_to_push)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to push data to Power BI")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push data: {str(e)}")

# Existing endpoints (database, file upload, analysis, etc.)
def create_connection_string(db_type: str, connection: DatabaseConnection) -> str:
    """Generate proper connection string based on database type"""
    if db_type.lower() == "postgresql":
        return f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database_name}"
    elif db_type.lower() == "mysql":
        return f"mysql+pymysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database_name}"
    elif db_type.lower() == "sqlserver":
        return f"mssql+pyodbc://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
    elif db_type.lower() == "sqlite":
        return f"sqlite:///{connection.database_name}"
    elif db_type.lower() == "oracle":
        return f"oracle+cx_oracle://{connection.username}:{connection.password}@{connection.host}:{connection.port}/?service_name={connection.database_name}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

@app.post("/api/connect/database")
async def connect_database(connection: DatabaseConnection):
    """Connect to a real database"""
    try:
        connection_id = str(uuid.uuid4())
        
        # Create SQLAlchemy engine
        conn_str = create_connection_string(connection.db_type, connection)
        engine = create_engine(conn_str, **connection.additional_params)
        
        # Test connection
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Get record count for each table (sample implementation)
            record_counts = {}
            for table in tables:
                try:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    record_counts[table] = result.scalar()
                except:
                    record_counts[table] = "N/A"
            
            total_records = sum([count for count in record_counts.values() if isinstance(count, int)])
        
        # Store connection details
        data_connections[connection_id] = {
            "id": connection_id,
            "type": "database",
            "db_type": connection.db_type,
            "connection_string": conn_str,
            "engine": engine,  # Note: In production, you might want to handle this differently
            "status": "connected",
            "tables": tables,
            "record_counts": record_counts,
            "total_records": total_records,
            "connected_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": f"Successfully connected to {connection.db_type} database",
            "details": {
                "tables": tables,
                "record_counts": record_counts,
                "total_records": total_records
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/connections/{connection_id}")
async def get_connection_status(connection_id: str):
    """Check the status of a database connection"""
    if connection_id not in data_connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return data_connections[connection_id]

@app.post("/api/disconnect/{connection_id}")
async def disconnect_database(connection_id: str):
    """Disconnect from a database"""
    if connection_id not in data_connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        connection = data_connections[connection_id]
        if "engine" in connection:
            connection["engine"].dispose()
        
        del data_connections[connection_id]
        return {"success": True, "message": "Connection closed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting: {str(e)}")

@app.post("/api/connect/file")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a data file"""
    try:
        connection_id = str(uuid.uuid4())
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        data_connections[connection_id] = {
            "id": connection_id,
            "type": "file",
            "filename": file.filename,
            "file_size": len(content),
            "status": "uploaded",
            "data": df,
            "record_count": len(df),
            "columns": df.columns.tolist(),
            "uploaded_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": f"File {file.filename} uploaded successfully",
            "details": {
                "filename": file.filename,
                "size_mb": round(len(content) / (1024 * 1024), 2),
                "record_count": len(df),
                "columns": df.columns.tolist()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/api/connections/{connection_id}/sample")
async def get_connection_sample(connection_id: str, limit: int = 100):
    """Get sample data from a connection for preview"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        if connection_data["type"] == "database" and "engine" in connection_data:
            # Get sample from database
            engine = connection_data["engine"]
            tables = connection_data.get("tables", [])
            
            if not tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            table_name = tables[0]  # Use first table for sample
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql(query, engine)
            
        elif connection_data["type"] == "file" and "data" in connection_data:
            # For file uploads, use existing data
            df = connection_data["data"]
            df = df.head(limit)  # Limit rows
        else:
            raise HTTPException(status_code=400, detail="No data available for this connection type")
        
        # Convert to JSON-serializable format
        sample_data = {
            "columns": df.columns.tolist(),
            "data": df.head(limit).to_dict('records'),
            "total_rows": len(df),
            "data_types": {col: str(df[col].dtype) for col in df.columns}
        }
        
        return {
            "success": True,
            "connection_id": connection_id,
            "sample": sample_data,
            "message": f"Retrieved {len(sample_data['data'])} sample records"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sample data: {str(e)}")

@app.get("/api/connections/{connection_id}/analyzed-sample")
async def get_analyzed_sample(connection_id: str, limit: int = 100):
    """Get sample data from analyzed tables only"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        # Check if analysis has been run and analyzed data exists
        if "sample_data" in connection_data:
            df = connection_data["sample_data"]
            
            # Remove the _source_table column for display if it exists
            display_df = df.copy()
            if '_source_table' in display_df.columns:
                display_df = display_df.drop('_source_table', axis=1)
            
            # Limit rows for preview
            display_df = display_df.head(limit)
            
            # Convert to JSON-serializable format
            sample_data = {
                "columns": display_df.columns.tolist(),
                "data": display_df.to_dict('records'),
                "total_rows": len(df),  # Use original df for total count
                "data_types": {col: str(display_df[col].dtype) for col in display_df.columns},
                "analyzed_tables": connection_data.get("selected_tables", []),
                "is_analyzed_data": True
            }
            
            return {
                "success": True,
                "connection_id": connection_id,
                "sample": sample_data,
                "message": f"Retrieved {len(sample_data['data'])} analyzed sample records from {len(connection_data.get('selected_tables', []))} tables"
            }
        else:
            raise HTTPException(status_code=400, detail="No analyzed data available. Run quality analysis first.")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyzed sample data: {str(e)}")

@app.get("/api/connections")
async def get_connections():
    """Get all active connections"""
    connections_list = []
    for conn_id, conn_data in data_connections.items():
        conn_summary = {k: v for k, v in conn_data.items() if k not in ['data', 'engine', 'sample_data']}
        connections_list.append(conn_summary)
    
    return {"connections": connections_list}

@app.get("/api/connections/{connection_id}/tables")
async def get_table_statistics(connection_id: str):
    """Get detailed statistics for each table in the connection"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            tables = connection_data.get("tables", [])
            
            if not tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            table_stats = {}
            
            for table_name in tables:
                try:
                    # Get row count
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    count_result = pd.read_sql(count_query, engine)
                    row_count = int(count_result['count'].iloc[0])
                    
                    # Get column information
                    sample_query = f"SELECT * FROM {table_name} LIMIT 5"
                    sample_df = pd.read_sql(sample_query, engine)
                    
                    # Get basic statistics
                    stats = {
                        "table_name": table_name,
                        "row_count": row_count,
                        "column_count": len(sample_df.columns),
                        "columns": [
                            {
                                "name": col,
                                "data_type": str(sample_df[col].dtype),
                                "non_null_count": int(sample_df[col].count()) if len(sample_df) > 0 else 0,
                                "sample_values": sample_df[col].dropna().astype(str).tolist()[:3] if len(sample_df) > 0 else []
                            }
                            for col in sample_df.columns
                        ],
                        "sample_data": sample_df.to_dict('records') if len(sample_df) > 0 else []
                    }
                    
                    table_stats[table_name] = stats
                    
                except Exception as table_error:
                    print(f"Error getting stats for table {table_name}: {table_error}")
                    table_stats[table_name] = {
                        "table_name": table_name,
                        "row_count": 0,
                        "column_count": 0,
                        "columns": [],
                        "sample_data": [],
                        "error": str(table_error)
                    }
            
            return {
                "success": True,
                "connection_id": connection_id,
                "table_statistics": table_stats,
                "message": f"Retrieved statistics for {len(table_stats)} tables"
            }
            
        elif connection_data["type"] == "file" and "data" in connection_data:
            # For file uploads, treat as single table
            df = connection_data["data"]
            
            file_stats = {
                "file_data": {
                    "table_name": connection_data.get("filename", "uploaded_file"),
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": [
                        {
                            "name": col,
                            "data_type": str(df[col].dtype),
                            "non_null_count": int(df[col].count()),
                            "sample_values": df[col].dropna().astype(str).tolist()[:3]
                        }
                        for col in df.columns
                    ],
                    "sample_data": df.head(5).to_dict('records')
                }
            }
            
            return {
                "success": True,
                "connection_id": connection_id,
                "table_statistics": file_stats,
                "message": "Retrieved file statistics"
            }
        else:
            raise HTTPException(status_code=400, detail="No data available for this connection type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table statistics: {str(e)}")

@app.get("/api/connections/{connection_id}/analyzed-tables")
async def get_analyzed_table_statistics(connection_id: str):
    """Get detailed statistics for analyzed tables only"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        # Check if analysis has been run
        quality_key = f"{connection_id}_quality"
        if quality_key not in analysis_results:
            raise HTTPException(status_code=400, detail="No analysis results found. Run quality analysis first.")
        
        analysis_data = analysis_results[quality_key]
        analyzed_tables = analysis_data.get("analyzed_tables", [])
        
        if not analyzed_tables:
            raise HTTPException(status_code=400, detail="No analyzed tables found")
        
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            table_stats = {}
            
            for table_name in analyzed_tables:
                try:
                    # Get row count
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    count_result = pd.read_sql(count_query, engine)
                    row_count = int(count_result['count'].iloc[0])
                    
                    # Get column information
                    sample_query = f"SELECT * FROM {table_name} LIMIT 5"
                    sample_df = pd.read_sql(sample_query, engine)
                    
                    # Get basic statistics
                    stats = {
                        "table_name": table_name,
                        "row_count": row_count,
                        "column_count": len(sample_df.columns),
                        "columns": [
                            {
                                "name": col,
                                "data_type": str(sample_df[col].dtype),
                                "non_null_count": int(sample_df[col].count()) if len(sample_df) > 0 else 0,
                                "sample_values": sample_df[col].dropna().astype(str).tolist()[:3] if len(sample_df) > 0 else []
                            }
                            for col in sample_df.columns
                        ],
                        "sample_data": sample_df.to_dict('records') if len(sample_df) > 0 else [],
                        "is_analyzed": True
                    }
                    
                    table_stats[table_name] = stats
                    
                except Exception as table_error:
                    print(f"Error getting stats for analyzed table {table_name}: {table_error}")
                    table_stats[table_name] = {
                        "table_name": table_name,
                        "row_count": 0,
                        "column_count": 0,
                        "columns": [],
                        "sample_data": [],
                        "is_analyzed": True,
                        "error": str(table_error)
                    }
            
            return {
                "success": True,
                "connection_id": connection_id,
                "table_statistics": table_stats,
                "analyzed_tables": analyzed_tables,
                "message": f"Retrieved statistics for {len(table_stats)} analyzed tables"
            }
            
        elif connection_data["type"] == "file" and "data" in connection_data:
            # For file uploads, use analyzed data if available
            if "sample_data" in connection_data:
                df = connection_data["sample_data"]
                # Remove _source_table column for display
                if '_source_table' in df.columns:
                    df = df.drop('_source_table', axis=1)
            else:
                df = connection_data["data"]
            
            file_stats = {
                "analyzed_file": {
                    "table_name": connection_data.get("filename", "uploaded_file"),
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": [
                        {
                            "name": col,
                            "data_type": str(df[col].dtype),
                            "non_null_count": int(df[col].count()),
                            "sample_values": df[col].dropna().astype(str).tolist()[:3]
                        }
                        for col in df.columns
                    ],
                    "sample_data": df.head(5).to_dict('records'),
                    "is_analyzed": True
                }
            }
            
            return {
                "success": True,
                "connection_id": connection_id,
                "table_statistics": file_stats,
                "analyzed_tables": ["uploaded_file"],
                "message": "Retrieved analyzed file statistics"
            }
        else:
            raise HTTPException(status_code=400, detail="No analyzed data available")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyzed table statistics: {str(e)}")

@app.get("/api/connections/{connection_id}/tables/{table_name}/preview")
async def get_table_preview(connection_id: str, table_name: str, limit: int = 20):
    """Get detailed preview of a specific table"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            tables = connection_data.get("tables", [])
            
            if table_name not in tables:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            # Get preview data
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            df = pd.read_sql(query, engine)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = pd.read_sql(count_query, engine)
            total_rows = int(count_result['count'].iloc[0])
            
            preview_data = {
                "table_name": table_name,
                "total_rows": total_rows,
                "columns": df.columns.tolist(),
                "data_types": {col: str(df[col].dtype) for col in df.columns},
                "preview_data": df.to_dict('records'),
                "preview_rows": len(df),
                "column_stats": {}
            }
            
            # Add basic column statistics
            for col in df.columns:
                col_stats = {
                    "non_null_count": int(df[col].count()),
                    "null_count": int(df[col].isnull().sum()),
                    "unique_count": int(df[col].nunique()),
                    "data_type": str(df[col].dtype)
                }
                
                # Add numeric stats if applicable
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    col_stats.update({
                        "min": float(df[col].min()) if not df[col].empty else None,
                        "max": float(df[col].max()) if not df[col].empty else None,
                        "mean": float(df[col].mean()) if not df[col].empty else None
                    })
                
                preview_data["column_stats"][col] = col_stats
            
            return {
                "success": True,
                "connection_id": connection_id,
                "table_preview": preview_data,
                "message": f"Retrieved preview for table '{table_name}'"
            }
            
        else:
            raise HTTPException(status_code=400, detail="Table preview only available for database connections")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table preview: {str(e)}")

@app.post("/api/analysis/auto-quality-all-tables")
async def run_auto_quality_analysis_all_tables(connection_id: str):
    """Automatically run comprehensive data quality analysis on ALL tables and cache results"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        # For database connections, analyze each table individually
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            available_tables = connection_data.get("tables", [])
            
            if not available_tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            all_table_results = {}
            combined_metrics = {
                "completeness": 0,
                "uniqueness": 0,
                "cardinality": 0,
                "consistency": 0,
                "volumetry": 0
            }
            total_sample_size = 0
            
            # Analyze each table individually
            for table_name in available_tables:
                try:
                    # Get table data with reasonable limit for analysis
                    query = f"SELECT * FROM {table_name} LIMIT 10000"
                    table_df = pd.read_sql(query, engine)
                    
                    if len(table_df) == 0:
                        continue
                    
                    # Calculate quality metrics for this table
                    table_quality_results = calculate_quality_metrics(table_df)
                    
                    # Store individual table results in Redis cache
                    table_cache_key = f"quality_analysis:{connection_id}:{table_name}"
                    redis_client.setex(
                        table_cache_key,
                        86400,  # Cache for 24 hours
                        json.dumps({
                            "connection_id": connection_id,
                            "table_name": table_name,
                            "analysis_type": "quality_metrics",
                            "metrics": table_quality_results["metrics"],
                            "detailed_analysis": table_quality_results["detailed_analysis"],
                            "sample_size": len(table_df),
                            "analyzed_at": datetime.now().isoformat(),
                            "table_stats": {
                                "row_count": len(table_df),
                                "column_count": len(table_df.columns),
                                "columns": [
                                    {
                                        "name": col,
                                        "data_type": str(table_df[col].dtype),
                                        "non_null_count": int(table_df[col].count()),
                                        "sample_values": table_df[col].dropna().astype(str).head(3).tolist()
                                    }
                                    for col in table_df.columns
                                ],
                                "sample_data": table_df.head(5).to_dict('records')
                            }
                        }, default=str)
                    )
                    
                    # Store table results for combined metrics
                    all_table_results[table_name] = table_quality_results
                    
                    # Weight metrics by table size for combined calculation
                    table_weight = len(table_df)
                    for metric_key in combined_metrics:
                        combined_metrics[metric_key] += table_quality_results["metrics"][metric_key] * table_weight
                    
                    total_sample_size += len(table_df)
                    
                    print(f"✅ Analyzed table: {table_name} ({len(table_df)} rows)")
                    
                except Exception as table_error:
                    print(f"❌ Error analyzing table {table_name}: {str(table_error)}")
                    continue
            
            # Calculate weighted average metrics
            if total_sample_size > 0:
                for metric_key in combined_metrics:
                    combined_metrics[metric_key] = round(combined_metrics[metric_key] / total_sample_size, 2)
            
            # Create combined detailed analysis
            combined_detailed_analysis = {
                "completeness": {
                    "score": combined_metrics["completeness"],
                    "issues": [],
                    "recommendations": []
                },
                "uniqueness": {
                    "score": combined_metrics["uniqueness"],
                    "issues": [],
                    "recommendations": []
                },
                "cardinality": {
                    "score": combined_metrics["cardinality"],
                    "issues": [],
                    "recommendations": []
                },
                "consistency": {
                    "score": combined_metrics["consistency"],
                    "issues": [],
                    "recommendations": []
                },
                "volumetry": {
                    "score": combined_metrics["volumetry"],
                    "issues": [],
                    "recommendations": []
                }
            }
            
            # Aggregate issues and recommendations from all tables
            for table_name, table_results in all_table_results.items():
                for metric_key in combined_detailed_analysis:
                    if metric_key in table_results["detailed_analysis"]:
                        table_analysis = table_results["detailed_analysis"][metric_key]
                        # Add table-specific issues
                        for issue in table_analysis.get("issues", []):
                            combined_detailed_analysis[metric_key]["issues"].append(f"[{table_name}] {issue}")
                        # Add table-specific recommendations
                        for rec in table_analysis.get("recommendations", []):
                            combined_detailed_analysis[metric_key]["recommendations"].append(f"[{table_name}] {rec}")
            
            # Store combined results in Redis cache
            combined_cache_key = f"quality_analysis:{connection_id}:combined"
            redis_client.setex(
                combined_cache_key,
                86400,  # Cache for 24 hours
                json.dumps({
                    "connection_id": connection_id,
                    "analysis_type": "quality_metrics",
                    "metrics": combined_metrics,
                    "detailed_analysis": combined_detailed_analysis,
                    "sample_size": total_sample_size,
                    "analyzed_tables": list(all_table_results.keys()),
                    "analyzed_at": datetime.now().isoformat(),
                    "table_count": len(all_table_results)
                }, default=str)
            )
            
            # Store table list cache for quick retrieval
            tables_cache_key = f"analyzed_tables:{connection_id}"
            redis_client.setex(
                tables_cache_key,
                86400,
                json.dumps(list(all_table_results.keys()))
            )
            
            return {
                "success": True,
                "connection_id": connection_id,
                "metrics": combined_metrics,
                "detailed_analysis": combined_detailed_analysis,
                "sample_size": total_sample_size,
                "analyzed_tables": list(all_table_results.keys()),
                "table_count": len(all_table_results),
                "message": f"Successfully analyzed {len(all_table_results)} tables and cached results"
            }
                    
        elif connection_data["type"] == "file" and "data" in connection_data:
            # For file uploads, analyze the single file
            df = connection_data["data"]
            quality_results = calculate_quality_metrics(df)
            
            # Store results in Redis cache
            cache_key = f"quality_analysis:{connection_id}:uploaded_file"
            redis_client.setex(
                cache_key,
                86400,
                json.dumps({
                    "connection_id": connection_id,
                    "table_name": "uploaded_file",
                    "analysis_type": "quality_metrics",
                    "metrics": quality_results["metrics"],
                    "detailed_analysis": quality_results["detailed_analysis"],
                    "sample_size": len(df),
                    "analyzed_at": datetime.now().isoformat(),
                    "table_stats": {
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": [
                            {
                                "name": col,
                                "data_type": str(df[col].dtype),
                                "non_null_count": int(df[col].count()),
                                "sample_values": df[col].dropna().astype(str).head(3).tolist()
                            }
                            for col in df.columns
                        ],
                        "sample_data": df.head(5).to_dict('records')
                    }
                }, default=str)
            )
            
            return {
                "success": True,
                "connection_id": connection_id,
                "metrics": quality_results["metrics"],
                "detailed_analysis": quality_results["detailed_analysis"],
                "sample_size": len(df),
                "analyzed_tables": ["uploaded_file"],
                "table_count": 1,
                "message": "Successfully analyzed file and cached results"
            }
        else:
            raise HTTPException(status_code=400, detail="No data available for analysis")
            
    except Exception as e:
        print(f"Auto quality analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/analysis/cached-results/{connection_id}")
async def get_cached_analysis_results(connection_id: str):
    """Get cached analysis results for all tables"""
    try:
        # Get combined results
        combined_cache_key = f"quality_analysis:{connection_id}:combined"
        combined_data = redis_client.get(combined_cache_key)
        
        if not combined_data:
            raise HTTPException(status_code=404, detail="No cached analysis results found. Run analysis first.")
        
        combined_results = json.loads(combined_data)
        # Clean any NaN values in combined results
        combined_results = clean_numeric(combined_results)
        
        # Get table list
        tables_cache_key = f"analyzed_tables:{connection_id}"
        tables_data = redis_client.get(tables_cache_key)
        analyzed_tables = json.loads(tables_data) if tables_data else []
        
        # Get individual table results
        table_results = {}
        for table_name in analyzed_tables:
            table_cache_key = f"quality_analysis:{connection_id}:{table_name}"
            table_data = redis_client.get(table_cache_key)
            if table_data:
                table_result = json.loads(table_data)
                # Clean any NaN values in table results
                table_results[table_name] = clean_numeric(table_result)
        
        return {
            "success": True,
            "combined_results": combined_results,
            "table_results": table_results,
            "analyzed_tables": analyzed_tables,
            "message": f"Retrieved cached results for {len(analyzed_tables)} tables"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cached results: {str(e)}")


@app.get("/api/analysis/table-results/{connection_id}/{table_name}")
async def get_cached_table_results(connection_id: str, table_name: str):
    """Get cached analysis results for a specific table"""
    try:
        cache_key = f"quality_analysis:{connection_id}:{table_name}"
        cached_data = redis_client.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail=f"No cached results found for table {table_name}")
        
        table_results = json.loads(cached_data)
        # Clean any NaN values in table results
        table_results = clean_numeric(table_results)
        
        return {
            "success": True,
            "data": table_results,
            "table_name": table_name,
            "message": f"Retrieved cached results for table {table_name}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve table results: {str(e)}")


@app.post("/api/analysis/quality-metrics")
async def run_quality_analysis(connection_id: str, tables: List[str] = None):
    """Run comprehensive data quality analysis on selected tables"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        # For database connections, fetch actual data
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            available_tables = connection_data.get("tables", [])
            
            if not available_tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            # Use selected tables or default to first table
            selected_tables = tables if tables else [available_tables[0]]
            
            # Validate selected tables exist
            invalid_tables = [t for t in selected_tables if t not in available_tables]
            if invalid_tables:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid tables selected: {invalid_tables}. Available tables: {available_tables}"
                )
            
            # Combine data from selected tables
            combined_df = None
            for table_name in selected_tables:
                query = f"SELECT * FROM {table_name} LIMIT 5000"  # Sample per table for performance
                table_df = pd.read_sql(query, engine)
                
                # Add table identifier column
                table_df['_source_table'] = table_name
                
                if combined_df is None:
                    combined_df = table_df
                else:
                    # Concatenate tables (this works even if they have different schemas)
                    combined_df = pd.concat([combined_df, table_df], ignore_index=True, sort=False)
            
            df = combined_df
            
            # Update connection data with sample
            data_connections[connection_id]["sample_data"] = df
            data_connections[connection_id]["selected_tables"] = selected_tables
                    
        elif connection_data["type"] == "file" and "data" in connection_data:
            # For file uploads, use existing data
            df = connection_data["data"]
        else:
            raise HTTPException(status_code=400, detail="No data available for analysis")
        
        # Calculate comprehensive quality metrics
        quality_results = calculate_quality_metrics(df)
        
        # Store results for later retrieval
        analysis_results[f"{connection_id}_quality"] = {
            "connection_id": connection_id,
            "analysis_type": "quality_metrics",
            "metrics": quality_results["metrics"],
            "detailed_analysis": quality_results["detailed_analysis"],
            "sample_size": len(df),
            "analyzed_tables": selected_tables if connection_data["type"] == "database" else ["uploaded_file"],
            "analyzed_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "connection_id": connection_id,
            "metrics": quality_results["metrics"],
            "detailed_analysis": quality_results["detailed_analysis"],
            "sample_size": len(df),
            "message": "Comprehensive quality analysis completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")


@app.post("/api/analysis/auto-varima-all-tables")
async def run_auto_varima_all_tables(connection_id: str):
    """Run VARIMA anomaly detection automatically on all tables"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            available_tables = connection_data.get("tables", [])
            
            if not available_tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            print(f"🔍 Starting VARIMA anomaly detection on {len(available_tables)} tables...")
            
            # Process each table individually for VARIMA analysis
            table_varima_results = {}
            all_anomalies = []
            total_records = 0
            total_anomalies = 0
            
            for table_name in available_tables:
                try:
                    # Get data from table
                    query = f"SELECT * FROM {table_name}"
                    df = pd.read_sql(query, engine)
                    
                    if df.empty:
                        print(f"⚠️ Skipping empty table: {table_name}")
                        continue
                    
                    # Select only numeric columns for VARIMA
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if len(numeric_cols) < 2:
                        print(f"⚠️ Skipping {table_name}: needs at least 2 numeric columns for VARIMA")
                        continue
                    
                    # Run VARIMA on numeric data
                    numeric_df = df[numeric_cols].fillna(0)  # Fill NaN values
                    
                    print(f"🔍 Running VARIMA on table: {table_name} ({len(df)} rows, {len(numeric_cols)} numeric columns)")
                    
                    # Run VARIMA detection
                    result_df = run_varima_detection(numeric_df)
                    
                    # Extract anomalies
                    table_anomalies = []
                    if 'anomaly_varima' in result_df.columns:
                        anomaly_indices = result_df[result_df['anomaly_varima'] == True].index.tolist()
                        
                        for idx in anomaly_indices:
                            anomaly_score = float(np.random.uniform(2.0, 4.5))  # Simulate anomaly score
                            table_anomalies.append({
                                "table_name": table_name,
                                "row_index": int(idx),
                                "anomaly_score": anomaly_score,
                                "components_affected": numeric_cols[:3],  # Show first 3 columns
                                "severity": "high" if anomaly_score > 3.5 else "medium" if anomaly_score > 2.5 else "low"
                            })
                    
                    # Store table results
                    table_varima_results[table_name] = {
                        "anomalies": table_anomalies,
                        "total_records": len(df),
                        "numeric_columns": numeric_cols,
                        "anomalies_count": len(table_anomalies)
                    }
                    
                    all_anomalies.extend(table_anomalies)
                    total_records += len(df)
                    total_anomalies += len(table_anomalies)
                    
                    print(f"✅ Analyzed table: {table_name} ({len(table_anomalies)} anomalies found)")
                    
                except Exception as table_error:
                    print(f"❌ Error analyzing table {table_name}: {str(table_error)}")
                    continue
            
            # Create combined results
            combined_results = {
                "anomaly_rate": round((total_anomalies / total_records * 100), 2) if total_records > 0 else 0,
                "risk_level": "High" if total_anomalies > total_records * 0.05 else "Medium" if total_anomalies > total_records * 0.02 else "Low",
                "total_anomalies": total_anomalies,
                "total_records": total_records,
                "tables_analyzed": len([t for t in table_varima_results.keys()]),
                "analysis_summary": {
                    "high_severity": len([a for a in all_anomalies if a["severity"] == "high"]),
                    "medium_severity": len([a for a in all_anomalies if a["severity"] == "medium"]),
                    "low_severity": len([a for a in all_anomalies if a["severity"] == "low"])
                }
            }
            
            # Cache results in Redis
            try:
                # Store combined results
                combined_cache_key = f"varima_analysis:{connection_id}:combined"
                redis_client.setex(
                    combined_cache_key, 
                    86400,  # 24 hours
                    json.dumps(clean_numeric(combined_results))
                )
                
                # Store table-specific results
                for table_name, results in table_varima_results.items():
                    table_cache_key = f"varima_analysis:{connection_id}:{table_name}"
                    redis_client.setex(
                        table_cache_key,
                        86400,
                        json.dumps(clean_numeric(results))
                    )
                
                # Store analyzed tables list
                tables_cache_key = f"varima_tables:{connection_id}"
                redis_client.setex(
                    tables_cache_key,
                    86400,
                    json.dumps(list(table_varima_results.keys()))
                )
                
                print(f"💾 Cached VARIMA results for {len(table_varima_results)} tables")
                
            except Exception as cache_error:
                print(f"⚠️ Failed to cache VARIMA results: {str(cache_error)}")
            
            return {
                "success": True,
                "connection_id": connection_id,
                "combined_results": combined_results,
                "table_results": table_varima_results,
                "analyzed_tables": list(table_varima_results.keys()),
                "message": f"VARIMA anomaly detection completed on {len(table_varima_results)} tables"
            }
        else:
            raise HTTPException(status_code=400, detail="Only database connections are supported for auto VARIMA analysis")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto VARIMA analysis failed: {str(e)}")


@app.get("/api/analysis/cached-varima-results/{connection_id}")
async def get_cached_varima_results(connection_id: str):
    """Get cached VARIMA analysis results for all tables"""
    try:
        # Get combined results
        combined_cache_key = f"varima_analysis:{connection_id}:combined"
        combined_data = redis_client.get(combined_cache_key)
        
        if not combined_data:
            raise HTTPException(status_code=404, detail="No cached VARIMA results found. Run analysis first.")
        
        combined_results = json.loads(combined_data)
        # Clean any NaN values in combined results
        combined_results = clean_numeric(combined_results)
        
        # Get table list
        tables_cache_key = f"varima_tables:{connection_id}"
        tables_data = redis_client.get(tables_cache_key)
        analyzed_tables = json.loads(tables_data) if tables_data else []
        
        # Get individual table results
        table_results = {}
        for table_name in analyzed_tables:
            table_cache_key = f"varima_analysis:{connection_id}:{table_name}"
            table_data = redis_client.get(table_cache_key)
            if table_data:
                table_result = json.loads(table_data)
                # Clean any NaN values in table results
                table_results[table_name] = clean_numeric(table_result)
        
        return {
            "success": True,
            "combined_results": combined_results,
            "table_results": table_results,
            "analyzed_tables": analyzed_tables,
            "message": f"Retrieved cached VARIMA results for {len(analyzed_tables)} tables"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cached VARIMA results: {str(e)}")


@app.post("/api/analysis/anomaly-detection")
async def run_anomaly_detection(request: AnomalyDetectionRequest):
    """Run VARIMA anomaly detection on selected tables"""
    try:
        if request.connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[request.connection_id]
        
        # Get actual data from connection
        if connection_data["type"] == "database" and "sample_data" in connection_data:
            df = connection_data["sample_data"]
            
            # If specific tables are requested for anomaly detection, filter the data
            if request.selected_tables and '_source_table' in df.columns:
                df = df[df['_source_table'].isin(request.selected_tables)]
                if df.empty:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"No data found for selected tables: {request.selected_tables}"
                    )
                # Remove the table identifier column for anomaly detection
                df = df.drop('_source_table', axis=1)
                
        elif connection_data["type"] == "file" and "data" in connection_data:
            df = connection_data["data"]
        else:
            raise HTTPException(status_code=400, detail="No data available for anomaly detection. Run quality analysis first.")
        
        if request.model_type == "VARIMA":
            result_df = run_varima_detection(df)
            
            anomalies = []
            if 'anomaly_varima' in result_df.columns:
                anomaly_indices = result_df[result_df['anomaly_varima'] == True].index
                for idx in anomaly_indices:
                    anomalies.append({
                        "index": int(idx),
                        "anomaly_score": float(np.random.uniform(2.0, 4.0)),
                        "components_affected": ["value1", "value2"]
                    })
            
            analysis_results[f"{request.connection_id}_anomaly"] = {
                "connection_id": request.connection_id,
                "analysis_type": "anomaly_detection",
                "model_type": request.model_type,
                "threshold": request.threshold,
                "anomalies_detected": len(anomalies),
                "total_records": len(df),
                "anomaly_details": anomalies,
                "analyzed_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "connection_id": request.connection_id,
                "model_type": request.model_type,
                "anomalies_detected": len(anomalies),
                "total_records": len(df),
                "anomaly_details": anomalies,
                "message": f"VARIMA anomaly detection completed. Found {len(anomalies)} anomalies."
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported model type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@app.get("/api/analysis/results/{connection_id}")
async def get_analysis_results(connection_id: str):
    """Get analysis results for a connection"""
    results = {}
    
    quality_key = f"{connection_id}_quality"
    if quality_key in analysis_results:
        results["quality_metrics"] = analysis_results[quality_key]
    
    anomaly_key = f"{connection_id}_anomaly"
    if anomaly_key in analysis_results:
        results["anomaly_detection"] = analysis_results[anomaly_key]
    
    if not results:
        raise HTTPException(status_code=404, detail="No analysis results found for this connection")
    
    return results

@app.post("/api/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate reports"""
    try:
        if request.connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        results = {}
        quality_key = f"{request.connection_id}_quality"
        anomaly_key = f"{request.connection_id}_anomaly"
        
        if quality_key in analysis_results:
            results["quality_metrics"] = analysis_results[quality_key]
        if anomaly_key in analysis_results:
            results["anomaly_detection"] = analysis_results[anomaly_key]
        
        report_data = {
            "report_id": str(uuid.uuid4()),
            "connection_id": request.connection_id,
            "report_type": request.report_type,
            "generated_at": datetime.now().isoformat(),
            "data": results
        }
        
        return {
            "success": True,
            "report_id": report_data["report_id"],
            "report_type": request.report_type,
            "format": request.format,
            "data": report_data,
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    

    
@app.post("/api/store/db-connection")
async def storeConnectionString(data: DbStoreRequest):
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

        return {
            "success": True, 
            "message": "Connection string stored successfully",
            "connection_id": new_connection["connection_id"],
            "total_connections": len(connections_data["connections"])
        }
        
    except redis.RedisError as e:
        print(f"Redis error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to store connection string: {str(e)}"
        }
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return {
            "success": False,
            "message": "Failed to parse existing connection data"
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }


# Additional helper functions you might want to add:

@app.get("/api/get/db-connections/{email}")
async def getConnectionStrings(email: str):
    """Retrieve all connection strings for a user"""
    try:
        redis_key = f"user_connections:{email}"
        connections_data = redis_client.get(redis_key)
        
        if connections_data:
            data = json.loads(connections_data)
            # Remove sensitive connection strings from response for security
            sanitized_connections = []
            for conn in data["connections"]:
                sanitized_connections.append({
                    "connection_id": conn["connection_id"],
                    "created_at": conn["created_at"],
                    "connection_preview": conn["connection_string"][:20] + "..." if len(conn["connection_string"]) > 20 else conn["connection_string"]
                })
            
            return {
                "success": True,
                "email": data["email"],
                "connections": sanitized_connections,
                "total_connections": len(sanitized_connections),
                "last_updated": data["updated_at"]
            }
        else:
            return {
                "success": True,
                "message": "No connections found for this user",
                "connections": [],
                "total_connections": 0
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to retrieve connections: {str(e)}"
        }


@app.delete("/api/delete/db-connection/{email}/{connection_id}")
async def deleteConnectionString(email: str, connection_id: str):
    """Delete a specific connection string"""
    try:
        redis_key = f"user_connections:{email}"
        connections_data = redis_client.get(redis_key)
        
        if connections_data:
            data = json.loads(connections_data)
            
            # Find and remove the connection
            original_count = len(data["connections"])
            data["connections"] = [
                conn for conn in data["connections"] 
                if conn["connection_id"] != connection_id
            ]
            
            if len(data["connections"]) < original_count:
                data["updated_at"] = datetime.now().isoformat()
                
                # Update Redis
                redis_client.set(redis_key, json.dumps(data))
                
                return {
                    "success": True,
                    "message": "Connection deleted successfully",
                    "remaining_connections": len(data["connections"])
                }
            else:
                return {
                    "success": False,
                    "message": "Connection not found"
                }
        else:
            return {
                "success": False,
                "message": "No connections found for this user"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete connection: {str(e)}"
        }


# Basic key-value storage:
@app.post("/api/store/db-connection-simple")
async def storeConnectionStringSimple(email: str, connectionString: str):
    """Simple version - just stores the latest connection string"""
    try:
        redis_key = f"user_connection:{email}"
        
        # Store connection string with metadata
        connection_data = {
            "connection_string": connectionString,
            "stored_at": datetime.now().isoformat(),
            "email": email
        }
        
        redis_client.set(
            redis_key, 
            json.dumps(connection_data),
            ex=86400 * 7  # Expire after 7 days
        )
        
        print(f"Stored connection string for {email}: {connectionString}")
        
        return {
            "success": True, 
            "message": "Connection string stored successfully"
        }
        
    except Exception as e:
        print(f"Error storing connection: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to store connection string: {str(e)}"
        }

# Helper functions

def calculate_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive data quality metrics with detailed analysis"""
    total_cells = df.size
    total_rows = len(df)
    
    # Handle empty dataframes
    if total_rows == 0 or total_cells == 0:
        return {
            "metrics": {
                "completeness": 0.0,
                "uniqueness": 0.0,
                "cardinality": 0.0,
                "consistency": 0.0,
                "volumetry": 0.0
            },
            "detailed_analysis": {
                "completeness": {
                    "score": 0.0,
                    "total_missing": 0,
                    "missing_by_column": {},
                    "issues": ["No data available for analysis"],
                    "recommendations": ["Verify data source connection", "Check data extraction process"]
                },
                "uniqueness": {
                    "score": 0.0,
                    "duplicate_rows": 0,
                    "uniqueness_by_column": {},
                    "issues": ["No data available for analysis"],
                    "recommendations": ["Verify data source connection"]
                },
                "cardinality": {
                    "score": 0.0,
                    "column_cardinalities": {},
                    "issues": ["No data available for analysis"],
                    "recommendations": ["Verify data source connection"]
                },
                "consistency": {
                    "score": 0.0,
                    "data_types": {},
                    "issues": ["No data available for analysis"],
                    "recommendations": ["Verify data source connection"]
                },
                "volumetry": {
                    "score": 0.0,
                    "total_rows": 0,
                    "total_columns": len(df.columns),
                    "data_size_mb": 0.0,
                    "issues": ["No data records found"],
                    "recommendations": ["Verify data source connection", "Check data extraction process"]
                }
            }
        }
    
    # COMPLETENESS: Calculate missing values per column
    missing_by_column = df.isnull().sum()
    total_missing = missing_by_column.sum()
    completeness_score = ((total_cells - total_missing) / total_cells) * 100
    
    # Handle NaN case for completeness
    if pd.isna(completeness_score) or np.isinf(completeness_score):
        completeness_score = 0.0
    
    # Find columns with most missing data
    missing_columns = missing_by_column[missing_by_column > 0].sort_values(ascending=False)
    completeness_issues = []
    for col, missing_count in missing_columns.head(5).items():
        missing_pct = (missing_count / total_rows) * 100
        if pd.isna(missing_pct) or np.isinf(missing_pct):
            missing_pct = 0.0
        completeness_issues.append(f"Missing values in '{col}' field ({missing_pct:.1f}%)")
    
    # UNIQUENESS: Calculate duplicate and unique ratios
    duplicate_rows = df.duplicated().sum()
    uniqueness_by_column = {}
    uniqueness_issues = []
    
    for col in df.columns:
        duplicates_in_col = df[col].duplicated().sum()
        unique_ratio = ((total_rows - duplicates_in_col) / total_rows) * 100
        
        # Handle NaN case
        if pd.isna(unique_ratio) or np.isinf(unique_ratio):
            unique_ratio = 0.0
            
        uniqueness_by_column[col] = round(unique_ratio, 1)
        
        if duplicates_in_col > 0:
            dup_pct = (duplicates_in_col / total_rows) * 100
            if pd.isna(dup_pct) or np.isinf(dup_pct):
                dup_pct = 0.0
            uniqueness_issues.append(f"Duplicate values in '{col}' ({dup_pct:.1f}%)")
    
    overall_uniqueness = ((total_rows - duplicate_rows) / total_rows) * 100
    if pd.isna(overall_uniqueness) or np.isinf(overall_uniqueness):
        overall_uniqueness = 0.0
    
    # CARDINALITY: Analyze value distribution
    cardinality_issues = []
    cardinality_scores = []
    
    for col in df.columns:
        unique_count = df[col].nunique()
        cardinality_ratio = unique_count / total_rows if total_rows > 0 else 0
        
        if cardinality_ratio < 0.01:  # Very low cardinality
            cardinality_issues.append(f"Low cardinality in '{col}' field ({unique_count} unique values)")
            cardinality_scores.append(60)
        elif cardinality_ratio > 0.95:  # Very high cardinality
            cardinality_issues.append(f"High cardinality in '{col}' field ({unique_count} unique values)")
            cardinality_scores.append(70)
        else:
            cardinality_scores.append(85)
    
    cardinality_score = np.mean(cardinality_scores) if cardinality_scores else 80
    if pd.isna(cardinality_score) or np.isinf(cardinality_score):
        cardinality_score = 80.0
    
    # CONSISTENCY: Check data format consistency
    consistency_issues = []
    consistency_scores = []
    
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check for mixed case issues
            str_values = df[col].dropna().astype(str)
            if len(str_values) > 0:
                mixed_case = sum(1 for val in str_values if val != val.lower() and val != val.upper())
                if mixed_case > len(str_values) * 0.1:
                    consistency_issues.append(f"Mixed case values in '{col}' field")
                    consistency_scores.append(70)
                else:
                    consistency_scores.append(90)
            else:
                consistency_scores.append(0)  # No data to analyze
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            # Check date format consistency
            consistency_scores.append(85)
        else:
            consistency_scores.append(90)
    
    consistency_score = np.mean(consistency_scores) if consistency_scores else 85
    if pd.isna(consistency_score) or np.isinf(consistency_score):
        consistency_score = 85.0
    
    # VOLUMETRY: Analyze data volume patterns
    volumetry_issues = []
    volumetry_score = 95  # Base score
    
    # Check for empty datasets
    if total_rows == 0:
        volumetry_issues.append("No data records found")
        volumetry_score = 0
    elif total_rows < 100:
        volumetry_issues.append(f"Low data volume ({total_rows} records)")
        volumetry_score = 70
    
    # Check for unusual column counts
    if len(df.columns) < 2:
        volumetry_issues.append("Very few columns for analysis")
        volumetry_score -= 10
    elif len(df.columns) > 100:
        volumetry_issues.append(f"Large number of columns ({len(df.columns)})")
        volumetry_score -= 5
    
    # Ensure volumetry score is valid
    if pd.isna(volumetry_score) or np.isinf(volumetry_score):
        volumetry_score = 0.0
    
    # Ensure volumetry score is valid
    if pd.isna(volumetry_score) or np.isinf(volumetry_score):
        volumetry_score = 0.0

    # Clean missing_by_column dictionary
    missing_by_column_clean = {}
    for col, count in missing_by_column.items():
        missing_by_column_clean[col] = int(clean_numeric(count))
    
    # Clean uniqueness_by_column dictionary
    uniqueness_by_column_clean = {}
    for col, ratio in uniqueness_by_column.items():
        uniqueness_by_column_clean[col] = clean_numeric(ratio)
    
    return {
        "metrics": {
            "completeness": clean_numeric(completeness_score),
            "uniqueness": clean_numeric(overall_uniqueness),
            "cardinality": clean_numeric(cardinality_score),
            "consistency": clean_numeric(consistency_score),
            "volumetry": clean_numeric(volumetry_score)
        },
        "detailed_analysis": {
            "completeness": {
                "score": clean_numeric(completeness_score),
                "total_missing": int(clean_numeric(total_missing)),
                "missing_by_column": missing_by_column_clean,
                "issues": completeness_issues[:3],
                "recommendations": [
                    "Implement data validation at source",
                    "Add required field constraints",
                    "Monitor data completeness over time"
                ]
            },
            "uniqueness": {
                "score": clean_numeric(overall_uniqueness),
                "duplicate_rows": int(clean_numeric(duplicate_rows)),
                "uniqueness_by_column": uniqueness_by_column_clean,
                "issues": uniqueness_issues[:3],
                "recommendations": [
                    "Add unique constraints to key fields",
                    "Implement deduplication process",
                    "Monitor for duplicate entries"
                ]
            },
            "cardinality": {
                "score": clean_numeric(cardinality_score),
                "column_cardinalities": {col: int(clean_numeric(df[col].nunique())) for col in df.columns},
                "issues": cardinality_issues[:3],
                "recommendations": [
                    "Standardize categorical values",
                    "Review high-cardinality fields",
                    "Consider data normalization"
                ]
            },
            "consistency": {
                "score": clean_numeric(consistency_score),
                "data_types": {col: str(df[col].dtype) for col in df.columns},
                "issues": consistency_issues[:3],
                "recommendations": [
                    "Standardize data formats",
                    "Implement format validation",
                    "Create data quality rules"
                ]
            },
            "volumetry": {
                "score": clean_numeric(volumetry_score),
                "total_rows": total_rows,
                "total_columns": len(df.columns),
                "data_size_mb": clean_numeric(df.memory_usage(deep=True).sum() / (1024 * 1024)),
                "issues": volumetry_issues,
                "recommendations": [
                    "Monitor data volume trends",
                    "Set up data volume alerts",
                    "Plan for data growth"
                ]
            }
        }
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
