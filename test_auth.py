#!/usr/bin/env python3
"""
Quick test script to verify authentication
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5001"
USERNAME = "admin"
PASSWORD = "g#Q^bqkbN7J]+Ob/"

print("🔐 Testing Sophia AI Authentication")
print("=" * 40)

# Test health endpoint
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Service: {data.get('service')}")
        print(f"   Status: {data.get('status')}")
except Exception as e:
    print(f"   Error: {e}")

# Test login
print("\n2. Testing login...")
try:
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    print(f"   Username: {USERNAME}")
    print(f"   Password: {PASSWORD[:5]}...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        if token:
            print(f"   ✅ Login successful!")
            print(f"   Token: {token[:20]}...")
            
            # Test authenticated request
            print("\n3. Testing authenticated request...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/api/company/overview", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Authenticated request successful!")
            else:
                print(f"   Response: {response.text}")
    else:
        print("   ❌ Login failed")
        
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 40)
print("Test complete!") 