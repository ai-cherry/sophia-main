#!/bin/bash
# Sophia AI Integration Test Script
# This script runs integration tests for all configured services

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Sophia AI Integration Test Suite    ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
  if [ -f "integration.env.example" ]; then
    cp integration.env.example .env
    echo -e "${GREEN}Created .env file from template.${NC}"
    echo -e "${YELLOW}Please edit .env file to add your credentials before running tests.${NC}"
    exit 1
  else
    echo -e "${RED}Error: integration.env.example file not found.${NC}"
    exit 1
  fi
fi

# Check for required dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
  exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null; then
  echo -e "${RED}Error: pip3 is required but not installed.${NC}"
  exit 1
fi

# Install dependencies if needed
if [ ! -f ".deps_installed" ] || [ integration_requirements.txt -nt ".deps_installed" ]; then
  echo -e "${YELLOW}Installing dependencies...${NC}"
  pip3 install -r integration_requirements.txt
  touch .deps_installed
  echo -e "${GREEN}Dependencies installed successfully.${NC}"
fi

# Parse command line arguments
TESTS="all"
OUTPUT_FILE="integration_test_results.json"
VERBOSE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --tests)
      TESTS="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE="--verbose"
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [--tests test1,test2,...] [--output results.json] [--verbose]"
      exit 1
      ;;
  esac
done

# Run the tests
echo -e "${BLUE}Running integration tests: ${TESTS}${NC}"
echo -e "${BLUE}Results will be saved to: ${OUTPUT_FILE}${NC}"
echo ""

python3 unified_integration_test.py --tests "$TESTS" --output "$OUTPUT_FILE" $VERBOSE

# Check if tests were successful
if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}Integration tests completed successfully.${NC}"
  
  # Display a summary of the results
  echo -e "${BLUE}Summary:${NC}"
  cat "$OUTPUT_FILE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Overall status: {data['status'].upper()}\")
print(f\"Tests run: {len(data['tests'])}\")
success = sum(1 for test in data['tests'] if test['status'] == 'success')
print(f\"Successful: {success}\")
print(f\"Failed: {len(data['tests']) - success}\")
  "
  
  echo ""
  echo -e "${BLUE}See ${OUTPUT_FILE} for detailed results.${NC}"
else
  echo ""
  echo -e "${RED}Integration tests failed.${NC}"
  echo -e "${BLUE}See ${OUTPUT_FILE} for detailed results.${NC}"
  exit 1
fi
