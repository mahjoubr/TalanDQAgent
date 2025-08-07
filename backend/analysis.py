"""
Data quality analysis and anomaly detection utilities
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import json
from fastapi import HTTPException

from redis_client import redis_client
from database import get_connection_info, get_database_engine, get_table_data, clean_numeric
from varima_detector import (
    run_varima_detection,
    detect_varima_anomalies,
    VarimaCleaner,
    cleanData,
    numeric_columns,
    date_column_by_variance
)


def calculate_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive data quality metrics for a DataFrame"""
    if df.empty:
        return {
            "total_rows": 0,
            "total_columns": 0,
            "quality_score": 0,
            "completeness": 0,
            "validity": 0,
            "consistency": 0,
            "uniqueness": 0,
            "accuracy": 0,
            "column_metrics": {}
        }

    total_rows = len(df)
    total_columns = len(df.columns)
    
    # Calculate column-level metrics
    column_metrics = {}
    completeness_scores = []
    validity_scores = []
    consistency_scores = []
    uniqueness_scores = []
    accuracy_scores = []
    
    for column in df.columns:
        col_data = df[column]
        
        # Completeness (non-null ratio)
        completeness = (col_data.notna().sum() / total_rows) * 100
        completeness_scores.append(completeness)
        
        # Validity (data type consistency)
        validity = 100  # Start with perfect score
        if col_data.dtype == 'object':
            # For string columns, check for consistent format
            try:
                # Try to convert to numeric if possible
                pd.to_numeric(col_data.dropna(), errors='raise')
                validity = 95  # Slightly lower for mixed types
            except:
                validity = 100  # Pure string column
        
        validity_scores.append(validity)
        
        # Consistency (pattern adherence)
        consistency = completeness  # Simplified: consistency correlates with completeness
        consistency_scores.append(consistency)
        
        # Uniqueness (for key columns)
        unique_ratio = (col_data.nunique() / col_data.notna().sum()) * 100 if col_data.notna().sum() > 0 else 0
        uniqueness = min(unique_ratio, 100)
        uniqueness_scores.append(uniqueness)
        
        # Accuracy (outlier detection for numeric columns)
        accuracy = 100
        if pd.api.types.is_numeric_dtype(col_data):
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            outlier_ratio = len(outliers) / len(col_data.dropna()) if len(col_data.dropna()) > 0 else 0
            accuracy = max(0, 100 - (outlier_ratio * 100))
        
        accuracy_scores.append(accuracy)
        
        column_metrics[column] = {
            "data_type": str(col_data.dtype),
            "completeness": clean_numeric(completeness),
            "validity": clean_numeric(validity),
            "consistency": clean_numeric(consistency),
            "uniqueness": clean_numeric(uniqueness),
            "accuracy": clean_numeric(accuracy),
            "null_count": int(col_data.isna().sum()),
            "unique_count": int(col_data.nunique()),
            "min_value": clean_numeric(col_data.min()) if pd.api.types.is_numeric_dtype(col_data) else None,
            "max_value": clean_numeric(col_data.max()) if pd.api.types.is_numeric_dtype(col_data) else None,
            "mean_value": clean_numeric(col_data.mean()) if pd.api.types.is_numeric_dtype(col_data) else None
        }
    
    # Calculate overall quality scores
    overall_completeness = np.mean(completeness_scores) if completeness_scores else 0
    overall_validity = np.mean(validity_scores) if validity_scores else 0
    overall_consistency = np.mean(consistency_scores) if consistency_scores else 0
    overall_uniqueness = np.mean(uniqueness_scores) if uniqueness_scores else 0
    overall_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0
    
    # Calculate composite quality score
    quality_score = (
        overall_completeness * 0.25 +
        overall_validity * 0.2 +
        overall_consistency * 0.2 +
        overall_uniqueness * 0.15 +
        overall_accuracy * 0.2
    )
    
    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "quality_score": clean_numeric(quality_score),
        "completeness": clean_numeric(overall_completeness),
        "validity": clean_numeric(overall_validity),
        "consistency": clean_numeric(overall_consistency),
        "uniqueness": clean_numeric(overall_uniqueness),
        "accuracy": clean_numeric(overall_accuracy),
        "column_metrics": column_metrics
    }


def analyze_all_tables(connection_id: str) -> Dict[str, Any]:
    """Analyze data quality for all tables in a connection"""
    try:
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "database":
            engine = get_database_engine(connection_id)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            results = {}
            overall_scores = []
            
            for table_name in tables:
                try:
                    df = get_table_data(connection_id, table_name, limit=10000)
                    metrics = calculate_quality_metrics(df)
                    results[table_name] = metrics
                    overall_scores.append(metrics["quality_score"])
                except Exception as e:
                    results[table_name] = {
                        "error": f"Failed to analyze table: {str(e)}",
                        "quality_score": 0
                    }
            
            # Calculate overall database quality score
            overall_quality = np.mean(overall_scores) if overall_scores else 0
            
            analysis_result = {
                "connection_id": connection_id,
                "overall_quality_score": clean_numeric(overall_quality),
                "total_tables": len(tables),
                "analyzed_tables": len([r for r in results.values() if "error" not in r]),
                "table_results": results,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            
        elif connection_info["type"] == "file":
            # Handle file analysis
            file_path = connection_info.get("file_path")
            if not file_path:
                raise HTTPException(status_code=400, detail="File path not found")
            
            df = pd.read_csv(file_path)
            metrics = calculate_quality_metrics(df)
            
            analysis_result = {
                "connection_id": connection_id,
                "overall_quality_score": metrics["quality_score"],
                "total_tables": 1,
                "analyzed_tables": 1,
                "table_results": {"file_data": metrics},
                "timestamp": pd.Timestamp.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported connection type")
        
        # Cache results in Redis
        redis_client.setex(f"analysis:{connection_id}", 3600, json.dumps(analysis_result))
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def run_anomaly_detection(connection_id: str, table_name: Optional[str] = None) -> Dict[str, Any]:
    """Run VARIMA anomaly detection on data"""
    try:
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "database":
            if not table_name:
                raise HTTPException(status_code=400, detail="Table name required for database connections")
            
            df = get_table_data(connection_id, table_name, limit=50000)
            
        elif connection_info["type"] == "file":
            file_path = connection_info.get("file_path")
            if not file_path:
                raise HTTPException(status_code=400, detail="File path not found")
            df = pd.read_csv(file_path)
            table_name = "file_data"
        else:
            raise HTTPException(status_code=400, detail="Unsupported connection type")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No data available for analysis")
        
        # Clean and prepare data for VARIMA
        cleaner = VarimaCleaner()
        cleaned_data = cleaner.fit_transform(df)
        
        # Get numeric columns for analysis
        numeric_cols = numeric_columns(cleaned_data)
        
        if len(numeric_cols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 numeric columns required for VARIMA analysis")
        
        # Run VARIMA detection
        varima_results = run_varima_detection(cleaned_data[numeric_cols])
        
        # Detect anomalies
        anomalies = detect_varima_anomalies(
            cleaned_data[numeric_cols], 
            varima_results['residuals'], 
            threshold=0.05
        )
        
        result = {
            "connection_id": connection_id,
            "table_name": table_name,
            "total_observations": len(df),
            "numeric_columns": len(numeric_cols),
            "columns_analyzed": numeric_cols,
            "anomalies_detected": len(anomalies),
            "anomaly_indices": anomalies.tolist() if hasattr(anomalies, 'tolist') else list(anomalies),
            "model_summary": {
                "aic": clean_numeric(varima_results.get('aic')),
                "bic": clean_numeric(varima_results.get('bic')),
                "log_likelihood": clean_numeric(varima_results.get('log_likelihood'))
            },
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Cache results
        redis_client.setex(f"varima:{connection_id}:{table_name}", 3600, json.dumps(result))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


def get_cached_analysis(connection_id: str) -> Dict[str, Any]:
    """Get cached analysis results"""
    try:
        cached_data = redis_client.get(f"analysis:{connection_id}")
        if not cached_data:
            raise HTTPException(status_code=404, detail="No cached analysis found")
        
        return json.loads(cached_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid cached analysis data")


def get_cached_varima(connection_id: str) -> Dict[str, Any]:
    """Get cached VARIMA results"""
    try:
        # Get all VARIMA results for this connection
        pattern = f"varima:{connection_id}:*"
        keys = redis_client.keys(pattern)
        
        if not keys:
            raise HTTPException(status_code=404, detail="No cached VARIMA results found")
        
        results = {}
        for key in keys:
            table_name = key.decode().split(':')[2]
            data = redis_client.get(key)
            if data:
                results[table_name] = json.loads(data)
        
        return {
            "connection_id": connection_id,
            "tables": results,
            "total_tables": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cached VARIMA results: {str(e)}")
