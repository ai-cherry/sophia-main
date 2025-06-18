# Prompt for Fixing Sophia AI Integration Issues

## Background

Sophia AI is an AI assistant orchestrator for Pay Ready company that serves as the central "Pay Ready Brain" orchestrating multiple AI agents and integrating with business systems. We're experiencing issues with the integration connectivity to several external services, particularly Estuary.

## Current State

We've updated the Estuary API URL from `https://api.estuary.dev` to `https://api.estuary.tech` in the documentation and verified that all configuration files already have the correct URL. However, when running integration tests, we're still encountering connection errors.

## Issues to Fix

1. **Estuary API Connection Issue**
   - Despite having the correct URL (`https://api.estuary.tech`) in all configuration files, the test is still trying to connect to `api.estuary.dev`
   - Error message: `Cannot connect to host api.estuary.dev:443 ssl:default [nodename nor servname provided, or not known]`
   - Files to investigate:
     - `unified_integration_test.py`
     - `test_integrations.py`
     - Any cached configuration or environment variables

2. **SSL Certificate Verification Issues**
   - All API connections (Gong, Snowflake, Estuary, Vercel) are failing with SSL certificate verification errors
   - Error: `SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')]`
   - This suggests a system-level issue with SSL certificates or a need to configure the requests library to handle certificate verification

3. **Snowflake MFA Authentication**
   - Snowflake connection requires multi-factor authentication
   - Error: `250001 (08001): None: Failed to connect to DB: MYJDJNU-FP71296.snowflakecomputing.com:443. Multi-factor authentication is required for this account. Log in to Snowsight to enroll.`
   - Need to update the authentication method to handle MFA requirements

## Requested Tasks

1. **Debug and fix the Estuary API URL issue**
   - Find where `api.estuary.dev` is still being referenced
   - Update all instances to use `api.estuary.tech`
   - Check for any caching mechanisms that might be storing the old URL

2. **Resolve SSL certificate verification issues**
   - Implement a solution for handling SSL certificate verification
   - Options include:
     - Installing required CA certificates
     - Configuring the requests/aiohttp library to use a specific certificate bundle
     - Implementing a temporary workaround for development environments (with appropriate security warnings)

3. **Update Snowflake authentication**
   - Research and implement a solution for handling Snowflake MFA requirements
   - Update the connection code to support the required authentication flow

4. **Improve error handling**
   - Enhance error handling in the integration tests to provide more detailed diagnostics
   - Add specific error messages and recovery suggestions for common failure scenarios

## Important Files

- `unified_integration_test.py`: Main integration test framework
- `test_integrations.py`: Integration test implementation
- `docs/INTEGRATION_MANAGEMENT_GUIDE.md`: Documentation for integration management
- `backend/integrations/estuary_flow_integration.py`: Estuary integration implementation
- `.env`: Environment variables configuration
- `integration.env.example`: Example environment variables template

## Development Standards

- Follow Python 3.11+ with type hints for all functions
- Adhere to PEP 8 with 88-character line limit (Black formatter)
- Use async/await for I/O operations
- Implement comprehensive error handling with logging
- Include detailed docstrings for all classes and methods

## Security Requirements

- Use encrypted storage for all API keys
- Implement proper authentication and authorization
- Log all security-relevant events
- Follow principle of least privilege
- Never hardcode secrets, always use environment variables

## Deliverables

1. Updated code files with fixes for the identified issues
2. Documentation of changes made and reasoning
3. Suggestions for long-term improvements to prevent similar issues
4. Updated test results showing successful connections
