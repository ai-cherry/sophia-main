#!/usr/bin/env python3
"""One-time secret setup script.

This script validates that `PULUMI_ACCESS_TOKEN` is set and then
synchronizes secrets from Pulumi ESC into local configuration files.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_ENV = f"{os.getenv('PULUMI_ORG', 'scoobyjava-org')}/default/sophia-ai-production"


def require_pulumi_token() -> str:
    token = os.getenv("PULUMI_ACCESS_TOKEN")
    if not token:
        sys.stderr.write("Error: PULUMI_ACCESS_TOKEN environment variable is required\n")
        sys.exit(1)
    return token


def ensure_pulumi_cli():
    try:
        subprocess.run(["pulumi", "version"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.stderr.write("Pulumi CLI not found. Please install Pulumi.\n")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Failed to run Pulumi CLI: {e}\n")
        sys.exit(1)


def load_esc_config(environment: str) -> dict:
    cmd = ["pulumi", "env", "open", environment, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Failed to load Pulumi ESC environment: {e.stderr}\n")
        sys.exit(1)


def write_env_file(env_vars: dict) -> None:
    path = Path(".env")
    lines = [f"{k}={v}" for k, v in env_vars.items()]
    path.write_text("\n".join(lines))
    print(f"✅ Wrote {path}")


def write_config(values: dict) -> None:
    path = Path("mcp_config.json")
    with path.open("w") as f:
        json.dump(values, f, indent=2)
    print(f"✅ Wrote {path}")


def main() -> None:
    require_pulumi_token()
    ensure_pulumi_cli()

    environment = os.getenv("PULUMI_ESC_ENV", DEFAULT_ENV)
    print(f"Syncing secrets from Pulumi ESC: {environment}")

    config = load_esc_config(environment)
    env_vars = config.get("environmentVariables", {})
    values = config.get("values", {})

    if env_vars:
        write_env_file(env_vars)
    if values:
        write_config(values)

    print("Secrets synchronized from Pulumi ESC.\n")


if __name__ == "__main__":
    main()
