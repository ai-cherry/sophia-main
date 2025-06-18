"""
Snowflake MCP Server for Sophia AI
Handles Snowflake data warehouse operations with MFA support
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import snowflake.connector
from snowflake.connector import DictCursor
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from mcp_base import MCPServer, Tool, Resource


class SnowflakeMCPServer(MCPServer):
    """MCP Server for Snowflake operations"""
    
    def __init__(self):
        super().__init__("snowflake-mcp")
        self.connection = None
        self.auth_method = os.getenv("SNOWFLAKE_AUTH_METHOD", "password")
        self.config = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "role": os.getenv("SNOWFLAKE_ROLE")
        }
        
    async def setup(self):
        """Setup Snowflake connection and register tools"""
        # Establish connection
        await self.connect()
        
        # Register tools
        self.register_tool(Tool(
            name="execute_query",
            description="Execute a SQL query on Snowflake",
            parameters={
                "query": {"type": "string", "required": True, "description": "SQL query to execute"},
                "parameters": {"type": "array", "items": {"type": "any"}, "description": "Query parameters"},
                "limit": {"type": "integer", "default": 1000, "description": "Maximum rows to return"}
            },
            handler=self.execute_query
        ))
        
        self.register_tool(Tool(
            name="list_tables",
            description="List tables in the current database/schema",
            parameters={
                "schema": {"type": "string", "description": "Schema name (optional)"},
                "pattern": {"type": "string", "description": "Table name pattern (optional)"}
            },
            handler=self.list_tables
        ))
        
        self.register_tool(Tool(
            name="describe_table",
            description="Get schema information for a table",
            parameters={
                "table_name": {"type": "string", "required": True, "description": "Table name"},
                "schema": {"type": "string", "description": "Schema name (optional)"}
            },
            handler=self.describe_table
        ))
        
        self.register_tool(Tool(
            name="get_table_sample",
            description="Get a sample of data from a table",
            parameters={
                "table_name": {"type": "string", "required": True, "description": "Table name"},
                "sample_size": {"type": "integer", "default": 10, "description": "Number of rows to sample"},
                "schema": {"type": "string", "description": "Schema name (optional)"}
            },
            handler=self.get_table_sample
        ))
        
        self.register_tool(Tool(
            name="create_table",
            description="Create a new table in Snowflake",
            parameters={
                "table_name": {"type": "string", "required": True, "description": "Table name"},
                "columns": {"type": "object", "required": True, "description": "Column definitions"},
                "schema": {"type": "string", "description": "Schema name (optional)"}
            },
            handler=self.create_table
        ))
        
        self.register_tool(Tool(
            name="upload_dataframe",
            description="Upload a pandas DataFrame to Snowflake",
            parameters={
                "table_name": {"type": "string", "required": True, "description": "Target table name"},
                "data": {"type": "array", "required": True, "description": "Data as array of objects"},
                "if_exists": {"type": "string", "default": "append", "description": "append, replace, or fail"},
                "schema": {"type": "string", "description": "Schema name (optional)"}
            },
            handler=self.upload_dataframe
        ))
        
        # Register resources
        self.register_resource(Resource(
            name="connection_info",
            description="Current Snowflake connection information",
            uri="/snowflake/connection"
        ))
        
        self.register_resource(Resource(
            name="query_history",
            description="Recent query execution history",
            uri="/snowflake/history"
        ))
    
    async def connect(self):
        """Connect to Snowflake with appropriate authentication method"""
        try:
            if self.auth_method == "keypair":
                # Use key pair authentication
                private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
                if not private_key_path:
                    raise ValueError("SNOWFLAKE_PRIVATE_KEY_PATH not set for keypair auth")
                
                with open(private_key_path, "rb") as key_file:
                    private_key_obj = serialization.load_pem_private_key(
                        key_file.read(),
                        password=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "").encode() or None,
                        backend=default_backend()
                    )
                
                private_key_bytes = private_key_obj.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                self.config["private_key"] = private_key_bytes
                self.logger.info("Using key pair authentication")
                
            elif self.auth_method == "oauth":
                # Use OAuth authentication
                self.config["authenticator"] = "oauth"
                self.config["token"] = os.getenv("SNOWFLAKE_OAUTH_TOKEN")
                self.logger.info("Using OAuth authentication")
                
            else:
                # Use password authentication
                self.config["password"] = os.getenv("SNOWFLAKE_PASSWORD")
                self.logger.info("Using password authentication")
            
            # Create connection
            self.connection = snowflake.connector.connect(**self.config)
            self.logger.info("Successfully connected to Snowflake")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Snowflake: {e}")
            if "Multi-factor authentication is required" in str(e):
                self.logger.error("MFA is required. Please use key pair or OAuth authentication.")
            raise
    
    async def execute_query(self, query: str, parameters: Optional[List[Any]] = None, limit: int = 1000) -> Dict[str, Any]:
        """Execute a SQL query"""
        try:
            cursor = self.connection.cursor(DictCursor)
            
            # Add limit if SELECT query without LIMIT
            if query.strip().upper().startswith("SELECT") and "LIMIT" not in query.upper():
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            # Execute query
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            # Get results for SELECT queries
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                return {
                    "success": True,
                    "rows": rows,
                    "columns": columns,
                    "row_count": len(rows),
                    "query_id": cursor.sfqid
                }
            else:
                # For non-SELECT queries
                return {
                    "success": True,
                    "rows_affected": cursor.rowcount,
                    "query_id": cursor.sfqid
                }
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
    
    async def list_tables(self, schema: Optional[str] = None, pattern: Optional[str] = None) -> Dict[str, Any]:
        """List tables in the current database/schema"""
        try:
            query = "SHOW TABLES"
            if schema:
                query += f" IN SCHEMA {schema}"
            if pattern:
                query += f" LIKE '{pattern}'"
            
            result = await self.execute_query(query)
            
            if result.get("success"):
                tables = [row["name"] for row in result["rows"]]
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables)
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def describe_table(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """Get schema information for a table"""
        try:
            full_name = f"{schema}.{table_name}" if schema else table_name
            query = f"DESCRIBE TABLE {full_name}"
            
            result = await self.execute_query(query)
            
            if result.get("success"):
                columns = []
                for row in result["rows"]:
                    columns.append({
                        "name": row.get("name"),
                        "type": row.get("type"),
                        "nullable": row.get("null?") == "Y",
                        "default": row.get("default"),
                        "primary_key": row.get("primary key") == "Y"
                    })
                
                return {
                    "success": True,
                    "table": table_name,
                    "columns": columns
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_table_sample(self, table_name: str, sample_size: int = 10, schema: Optional[str] = None) -> Dict[str, Any]:
        """Get a sample of data from a table"""
        try:
            full_name = f"{schema}.{table_name}" if schema else table_name
            query = f"SELECT * FROM {full_name} SAMPLE ({sample_size} ROWS)"
            
            return await self.execute_query(query)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_table(self, table_name: str, columns: Dict[str, str], schema: Optional[str] = None) -> Dict[str, Any]:
        """Create a new table"""
        try:
            full_name = f"{schema}.{table_name}" if schema else table_name
            
            # Build column definitions
            col_defs = []
            for col_name, col_type in columns.items():
                col_defs.append(f"{col_name} {col_type}")
            
            query = f"CREATE TABLE {full_name} ({', '.join(col_defs)})"
            
            return await self.execute_query(query)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def upload_dataframe(self, table_name: str, data: List[Dict[str, Any]], 
                             if_exists: str = "append", schema: Optional[str] = None) -> Dict[str, Any]:
        """Upload data to Snowflake table"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Get full table name
            full_name = f"{schema}.{table_name}" if schema else table_name
            
            # Use Snowflake's write_pandas method
            success, nrows, nchunks, errors = self.connection.cursor().write_pandas(
                df, 
                table_name,
                database=self.config["database"],
                schema=schema or self.config["schema"],
                auto_create_table=(if_exists == "replace")
            )
            
            if success:
                return {
                    "success": True,
                    "rows_uploaded": nrows,
                    "chunks": nchunks
                }
            else:
                return {
                    "success": False,
                    "errors": errors
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.connection:
            self.connection.close()
            self.logger.info("Closed Snowflake connection")


async def main():
    """Main entry point"""
    server = SnowflakeMCPServer()
    try:
        # The new start method runs a web server
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down.")
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 