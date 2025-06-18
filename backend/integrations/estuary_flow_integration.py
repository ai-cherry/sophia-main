import logging
import json
import asyncio
import aiohttp
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from ..core.secret_manager import secret_manager

class EstuaryFlowClient:
    """Client for Estuary Flow real-time data streaming platform"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = None
        self.base_url = None
        self.session = None
        self.initialized = False
        
    async def setup(self):
        """Initialize the Estuary Flow client"""
        if self.initialized:
            return
        
        try:
            # Get API key from secret manager
            self.api_key = await secret_manager.get_secret("api_key", "estuary")
            
            # Get base URL from environment or use default
            self.base_url = os.environ.get("ESTUARY_API_URL", "https://api.estuary.dev")
            
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            self.initialized = True
            self.logger.info("Estuary Flow client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Estuary Flow client: {e}")
            raise
    
    async def close(self):
        """Close the Estuary Flow client"""
        if self.session:
            await self.session.close()
            self.session = None
            self.initialized = False
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Estuary Flow API"""
        if not self.initialized:
            await self.setup()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_text = await response.text()
                
                if response.status >= 400:
                    self.logger.error(f"Estuary Flow API error: {response.status} - {response_text}")
                    raise ValueError(f"Estuary Flow API error: {response.status} - {response_text}")
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"text": response_text}
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Estuary Flow API request error: {e}")
            raise
    
    async def create_capture(self, name: str, connector_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new capture (data source)"""
        payload = {
            "name": name,
            "connector_type": connector_type,
            "config": config
        }
        
        return await self._make_request("POST", "/v1/captures", json=payload)
    
    async def list_captures(self) -> List[Dict[str, Any]]:
        """List all captures"""
        response = await self._make_request("GET", "/v1/captures")
        return response.get("captures", [])
    
    async def get_capture(self, capture_id: str) -> Dict[str, Any]:
        """Get details of a specific capture"""
        return await self._make_request("GET", f"/v1/captures/{capture_id}")
    
    async def delete_capture(self, capture_id: str) -> Dict[str, Any]:
        """Delete a capture"""
        return await self._make_request("DELETE", f"/v1/captures/{capture_id}")
    
    async def create_materialization(self, name: str, connector_type: str, config: Dict[str, Any], bindings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new materialization (data destination)"""
        payload = {
            "name": name,
            "connector_type": connector_type,
            "config": config,
            "bindings": bindings
        }
        
        return await self._make_request("POST", "/v1/materializations", json=payload)
    
    async def list_materializations(self) -> List[Dict[str, Any]]:
        """List all materializations"""
        response = await self._make_request("GET", "/v1/materializations")
        return response.get("materializations", [])
    
    async def get_materialization(self, materialization_id: str) -> Dict[str, Any]:
        """Get details of a specific materialization"""
        return await self._make_request("GET", f"/v1/materializations/{materialization_id}")
    
    async def delete_materialization(self, materialization_id: str) -> Dict[str, Any]:
        """Delete a materialization"""
        return await self._make_request("DELETE", f"/v1/materializations/{materialization_id}")
    
    async def create_collection(self, name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection (data stream)"""
        payload = {
            "name": name,
            "schema": schema
        }
        
        return await self._make_request("POST", "/v1/collections", json=payload)
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        response = await self._make_request("GET", "/v1/collections")
        return response.get("collections", [])
    
    async def get_collection(self, collection_name: str) -> Dict[str, Any]:
        """Get details of a specific collection"""
        return await self._make_request("GET", f"/v1/collections/{collection_name}")
    
    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection"""
        return await self._make_request("DELETE", f"/v1/collections/{collection_name}")
    
    async def publish_events(self, collection_name: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Publish events to a collection"""
        payload = {
            "events": events
        }
        
        return await self._make_request("POST", f"/v1/collections/{collection_name}/publish", json=payload)
    
    async def create_derivation(self, name: str, source_collection: str, target_collection: str, transform_sql: str) -> Dict[str, Any]:
        """Create a new derivation (transformation)"""
        payload = {
            "name": name,
            "source_collection": source_collection,
            "target_collection": target_collection,
            "transform_sql": transform_sql
        }
        
        return await self._make_request("POST", "/v1/derivations", json=payload)
    
    async def list_derivations(self) -> List[Dict[str, Any]]:
        """List all derivations"""
        response = await self._make_request("GET", "/v1/derivations")
        return response.get("derivations", [])
    
    async def get_derivation(self, derivation_id: str) -> Dict[str, Any]:
        """Get details of a specific derivation"""
        return await self._make_request("GET", f"/v1/derivations/{derivation_id}")
    
    async def delete_derivation(self, derivation_id: str) -> Dict[str, Any]:
        """Delete a derivation"""
        return await self._make_request("DELETE", f"/v1/derivations/{derivation_id}")
    
    async def create_task(self, name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task (scheduled job)"""
        payload = {
            "name": name,
            "spec": spec
        }
        
        return await self._make_request("POST", "/v1/tasks", json=payload)
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        response = await self._make_request("GET", "/v1/tasks")
        return response.get("tasks", [])
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get details of a specific task"""
        return await self._make_request("GET", f"/v1/tasks/{task_id}")
    
    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task"""
        return await self._make_request("DELETE", f"/v1/tasks/{task_id}")
    
    async def create_snowflake_materialization(self, name: str, snowflake_config: Dict[str, Any], collections: List[str]) -> Dict[str, Any]:
        """Create a Snowflake materialization for the specified collections"""
        # Prepare bindings
        bindings = []
        for collection in collections:
            binding = {
                "resource": {
                    "name": collection
                },
                "target": {
                    "name": collection.replace("-", "_").upper()
                }
            }
            bindings.append(binding)
        
        # Create materialization
        return await self.create_materialization(
            name=name,
            connector_type="snowflake",
            config=snowflake_config,
            bindings=bindings
        )
    
    async def create_postgres_materialization(self, name: str, postgres_config: Dict[str, Any], collections: List[str]) -> Dict[str, Any]:
        """Create a PostgreSQL materialization for the specified collections"""
        # Prepare bindings
        bindings = []
        for collection in collections:
            binding = {
                "resource": {
                    "name": collection
                },
                "target": {
                    "name": collection.replace("-", "_").lower()
                }
            }
            bindings.append(binding)
        
        # Create materialization
        return await self.create_materialization(
            name=name,
            connector_type="postgres",
            config=postgres_config,
            bindings=bindings
        )
    
    async def create_hubspot_capture(self, name: str, hubspot_config: Dict[str, Any], entity_types: List[str]) -> Dict[str, Any]:
        """Create a HubSpot capture for the specified entity types"""
        # Add entity types to config
        config = {
            **hubspot_config,
            "entity_types": entity_types
        }
        
        # Create capture
        return await self.create_capture(
            name=name,
            connector_type="hubspot",
            config=config
        )
    
    async def create_salesforce_capture(self, name: str, salesforce_config: Dict[str, Any], objects: List[str]) -> Dict[str, Any]:
        """Create a Salesforce capture for the specified objects"""
        # Add objects to config
        config = {
            **salesforce_config,
            "objects": objects
        }
        
        # Create capture
        return await self.create_capture(
            name=name,
            connector_type="salesforce",
            config=config
        )
    
    async def create_gong_capture(self, name: str, gong_config: Dict[str, Any], entity_types: List[str]) -> Dict[str, Any]:
        """Create a Gong capture for the specified entity types"""
        # Add entity types to config
        config = {
            **gong_config,
            "entity_types": entity_types
        }
        
        # Create capture
        return await self.create_capture(
            name=name,
            connector_type="gong",
            config=config
        )
    
    async def setup_real_time_pipeline(self, source_config: Dict[str, Any], transform_sql: Optional[str], destination_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up a complete real-time data pipeline"""
        try:
            # 1. Create source capture
            capture_response = await self.create_capture(
                name=source_config["name"],
                connector_type=source_config["connector_type"],
                config=source_config["config"]
            )
            
            source_collection = capture_response["collection"]["name"]
            
            # 2. Create transformation if provided
            target_collection = source_collection
            if transform_sql:
                # Create target collection for transformed data
                target_collection = f"{source_collection}-transformed"
                
                # Create derivation
                await self.create_derivation(
                    name=f"{source_config['name']}-transform",
                    source_collection=source_collection,
                    target_collection=target_collection,
                    transform_sql=transform_sql
                )
            
            # 3. Create destination materialization
            materialization_response = await self.create_materialization(
                name=destination_config["name"],
                connector_type=destination_config["connector_type"],
                config=destination_config["config"],
                bindings=[
                    {
                        "resource": {
                            "name": target_collection
                        },
                        "target": destination_config.get("target", {"name": target_collection.replace("-", "_")})
                    }
                ]
            )
            
            # Return pipeline details
            return {
                "pipeline_id": str(uuid.uuid4()),
                "source": {
                    "capture_id": capture_response["id"],
                    "collection": source_collection
                },
                "transformation": {
                    "enabled": transform_sql is not None,
                    "target_collection": target_collection if transform_sql else None
                },
                "destination": {
                    "materialization_id": materialization_response["id"]
                },
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to set up real-time pipeline: {e}")
            raise
