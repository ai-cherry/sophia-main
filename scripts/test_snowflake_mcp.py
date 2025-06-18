#!/usr/bin/env python3
"""
Simple test script for Snowflake MCP Server
Tests basic connectivity and operations
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mcp.mcp_client import MCPClient


async def test_snowflake_mcp():
    """Test Snowflake MCP server functionality"""
    print("🧪 Testing Snowflake MCP Server")
    print("=" * 50)
    
    # Initialize client
    client = MCPClient("http://localhost:8090")
    
    try:
        # Connect to MCP gateway
        print("\n1. Connecting to MCP gateway...")
        await client.connect()
        print("✅ Connected successfully")
        
        # List available servers
        print("\n2. Available MCP servers:")
        servers = client.list_servers()
        for server in servers:
            print(f"   - {server}")
        
        # List Snowflake tools
        print("\n3. Snowflake MCP tools:")
        tools = client.list_tools("snowflake")
        for tool in tools:
            tool_info = client.get_tool_info(tool)
            print(f"   - {tool}: {tool_info.get('description', 'No description')}")
        
        # Test basic operations (if Snowflake is configured)
        if os.getenv("SNOWFLAKE_ACCOUNT"):
            print("\n4. Testing Snowflake operations:")
            
            # List tables
            print("   - Listing tables...")
            result = await client.call_tool("snowflake", "list_tables")
            if result.get("success"):
                tables = result.get("tables", [])
                print(f"   ✅ Found {len(tables)} tables")
                for table in tables[:5]:  # Show first 5
                    print(f"      • {table}")
            else:
                print(f"   ❌ Error: {result.get('error')}")
            
            # Test query
            print("\n   - Testing query execution...")
            result = await client.call_tool(
                "snowflake", 
                "execute_query",
                query="SELECT CURRENT_VERSION() as version, CURRENT_DATABASE() as db"
            )
            if result.get("success"):
                rows = result.get("rows", [])
                if rows:
                    print(f"   ✅ Snowflake version: {rows[0].get('VERSION')}")
                    print(f"   ✅ Current database: {rows[0].get('DB')}")
            else:
                print(f"   ❌ Error: {result.get('error')}")
        else:
            print("\n⚠️  Snowflake credentials not configured in .env")
            print("   Add SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, etc. to test operations")
        
        print("\n✅ MCP test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


async def test_mcp_workflow():
    """Test a multi-step MCP workflow"""
    print("\n\n🔄 Testing MCP Workflow Execution")
    print("=" * 50)
    
    client = MCPClient("http://localhost:8090")
    
    try:
        await client.connect()
        
        # Define a simple workflow
        workflow = [
            {
                "server": "snowflake",
                "tool": "list_tables",
                "parameters": {},
                "store_as": "tables"
            },
            {
                "server": "snowflake",
                "tool": "describe_table",
                "parameters": {
                    "table_name": "$tables.tables.0"  # Use first table from previous step
                },
                "stop_on_error": True
            }
        ]
        
        print("Executing workflow:")
        print("1. List tables")
        print("2. Describe first table")
        
        results = await client.execute_workflow(workflow)
        
        print(f"\nWorkflow completed with {len(results)} steps")
        for i, result in enumerate(results):
            status = "✅" if result.get("success") else "❌"
            print(f"Step {i+1}: {status}")
            
    except Exception as e:
        print(f"\n❌ Workflow test failed: {e}")
    finally:
        await client.close()


async def main():
    """Main test execution"""
    # Basic connectivity test
    await test_snowflake_mcp()
    
    # Workflow test (if connected)
    if os.getenv("SNOWFLAKE_ACCOUNT"):
        await test_mcp_workflow()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Configure other services in docker-compose.mcp.yml")
    print("2. Implement HubSpot and Asana MCP servers")
    print("3. Use MCP tools in your AI agents")


if __name__ == "__main__":
    asyncio.run(main()) 