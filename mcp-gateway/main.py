import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import aiohttp

CONFIG_PATH = os.environ.get("MCP_SERVERS_CONFIG", "/app/mcp_servers.json")

app = FastAPI(title="Sophia AI Real MCP Gateway")

@app.on_event("startup")
async def startup_event():
    # Load MCP servers from config file
    with open(CONFIG_PATH, "r") as f:
        app.state.mcp_servers = {s["name"]: s["url"] for s in json.load(f)}
    app.state.http_session = aiohttp.ClientSession()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.http_session.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "discovered_servers": list(app.state.mcp_servers.keys())}

@app.post("/tool-call")
async def tool_call(request: Request):
    payload = await request.json()
    server_name = payload.get("server")
    server_url = app.state.mcp_servers.get(server_name)
    if not server_url:
        return JSONResponse(status_code=404, content={"error": f"Server '{server_name}' not found in config."})
    try:
        async with app.state.http_session.post(f"{server_url}/mcp", json=payload) as response:
            response_json = await response.json()
            return JSONResponse(status_code=response.status, content=response_json)
    except aiohttp.ClientConnectorError as e:
        return JSONResponse(status_code=502, content={"error": f"Gateway could not connect to server '{server_name}'."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)}) 