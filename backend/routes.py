"""
API routes for the Data Quality Pipeline
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json

from models import (
    DatabaseConnection, PowerBIAuth, DbStoreRequest, PowerBIEmbedRequest,
    DataQualityMetrics, AnomalyDetectionRequest, ReportRequest, PowerBIDatasetCreate
)
from database import (
    test_database_connection, get_connection_info, disconnect_database,
    get_table_list, get_table_data
)
from analysis import (
    analyze_all_tables, run_anomaly_detection, get_cached_analysis, 
    get_cached_varima, calculate_quality_metrics
)
from export import (
    export_cleaned_data_csv, export_table_csv, export_statistics_csv,
    create_powerbi_package, get_powerbi_package
)
from file_utils import (
    process_uploaded_file, get_file_sample, get_analyzed_file_sample,
    cleanup_file_connection
)
from powerbi_service import PowerBIService
from redis_client import redis_client

# Create router
router = APIRouter()

# Initialize Power BI service
powerbi_service = PowerBIService()


@router.get("/")
async def root():
    return {"message": "Data Quality Pipeline API", "version": "1.0.0"}


# Power BI Routes
@router.post("/api/powerbi/authenticate")
async def authenticate_powerbi(auth: PowerBIAuth):
    """Authenticate with Power BI service"""
    try:
        result = powerbi_service.authenticate(
            auth.client_id,
            auth.client_secret,
            auth.tenant_id,
            auth.username,
            auth.password
        )
        return {"success": True, "message": "Authentication successful", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/api/powerbi/workspaces")
async def get_workspaces(authorization: str = Header(None)):
    """Get Power BI workspaces"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Valid authorization token required")
        
        token = authorization.replace("Bearer ", "")
        workspaces = powerbi_service.get_workspaces(token)
        return {"success": True, "data": workspaces}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get workspaces: {str(e)}")


@router.post("/api/powerbi/open-online")
async def open_powerbi_online(request: dict):
    """Create Power BI package and open Power BI Service"""
    connection_id = request.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    return create_powerbi_package(connection_id)


@router.get("/api/download/powerbi-package/{connection_id}")
async def download_powerbi_package(connection_id: str):
    """Download Power BI package ZIP file"""
    return get_powerbi_package(connection_id)


# Database Connection Routes
@router.post("/api/connect/database")
async def connect_database(connection: DatabaseConnection):
    """Connect to database and test connection"""
    return test_database_connection(connection)


@router.get("/api/connections/{connection_id}")
async def get_connection(connection_id: str):
    """Get connection information"""
    return get_connection_info(connection_id)


@router.post("/api/disconnect/{connection_id}")
async def disconnect(connection_id: str):
    """Disconnect from database"""
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] == "database":
        return disconnect_database(connection_id)
    elif connection_info["type"] == "file":
        return cleanup_file_connection(connection_id)
    else:
        raise HTTPException(status_code=400, detail="Unsupported connection type")


# File Upload Routes
@router.post("/api/connect/file")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process CSV file"""
    return process_uploaded_file(file)


@router.get("/api/connections/{connection_id}/sample")
async def get_sample_data(connection_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get sample data from connection"""
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] == "database":
        # Return database sample logic here
        from sqlalchemy import inspect
        from database import get_database_engine
        
        engine = get_database_engine(connection_id)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        sample_data = {}
        for table_name in tables[:3]:  # Limit to first 3 tables
            try:
                df = get_table_data(connection_id, table_name, limit=10)
                sample_data[table_name] = df.head(5).to_dict('records')
            except:
                sample_data[table_name] = {"error": "Could not retrieve sample"}
        
        return {
            "connection_id": connection_id,
            "type": "database",
            "tables": tables,
            "sample_data": sample_data
        }
    
    elif connection_info["type"] == "file":
        return get_file_sample(connection_id, limit)
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported connection type")


@router.get("/api/connections/{connection_id}/analyzed-sample")
async def get_analyzed_sample(connection_id: str):
    """Get analyzed sample data"""
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] == "file":
        return get_analyzed_file_sample(connection_id)
    else:
        # For database connections, return basic table info
        return {"message": "Analysis available through quality metrics endpoint"}


@router.get("/api/connections")
async def list_connections():
    """List all active connections"""
    try:
        pattern = "connection:*"
        keys = redis_client.keys(pattern)
        
        connections = []
        for key in keys:
            try:
                data = redis_client.get(key)
                if data:
                    connection_info = json.loads(data)
                    connections.append({
                        "id": connection_info["id"],
                        "type": connection_info["type"],
                        "status": connection_info.get("status", "unknown")
                    })
            except:
                continue
        
        return {"success": True, "data": {"connections": connections}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list connections: {str(e)}")


# Analysis Routes
@router.post("/api/analysis/auto-quality-all-tables")
async def analyze_quality_all_tables(request: dict):
    """Analyze data quality for all tables in connection"""
    connection_id = request.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    return analyze_all_tables(connection_id)


@router.get("/api/analysis/cached-results/{connection_id}")
async def get_cached_results(connection_id: str):
    """Get cached analysis results"""
    return get_cached_analysis(connection_id)


@router.post("/api/analysis/quality-metrics")
async def calculate_metrics(request: DataQualityMetrics):
    """Calculate quality metrics for specific table or dataset"""
    connection_info = get_connection_info(request.connection_id)
    
    if connection_info["type"] == "database" and request.table_name:
        df = get_table_data(request.connection_id, request.table_name, limit=10000)
        metrics = calculate_quality_metrics(df)
        return {
            "success": True,
            "connection_id": request.connection_id,
            "table_name": request.table_name,
            "metrics": metrics
        }
    elif connection_info["type"] == "file":
        import pandas as pd
        file_path = connection_info.get("file_path")
        df = pd.read_csv(file_path)
        metrics = calculate_quality_metrics(df)
        return {
            "success": True,
            "connection_id": request.connection_id,
            "metrics": metrics
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid request parameters")


@router.post("/api/analysis/auto-varima-all-tables")
async def analyze_varima_all_tables(request: dict):
    """Run VARIMA anomaly detection for all tables"""
    connection_id = request.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] == "database":
        tables = get_table_list(connection_id)
        results = {}
        
        for table_name in tables:
            try:
                result = run_anomaly_detection(connection_id, table_name)
                results[table_name] = result
            except Exception as e:
                results[table_name] = {"error": str(e)}
        
        return {
            "success": True,
            "connection_id": connection_id,
            "results": results
        }
    
    elif connection_info["type"] == "file":
        result = run_anomaly_detection(connection_id)
        return {
            "success": True,
            "connection_id": connection_id,
            "results": {"file_data": result}
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported connection type")


@router.get("/api/analysis/cached-varima-results/{connection_id}")
async def get_cached_varima_results(connection_id: str):
    """Get cached VARIMA results"""
    return get_cached_varima(connection_id)


@router.post("/api/analysis/anomaly-detection")
async def detect_anomalies(request: AnomalyDetectionRequest):
    """Run anomaly detection on specific table or dataset"""
    return run_anomaly_detection(request.connection_id, request.table_name)


# Export Routes
@router.post("/api/analysis/export-cleaned-data")
async def export_cleaned_data(request: dict):
    """Export cleaned data as CSV"""
    connection_id = request.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    return export_cleaned_data_csv(connection_id)


@router.post("/api/analysis/export-cleaned-table")
async def export_cleaned_table(request: dict):
    """Export specific table data as CSV"""
    connection_id = request.get("connection_id")
    table_name = request.get("table_name")
    
    if not connection_id or not table_name:
        raise HTTPException(status_code=400, detail="Connection ID and table name required")
    
    return export_table_csv(connection_id, table_name)


@router.post("/api/analysis/export-statistics")
async def export_statistics(request: dict):
    """Export comprehensive statistics as CSV"""
    connection_id = request.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    return export_statistics_csv(connection_id)
