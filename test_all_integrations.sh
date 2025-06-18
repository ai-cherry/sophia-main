#!/bin/bash
# Sophia AI - Test All Integrations
# This script tests connectivity to Snowflake, Gong, Vercel, and Estuary

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "SOPHIA AI - Integration Connectivity Test"
echo "=================================================="
echo "Starting tests at $(date)"
echo ""

# Check for required environment variables
echo "Checking environment variables..."
MISSING_VARS=0

# Snowflake variables
if [ -z "$SNOWFLAKE_ACCOUNT" ] || [ -z "$SNOWFLAKE_USER" ] || [ -z "$SNOWFLAKE_PASSWORD" ]; then
    echo "❌ Missing required Snowflake environment variables"
    MISSING_VARS=1
else
    echo "✅ Snowflake environment variables found"
fi

# Gong variables
if [ -z "$GONG_API_KEY" ] || [ -z "$GONG_API_SECRET" ]; then
    echo "❌ Missing required Gong environment variables"
    MISSING_VARS=1
else
    echo "✅ Gong environment variables found"
fi

# Vercel variables
if [ -z "$VERCEL_ACCESS_TOKEN" ]; then
    echo "❌ Missing required Vercel environment variables"
    MISSING_VARS=1
else
    echo "✅ Vercel environment variables found"
fi

# Estuary variables
if [ -z "$ESTUARY_API_KEY" ]; then
    echo "❌ Missing required Estuary environment variables"
    MISSING_VARS=1
else
    echo "✅ Estuary environment variables found"
fi

echo ""

# Check if any variables are missing
if [ $MISSING_VARS -eq 1 ]; then
    echo "Warning: Some required environment variables are missing."
    echo "You can load them from a .env file using:"
    echo "  source <(grep -v '^#' .env | sed -E 's/(.*)=(.*)/export \\1=\\2/')"
    echo ""
    
    # Ask if user wants to continue
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Test aborted."
        exit 1
    fi
fi

# Check for Python and required packages
echo "Checking for required Python packages..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check for required Python packages
REQUIRED_PACKAGES=("aiohttp" "snowflake-connector-python")
MISSING_PACKAGES=0

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" &> /dev/null; then
        echo "❌ Missing Python package: $package"
        MISSING_PACKAGES=1
    else
        echo "✅ Python package found: $package"
    fi
done

echo ""

# Install missing packages if needed
if [ $MISSING_PACKAGES -eq 1 ]; then
    echo "Some required Python packages are missing."
    read -p "Do you want to install them now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing missing packages..."
        pip install aiohttp snowflake-connector-python
    else
        echo "Test aborted. Please install the required packages manually."
        exit 1
    fi
fi

# Run the unified integration test
echo "Running integration tests..."
echo ""

# Check if unified_integration_test.py exists and is executable
if [ -f "./unified_integration_test.py" ] && [ -x "./unified_integration_test.py" ]; then
    ./unified_integration_test.py
else
    # Try running with python3
    python3 unified_integration_test.py
fi

# Check the exit code
TEST_RESULT=$?

echo ""
echo "=================================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All integration tests passed successfully!"
elif [ $TEST_RESULT -eq 1 ]; then
    echo "⚠️ Some integration tests failed. See above for details."
else
    echo "❌ Integration tests failed. See above for details."
fi
echo "Test completed at $(date)"
echo "=================================================="

# Return the test result
exit $TEST_RESULT
