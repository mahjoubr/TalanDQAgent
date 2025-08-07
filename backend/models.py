"""
Data models for the Data Quality Pipeline API
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DatabaseConnection(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    db_type: str  # 'postgresql', 'mysql', 'sqlserver'


class PowerBIAuth(BaseModel):
    client_id: str
    client_secret: str
    tenant_id: str
    username: str
    password: str


class DbStoreRequest(BaseModel):
    email: str
    connections: List[DatabaseConnection]


class PowerBIEmbedRequest(BaseModel):
    workspace_id: str
    report_id: str
    access_token: str


class DataQualityMetrics(BaseModel):
    connection_id: str
    table_name: Optional[str] = None
    calculate_advanced: bool = False


class AnomalyDetectionRequest(BaseModel):
    connection_id: str
    table_name: Optional[str] = None
    target_columns: Optional[List[str]] = None
    window_size: int = 30
    threshold: float = 0.05


class ReportRequest(BaseModel):
    connection_id: str
    include_charts: bool = True
    format: str = "pdf"


class PowerBIDatasetCreate(BaseModel):
    name: str
    workspace_id: str
