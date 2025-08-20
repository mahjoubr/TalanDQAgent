"""
API routes for the Data Quality Pipeline
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
import pandas as pd
import numpy as np

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
    cleanup_file_connection, update_file_row
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
async def get_sample_data(connection_id: str, limit: int = Query(100, ge=1, le=1000), table_name: str = Query(None)):
    """Get sample data from connection"""
    connection_info = get_connection_info(connection_id)
    
    if connection_info["type"] == "database":
        from sqlalchemy import inspect
        from database import get_database_engine
        
        engine = get_database_engine(connection_id)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if table_name:
            # Return sample data for specific table
            if table_name not in tables:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            try:
                df = get_table_data(connection_id, table_name, limit=limit)
                sample_data = df.head(limit).to_dict('records')
                
                # Clean sample data for JSON serialization
                for row in sample_data:
                    for key, value in row.items():
                        if pd.isna(value):
                            row[key] = None
                        elif isinstance(value, (np.int64, np.int32)):
                            row[key] = int(value)
                        elif isinstance(value, (np.float64, np.float32)):
                            row[key] = float(value)
                
                return {
                    "connection_id": connection_id,
                    "table_name": table_name,
                    "total_rows": len(df),
                    "sample_rows": len(sample_data),
                    "columns": df.columns.tolist(),
                    "sample_data": sample_data
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get sample data for table {table_name}: {str(e)}")
        else:
            # Return sample data for all tables (legacy behavior)
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


@router.put("/api/connections/{connection_id}/update-row")
async def update_row_data(connection_id: str, request: dict):
    """Update a specific row in the dataset"""
    try:
        row_index = request.get("row_index")
        updated_data = request.get("updated_data")
        
        if row_index is None or updated_data is None:
            raise HTTPException(status_code=400, detail="row_index and updated_data are required")
        
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "file":
            # Update file data
            result = update_file_row(connection_id, row_index, updated_data)
            return result
        else:
            raise HTTPException(status_code=400, detail="Row updates only supported for file connections currently")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update row: {str(e)}")


# Data Cleaning Endpoints
@router.post("/api/data-cleaning/preview-options")
async def get_cleaning_options(request: Request):
    """Get available cleaning options for a dataset"""
    try:
        request_data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
    connection_id = request_data.get("connection_id")
    table_name = request_data.get("table_name")  # Optional for database connections
    
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    try:
        from data_cleaner import DataCleaner
        import os
        
        # Get data sample based on connection type
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "file":
            import pandas as pd
            file_path = connection_info.get("file_path")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            df = pd.read_csv(file_path)
        else:
            # For database connections, get first table if no table specified
            if not table_name:
                tables = get_table_list(connection_id)
                if not tables:
                    raise HTTPException(status_code=404, detail="No tables found")
                table_name = tables[0]
            
            df = get_table_data(connection_id, table_name)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Analyze data for cleaning recommendations
        cleaner = DataCleaner(df)
        
        # Get data info
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_columns = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Calculate statistics
        null_counts = df.isnull().sum()
        null_percentages = (df.isnull().sum() / len(df) * 100).round(2)
        duplicate_count = df.duplicated().sum()
        
        # Outlier detection preview (for numeric columns)
        outlier_info = {}
        for col in numeric_columns[:5]:  # Limit to first 5 numeric columns for preview
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            outlier_info[col] = outliers
        
        return {
            "success": True,
            "data": {
                "dataset_info": {
                    "shape": df.shape,
                    "columns": {
                        "numeric": numeric_columns,
                        "categorical": categorical_columns,
                        "datetime": datetime_columns,
                        "all_columns": df.columns.tolist()
                    },
                    "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
                },
                "data_quality": {
                    "null_values": {
                        "counts": null_counts.to_dict(),
                        "percentages": null_percentages.to_dict(),
                        "columns_with_nulls": null_counts[null_counts > 0].index.tolist()
                    },
                    "duplicates": {
                        "count": int(duplicate_count),
                        "percentage": round(duplicate_count / len(df) * 100, 2)
                    },
                    "outliers_preview": outlier_info
                },
                "cleaning_options": {
                    "drop_nulls": {
                        "available": True,
                        "methods": ["any", "all", "threshold"],
                        "recommendation": "threshold" if null_counts.sum() > 0 else None
                    },
                    "drop_duplicates": {
                        "available": True,
                        "recommendation": duplicate_count > 0
                    },
                    "fill_missing": {
                        "available": True,
                        "methods": {
                            "numeric": ["mean", "median", "interpolate", "constant"],
                            "categorical": ["mode", "constant", "forward_fill", "backward_fill"]
                        },
                        "applicable_columns": {
                            "numeric": [col for col in numeric_columns if null_counts[col] > 0],
                            "categorical": [col for col in categorical_columns if null_counts[col] > 0]
                        }
                    },
                    "remove_outliers": {
                        "available": len(numeric_columns) > 0,
                        "methods": ["iqr", "zscore"],
                        "applicable_columns": numeric_columns,
                        "outlier_counts": outlier_info
                    },
                    "standardize": {
                        "available": len(numeric_columns) > 0,
                        "methods": ["zscore", "minmax"],
                        "applicable_columns": numeric_columns
                    },
                    "convert_types": {
                        "available": True,
                        "suggestions": get_type_conversion_suggestions(df)
                    }
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze data: {str(e)}")


@router.post("/api/data-cleaning/clean-data")
async def clean_data_endpoint(request: Request):
    """Clean data based on selected options"""
    try:
        request_data = await request.json()
        print(f"Received request data: {request_data}")  # Debug log
    except Exception as e:
        print(f"JSON parsing error: {e}")  # Debug log
        raise HTTPException(status_code=400, detail=f"Invalid JSON in request body: {str(e)}")
        
    connection_id = request_data.get("connection_id")
    table_name = request_data.get("table_name")  # Optional for database connections
    cleaning_options = request_data.get("cleaning_options", {})
    
    if not connection_id:
        raise HTTPException(status_code=400, detail="Connection ID required")
    
    try:
        from data_cleaner import DataCleaner
        import tempfile
        import os
        import time
        
        # Get data based on connection type
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "file":
            import pandas as pd
            file_path = connection_info.get("file_path")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            df = pd.read_csv(file_path)
        else:
            # For database connections, get first table if no table specified
            if not table_name:
                tables = get_table_list(connection_id)
                if not tables:
                    raise HTTPException(status_code=404, detail="No tables found")
                table_name = tables[0]
            
            df = get_table_data(connection_id, table_name)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Use DataCleaner class
        cleaner = DataCleaner(df)
        
        # Apply cleaning options
        if cleaning_options.get("drop_nulls", False):
            cleaner.drop_null_values()
        
        if cleaning_options.get("drop_duplicates", False):
            cleaner.drop_duplicates()
            
        if cleaning_options.get("fill_missing", False):
            fill_method = cleaning_options.get("fill_method", "mean")
            cleaner.fill_missing_values(method=fill_method)
        
        # Export cleaned data
        filename = f"cleaned_data_{connection_id}_{int(time.time())}.csv"
        export_path = cleaner.export_to_csv(filename)
        
        # Get basic stats without complex objects
        original_shape = cleaner.stats["original_shape"]
        final_shape = cleaner.df.shape
        
        # Create a simple, JSON-safe response
        return {
            "success": True,
            "message": "Data cleaned successfully",
            "filename": filename,
            "data": {
                "original_shape": [int(original_shape[0]), int(original_shape[1])],
                "final_shape": [int(final_shape[0]), int(final_shape[1])],
                "original_nulls": int(cleaner.stats["original_nulls"]),
                "original_duplicates": int(cleaner.stats["original_duplicates"]),
                "final_nulls": int(cleaner.df.isnull().sum().sum()),
                "final_duplicates": int(cleaner.df.duplicated().sum()),
                "rows_removed": int(original_shape[0] - final_shape[0]),
                "cleaning_operations": len(cleaner.cleaning_log)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean data: {str(e)}")


@router.get("/api/data-cleaning/download/{filename}")
async def download_cleaned_data(filename: str):
    """Download cleaned data file"""
    try:
        import tempfile
        import os
        from fastapi.responses import FileResponse
        
        file_path = os.path.join(tempfile.gettempdir(), filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/csv'
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


def get_type_conversion_suggestions(df):
    """Get suggestions for data type conversions"""
    suggestions = {}
    
    for col in df.columns:
        current_type = str(df[col].dtype)
        
        # Check if object column can be converted to numeric
        if current_type == 'object':
            try:
                pd.to_numeric(df[col].dropna().head(100), errors='raise')
                suggestions[col] = {
                    'current': current_type,
                    'suggested': 'numeric',
                    'reason': 'Column contains numeric values stored as text'
                }
            except:
                # Check if it could be datetime
                try:
                    pd.to_datetime(df[col].dropna().head(100), errors='raise')
                    suggestions[col] = {
                        'current': current_type,
                        'suggested': 'datetime',
                        'reason': 'Column contains date/time values'
                    }
                except:
                    # Check if it should be category
                    unique_ratio = df[col].nunique() / len(df)
                    if unique_ratio < 0.05:  # Less than 5% unique values
                        suggestions[col] = {
                            'current': current_type,
                            'suggested': 'category',
                            'reason': 'Low cardinality, suitable for categorical type'
                        }
    
    return suggestions
