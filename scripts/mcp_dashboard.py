#!/usr/bin/env python3
"""
MCP Monitoring Dashboard for Sophia AI
Real-time monitoring of MCP server health and metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="Sophia AI MCP Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-healthy {
        color: #28a745;
    }
    .status-unhealthy {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Dashboard title
st.title("🤖 Sophia AI MCP Dashboard")
st.markdown("Real-time monitoring and control for MCP servers")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    gateway_url = st.text_input("MCP Gateway URL", value="http://localhost:8090")
    refresh_rate = st.slider("Refresh Rate (seconds)", 5, 60, 10)
    
    st.header("Filters")
    selected_servers = st.multiselect(
        "Select Servers",
        ["All", "snowflake", "pinecone", "pulumi", "hubspot", "asana", "gong"],
        default=["All"]
    )

# Main dashboard
async def fetch_server_status(session, url):
    """Fetch status of all MCP servers"""
    try:
        async with session.get(f"{url}/servers") as response:
            if response.status == 200:
                return await response.json()
            return []
    except Exception as e:
        st.error(f"Failed to connect to MCP gateway: {e}")
        return []

async def fetch_server_metrics(session, url, server_name):
    """Fetch metrics for a specific server"""
    try:
        async with session.get(f"{url}/servers/{server_name}/metrics") as response:
            if response.status == 200:
                return await response.json()
            return {}
    except:
        return {}

async def main():
    """Main dashboard loop"""
    # Create layout
    col1, col2, col3 = st.columns(3)
    
    # Metrics placeholders
    with col1:
        total_servers = st.empty()
    with col2:
        healthy_servers = st.empty()
    with col3:
        total_requests = st.empty()
    
    # Server status section
    st.header("Server Status")
    server_status_container = st.empty()
    
    # Metrics graphs
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Request Rate (per minute)")
        request_chart = st.empty()
    
    with col2:
        st.subheader("Response Time (ms)")
        response_chart = st.empty()
    
    # Tool usage section
    st.header("Tool Usage")
    tool_usage_container = st.empty()
    
    # Recent activity
    st.header("Recent Activity")
    activity_container = st.empty()
    
    # Main loop
    async with aiohttp.ClientSession() as session:
        while True:
            # Fetch server status
            servers = await fetch_server_status(session, gateway_url)
            
            if servers:
                # Update metrics
                total = len(servers)
                healthy = sum(1 for s in servers if s.get("status") == "healthy")
                
                total_servers.metric("Total Servers", total)
                healthy_servers.metric("Healthy Servers", healthy, delta=f"{healthy/total*100:.0f}%")
                
                # Server status table
                status_data = []
                for server in servers:
                    if "All" in selected_servers or server["name"] in selected_servers:
                        metrics = await fetch_server_metrics(session, gateway_url, server["name"])
                        status_data.append({
                            "Server": server["name"],
                            "Status": "🟢 Healthy" if server.get("status") == "healthy" else "🔴 Unhealthy",
                            "Uptime": server.get("uptime", "Unknown"),
                            "CPU %": metrics.get("cpu_percent", 0),
                            "Memory MB": metrics.get("memory_mb", 0),
                            "Tools": len(server.get("tools", [])),
                            "Requests": metrics.get("total_requests", 0)
                        })
                
                if status_data:
                    df = pd.DataFrame(status_data)
                    server_status_container.dataframe(df, use_container_width=True)
                
                # Request rate chart (mock data for demo)
                times = pd.date_range(end=datetime.now(), periods=20, freq='1min')
                request_data = pd.DataFrame({
                    'Time': times,
                    'Requests': [50 + i * 5 + (i % 3) * 10 for i in range(20)]
                })
                
                fig_requests = px.line(request_data, x='Time', y='Requests')
                fig_requests.update_layout(height=300)
                request_chart.plotly_chart(fig_requests, use_container_width=True)
                
                # Response time chart (mock data for demo)
                response_data = pd.DataFrame({
                    'Time': times,
                    'Response Time': [100 + i * 2 + (i % 5) * 20 for i in range(20)]
                })
                
                fig_response = px.line(response_data, x='Time', y='Response Time')
                fig_response.update_layout(height=300)
                response_chart.plotly_chart(fig_response, use_container_width=True)
                
                # Tool usage (mock data for demo)
                tool_data = pd.DataFrame({
                    'Tool': ['execute_query', 'get_contacts', 'create_task', 'semantic_search', 'get_calls'],
                    'Usage': [150, 120, 80, 200, 90]
                })
                
                fig_tools = px.bar(tool_data, x='Tool', y='Usage')
                fig_tools.update_layout(height=300)
                tool_usage_container.plotly_chart(fig_tools, use_container_width=True)
                
                # Recent activity (mock data for demo)
                activity_data = []
                for i in range(5):
                    activity_data.append({
                        "Time": (datetime.now() - timedelta(minutes=i*2)).strftime("%H:%M:%S"),
                        "Server": ["snowflake", "hubspot", "asana", "gong", "pinecone"][i % 5],
                        "Tool": ["execute_query", "get_contacts", "create_task", "get_calls", "semantic_search"][i % 5],
                        "Status": "✅ Success" if i % 3 != 0 else "❌ Failed",
                        "Duration": f"{100 + i * 20}ms"
                    })
                
                activity_df = pd.DataFrame(activity_data)
                activity_container.dataframe(activity_df, use_container_width=True)
                
                # Update total requests
                total_reqs = sum(metrics.get("total_requests", 0) for server in servers)
                total_requests.metric("Total Requests", f"{total_reqs:,}")
            
            # Wait before refresh
            await asyncio.sleep(refresh_rate)

# Run the dashboard
if __name__ == "__main__":
    # Add control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh Now"):
            st.experimental_rerun()
    with col2:
        if st.button("📊 Export Metrics"):
            st.info("Metrics export functionality coming soon!")
    with col3:
        if st.button("⚙️ Server Config"):
            st.info("Server configuration panel coming soon!")
    
    # Run async main
    asyncio.run(main()) 