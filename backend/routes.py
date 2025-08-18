"""
API routes for the Data Quality Pipeline
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime

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


@router.get("/debug/redis-keys")
async def debug_redis_keys():
    """Debug endpoint to see all Redis keys"""
    try:
        all_keys = redis_client.keys("*")
        db_store_keys = redis_client.keys("db_store:*")
        
        result = {
            "total_keys": len(all_keys),
            "db_store_keys": len(db_store_keys),
            "all_keys": [key.decode('utf-8') if isinstance(key, bytes) else key for key in all_keys],
            "db_store_keys": [key.decode('utf-8') if isinstance(key, bytes) else key for key in db_store_keys]
        }
        return result
    except Exception as e:
        return {"error": str(e)}


@router.post("/api/test-store")
async def test_store():
    """Simple test endpoint for debugging routing"""
    return {"message": "Test store endpoint working", "method": "POST"}


@router.get("/api/test-store")
async def test_store_get():
    """Simple test endpoint for debugging routing"""
    return {"message": "Test store endpoint working", "method": "GET"}


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
    try:
        print(f"Received file upload request: {file.filename}, size: {file.size}")
        result = process_uploaded_file(file)
        print(f"File processing successful: {result}")
        return result
    except Exception as e:
        print(f"File processing error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


# Database Connection Storage Routes
@router.post("/api/store/db-connection")
async def store_db_connection(request: dict):
    """Store database connection string for a user"""
    try:
        email = request.get("email")
        connection_string = request.get("connection_string")
        
        if not email or not connection_string:
            raise HTTPException(status_code=400, detail="Email and connection_string are required")
        
        # Generate unique connection ID
        connection_id = str(uuid.uuid4())
        
        # Create storage key
        key = f"db_store:{email}:{connection_id}"
        
        # Store connection data
        connection_data = {
            "connection_string": connection_string,
            "created_at": datetime.now().isoformat(),
            "email": email
        }
        
        # Store in Redis
        redis_client.set(key, json.dumps(connection_data))
        
        return {
            "success": True,
            "data": {
                "connection_id": connection_id,
                "created_at": connection_data["created_at"]
            },
            "message": "Connection stored successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store connection: {str(e)}")


@router.delete("/api/delete/db-connection/{email}/{connection_id}")
async def delete_db_connection(email: str, connection_id: str):
    """Delete a stored database connection"""
    try:
        key = f"db_store:{email}:{connection_id}"
        
        # Check if connection exists
        if not redis_client.exists(key):
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Delete the connection
        redis_client.delete(key)
        
        # Count remaining connections for this email
        pattern = f"db_store:{email}:*"
        remaining_keys = redis_client.keys(pattern)
        remaining_connections = len(remaining_keys)
        
        return {
            "success": True,
            "data": {
                "remaining_connections": remaining_connections
            },
            "message": "Connection deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete connection: {str(e)}")


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


@router.get("/api/get/db-connections/{email}")
async def get_stored_connections(email: str):
    """Get stored connections for a specific email"""
    try:
        pattern = f"db_store:{email}:*"
        keys = redis_client.keys(pattern)
        
        connections = []
        for key in keys:
            try:
                # Handle key decoding if it's bytes
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                
                data = redis_client.get(key)
                
                if data:
                    # Handle data decoding if it's bytes
                    data_str = data.decode('utf-8') if isinstance(data, bytes) else str(data)
                    connection_data = json.loads(data_str)
                    
                    # Extract connection ID from key pattern
                    connection_id = key_str.split(":")[-1]
                    
                    connections.append({
                        "connection_id": connection_id,
                        "created_at": connection_data.get("created_at", ""),
                        "connection_preview": connection_data.get("connection_string", "")[:50] + "..." if len(connection_data.get("connection_string", "")) > 50 else connection_data.get("connection_string", "")
                    })
            except Exception as e:
                # Skip failed connections but don't crash
                continue
        
        return {
            "success": True, 
            "data": {
                "email": email,
                "connections": connections,
                "total_connections": len(connections),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Analysis Routes
@router.post("/api/analysis/auto-quality-all-tables")
async def analyze_quality_all_tables(connection_id: str = Query(...)):
    """Analyze data quality for all tables in connection"""
    raw_result = analyze_all_tables(connection_id)
    
    # Transform to frontend-expected format
    table_results = raw_result.get("table_results", {})
    
    # Calculate average metrics across all tables for combined_results
    all_completeness = []
    all_validity = []
    all_consistency = []
    all_uniqueness = []
    all_accuracy = []
    
    from analysis import clean_numeric
    
    for table_name, result in table_results.items():
        if "error" not in result:
            all_completeness.append(result.get("completeness", 0))
            all_validity.append(result.get("validity", 0))
            all_consistency.append(result.get("consistency", 0))
            all_uniqueness.append(result.get("uniqueness", 0))
            all_accuracy.append(result.get("accuracy", 0))
    
    # Calculate averages
    avg_completeness = sum(all_completeness) / len(all_completeness) if all_completeness else 0
    avg_validity = sum(all_validity) / len(all_validity) if all_validity else 0
    avg_consistency = sum(all_consistency) / len(all_consistency) if all_consistency else 0
    avg_uniqueness = sum(all_uniqueness) / len(all_uniqueness) if all_uniqueness else 0
    avg_accuracy = sum(all_accuracy) / len(all_accuracy) if all_accuracy else 0
    
    # Format response to match frontend expectations
    formatted_response = {
        "combined_results": {
            "metrics": {
                "completeness": clean_numeric(avg_completeness),
                "validity": clean_numeric(avg_validity), 
                "consistency": clean_numeric(avg_consistency),
                "uniqueness": clean_numeric(avg_uniqueness),
                "cardinality": clean_numeric(avg_accuracy),  # Map accuracy to cardinality
                "volumetry": clean_numeric(raw_result.get("overall_quality_score", 0))
            },
            "overall_score": clean_numeric(raw_result.get("overall_quality_score", 0)),
            "total_tables": raw_result.get("total_tables", 0),
            "analyzed_tables": raw_result.get("analyzed_tables", 0)
        },
        "table_results": table_results,
        "analyzed_tables": list(table_results.keys())
    }
    
    return formatted_response


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
        total_anomalies = 0
        total_records = 0
        tables_with_anomalies = 0
        
        for table_name in tables:
            try:
                result = run_anomaly_detection(connection_id, table_name)
                results[table_name] = result
                
                # Aggregate statistics
                if 'anomalies_detected' in result:
                    anomalies = result['anomalies_detected']
                    total_anomalies += anomalies
                    if anomalies > 0:
                        tables_with_anomalies += 1
                
                if 'total_observations' in result:
                    total_records += result['total_observations']
                    
            except Exception as e:
                results[table_name] = {"error": str(e)}
        
        # Calculate summary metrics
        from analysis import clean_numeric
        anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0.0
        
        # Determine risk level based on anomaly rate
        if anomaly_rate == 0:
            risk_level = "low"
        elif anomaly_rate < 5:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Return format matching frontend expectations
        return {
            "combined_results": {
                "anomaly_rate": clean_numeric(anomaly_rate),
                "risk_level": risk_level,
                "total_anomalies": total_anomalies,
                "total_records": total_records,
                "tables_analyzed": len(results),
                "tables_with_anomalies": tables_with_anomalies,
                "connection_id": connection_id,
                "analysis_type": "VARIMA"
            },
            "table_results": results,
            "analyzed_tables": list(results.keys())
        }
    
    elif connection_info["type"] == "file":
        result = run_anomaly_detection(connection_id)
        
        # Format for file analysis
        total_anomalies = result.get('anomalies_detected', 0)
        total_records = result.get('total_observations', 0)
        anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0.0
        
        # Determine risk level
        if anomaly_rate == 0:
            risk_level = "low"
        elif anomaly_rate < 5:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        from analysis import clean_numeric
        return {
            "combined_results": {
                "anomaly_rate": clean_numeric(anomaly_rate),
                "risk_level": risk_level,
                "total_anomalies": total_anomalies,
                "total_records": total_records,
                "tables_analyzed": 1,
                "tables_with_anomalies": 1 if total_anomalies > 0 else 0,
                "connection_id": connection_id,
                "analysis_type": "VARIMA"
            },
            "table_results": {"file_data": result},
            "analyzed_tables": ["file_data"]
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
