"""
File upload and management utilities
"""
import pandas as pd
import numpy as np
import io
import json
import uuid
import os
import tempfile
from typing import Dict, Any
from fastapi import HTTPException, UploadFile

from redis_client import redis_client
from database import clean_numeric


def process_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """Process uploaded CSV file and create connection"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        content = file.file.read()
        
        # Try to parse CSV
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Save file to temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{connection_id}_{file.filename}")
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create connection info
        connection_info = {
            "id": connection_id,
            "type": "file",
            "filename": file.filename,
            "file_path": file_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "status": "connected"
        }
        
        # Store in Redis
        redis_client.setex(f"connection:{connection_id}", 3600, json.dumps(connection_info))
        
        # Get sample data
        sample_data = df.head(10).to_dict('records')
        
        # Clean sample data for JSON serialization
        for row in sample_data:
            for key, value in row.items():
                row[key] = clean_numeric(value)
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": f"Successfully uploaded {file.filename}",
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "sample_data": sample_data,
            "column_info": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "null_count": int(df[col].isna().sum()),
                    "unique_count": int(df[col].nunique())
                }
                for col in df.columns
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


def get_file_sample(connection_id: str, limit: int = 100) -> Dict[str, Any]:
    """Get sample data from uploaded file"""
    try:
        connection_info_data = redis_client.get(f"connection:{connection_id}")
        if not connection_info_data:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_info = json.loads(connection_info_data)
        
        if connection_info["type"] != "file":
            raise HTTPException(status_code=400, detail="Not a file connection")
        
        file_path = connection_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file
        df = pd.read_csv(file_path)
        
        # Get sample
        sample_df = df.head(limit)
        sample_data = sample_df.to_dict('records')
        
        # Clean sample data for JSON serialization
        for row in sample_data:
            for key, value in row.items():
                row[key] = clean_numeric(value)
        
        return {
            "connection_id": connection_id,
            "filename": connection_info.get("filename"),
            "total_rows": len(df),
            "sample_rows": len(sample_df),
            "columns": df.columns.tolist(),
            "sample_data": sample_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file sample: {str(e)}")


def get_analyzed_file_sample(connection_id: str) -> Dict[str, Any]:
    """Get analyzed sample data from uploaded file"""
    try:
        connection_info_data = redis_client.get(f"connection:{connection_id}")
        if not connection_info_data:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        connection_info = json.loads(connection_info_data)
        
        if connection_info["type"] != "file":
            raise HTTPException(status_code=400, detail="Not a file connection")
        
        file_path = connection_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file
        df = pd.read_csv(file_path)
        
        # Analyze data types and quality
        column_analysis = []
        
        for column in df.columns:
            col_data = df[column]
            
            # Determine suggested data type
            suggested_type = "text"
            if pd.api.types.is_numeric_dtype(col_data):
                if col_data.dtype == 'int64':
                    suggested_type = "integer"
                else:
                    suggested_type = "decimal"
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                suggested_type = "datetime"
            elif col_data.nunique() == 2:
                suggested_type = "boolean"
            
            # Calculate quality metrics
            completeness = (col_data.notna().sum() / len(col_data)) * 100
            uniqueness = (col_data.nunique() / len(col_data)) * 100
            
            column_analysis.append({
                "name": column,
                "current_type": str(col_data.dtype),
                "suggested_type": suggested_type,
                "completeness": clean_numeric(completeness),
                "uniqueness": clean_numeric(uniqueness),
                "null_count": int(col_data.isna().sum()),
                "unique_count": int(col_data.nunique()),
                "sample_values": col_data.dropna().head(3).tolist()
            })
        
        # Get sample data
        sample_df = df.head(50)
        sample_data = sample_df.to_dict('records')
        
        # Clean sample data for JSON serialization
        for row in sample_data:
            for key, value in row.items():
                row[key] = clean_numeric(value)
        
        return {
            "connection_id": connection_id,
            "filename": connection_info.get("filename"),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_analysis": column_analysis,
            "sample_data": sample_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")


def cleanup_file_connection(connection_id: str) -> Dict[str, Any]:
    """Clean up file connection and remove temporary files"""
    try:
        connection_info_data = redis_client.get(f"connection:{connection_id}")
        if connection_info_data:
            connection_info = json.loads(connection_info_data)
            
            # Remove temporary file
            file_path = connection_info.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove from Redis
        redis_client.delete(f"connection:{connection_id}")
        redis_client.delete(f"analysis:{connection_id}")
        redis_client.delete(f"varima:{connection_id}:file_data")
        
        return {"success": True, "message": "File connection cleaned up successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
