"""
Data export utilities for CSV, statistics, and Power BI integration
"""
import pandas as pd
import numpy as np
import csv
import io
import json
import tempfile
import zipfile
import os
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from redis_client import redis_client
from database import get_connection_info, get_database_engine, get_table_data, clean_numeric
from analysis import get_cached_analysis, calculate_quality_metrics


def export_cleaned_data_csv(connection_id: str) -> StreamingResponse:
    """Export cleaned data as CSV"""
    try:
        connection_info = get_connection_info(connection_id)
        
        if connection_info["type"] == "database":
            engine = get_database_engine(connection_id)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Create CSV content for all tables
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Table", "Column", "Data_Type", "Null_Count", "Unique_Count", "Sample_Values"])
            
            for table_name in tables:
                try:
                    df = get_table_data(connection_id, table_name, limit=1000)
                    for column in df.columns:
                        col_data = df[column]
                        sample_values = col_data.dropna().head(3).tolist()
                        writer.writerow([
                            table_name,
                            column,
                            str(col_data.dtype),
                            col_data.isna().sum(),
                            col_data.nunique(),
                            str(sample_values)[:100]  # Limit sample values length
                        ])
                except Exception as e:
                    writer.writerow([table_name, "ERROR", str(e), "", "", ""])
            
        elif connection_info["type"] == "file":
            file_path = connection_info.get("file_path")
            if not file_path:
                raise HTTPException(status_code=400, detail="File path not found")
            
            df = pd.read_csv(file_path)
            output = io.StringIO()
            df.to_csv(output, index=False)
        else:
            raise HTTPException(status_code=400, detail="Unsupported connection type")
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cleaned_data.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def export_table_csv(connection_id: str, table_name: str) -> StreamingResponse:
    """Export specific table data as CSV"""
    try:
        df = get_table_data(connection_id, table_name, limit=50000)
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table_name}_data.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table export failed: {str(e)}")


def export_statistics_csv(connection_id: str) -> StreamingResponse:
    """Export comprehensive statistics with table-level metrics"""
    try:
        # Get cached analysis or run new analysis
        try:
            analysis_results = get_cached_analysis(connection_id)
        except:
            from analysis import analyze_all_tables
            analysis_results = analyze_all_tables(connection_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary header
        writer.writerow([
            "Table_Name", "Total_Rows", "Total_Columns", "Quality_Score", 
            "Completeness", "Validity", "Consistency", "Uniqueness", "Accuracy"
        ])
        
        # Write table-level statistics
        for table_name, metrics in analysis_results.get("table_results", {}).items():
            if "error" not in metrics:
                writer.writerow([
                    table_name,
                    metrics.get("total_rows", 0),
                    metrics.get("total_columns", 0),
                    clean_numeric(metrics.get("quality_score", 0)),
                    clean_numeric(metrics.get("completeness", 0)),
                    clean_numeric(metrics.get("validity", 0)),
                    clean_numeric(metrics.get("consistency", 0)),
                    clean_numeric(metrics.get("uniqueness", 0)),
                    clean_numeric(metrics.get("accuracy", 0))
                ])
        
        # Add column-level details
        writer.writerow([])  # Empty row
        writer.writerow([
            "Table_Name", "Column_Name", "Data_Type", "Completeness", 
            "Validity", "Consistency", "Uniqueness", "Accuracy", 
            "Null_Count", "Unique_Count", "Min_Value", "Max_Value", "Mean_Value"
        ])
        
        for table_name, metrics in analysis_results.get("table_results", {}).items():
            if "error" not in metrics and "column_metrics" in metrics:
                for column_name, col_metrics in metrics["column_metrics"].items():
                    writer.writerow([
                        table_name,
                        column_name,
                        col_metrics.get("data_type", ""),
                        clean_numeric(col_metrics.get("completeness", 0)),
                        clean_numeric(col_metrics.get("validity", 0)),
                        clean_numeric(col_metrics.get("consistency", 0)),
                        clean_numeric(col_metrics.get("uniqueness", 0)),
                        clean_numeric(col_metrics.get("accuracy", 0)),
                        col_metrics.get("null_count", 0),
                        col_metrics.get("unique_count", 0),
                        clean_numeric(col_metrics.get("min_value")),
                        clean_numeric(col_metrics.get("max_value")),
                        clean_numeric(col_metrics.get("mean_value"))
                    ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=quality_statistics.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics export failed: {str(e)}")


def create_powerbi_package(connection_id: str) -> Dict[str, Any]:
    """Create and return Power BI package with templates and data"""
    try:
        # Get analysis results
        try:
            analysis_results = get_cached_analysis(connection_id)
        except:
            from analysis import analyze_all_tables
            analysis_results = analyze_all_tables(connection_id)
        
        # Create temporary directory for package
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create statistics CSV
            stats_path = os.path.join(temp_dir, "quality_statistics.csv")
            with open(stats_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write table-level statistics
                writer.writerow([
                    "Table_Name", "Total_Rows", "Total_Columns", "Quality_Score", 
                    "Completeness", "Validity", "Consistency", "Uniqueness", "Accuracy"
                ])
                
                for table_name, metrics in analysis_results.get("table_results", {}).items():
                    if "error" not in metrics:
                        writer.writerow([
                            table_name,
                            metrics.get("total_rows", 0),
                            metrics.get("total_columns", 0),
                            clean_numeric(metrics.get("quality_score", 0)),
                            clean_numeric(metrics.get("completeness", 0)),
                            clean_numeric(metrics.get("validity", 0)),
                            clean_numeric(metrics.get("consistency", 0)),
                            clean_numeric(metrics.get("uniqueness", 0)),
                            clean_numeric(metrics.get("accuracy", 0))
                        ])
            
            # Check for Power BI template files
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            source_template = os.path.join(backend_dir, "dashboardDQ.pbit")
            source_pbix = os.path.join(backend_dir, "dashboardDQ.pbix")
            
            template_path = os.path.join(temp_dir, "dashboardDQ.pbit")
            pbix_path = os.path.join(temp_dir, "dashboardDQ.pbix")
            
            template_available = False
            pbix_available = False
            
            if os.path.exists(source_template):
                import shutil
                shutil.copy2(source_template, template_path)
                template_available = True
            
            if os.path.exists(source_pbix):
                import shutil
                shutil.copy2(source_pbix, pbix_path)
                pbix_available = True
            
            # Create setup guide
            guide_path = os.path.join(temp_dir, "SETUP_GUIDE.txt")
            
            simple_guide = f"""Power BI Data Quality Dashboard - Setup Guide

FILES INCLUDED:
- quality_statistics.csv (Data export file)
{f"- dashboardDQ.pbit (Power BI template file)" if template_available else ""}
{f"- dashboardDQ.pbix (Pre-built dashboard file)" if pbix_available else ""}

SETUP INSTRUCTIONS:
{f"1. Open dashboardDQ.pbit in Power BI Desktop" if template_available else "1. Open Power BI Desktop or Power BI Service"}
2. Import quality_statistics.csv as your data source
{f"3. The dashboard will auto-populate with visualizations" if template_available else "3. Create charts using the CSV data columns"}

The CSV file contains data ready for visualization in Power BI.
"""
            
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(simple_guide)
            
            # Create ZIP package
            zip_path = os.path.join(temp_dir, f"powerbi_package_{connection_id}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add statistics CSV
                zipf.write(stats_path, "data/quality_statistics.csv")
                
                # Add template files if available
                if template_available:
                    zipf.write(template_path, "template/dashboardDQ.pbit")
                
                if pbix_available:
                    zipf.write(pbix_path, "template/dashboardDQ.pbix")
                
                # Add setup guide
                zipf.write(guide_path, "SETUP_GUIDE.txt")
            
            # Read ZIP file content
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Store ZIP content in Redis temporarily (5 minutes)
            redis_client.setex(f"powerbi_package:{connection_id}", 300, zip_content)
            
            # Open Power BI Service in browser
            powerbi_url = "https://app.powerbi.com/"
            webbrowser.open(powerbi_url)
            
            return {
                "success": True,
                "message": "Power BI package created successfully",
                "download_url": f"/api/download/powerbi-package/{connection_id}",
                "powerbi_url": powerbi_url,
                "package_contents": {
                    "data_file": "data/quality_statistics.csv",
                    "template": "template/dashboardDQ.pbit" if template_available else None,
                    "dashboard": "template/dashboardDQ.pbix" if pbix_available else None,
                    "guide": "SETUP_GUIDE.txt"
                },
                "instructions": [
                    "Power BI Service opened in your browser",
                    "Download the package using the provided URL",
                    f"{'Template file included' if template_available else 'Dashboard creation ready'}",
                    "Follow the setup guide for complete instructions"
                ]
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package creation failed: {str(e)}")


def get_powerbi_package(connection_id: str) -> StreamingResponse:
    """Download Power BI package ZIP file"""
    try:
        zip_content = redis_client.get(f"powerbi_package:{connection_id}")
        if not zip_content:
            raise HTTPException(status_code=404, detail="Package not found or expired")
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=powerbi_package_{connection_id}.zip"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package download failed: {str(e)}")
