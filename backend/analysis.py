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


def ensure_json_serializable(obj):
    """Recursively convert numpy/pandas types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj


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

    total_rows = int(len(df))  # Convert to Python int
    total_columns = int(len(df.columns))  # Convert to Python int
    
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
        try:
            non_null_count = col_data.notna().sum()
            completeness = float((non_null_count / total_rows) * 100) if total_rows > 0 else 0.0
        except Exception as e:
            print(f"Warning: Completeness calculation failed for column {column}: {str(e)}")
            completeness = 0.0
        completeness_scores.append(completeness)
        
        # Validity (data type consistency)
        validity = 100.0  # Start with perfect score
        if col_data.dtype == 'object':
            # For string columns, check for consistent format
            try:
                # Try to convert to numeric if possible
                pd.to_numeric(col_data.dropna(), errors='raise')
                validity = 95.0  # Slightly lower for mixed types
            except:
                validity = 100.0  # Pure string column
        
        validity_scores.append(validity)
        
        # Consistency (pattern adherence)
        consistency = completeness  # Simplified: consistency correlates with completeness
        consistency_scores.append(consistency)
        
        # Uniqueness (for key columns)
        try:
            non_null_count = col_data.notna().sum()
            if non_null_count > 0:
                unique_count = col_data.nunique()
                unique_ratio = float((unique_count / non_null_count) * 100)
                uniqueness = min(unique_ratio, 100.0)
            else:
                uniqueness = 0.0
        except Exception as e:
            print(f"Warning: Uniqueness calculation failed for column {column}: {str(e)}")
            uniqueness = 0.0
        uniqueness_scores.append(uniqueness)
        
        # Accuracy (outlier detection for numeric columns)
        accuracy = 100.0
        if pd.api.types.is_numeric_dtype(col_data):
            try:
                # Ensure we only work with numeric, non-null values
                numeric_col_data = col_data.dropna()
                if len(numeric_col_data) > 0:
                    Q1 = numeric_col_data.quantile(0.25)
                    Q3 = numeric_col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    if pd.notna(IQR) and IQR > 0:
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        # Use boolean indexing safely
                        outlier_mask = (numeric_col_data < lower_bound) | (numeric_col_data > upper_bound)
                        outliers = numeric_col_data[outlier_mask]
                        outlier_ratio = float(len(outliers) / len(numeric_col_data))
                        accuracy = max(0.0, 100.0 - (outlier_ratio * 100))
                    else:
                        accuracy = 100.0
                else:
                    accuracy = 100.0
            except Exception as e:
                print(f"Warning: Accuracy calculation failed for column {column}: {str(e)}")
                accuracy = 100.0
        
        accuracy_scores.append(accuracy)
        
        try:
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
        except Exception as e:
            print(f"Warning: Column metrics creation failed for column {column}: {str(e)}")
            column_metrics[column] = {
                "data_type": str(col_data.dtype),
                "completeness": 0.0,
                "validity": 0.0,
                "consistency": 0.0,
                "uniqueness": 0.0,
                "accuracy": 0.0,
                "null_count": 0,
                "unique_count": 0,
                "min_value": None,
                "max_value": None,
                "mean_value": None
            }
        
        # Ensure all metrics are JSON serializable
        column_metrics[column] = ensure_json_serializable(column_metrics[column])
    
    # Calculate overall quality scores
    try:
        overall_completeness = float(np.mean(completeness_scores)) if completeness_scores else 0.0
        overall_validity = float(np.mean(validity_scores)) if validity_scores else 0.0
        overall_consistency = float(np.mean(consistency_scores)) if consistency_scores else 0.0
        overall_uniqueness = float(np.mean(uniqueness_scores)) if uniqueness_scores else 0.0
        overall_accuracy = float(np.mean(accuracy_scores)) if accuracy_scores else 0.0
        
        # Ensure all values are finite
        overall_completeness = overall_completeness if np.isfinite(overall_completeness) else 0.0
        overall_validity = overall_validity if np.isfinite(overall_validity) else 0.0
        overall_consistency = overall_consistency if np.isfinite(overall_consistency) else 0.0
        overall_uniqueness = overall_uniqueness if np.isfinite(overall_uniqueness) else 0.0
        overall_accuracy = overall_accuracy if np.isfinite(overall_accuracy) else 0.0
    except Exception as e:
        print(f"Warning: Overall metrics calculation failed: {str(e)}")
        overall_completeness = overall_validity = overall_consistency = overall_uniqueness = overall_accuracy = 0.0
    
    # Calculate composite quality score
    try:
        quality_score = float(
            overall_completeness * 0.25 +
            overall_validity * 0.2 +
            overall_consistency * 0.2 +
            overall_uniqueness * 0.15 +
            overall_accuracy * 0.2
        )
        quality_score = quality_score if np.isfinite(quality_score) else 0.0
    except Exception as e:
        print(f"Warning: Quality score calculation failed: {str(e)}")
        quality_score = 0.0

    result = {
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
    
    # Ensure everything is JSON serializable
    return ensure_json_serializable(result)


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
            overall_quality = float(np.mean(overall_scores)) if overall_scores else 0.0
            
            analysis_result = {
                "connection_id": connection_id,
                "overall_quality_score": clean_numeric(overall_quality),
                "total_tables": int(len(tables)),
                "analyzed_tables": int(len([r for r in results.values() if "error" not in r])),
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
        analysis_result = ensure_json_serializable(analysis_result)
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
        
        # Get numeric columns for analysis
        numeric_cols = numeric_columns(df)
        
        if len(numeric_cols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 numeric columns required for VARIMA analysis")
        
        # Use the existing run_varima_detection function from varima_detector.py
        varima_results = run_varima_detection(df[numeric_cols], threshold=2.0, max_components=5)
        
        # Extract results
        anomaly_count = int(varima_results['anomaly_varima'].sum()) if 'anomaly_varima' in varima_results else 0
        anomaly_indices = varima_results[varima_results['anomaly_varima'] == True].index.tolist() if 'anomaly_varima' in varima_results else []
        
        result = {
            "connection_id": connection_id,
            "table_name": table_name,
            "total_observations": len(df),
            "numeric_columns": len(numeric_cols),
            "columns_analyzed": numeric_cols,
            "anomalies_detected": anomaly_count,
            "anomaly_indices": anomaly_indices,
            "anomaly_percentage": float(anomaly_count / len(df) * 100) if len(df) > 0 else 0.0,
            "model_summary": {
                "method": "VARIMA",
                "threshold": 2.0,
                "max_components": 5,
                "data_shape": list(df.shape),
                "numeric_columns_used": numeric_cols
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
        
        raw_data = json.loads(cached_data)
        
        # Transform data to match frontend expectations
        table_results = raw_data.get("table_results", {})
        
        # Calculate average metrics across all tables for combined_results
        all_completeness = []
        all_validity = []
        all_consistency = []
        all_uniqueness = []
        all_accuracy = []
        
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
                    "volumetry": clean_numeric(raw_data.get("overall_quality_score", 0))
                },
                "overall_score": clean_numeric(raw_data.get("overall_quality_score", 0)),
                "total_tables": raw_data.get("total_tables", 0),
                "analyzed_tables": raw_data.get("analyzed_tables", 0)
            },
            "table_results": table_results,
            "analyzed_tables": list(table_results.keys())
        }
        
        return formatted_response
        
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
        total_anomalies = 0
        total_records = 0
        tables_with_anomalies = 0
        
        for key in keys:
            # Keys are already strings when decode_responses=True
            table_name = key.split(':')[2]
            data = redis_client.get(key)
            if data:
                # Data is already decoded when decode_responses=True
                if isinstance(data, str):
                    table_result = json.loads(data)
                else:
                    table_result = data
                
                results[table_name] = table_result
                
                # Aggregate statistics for combined results
                if 'anomalies_detected' in table_result:
                    anomalies = table_result['anomalies_detected']
                    total_anomalies += anomalies
                    if anomalies > 0:
                        tables_with_anomalies += 1
                
                if 'total_observations' in table_result:
                    total_records += table_result['total_observations']
        
        # Calculate summary metrics
        anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0.0
        
        # Determine risk level based on anomaly rate
        if anomaly_rate == 0:
            risk_level = "low"
        elif anomaly_rate < 5:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Format response to match frontend expectations
        formatted_response = {
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
        
        return formatted_response
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without wrapping them
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cached VARIMA results: {str(e)}")
