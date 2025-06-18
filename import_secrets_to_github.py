#!/usr/bin/env python3
"""
SOPHIA AI System - Import Secrets to GitHub Actions

This script imports secrets from a .env file to GitHub Actions secrets.
It uses the GitHub CLI to set secrets for a repository.

Requirements:
- Python 3.11+
- GitHub CLI (gh)

Usage:
    python import_secrets_to_github.py --env-file .env.secure --repo ai-cherry/sophia
"""

import argparse
import os
import subprocess
import sys
from typing import Dict, List, Optional


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Import secrets from a .env file to GitHub Actions"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env.secure",
        help="Path to .env file containing secrets (default: .env.secure)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="GitHub repository (e.g., ai-cherry/sophia)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return parser.parse_args()


def read_env_file(file_path: str) -> Dict[str, str]:
    """Read secrets from a .env file."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)

    secrets = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                key, value = line.split("=", 1)
                secrets[key.strip()] = value.strip()
            except ValueError:
                print(f"Warning: Skipping invalid line: {line}")
    
    return secrets


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if GitHub CLI is installed
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
        
        # Check if authenticated with GitHub
        result = subprocess.run(["gh", "auth", "status"], capture_output=True)
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def set_github_secret(repo: str, key: str, value: str, dry_run: bool = False) -> bool:
    """Set a GitHub Actions secret."""
    if dry_run:
        print(f"Would set GitHub secret: {key}")
        return True
    
    try:
        # Use GitHub CLI to set the secret
        process = subprocess.Popen(
            ["gh", "secret", "set", key, "--repo", repo],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=value)
        
        if process.returncode == 0:
            print(f"Successfully set GitHub secret: {key}")
            return True
        else:
            print(f"Error setting GitHub secret {key}: {stderr}")
            return False
    except subprocess.SubprocessError as e:
        print(f"Error executing GitHub CLI: {e}")
        return False


def main() -> None:
    """Main function."""
    args = parse_args()
    
    # Check if GitHub CLI is installed and authenticated
    if not check_gh_cli():
        print("Error: GitHub CLI is not installed or not authenticated.")
        print("Please install GitHub CLI and run 'gh auth login' to authenticate.")
        sys.exit(1)
    
    # Read secrets from .env file
    secrets = read_env_file(args.env_file)
    print(f"Read {len(secrets)} secrets from {args.env_file}")
    
    # Set GitHub Actions secrets
    success_count = 0
    for key, value in secrets.items():
        # Skip empty values
        if not value:
            print(f"Skipping empty secret: {key}")
            continue
        
        # Skip GitHub PAT (not allowed as a GitHub Actions secret)
        if key.startswith("GITHUB_"):
            print(f"Skipping GitHub secret: {key} (GitHub secrets cannot start with GITHUB_)")
            continue
            
        # Set the secret
        if set_github_secret(args.repo, key, value, args.dry_run):
            success_count += 1
    
    print(f"\nSuccessfully set {success_count} GitHub secrets for {args.repo}.")


if __name__ == "__main__":
    main()
