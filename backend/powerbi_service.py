import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class PowerBIService:
    """Power BI Service for authentication and API operations"""
    
    def __init__(self):
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.login_url = "https://login.microsoftonline.com"
        self.resource = "https://analysis.windows.net/powerbi/api"
        
    async def authenticate(self, tenant_id: str, client_id: str, client_secret: str, 
                          username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate with Power BI using service principal or user credentials"""
        
        token_url = f"{self.login_url}/{tenant_id}/oauth2/v2.0/token"
        
        if username and password:
            # User authentication (Resource Owner Password Credentials)
            data = {
                'grant_type': 'password',
                'client_id': client_id,
                'client_secret': client_secret,
                'resource': self.resource,
                'scope': 'https://analysis.windows.net/powerbi/api/.default',
                'username': username,
                'password': password
            }
        else:
            # Service principal authentication (Client Credentials)
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://analysis.windows.net/powerbi/api/.default'
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return {
                        'access_token': token_data['access_token'],
                        'expires_in': token_data.get('expires_in', 3600),
                        'token_type': token_data.get('token_type', 'Bearer')
                    }
                else:
                    error_data = await response.json()
                    raise Exception(f"Authentication failed: {error_data.get('error_description', 'Unknown error')}")
    
    async def get_workspaces(self, access_token: str) -> List[Dict[str, Any]]:
        """Get list of Power BI workspaces"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/groups", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    raise Exception(f"Failed to fetch workspaces: {response.status}")
    
    async def get_reports(self, access_token: str, workspace_id: str) -> List[Dict[str, Any]]:
        """Get reports in a specific workspace"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/groups/{workspace_id}/reports"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    raise Exception(f"Failed to fetch reports: {response.status}")
    
    async def get_datasets(self, access_token: str, workspace_id: str) -> List[Dict[str, Any]]:
        """Get datasets in a specific workspace"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/groups/{workspace_id}/datasets"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    raise Exception(f"Failed to fetch datasets: {response.status}")
    
    async def get_embed_token(self, access_token: str, workspace_id: str, 
                             report_id: str, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Get embed token for a Power BI report"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare embed token request
        embed_request = {
            'reports': [{'id': report_id}],
            'targetWorkspaces': [{'id': workspace_id}]
        }
        
        if dataset_id:
            embed_request['datasets'] = [{'id': dataset_id}]
        
        url = f"{self.base_url}/GenerateToken"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=embed_request) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'token': data['token'],
                        'embed_url': f"https://app.powerbi.com/reportEmbed?reportId={report_id}&groupId={workspace_id}",
                        'expires_at': data.get('expiration', (datetime.now() + timedelta(hours=1)).isoformat())
                    }
                else:
                    error_data = await response.json()
                    raise Exception(f"Failed to get embed token: {error_data}")
    
    async def get_dataset_data(self, access_token: str, dataset_id: str, 
                              table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract data from a Power BI dataset"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # If no table name provided, get the first table
        if not table_name:
            tables_url = f"{self.base_url}/datasets/{dataset_id}/tables"
            async with aiohttp.ClientSession() as session:
                async with session.get(tables_url, headers=headers) as response:
                    if response.status == 200:
                        tables_data = await response.json()
                        tables = tables_data.get('value', [])
                        if tables:
                            table_name = tables[0]['name']
                        else:
                            raise Exception("No tables found in dataset")
        
        # Get data from the table
        data_url = f"{self.base_url}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(data_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    raise Exception(f"Failed to fetch dataset data: {response.status}")
    
    async def push_data_to_dataset(self, access_token: str, dataset_id: str, 
                                  table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Push data to a Power BI dataset"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        # Prepare data payload
        payload = {'rows': data}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                return response.status == 200
    
    async def create_dataset(self, access_token: str, workspace_id: str, 
                           dataset_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Power BI dataset"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/groups/{workspace_id}/datasets"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=dataset_config) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"Failed to create dataset: {error_data}")
    
    async def refresh_dataset(self, access_token: str, dataset_id: str) -> bool:
        """Trigger a dataset refresh"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/datasets/{dataset_id}/refreshes"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={}) as response:
                return response.status == 202
