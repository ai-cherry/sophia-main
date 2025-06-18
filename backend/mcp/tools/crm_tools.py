import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

from ..sophia_mcp_server import MCPTool
from ...core.secret_manager import secret_manager

class CrmSyncTool(MCPTool):
    """Tool for synchronizing data with CRM systems"""
    
    def __init__(self):
        super().__init__(
            name="crm_sync",
            description="Synchronize data with CRM systems (HubSpot, Salesforce)",
            parameters={
                "crm_type": {
                    "type": "string",
                    "description": "Type of CRM to sync with",
                    "enum": ["hubspot", "salesforce"],
                    "required": True
                },
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity to sync",
                    "enum": ["contact", "company", "deal", "ticket"],
                    "required": True
                },
                "data": {
                    "type": "object",
                    "description": "Data to sync",
                    "required": True
                },
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": ["create", "update", "upsert"],
                    "required": False,
                    "default": "upsert"
                },
                "external_id": {
                    "type": "string",
                    "description": "External ID for the entity (required for update/upsert)",
                    "required": False
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.hubspot_client = None
        self.salesforce_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        crm_type = parameters["crm_type"]
        entity_type = parameters["entity_type"]
        data = parameters["data"]
        operation = parameters.get("operation", "upsert")
        external_id = parameters.get("external_id")
        
        # Validate parameters
        if operation in ["update", "upsert"] and not external_id:
            return {
                "success": False,
                "error": "External ID is required for update/upsert operations"
            }
        
        try:
            # Perform operation based on CRM type
            if crm_type == "hubspot":
                result = await self._sync_hubspot(entity_type, data, operation, external_id)
            elif crm_type == "salesforce":
                result = await self._sync_salesforce(entity_type, data, operation, external_id)
            else:
                raise ValueError(f"Unsupported CRM type: {crm_type}")
            
            # Prepare response
            response = {
                "success": True,
                "crm_type": crm_type,
                "entity_type": entity_type,
                "operation": operation,
                "result": result,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error syncing with CRM: {e}")
            return {
                "success": False,
                "error": str(e),
                "crm_type": crm_type,
                "entity_type": entity_type,
                "operation": operation
            }
    
    async def _sync_hubspot(self, entity_type: str, data: Dict[str, Any], operation: str, external_id: Optional[str]) -> Dict[str, Any]:
        """Sync data with HubSpot"""
        if not self.hubspot_client:
            import hubspot
            
            api_key = await secret_manager.get_secret("api_key", "hubspot")
            self.hubspot_client = hubspot.Client.create(api_key=api_key)
        
        # Map entity types to HubSpot endpoints
        entity_map = {
            "contact": "contacts",
            "company": "companies",
            "deal": "deals",
            "ticket": "tickets"
        }
        
        if entity_type not in entity_map:
            raise ValueError(f"Unsupported entity type for HubSpot: {entity_type}")
        
        hubspot_entity = entity_map[entity_type]
        
        # Prepare data for HubSpot
        hubspot_data = self._prepare_hubspot_data(entity_type, data)
        
        # Perform operation
        if operation == "create":
            # Create new entity
            api_response = self.hubspot_client.crm[hubspot_entity].basic_api.create(
                body=hubspot_data
            )
            
            return {
                "id": api_response.id,
                "created": True
            }
            
        elif operation == "update":
            # Update existing entity
            api_response = self.hubspot_client.crm[hubspot_entity].basic_api.update(
                record_id=external_id,
                body=hubspot_data
            )
            
            return {
                "id": external_id,
                "updated": True
            }
            
        elif operation == "upsert":
            # Try to update, create if not exists
            try:
                # Try to update
                api_response = self.hubspot_client.crm[hubspot_entity].basic_api.update(
                    record_id=external_id,
                    body=hubspot_data
                )
                
                return {
                    "id": external_id,
                    "updated": True,
                    "created": False
                }
                
            except hubspot.exceptions.ApiException as e:
                if e.status == 404:
                    # Entity not found, create new
                    api_response = self.hubspot_client.crm[hubspot_entity].basic_api.create(
                        body=hubspot_data
                    )
                    
                    return {
                        "id": api_response.id,
                        "updated": False,
                        "created": True
                    }
                else:
                    # Other error
                    raise
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    async def _sync_salesforce(self, entity_type: str, data: Dict[str, Any], operation: str, external_id: Optional[str]) -> Dict[str, Any]:
        """Sync data with Salesforce"""
        if not self.salesforce_client:
            from simple_salesforce import Salesforce
            
            username = await secret_manager.get_secret("username", "salesforce")
            password = await secret_manager.get_secret("password", "salesforce")
            security_token = await secret_manager.get_secret("security_token", "salesforce")
            
            self.salesforce_client = Salesforce(
                username=username,
                password=password,
                security_token=security_token
            )
        
        # Map entity types to Salesforce objects
        entity_map = {
            "contact": "Contact",
            "company": "Account",
            "deal": "Opportunity",
            "ticket": "Case"
        }
        
        if entity_type not in entity_map:
            raise ValueError(f"Unsupported entity type for Salesforce: {entity_type}")
        
        salesforce_object = entity_map[entity_type]
        
        # Prepare data for Salesforce
        salesforce_data = self._prepare_salesforce_data(entity_type, data)
        
        # Perform operation
        if operation == "create":
            # Create new entity
            result = self.salesforce_client.__getattr__(salesforce_object).create(salesforce_data)
            
            if result["success"]:
                return {
                    "id": result["id"],
                    "created": True
                }
            else:
                raise ValueError(f"Failed to create {entity_type}: {result['errors']}")
            
        elif operation == "update":
            # Update existing entity
            result = self.salesforce_client.__getattr__(salesforce_object).update(external_id, salesforce_data)
            
            if result == 204:  # HTTP 204 No Content indicates success
                return {
                    "id": external_id,
                    "updated": True
                }
            else:
                raise ValueError(f"Failed to update {entity_type}: {result}")
            
        elif operation == "upsert":
            # Upsert entity
            # Note: Salesforce upsert requires an external ID field to be defined on the object
            # For simplicity, we'll use a standard approach here
            try:
                # Try to update
                result = self.salesforce_client.__getattr__(salesforce_object).update(external_id, salesforce_data)
                
                if result == 204:  # HTTP 204 No Content indicates success
                    return {
                        "id": external_id,
                        "updated": True,
                        "created": False
                    }
                else:
                    raise ValueError(f"Failed to update {entity_type}: {result}")
                    
            except Exception as e:
                if "NOT_FOUND" in str(e):
                    # Entity not found, create new
                    result = self.salesforce_client.__getattr__(salesforce_object).create(salesforce_data)
                    
                    if result["success"]:
                        return {
                            "id": result["id"],
                            "updated": False,
                            "created": True
                        }
                    else:
                        raise ValueError(f"Failed to create {entity_type}: {result['errors']}")
                else:
                    # Other error
                    raise
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    def _prepare_hubspot_data(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for HubSpot API"""
        # HubSpot expects properties as a flat object
        properties = {}
        
        for key, value in data.items():
            # Handle nested objects
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    properties[f"{key}_{nested_key}"] = str(nested_value)
            else:
                properties[key] = str(value)
        
        return {
            "properties": properties
        }
    
    def _prepare_salesforce_data(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for Salesforce API"""
        # Map common field names to Salesforce field names
        field_map = {
            "contact": {
                "email": "Email",
                "firstName": "FirstName",
                "lastName": "LastName",
                "phone": "Phone",
                "company": "Company"
            },
            "company": {
                "name": "Name",
                "website": "Website",
                "industry": "Industry",
                "employees": "NumberOfEmployees"
            },
            "deal": {
                "name": "Name",
                "amount": "Amount",
                "stage": "StageName",
                "closeDate": "CloseDate"
            },
            "ticket": {
                "subject": "Subject",
                "description": "Description",
                "priority": "Priority",
                "status": "Status"
            }
        }
        
        # Prepare data
        salesforce_data = {}
        
        for key, value in data.items():
            # Map field name if exists in map
            if key in field_map.get(entity_type, {}):
                salesforce_key = field_map[entity_type][key]
            else:
                # Use original key if no mapping exists
                salesforce_key = key
            
            # Handle nested objects
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    nested_salesforce_key = f"{salesforce_key}_{nested_key}"
                    salesforce_data[nested_salesforce_key] = nested_value
            else:
                salesforce_data[salesforce_key] = value
        
        return salesforce_data

class CrmQueryTool(MCPTool):
    """Tool for querying data from CRM systems"""
    
    def __init__(self):
        super().__init__(
            name="crm_query",
            description="Query data from CRM systems (HubSpot, Salesforce)",
            parameters={
                "crm_type": {
                    "type": "string",
                    "description": "Type of CRM to query",
                    "enum": ["hubspot", "salesforce"],
                    "required": True
                },
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity to query",
                    "enum": ["contact", "company", "deal", "ticket"],
                    "required": True
                },
                "query_type": {
                    "type": "string",
                    "description": "Type of query to perform",
                    "enum": ["get_by_id", "search", "list"],
                    "required": True
                },
                "query_params": {
                    "type": "object",
                    "description": "Parameters for the query",
                    "required": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "required": False,
                    "default": 10
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.hubspot_client = None
        self.salesforce_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        crm_type = parameters["crm_type"]
        entity_type = parameters["entity_type"]
        query_type = parameters["query_type"]
        query_params = parameters["query_params"]
        limit = parameters.get("limit", 10)
        
        try:
            # Perform query based on CRM type
            if crm_type == "hubspot":
                results = await self._query_hubspot(entity_type, query_type, query_params, limit)
            elif crm_type == "salesforce":
                results = await self._query_salesforce(entity_type, query_type, query_params, limit)
            else:
                raise ValueError(f"Unsupported CRM type: {crm_type}")
            
            # Prepare response
            response = {
                "success": True,
                "crm_type": crm_type,
                "entity_type": entity_type,
                "query_type": query_type,
                "results": results,
                "metadata": {
                    "count": len(results) if isinstance(results, list) else 1,
                    "limit": limit,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error querying CRM: {e}")
            return {
                "success": False,
                "error": str(e),
                "crm_type": crm_type,
                "entity_type": entity_type,
                "query_type": query_type
            }
    
    async def _query_hubspot(self, entity_type: str, query_type: str, query_params: Dict[str, Any], limit: int) -> Any:
        """Query data from HubSpot"""
        if not self.hubspot_client:
            import hubspot
            
            api_key = await secret_manager.get_secret("api_key", "hubspot")
            self.hubspot_client = hubspot.Client.create(api_key=api_key)
        
        # Map entity types to HubSpot endpoints
        entity_map = {
            "contact": "contacts",
            "company": "companies",
            "deal": "deals",
            "ticket": "tickets"
        }
        
        if entity_type not in entity_map:
            raise ValueError(f"Unsupported entity type for HubSpot: {entity_type}")
        
        hubspot_entity = entity_map[entity_type]
        
        # Perform query based on query type
        if query_type == "get_by_id":
            # Get entity by ID
            entity_id = query_params.get("id")
            if not entity_id:
                raise ValueError("ID is required for get_by_id query")
            
            api_response = self.hubspot_client.crm[hubspot_entity].basic_api.get_by_id(
                record_id=entity_id,
                properties=query_params.get("properties", [])
            )
            
            # Convert to dict
            result = api_response.to_dict()
            
            return result
            
        elif query_type == "search":
            # Search entities
            filter_groups = []
            
            # Process filters
            if "filters" in query_params:
                for filter_group in query_params["filters"]:
                    filters = []
                    
                    for filter_item in filter_group:
                        hubspot_filter = {
                            "propertyName": filter_item["property"],
                            "operator": filter_item["operator"],
                            "value": filter_item["value"]
                        }
                        filters.append(hubspot_filter)
                    
                    filter_groups.append({"filters": filters})
            
            # Create search request
            search_request = {
                "filterGroups": filter_groups,
                "sorts": query_params.get("sorts", []),
                "properties": query_params.get("properties", []),
                "limit": limit
            }
            
            api_response = self.hubspot_client.crm[hubspot_entity].search_api.do_search(
                body=search_request
            )
            
            # Convert to list of dicts
            results = [result.to_dict() for result in api_response.results]
            
            return results
            
        elif query_type == "list":
            # List entities
            api_response = self.hubspot_client.crm[hubspot_entity].basic_api.get_page(
                limit=limit,
                properties=query_params.get("properties", [])
            )
            
            # Convert to list of dicts
            results = [result.to_dict() for result in api_response.results]
            
            return results
            
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
    
    async def _query_salesforce(self, entity_type: str, query_type: str, query_params: Dict[str, Any], limit: int) -> Any:
        """Query data from Salesforce"""
        if not self.salesforce_client:
            from simple_salesforce import Salesforce
            
            username = await secret_manager.get_secret("username", "salesforce")
            password = await secret_manager.get_secret("password", "salesforce")
            security_token = await secret_manager.get_secret("security_token", "salesforce")
            
            self.salesforce_client = Salesforce(
                username=username,
                password=password,
                security_token=security_token
            )
        
        # Map entity types to Salesforce objects
        entity_map = {
            "contact": "Contact",
            "company": "Account",
            "deal": "Opportunity",
            "ticket": "Case"
        }
        
        if entity_type not in entity_map:
            raise ValueError(f"Unsupported entity type for Salesforce: {entity_type}")
        
        salesforce_object = entity_map[entity_type]
        
        # Perform query based on query type
        if query_type == "get_by_id":
            # Get entity by ID
            entity_id = query_params.get("id")
            if not entity_id:
                raise ValueError("ID is required for get_by_id query")
            
            result = self.salesforce_client.__getattr__(salesforce_object).get(entity_id)
            
            return result
            
        elif query_type == "search":
            # Search entities using SOQL
            where_clauses = []
            
            # Process filters
            if "filters" in query_params:
                for filter_item in query_params["filters"]:
                    field = filter_item["field"]
                    operator = filter_item["operator"]
                    value = filter_item["value"]
                    
                    # Format value based on type
                    if isinstance(value, str):
                        formatted_value = f"'{value}'"
                    else:
                        formatted_value = str(value)
                    
                    where_clauses.append(f"{field} {operator} {formatted_value}")
            
            # Build SOQL query
            fields = query_params.get("fields", ["Id", "Name"])
            fields_str = ", ".join(fields)
            
            soql = f"SELECT {fields_str} FROM {salesforce_object}"
            
            if where_clauses:
                soql += " WHERE " + " AND ".join(where_clauses)
            
            if "order_by" in query_params:
                soql += f" ORDER BY {query_params['order_by']}"
            
            soql += f" LIMIT {limit}"
            
            # Execute query
            query_result = self.salesforce_client.query(soql)
            
            # Extract records
            results = query_result["records"]
            
            return results
            
        elif query_type == "list":
            # List entities using SOQL
            fields = query_params.get("fields", ["Id", "Name"])
            fields_str = ", ".join(fields)
            
            soql = f"SELECT {fields_str} FROM {salesforce_object} LIMIT {limit}"
            
            # Execute query
            query_result = self.salesforce_client.query(soql)
            
            # Extract records
            results = query_result["records"]
            
            return results
            
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
