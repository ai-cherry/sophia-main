#!/bin/bash
# Sophia AI - Secret Synchronization CI Script
# This script is used in CI/CD pipelines to synchronize secrets between GitHub and Pulumi ESC

set -e

# Default values
GITHUB_ORG="ai-cherry"
PULUMI_ORG="ai-cherry"
PULUMI_ENV="sophia-production"
DIRECTION="github-to-pulumi"
DRY_RUN=false
OUTPUT_FILE="sync_results.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --github-org)
      GITHUB_ORG="$2"
      shift
      shift
      ;;
    --pulumi-org)
      PULUMI_ORG="$2"
      shift
      shift
      ;;
    --pulumi-env)
      PULUMI_ENV="$2"
      shift
      shift
      ;;
    --direction)
      DIRECTION="$2"
      shift
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required"
  exit 1
fi

if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
  echo "Error: PULUMI_ACCESS_TOKEN environment variable is required"
  exit 1
fi

# Print configuration
echo "GitHub Organization: $GITHUB_ORG"
echo "Pulumi Organization: $PULUMI_ORG"
echo "Pulumi Environment: $PULUMI_ENV"
echo "Direction: $DIRECTION"
echo "Dry Run: $DRY_RUN"
echo "Output File: $OUTPUT_FILE"

# Build command
CMD="python3 $(dirname "$0")/github_sync_bidirectional.py --github-org $GITHUB_ORG --pulumi-org $PULUMI_ORG --pulumi-env $PULUMI_ENV --direction $DIRECTION --output $OUTPUT_FILE"

if [ "$DRY_RUN" = true ]; then
  CMD="$CMD --dry-run"
fi

# Run synchronization
echo "Running synchronization..."
eval $CMD

# Check result
if [ $? -eq 0 ]; then
  echo "Synchronization completed successfully"
  exit 0
else
  echo "Synchronization failed"
  exit 1
fi

