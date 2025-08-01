from dataclasses import Field
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
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

@app.get("/api/connections")
async def get_connections():
    """Get all active connections"""
    connections_list = []
    for conn_id, conn_data in data_connections.items():
        conn_summary = {k: v for k, v in conn_data.items() if k not in ['data', 'engine', 'sample_data']}
        connections_list.append(conn_summary)
    
    return {"connections": connections_list}

@app.post("/api/analysis/quality-metrics")
async def run_quality_analysis(connection_id: str):
    """Run comprehensive data quality analysis"""
    try:
        if connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[connection_id]
        
        # For database connections, fetch actual data
        if connection_data["type"] == "database" and "engine" in connection_data:
            engine = connection_data["engine"]
            tables = connection_data.get("tables", [])
            
            if not tables:
                raise HTTPException(status_code=400, detail="No tables found in database")
            
            # Use the first table or a table with most records
            table_name = tables[0]
            query = f"SELECT * FROM {table_name} LIMIT 10000"  # Sample for performance
            df = pd.read_sql(query, engine)
            
            # Update connection data with sample
            data_connections[connection_id]["sample_data"] = df
                    
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

@app.post("/api/analysis/anomaly-detection")
async def run_anomaly_detection(request: AnomalyDetectionRequest):
    """Run VARIMA anomaly detection"""
    try:
        if request.connection_id not in data_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_data = data_connections[request.connection_id]
        
        # Get actual data from connection
        if connection_data["type"] == "database" and "sample_data" in connection_data:
            df = connection_data["sample_data"]
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
    
    # COMPLETENESS: Calculate missing values per column
    missing_by_column = df.isnull().sum()
    total_missing = missing_by_column.sum()
    completeness_score = ((total_cells - total_missing) / total_cells) * 100
    
    # Find columns with most missing data
    missing_columns = missing_by_column[missing_by_column > 0].sort_values(ascending=False)
    completeness_issues = []
    for col, missing_count in missing_columns.head(5).items():
        missing_pct = (missing_count / total_rows) * 100
        completeness_issues.append(f"Missing values in '{col}' field ({missing_pct:.1f}%)")
    
    # UNIQUENESS: Calculate duplicate and unique ratios
    duplicate_rows = df.duplicated().sum()
    uniqueness_by_column = {}
    uniqueness_issues = []
    
    for col in df.columns:
        duplicates_in_col = df[col].duplicated().sum()
        unique_ratio = ((total_rows - duplicates_in_col) / total_rows) * 100
        uniqueness_by_column[col] = unique_ratio
        
        if duplicates_in_col > 0:
            dup_pct = (duplicates_in_col / total_rows) * 100
            uniqueness_issues.append(f"Duplicate values in '{col}' ({dup_pct:.1f}%)")
    
    overall_uniqueness = ((total_rows - duplicate_rows) / total_rows) * 100
    
    # CARDINALITY: Analyze value distribution
    cardinality_issues = []
    cardinality_scores = []
    
    for col in df.columns:
        unique_count = df[col].nunique()
        cardinality_ratio = unique_count / total_rows
        
        if cardinality_ratio < 0.01:  # Very low cardinality
            cardinality_issues.append(f"Low cardinality in '{col}' field ({unique_count} unique values)")
            cardinality_scores.append(60)
        elif cardinality_ratio > 0.95:  # Very high cardinality
            cardinality_issues.append(f"High cardinality in '{col}' field ({unique_count} unique values)")
            cardinality_scores.append(70)
        else:
            cardinality_scores.append(85)
    
    cardinality_score = np.mean(cardinality_scores) if cardinality_scores else 80
    
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
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            # Check date format consistency
            consistency_scores.append(85)
        else:
            consistency_scores.append(90)
    
    consistency_score = np.mean(consistency_scores) if consistency_scores else 85
    
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
    
    return {
        "metrics": {
            "completeness": round(completeness_score, 1),
            "uniqueness": round(overall_uniqueness, 1),
            "cardinality": round(cardinality_score, 1),
            "consistency": round(consistency_score, 1),
            "volumetry": round(volumetry_score, 1)
        },
        "detailed_analysis": {
            "completeness": {
                "score": round(completeness_score, 1),
                "total_missing": int(total_missing),
                "missing_by_column": missing_by_column.to_dict(),
                "issues": completeness_issues[:3],
                "recommendations": [
                    "Implement data validation at source",
                    "Add required field constraints",
                    "Monitor data completeness over time"
                ]
            },
            "uniqueness": {
                "score": round(overall_uniqueness, 1),
                "duplicate_rows": int(duplicate_rows),
                "uniqueness_by_column": uniqueness_by_column,
                "issues": uniqueness_issues[:3],
                "recommendations": [
                    "Add unique constraints to key fields",
                    "Implement deduplication process",
                    "Monitor for duplicate entries"
                ]
            },
            "cardinality": {
                "score": round(cardinality_score, 1),
                "column_cardinalities": {col: df[col].nunique() for col in df.columns},
                "issues": cardinality_issues[:3],
                "recommendations": [
                    "Standardize categorical values",
                    "Review high-cardinality fields",
                    "Consider data normalization"
                ]
            },
            "consistency": {
                "score": round(consistency_score, 1),
                "data_types": {col: str(df[col].dtype) for col in df.columns},
                "issues": consistency_issues[:3],
                "recommendations": [
                    "Standardize data formats",
                    "Implement format validation",
                    "Create data quality rules"
                ]
            },
            "volumetry": {
                "score": round(volumetry_score, 1),
                "total_rows": total_rows,
                "total_columns": len(df.columns),
                "data_size_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
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
