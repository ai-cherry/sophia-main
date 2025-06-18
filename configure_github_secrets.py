#!/usr/bin/env python3
"""
SOPHIA AI System - GitHub Secrets Configuration Script

This script configures GitHub repository secrets for CI/CD workflows.
It reads secrets from a .env file and sets them as GitHub repository secrets.

Requirements:
- Python 3.11+
- PyGithub package
- GitHub Personal Access Token with repo scope

Usage:
    python configure_github_secrets.py --env-file .env --repo owner/repo
"""

import argparse
import os
import sys
from base64 import b64encode
from getpass import getpass
from typing import Dict, List, Optional, Tuple

try:
    from github import Github, GithubException, Repository
    from nacl import encoding, public
except ImportError:
    print("Required packages not installed. Installing...")
    os.system("pip install PyGithub pynacl")
    from github import Github, GithubException, Repository
    from nacl import encoding, public


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Configure GitHub repository secrets for SOPHIA AI System"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to .env file containing secrets (default: .env)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repository in format owner/repo (e.g., payready/sophia)",
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


def get_github_repo(token: str, repo_name: str) -> Repository.Repository:
    """Get GitHub repository object."""
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        return repo
    except GithubException as e:
        print(f"Error accessing GitHub repository: {e}")
        sys.exit(1)


def encrypt_secret(public_key: str, secret_value: str) -> Tuple[str, str]:
    """Encrypt a secret using the repository's public key."""
    public_key_bytes = public.PublicKey(
        public_key.encode("utf-8"), encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(public_key_bytes)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def set_repo_secrets(
    repo: Repository.Repository, secrets: Dict[str, str], dry_run: bool = False
) -> None:
    """Set repository secrets."""
    public_key = repo.get_public_key()
    
    for key, value in secrets.items():
        # Skip empty values
        if not value:
            print(f"Skipping empty secret: {key}")
            continue
            
        if dry_run:
            print(f"Would set secret: {key}")
        else:
            try:
                encrypted_value = encrypt_secret(public_key.key, value)
                repo.create_secret(key, encrypted_value, public_key.key_id)
                print(f"Successfully set secret: {key}")
            except GithubException as e:
                print(f"Error setting secret {key}: {e}")


def list_repo_secrets(repo: Repository.Repository) -> None:
    """List repository secrets (names only)."""
    try:
        secrets = repo.get_secrets()
        print("\nRepository Secrets:")
        print("-------------------")
        for secret in secrets:
            print(f"- {secret.name}")
        print(f"\nTotal: {secrets.totalCount} secrets")
    except GithubException as e:
        print(f"Error listing secrets: {e}")


def delete_repo_secret(repo: Repository.Repository, secret_name: str, dry_run: bool = False) -> None:
    """Delete a repository secret."""
    if dry_run:
        print(f"Would delete secret: {secret_name}")
    else:
        try:
            repo.delete_secret(secret_name)
            print(f"Successfully deleted secret: {secret_name}")
        except GithubException as e:
            print(f"Error deleting secret {secret_name}: {e}")


def delete_all_repo_secrets(repo: Repository.Repository, dry_run: bool = False) -> None:
    """Delete all repository secrets."""
    try:
        secrets = repo.get_secrets()
        for secret in secrets:
            if dry_run:
                print(f"Would delete secret: {secret.name}")
            else:
                repo.delete_secret(secret.name)
                print(f"Deleted secret: {secret.name}")
    except GithubException as e:
        print(f"Error deleting secrets: {e}")


def main() -> None:
    """Main function."""
    args = parse_args()
    
    # Get GitHub token
    token = args.token
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            token = getpass("GitHub Personal Access Token: ")
    
    # Get repository name
    repo_name = args.repo
    if not repo_name:
        repo_name = os.environ.get("GITHUB_REPOSITORY")
        if not repo_name:
            # Try to get from git remote
            try:
                import subprocess
                remote_url = subprocess.check_output(
                    ["git", "config", "--get", "remote.origin.url"], 
                    universal_newlines=True
                ).strip()
                if "github.com" in remote_url:
                    if remote_url.startswith("git@github.com:"):
                        repo_name = remote_url.split("git@github.com:")[1].split(".git")[0]
                    elif remote_url.startswith("https://github.com/"):
                        repo_name = remote_url.split("https://github.com/")[1].split(".git")[0]
            except (subprocess.SubprocessError, IndexError):
                pass
            
            if not repo_name:
                repo_name = input("GitHub Repository (owner/repo): ")
    
    # Get repository
    repo = get_github_repo(token, repo_name)
    print(f"Connected to GitHub repository: {repo.full_name}")
    
    # List secrets
    if args.list:
        list_repo_secrets(repo)
        return
    
    # Delete a specific secret
    if args.delete:
        delete_repo_secret(repo, args.delete, args.dry_run)
        return
    
    # Delete all secrets
    if args.delete_all:
        confirm = input("Are you sure you want to delete ALL secrets? (y/N): ")
        if confirm.lower() == "y":
            delete_all_repo_secrets(repo, args.dry_run)
        else:
            print("Operation cancelled.")
        return
    
    # Read secrets from .env file
    secrets = read_env_file(args.env_file)
    print(f"Read {len(secrets)} secrets from {args.env_file}")
    
    # Set secrets
    set_repo_secrets(repo, secrets, args.dry_run)
    
    if not args.dry_run:
        print("\nAll secrets have been configured successfully.")
        print("You can now use these secrets in your GitHub Actions workflows.")


if __name__ == "__main__":
    main()
