#!/usr/bin/env python3
"""
Airbyte Cloud Integration for Pay Ready Multi-Source Data Pipeline
Integrates Gong, Salesforce, HubSpot, Slack data into unified Sophia database
"""

import asyncio
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import jwt
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AirbyteCredentials:
    """Airbyte Cloud API credentials"""
    access_token: str
    client_id: str
    client_secret: str
    base_url: str = "https://api.airbyte.com/v1"

@dataclass
class DataSourceConfig:
    """Configuration for each data source"""
    name: str
    source_type: str
    destination_id: str
    connection_config: Dict[str, Any]
    sync_frequency: str  # hourly, daily, weekly
    field_mappings: Dict[str, str]

class AirbyteCloudManager:
    """Manages Airbyte Cloud connections and data synchronization"""
    
    def __init__(self, credentials: AirbyteCredentials):
        self.credentials = credentials
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {credentials.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def decode_token_info(self) -> Dict[str, Any]:
        """Decode JWT token to get user and workspace information"""
        try:
            # Decode without verification for inspection (token is already validated by Airbyte)
            decoded = jwt.decode(self.credentials.access_token, options={"verify_signature": False})
            return {
                'user_id': decoded.get('user_id'),
                'client_id': decoded.get('client_id'),
                'expires_at': datetime.fromtimestamp(decoded.get('exp', 0)),
                'issued_at': datetime.fromtimestamp(decoded.get('iat', 0)),
                'scopes': decoded.get('scope', '').split()
            }
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return {}
    
    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all available workspaces"""
        try:
            response = self.session.get(f"{self.credentials.base_url}/workspaces")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Failed to get workspaces: {e}")
            return []
    
    async def get_sources(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all sources in a workspace"""
        try:
            response = self.session.get(
                f"{self.credentials.base_url}/sources",
                params={'workspaceId': workspace_id}
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return []
    
    async def get_destinations(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all destinations in a workspace"""
        try:
            response = self.session.get(
                f"{self.credentials.base_url}/destinations",
                params={'workspaceId': workspace_id}
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Failed to get destinations: {e}")
            return []
    
    async def create_gong_source(self, workspace_id: str, gong_credentials: Dict[str, str]) -> Optional[str]:
        """Create Gong source connector"""
        source_config = {
            "name": "Pay Ready Gong Source",
            "workspaceId": workspace_id,
            "configuration": {
                "sourceType": "gong",
                "access_key": gong_credentials['access_key'],
                "access_key_secret": gong_credentials['access_key_secret'],
                "start_date": (datetime.now() - timedelta(days=90)).isoformat()
            }
        }
        
        try:
            response = self.session.post(
                f"{self.credentials.base_url}/sources",
                json=source_config
            )
            response.raise_for_status()
            source_data = response.json()
            logger.info(f"Created Gong source: {source_data.get('sourceId')}")
            return source_data.get('sourceId')
        except Exception as e:
            logger.error(f"Failed to create Gong source: {e}")
            return None
    
    async def create_postgres_destination(self, workspace_id: str, db_config: Dict[str, str]) -> Optional[str]:
        """Create PostgreSQL destination for Sophia database"""
        destination_config = {
            "name": "Sophia Unified Database",
            "workspaceId": workspace_id,
            "configuration": {
                "destinationType": "postgres",
                "host": db_config['host'],
                "port": int(db_config['port']),
                "database": db_config['database'],
                "username": db_config['username'],
                "password": db_config['password'],
                "schema": "public",
                "ssl_mode": {
                    "mode": "prefer"
                }
            }
        }
        
        try:
            response = self.session.post(
                f"{self.credentials.base_url}/destinations",
                json=destination_config
            )
            response.raise_for_status()
            dest_data = response.json()
            logger.info(f"Created PostgreSQL destination: {dest_data.get('destinationId')}")
            return dest_data.get('destinationId')
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL destination: {e}")
            return None
    
    async def create_connection(self, source_id: str, destination_id: str, 
                              workspace_id: str, sync_frequency: str = "hourly") -> Optional[str]:
        """Create connection between source and destination"""
        connection_config = {
            "name": "Gong to Sophia Database",
            "sourceId": source_id,
            "destinationId": destination_id,
            "workspaceId": workspace_id,
            "configurations": {
                "streams": [
                    {
                        "name": "calls",
                        "syncMode": "incremental",
                        "destinationSyncMode": "append_dedup"
                    },
                    {
                        "name": "users", 
                        "syncMode": "full_refresh",
                        "destinationSyncMode": "overwrite"
                    }
                ]
            },
            "schedule": {
                "scheduleType": "cron",
                "cronExpression": "0 * * * *" if sync_frequency == "hourly" else "0 0 * * *"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.credentials.base_url}/connections",
                json=connection_config
            )
            response.raise_for_status()
            conn_data = response.json()
            logger.info(f"Created connection: {conn_data.get('connectionId')}")
            return conn_data.get('connectionId')
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    async def trigger_sync(self, connection_id: str) -> bool:
        """Trigger manual sync for a connection"""
        try:
            response = self.session.post(
                f"{self.credentials.base_url}/jobs",
                json={
                    "connectionId": connection_id,
                    "jobType": "sync"
                }
            )
            response.raise_for_status()
            job_data = response.json()
            logger.info(f"Triggered sync job: {job_data.get('jobId')}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger sync: {e}")
            return False

class DataDictionaryManager:
    """Manages central data dictionary and field mappings"""
    
    def __init__(self):
        self.data_dictionary = {}
        self.field_mappings = {}
        
    def load_data_dictionary(self, file_path: str = "/home/ubuntu/data_dictionary.json"):
        """Load existing data dictionary"""
        try:
            with open(file_path, 'r') as f:
                self.data_dictionary = json.load(f)
            logger.info(f"Loaded data dictionary with {len(self.data_dictionary)} fields")
        except FileNotFoundError:
            logger.info("No existing data dictionary found, starting fresh")
            self.data_dictionary = {}
    
    def save_data_dictionary(self, file_path: str = "/home/ubuntu/data_dictionary.json"):
        """Save data dictionary to file"""
        with open(file_path, 'w') as f:
            json.dump(self.data_dictionary, f, indent=2)
        logger.info(f"Saved data dictionary with {len(self.data_dictionary)} fields")
    
    def add_field_definition(self, field_name: str, definition: Dict[str, Any]):
        """Add or update field definition"""
        self.data_dictionary[field_name] = {
            'description': definition.get('description', ''),
            'data_type': definition.get('data_type', 'VARCHAR'),
            'source_systems': definition.get('source_systems', []),
            'business_rules': definition.get('business_rules', []),
            'validation_rules': definition.get('validation_rules', []),
            'apartment_industry_context': definition.get('apartment_industry_context', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def get_field_mappings(self, source_system: str) -> Dict[str, str]:
        """Get field mappings for a specific source system"""
        mappings = {}
        for standard_field, definition in self.data_dictionary.items():
            source_systems = definition.get('source_systems', [])
            for system in source_systems:
                if system['name'] == source_system:
                    mappings[system['field_name']] = standard_field
        return mappings

async def setup_pay_ready_data_pipeline():
    """Main function to set up Pay Ready's multi-source data pipeline"""
    
    # Initialize Airbyte credentials
    credentials = AirbyteCredentials(
        access_token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6Z1BPdmhDSC1Ic21OQnhhV3lnLU11dlF6dHJERTBDSEJHZDB2MVh0Vnk0In0.eyJleHAiOjE3NTAxNzA0MTcsImlhdCI6MTc1MDE2OTUxNywianRpIjoiYzAxMDRmODItOTQ3MC00NDJkLThiZDAtNDlmZDIzMDk5NTM0IiwiaXNzIjoiaHR0cHM6Ly9jbG91ZC5haXJieXRlLmNvbS9hdXRoL3JlYWxtcy9fYWlyYnl0ZS1hcHBsaWNhdGlvbi1jbGllbnRzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjkwNzJmYzI0LTE0MjUtNDBlNy05ZmU4LTg0ZWYxM2I2M2Q4MCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImQ3OGNhZDM2LWU4MDAtNDhjOS04NTcxLTFkYWNiZDFiMjE3YyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtX2FpcmJ5dGUtYXBwbGljYXRpb24tY2xpZW50cyJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudEhvc3QiOiIxNzIuMjMuMC4yNDMiLCJ1c2VyX2lkIjoiOTA3MmZjMjQtMTQyNS00MGU3LTlmZTgtODRlZjEzYjYzZDgwIiwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LWQ3OGNhZDM2LWU4MDAtNDhjOS04NTcxLTFkYWNiZDFiMjE3YyIsImNsaWVudEFkZHJlc3MiOiIxNzIuMjMuMC4yNDMiLCJjbGllbnRfaWQiOiJkNzhjYWQzNi1lODAwLTQ4YzktODU3MS0xZGFjYmQxYjIxN2MifQ.P8qAiLkkEO05MPEZJ1JfiE41aMQHxr7IoUxam-X66GtnSv_SvqUMgyxTg61Gmee6y7OU2EEcXaEmWzKPaqDFIXimXKrInn9DiOfMqB2gGfDiZmDmLT6rU9a5yHydflGNb8Z8V2hCvZDdpX48SmGtUUv-QEIytElP_LaYzaB20-fGXPwYCHzUEWZchC1N97xSWdYm-SneB_wNwNmAvoBZ3MYB9Il0LIwNAIJjihc6bnI9ka2Mlvxa1JbVp55vwmEDAOE86DAe6arJkOIz4xgjy6fvcSyqLQAPzcArdHHZJZe1WhJI2AZW64hzBXvUxuWooPH3eW-YGb6Vr2vSeOuHCQ",
        client_id="d78cad36-e800-48c9-8571-1dacbd1b217c",
        client_secret="VNZav8LJmsA3xKpoGMaZss3aDHuFS7da"
    )
    
    # Initialize managers
    airbyte = AirbyteCloudManager(credentials)
    data_dict = DataDictionaryManager()
    
    # Decode token info
    token_info = airbyte.decode_token_info()
    logger.info(f"Token expires at: {token_info.get('expires_at')}")
    logger.info(f"User ID: {token_info.get('user_id')}")
    
    # Get workspaces
    workspaces = await airbyte.get_workspaces()
    logger.info(f"Found {len(workspaces)} workspaces")
    
    if not workspaces:
        logger.error("No workspaces found - check credentials")
        return
    
    # Use first workspace (or find Sophia workspace)
    workspace_id = workspaces[0]['workspaceId']
    logger.info(f"Using workspace: {workspace_id}")
    
    # Get existing sources and destinations
    sources = await airbyte.get_sources(workspace_id)
    destinations = await airbyte.get_destinations(workspace_id)
    
    logger.info(f"Found {len(sources)} sources and {len(destinations)} destinations")
    
    # Gong credentials
    gong_credentials = {
        'access_key': 'TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N',
        'access_key_secret': 'eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU'
    }
    
    # Database configuration
    db_config = {
        'host': '170.9.9.253',
        'port': '5432',
        'database': 'sophia_unified_db',
        'username': 'sophia_user',
        'password': 'sophia_secure_2024'
    }
    
    # Create Gong source if it doesn't exist
    gong_source_id = None
    for source in sources:
        if 'gong' in source.get('name', '').lower():
            gong_source_id = source['sourceId']
            break
    
    if not gong_source_id:
        gong_source_id = await airbyte.create_gong_source(workspace_id, gong_credentials)
    
    # Create PostgreSQL destination if it doesn't exist
    postgres_dest_id = None
    for dest in destinations:
        if 'sophia' in dest.get('name', '').lower() or 'postgres' in dest.get('name', '').lower():
            postgres_dest_id = dest['destinationId']
            break
    
    if not postgres_dest_id:
        postgres_dest_id = await airbyte.create_postgres_destination(workspace_id, db_config)
    
    # Create connection if both source and destination exist
    if gong_source_id and postgres_dest_id:
        connection_id = await airbyte.create_connection(
            gong_source_id, postgres_dest_id, workspace_id, "hourly"
        )
        
        if connection_id:
            # Trigger initial sync
            await airbyte.trigger_sync(connection_id)
            logger.info("Successfully set up Gong to Sophia database pipeline!")
        else:
            logger.error("Failed to create connection")
    else:
        logger.error("Failed to create source or destination")
    
    return {
        'workspace_id': workspace_id,
        'gong_source_id': gong_source_id,
        'postgres_dest_id': postgres_dest_id,
        'token_info': token_info
    }

if __name__ == "__main__":
    result = asyncio.run(setup_pay_ready_data_pipeline())
    print(f"Pipeline setup result: {result}")

