#!/usr/bin/env python3
"""
Schema-Aligned Database Storage Implementation
Uses correct column names from actual database schema
"""

import os
import json
import asyncio
import asyncpg
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaAlignedStorage:
    """
    Stores Gong data using the correct database schema column names
    """
    
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    async def store_gong_data(self) -> dict:
        """Store Gong data using correct schema column names"""
        
        try:
            # Read the latest extraction results
            extraction_file = "gong_alternative_extraction_20250617_203525.json"
            
            if not os.path.exists(extraction_file):
                return {
                    "success": False,
                    "error": f"Extraction file {extraction_file} not found"
                }
            
            with open(extraction_file, 'r') as f:
                extraction_data = json.load(f)
            
            logger.info(f"Loaded extraction data from {extraction_file}")
            
            # Connect to database
            conn = await asyncpg.connect(**self.db_config)
            logger.info("Connected to database")
            
            storage_results = {
                "users_stored": 0,
                "workspaces_stored": 0,
                "calls_stored": 0,
                "errors": []
            }
            
            # Store users using correct column names
            users_data = extraction_data.get("users", {})
            if users_data.get("success", False):
                users = users_data.get("users", [])
                logger.info(f"Storing {len(users)} users...")
                
                for user in users:
                    try:
                        await conn.execute("""
                            INSERT INTO gong_users 
                            (user_id, email_address, first_name, last_name, title, 
                             phone_number, is_active, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (user_id) DO UPDATE SET
                                email_address = EXCLUDED.email_address,
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name,
                                title = EXCLUDED.title,
                                phone_number = EXCLUDED.phone_number,
                                is_active = EXCLUDED.is_active,
                                updated_at = EXCLUDED.updated_at
                        """,
                            str(user.get("id", "")),
                            str(user.get("emailAddress", "")),
                            str(user.get("firstName", "")),
                            str(user.get("lastName", "")),
                            str(user.get("title", "")),
                            str(user.get("phoneNumber", "")),
                            bool(user.get("active", True)),
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                        storage_results["users_stored"] += 1
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing user {user.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing user: {str(e)}")
            
            # Store workspaces using correct column names
            workspaces_data = extraction_data.get("workspaces", {})
            if workspaces_data.get("success", False):
                workspaces = workspaces_data.get("workspaces", [])
                logger.info(f"Storing {len(workspaces)} workspaces...")
                
                for workspace in workspaces:
                    try:
                        await conn.execute("""
                            INSERT INTO gong_workspaces 
                            (workspace_id, name, created_at, updated_at)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (workspace_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                updated_at = EXCLUDED.updated_at
                        """,
                            str(workspace.get("id", "")),
                            str(workspace.get("name", "")),
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                        storage_results["workspaces_stored"] += 1
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing workspace {workspace.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing workspace: {str(e)}")
            
            # Store calls using correct column names
            calls_data = extraction_data.get("calls", {})
            if calls_data.get("success", False):
                calls = calls_data.get("calls", [])
                logger.info(f"Storing {len(calls)} calls...")
                
                for call in calls:
                    try:
                        # Parse started time
                        started_time = None
                        if call.get("started"):
                            try:
                                started_time = datetime.fromisoformat(call.get("started", "").replace("Z", "+00:00"))
                            except:
                                pass
                        
                        await conn.execute("""
                            INSERT INTO gong_calls 
                            (call_id, title, started, duration_seconds, direction, url)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (call_id) DO UPDATE SET
                                title = EXCLUDED.title,
                                started = EXCLUDED.started,
                                duration_seconds = EXCLUDED.duration_seconds,
                                direction = EXCLUDED.direction,
                                url = EXCLUDED.url
                        """,
                            str(call.get("id", "")),
                            str(call.get("title", "")),
                            started_time,
                            int(call.get("duration", 0)),
                            str(call.get("direction", "")),
                            str(call.get("url", ""))
                        )
                        storage_results["calls_stored"] += 1
                        
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing call {call.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing call: {str(e)}")
            
            await conn.close()
            logger.info("Database connection closed")
            
            storage_results["success"] = True
            storage_results["total_records"] = (
                storage_results["users_stored"] + 
                storage_results["workspaces_stored"] + 
                storage_results["calls_stored"]
            )
            
            return storage_results
            
        except Exception as e:
            logger.error(f"Error in store_gong_data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_stored": 0,
                "workspaces_stored": 0,
                "calls_stored": 0
            }
    
    async def verify_stored_data(self) -> dict:
        """Verify that data was stored correctly"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Count records in each table
            users_count = await conn.fetchval("SELECT COUNT(*) FROM gong_users")
            workspaces_count = await conn.fetchval("SELECT COUNT(*) FROM gong_workspaces")
            calls_count = await conn.fetchval("SELECT COUNT(*) FROM gong_calls")
            
            # Get sample data for verification
            sample_users = await conn.fetch(
                "SELECT first_name, last_name, title, email_address FROM gong_users LIMIT 10"
            )
            
            sample_calls = await conn.fetch(
                "SELECT title, started, duration_seconds, direction FROM gong_calls ORDER BY started DESC LIMIT 10"
            )
            
            # Get apartment industry insights
            apartment_keywords = ['apartment', 'rental', 'lease', 'tenant', 'property', 'multifamily', 'resident']
            apartment_calls = 0
            
            for keyword in apartment_keywords:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM gong_calls WHERE LOWER(title) LIKE $1",
                    f"%{keyword.lower()}%"
                )
                apartment_calls += count
            
            await conn.close()
            
            return {
                "success": True,
                "record_counts": {
                    "users": users_count,
                    "workspaces": workspaces_count,
                    "calls": calls_count
                },
                "apartment_intelligence": {
                    "apartment_relevant_calls": apartment_calls,
                    "relevance_percentage": round((apartment_calls / max(calls_count, 1)) * 100, 2)
                },
                "sample_data": {
                    "users": [dict(row) for row in sample_users],
                    "calls": [dict(row) for row in sample_calls]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_apartment_intelligence_columns(self) -> dict:
        """Add apartment industry intelligence columns to existing tables"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Add apartment relevance columns
            await conn.execute("""
                ALTER TABLE gong_calls 
                ADD COLUMN IF NOT EXISTS apartment_relevance DECIMAL(3,2) DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS sophia_insights JSONB DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS business_intelligence JSONB DEFAULT '{}'
            """)
            
            await conn.execute("""
                ALTER TABLE gong_users 
                ADD COLUMN IF NOT EXISTS apartment_relevance DECIMAL(3,2) DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS sophia_profile JSONB DEFAULT '{}'
            """)
            
            # Calculate apartment relevance for existing calls
            apartment_keywords = ['apartment', 'rental', 'lease', 'tenant', 'property', 'multifamily', 'resident', 'pay ready']
            
            for keyword in apartment_keywords:
                relevance_score = 0.8 if keyword == 'pay ready' else 0.6
                await conn.execute("""
                    UPDATE gong_calls 
                    SET apartment_relevance = $1,
                        sophia_insights = jsonb_build_object(
                            'keyword_match', $2,
                            'relevance_reason', 'Title contains apartment industry keyword',
                            'analysis_timestamp', $3
                        )
                    WHERE LOWER(title) LIKE $4 AND apartment_relevance < $1
                """, 
                    relevance_score,
                    keyword,
                    datetime.utcnow().isoformat(),
                    f"%{keyword.lower()}%"
                )
            
            # Calculate apartment relevance for users based on their calls
            await conn.execute("""
                UPDATE gong_users 
                SET apartment_relevance = (
                    SELECT COALESCE(AVG(c.apartment_relevance), 0.0)
                    FROM gong_calls c
                    JOIN gong_participants p ON c.call_id = p.call_id
                    WHERE p.email_address = gong_users.email_address
                ),
                sophia_profile = jsonb_build_object(
                    'apartment_call_count', (
                        SELECT COUNT(*)
                        FROM gong_calls c
                        JOIN gong_participants p ON c.call_id = p.call_id
                        WHERE p.email_address = gong_users.email_address
                        AND c.apartment_relevance > 0.5
                    ),
                    'analysis_timestamp', $1
                )
            """, datetime.utcnow().isoformat())
            
            await conn.close()
            
            return {
                "success": True,
                "message": "Apartment intelligence columns added and populated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

async def main():
    """Main function to store and verify Gong data"""
    
    storage = SchemaAlignedStorage()
    
    print("🔧 STORING GONG DATA WITH CORRECT SCHEMA...")
    storage_result = await storage.store_gong_data()
    
    if storage_result["success"]:
        print(f"✅ Gong data stored successfully!")
        print(f"Users stored: {storage_result['users_stored']}")
        print(f"Workspaces stored: {storage_result['workspaces_stored']}")
        print(f"Calls stored: {storage_result['calls_stored']}")
        print(f"Total records: {storage_result['total_records']}")
        
        if storage_result["errors"]:
            print(f"⚠️ {len(storage_result['errors'])} errors occurred during storage")
    else:
        print(f"❌ Data storage failed: {storage_result.get('error', 'Unknown error')}")
        return
    
    print("\n🧠 ADDING APARTMENT INTELLIGENCE COLUMNS...")
    intelligence_result = await storage.add_apartment_intelligence_columns()
    
    if intelligence_result["success"]:
        print(f"✅ {intelligence_result['message']}")
    else:
        print(f"❌ Intelligence enhancement failed: {intelligence_result.get('error', 'Unknown error')}")
    
    print("\n🔍 VERIFYING STORED DATA...")
    verification_result = await storage.verify_stored_data()
    
    if verification_result["success"]:
        counts = verification_result["record_counts"]
        intelligence = verification_result["apartment_intelligence"]
        
        print(f"✅ Data verification complete!")
        print(f"📊 RECORD COUNTS:")
        print(f"   Users: {counts['users']}")
        print(f"   Workspaces: {counts['workspaces']}")
        print(f"   Calls: {counts['calls']}")
        
        print(f"\n🏢 APARTMENT INTELLIGENCE:")
        print(f"   Apartment-relevant calls: {intelligence['apartment_relevant_calls']}")
        print(f"   Relevance percentage: {intelligence['relevance_percentage']}%")
        
        print(f"\n👥 SAMPLE USERS:")
        for user in verification_result["sample_data"]["users"][:5]:
            print(f"   {user['first_name']} {user['last_name']} ({user['title']}) - {user['email_address']}")
        
        print(f"\n📞 RECENT CALLS:")
        for call in verification_result["sample_data"]["calls"][:5]:
            duration_min = call['duration_seconds'] // 60 if call['duration_seconds'] else 0
            print(f"   {call['title']} - {duration_min}min ({call['direction']})")
    else:
        print(f"❌ Data verification failed: {verification_result.get('error', 'Unknown error')}")
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"schema_aligned_storage_{timestamp}.json"
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "storage_result": storage_result,
        "intelligence_result": intelligence_result,
        "verification_result": verification_result
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())

