import os
import tempfile
import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

app = FastAPI(title="Pulumi AI MCP Server")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/mcp")
async def mcp_tool(request: Request):
    payload = await request.json()
    tool = payload.get("tool")
    params = payload.get("parameters", {})

    if tool == "generate_infrastructure":
        return await generate_infrastructure(params)
    elif tool == "preview_plan":
        return await preview_plan(params)
    elif tool == "apply_changes":
        return await apply_changes(params)
    else:
        return JSONResponse(status_code=400, content={"error": f"Unknown tool: {tool}"})

async def generate_infrastructure(params: Dict[str, Any]):
    prompt = params.get("prompt")
    language = params.get("language", "python")
    provider = params.get("provider", "aws")
    # Placeholder: In production, call Pulumi AI API or use LLM
    code = f"""# Pulumi {language} code for: {prompt}\n# Provider: {provider}\n"""
    return {"success": True, "code": code, "language": language, "provider": provider}

async def preview_plan(params: Dict[str, Any]):
    code = params.get("code")
    language = params.get("language", "python")
    # Write code to temp dir and run `pulumi preview`
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, f"main.{language if language != 'python' else 'py'}")
        with open(code_file, "w") as f:
            f.write(code)
        # Initialize Pulumi project (scaffold only)
        subprocess.run(["pulumi", "new", language, "--yes", "--force"], cwd=tmpdir, check=False)
        # Run preview
        result = subprocess.run(["pulumi", "preview", "--non-interactive"], cwd=tmpdir, capture_output=True, text=True)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}

async def apply_changes(params: Dict[str, Any]):
    code = params.get("code")
    language = params.get("language", "python")
    # Write code to temp dir and run `pulumi up`
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, f"main.{language if language != 'python' else 'py'}")
        with open(code_file, "w") as f:
            f.write(code)
        # Initialize Pulumi project (scaffold only)
        subprocess.run(["pulumi", "new", language, "--yes", "--force"], cwd=tmpdir, check=False)
        # Run up
        result = subprocess.run(["pulumi", "up", "--yes", "--non-interactive"], cwd=tmpdir, capture_output=True, text=True)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr} 