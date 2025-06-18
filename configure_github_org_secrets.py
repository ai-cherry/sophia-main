#!/usr/bin/env python3
"""
SOPHIA AI System - GitHub Organization Secrets Configuration Script

This script configures GitHub organization secrets for CI/CD workflows.
It reads secrets from a .env file and sets them as GitHub organization secrets.

Requirements:
- Python 3.11+
- PyGithub package
- GitHub Personal Access Token with admin:org scope

Usage:
    python configure_github_org_secrets.py --env-file .env.secure --org ai-cherry
"""

import argparse
import os
import sys
from base64 import b64encode
from getpass import getpass
from typing import Dict, List, Optional, Tuple

try:
    from github import Github, GithubException, Organization
    from nacl import encoding, public
except ImportError:
    print("Required packages not installed. Installing...")
    os.system("pip install PyGithub pynacl")
    from github import Github, GithubException, Organization
    from nacl import encoding, public


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Configure GitHub organization secrets for SOPHIA AI System"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env.secure",
        help="Path to .env file containing secrets (default: .env.secure)",
    )
    parser.add_argument(
        "--org",
        type=str,
        help="GitHub organization name (e.g., ai-cherry)",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub Personal Access Token (if not provided, will prompt)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing secrets (names only, not values)",
    )
    parser.add_argument(
        "--delete",
        type=str,
        help="Delete a specific secret by name",
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete all secrets (will prompt for confirmation)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--visibility",
        type=str,
        default="all",
        choices=["all", "private", "selected"],
        help="Secret visibility (all, private, or selected repositories)",
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


def get_github_org(token: str, org_name: str) -> Organization.Organization:
    """Get GitHub organization object."""
    try:
        g = Github(token)
        org = g.get_organization(org_name)
        return org
    except GithubException as e:
        print(f"Error accessing GitHub organization: {e}")
        sys.exit(1)


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using the organization's public key."""
    public_key_bytes = public.PublicKey(
        public_key.encode("utf-8"), encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(public_key_bytes)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def set_org_secrets(
    org: Organization.Organization, 
    secrets: Dict[str, str], 
    visibility: str = "all",
    dry_run: bool = False
) -> None:
    """Set organization secrets."""
    # Get the organization's public key
    public_key = org.get_public_key()
    
    for key, value in secrets.items():
        # Skip empty values
        if not value:
            print(f"Skipping empty secret: {key}")
            continue
            
        if dry_run:
            print(f"Would set organization secret: {key} (visibility: {visibility})")
        else:
            try:
                encrypted_value = encrypt_secret(public_key.key, value)
                
                # For organization secrets, we need to use a different approach
                # The PyGithub library doesn't directly support setting visibility
                # We'll use the raw_data parameter to set the visibility
                headers = {"Accept": "application/vnd.github.v3+json"}
                org._requester.requestJsonAndCheck(
                    "PUT",
                    f"/orgs/{org.login}/actions/secrets/{key}",
                    input={
                        "encrypted_value": encrypted_value,
                        "key_id": public_key.key_id,
                        "visibility": visibility
                    },
                    headers=headers
                )
                
                print(f"Successfully set organization secret: {key}")
            except GithubException as e:
                print(f"Error setting organization secret {key}: {e}")


def list_org_secrets(org: Organization.Organization) -> None:
    """List organization secrets (names only)."""
    try:
        secrets = org.get_secrets()
        print("\nOrganization Secrets:")
        print("---------------------")
        for secret in secrets:
            print(f"- {secret.name} (Visibility: {secret.visibility})")
        print(f"\nTotal: {secrets.totalCount} secrets")
    except GithubException as e:
        print(f"Error listing organization secrets: {e}")


def delete_org_secret(org: Organization.Organization, secret_name: str, dry_run: bool = False) -> None:
    """Delete an organization secret."""
    if dry_run:
        print(f"Would delete organization secret: {secret_name}")
    else:
        try:
            org.delete_secret(secret_name)
            print(f"Successfully deleted organization secret: {secret_name}")
        except GithubException as e:
            print(f"Error deleting organization secret {secret_name}: {e}")


def delete_all_org_secrets(org: Organization.Organization, dry_run: bool = False) -> None:
    """Delete all organization secrets."""
    try:
        secrets = org.get_secrets()
        for secret in secrets:
            if dry_run:
                print(f"Would delete organization secret: {secret.name}")
            else:
                org.delete_secret(secret.name)
                print(f"Deleted organization secret: {secret.name}")
    except GithubException as e:
        print(f"Error deleting organization secrets: {e}")


def main() -> None:
    """Main function."""
    args = parse_args()
    
    # Get GitHub token
    token = args.token
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            token = getpass("GitHub Personal Access Token: ")
    
    # Get organization name
    org_name = args.org
    if not org_name:
        org_name = input("GitHub Organization name: ")
    
    # Get organization
    org = get_github_org(token, org_name)
    print(f"Connected to GitHub organization: {org.login}")
    
    # List secrets
    if args.list:
        list_org_secrets(org)
        return
    
    # Delete a specific secret
    if args.delete:
        delete_org_secret(org, args.delete, args.dry_run)
        return
    
    # Delete all secrets
    if args.delete_all:
        confirm = input("Are you sure you want to delete ALL organization secrets? (y/N): ")
        if confirm.lower() == "y":
            delete_all_org_secrets(org, args.dry_run)
        else:
            print("Operation cancelled.")
        return
    
    # Read secrets from .env file
    secrets = read_env_file(args.env_file)
    print(f"Read {len(secrets)} secrets from {args.env_file}")
    
    # Set secrets
    set_org_secrets(org, secrets, args.visibility, args.dry_run)
    
    if not args.dry_run:
        print("\nAll organization secrets have been configured successfully.")
        print("You can now use these secrets in your GitHub Actions workflows across the organization.")


if __name__ == "__main__":
    main()
