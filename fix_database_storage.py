#!/usr/bin/env python3
"""
Fixed Database Storage Implementation
Ensures all extracted Gong data gets properly stored in Sophia database
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

class DatabaseStorageFixer:
    """
    Fixes database storage issues and ensures all Gong data is properly stored
    """
    
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    async def fix_database_storage(self) -> dict:
        """Fix database storage and load extracted data"""
        
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
                "participants_stored": 0,
                "errors": []
            }
            
            # Store users with enhanced data
            users_data = extraction_data.get("users", {})
            if users_data.get("success", False):
                users = users_data.get("users", [])
                logger.info(f"Storing {len(users)} users...")
                
                for user in users:
                    try:
                        await conn.execute("""
                            INSERT INTO gong_users 
                            (gong_user_id, email, first_name, last_name, title, company, 
                             phone_number, apartment_relevance, sophia_profile, 
                             created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (gong_user_id) DO UPDATE SET
                                email = EXCLUDED.email,
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name,
                                title = EXCLUDED.title,
                                company = EXCLUDED.company,
                                phone_number = EXCLUDED.phone_number,
                                apartment_relevance = EXCLUDED.apartment_relevance,
                                sophia_profile = EXCLUDED.sophia_profile,
                                updated_at = EXCLUDED.updated_at
                        """,
                            str(user.get("id", "")),
                            str(user.get("emailAddress", "")),
                            str(user.get("firstName", "")),
                            str(user.get("lastName", "")),
                            str(user.get("title", "")),
                            str(user.get("company", "")),
                            str(user.get("phoneNumber", "")),
                            float(user.get("apartment_relevance", 0.0)),
                            json.dumps(user.get("sophia_profile", {})),
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                        storage_results["users_stored"] += 1
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing user {user.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing user: {str(e)}")
            
            # Store workspaces
            workspaces_data = extraction_data.get("workspaces", {})
            if workspaces_data.get("success", False):
                workspaces = workspaces_data.get("workspaces", [])
                logger.info(f"Storing {len(workspaces)} workspaces...")
                
                for workspace in workspaces:
                    try:
                        await conn.execute("""
                            INSERT INTO gong_workspaces 
                            (gong_workspace_id, name, description, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (gong_workspace_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                updated_at = EXCLUDED.updated_at
                        """,
                            str(workspace.get("id", "")),
                            str(workspace.get("name", "")),
                            str(workspace.get("description", "")),
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                        storage_results["workspaces_stored"] += 1
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing workspace {workspace.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing workspace: {str(e)}")
            
            # Store calls with enhanced analysis
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
                            (gong_call_id, title, started, duration, direction, 
                             apartment_relevance, sophia_insights, business_intelligence,
                             created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                            ON CONFLICT (gong_call_id) DO UPDATE SET
                                title = EXCLUDED.title,
                                started = EXCLUDED.started,
                                duration = EXCLUDED.duration,
                                direction = EXCLUDED.direction,
                                apartment_relevance = EXCLUDED.apartment_relevance,
                                sophia_insights = EXCLUDED.sophia_insights,
                                business_intelligence = EXCLUDED.business_intelligence,
                                updated_at = EXCLUDED.updated_at
                        """,
                            str(call.get("id", "")),
                            str(call.get("title", "")),
                            started_time,
                            int(call.get("duration", 0)),
                            str(call.get("direction", "")),
                            float(call.get("apartment_relevance", 0.0)),
                            json.dumps(call.get("sophia_insights", {})),
                            json.dumps(call.get("business_intelligence", {})),
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                        storage_results["calls_stored"] += 1
                        
                        # Store participants if available
                        participants = call.get("participants", [])
                        if isinstance(participants, list):
                            for participant in participants:
                                if isinstance(participant, dict):
                                    try:
                                        await conn.execute("""
                                            INSERT INTO gong_participants 
                                            (gong_call_id, gong_user_id, email, name, company, 
                                             title, phone_number, created_at, updated_at)
                                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                            ON CONFLICT (gong_call_id, email) DO UPDATE SET
                                                name = EXCLUDED.name,
                                                company = EXCLUDED.company,
                                                title = EXCLUDED.title,
                                                phone_number = EXCLUDED.phone_number,
                                                updated_at = EXCLUDED.updated_at
                                        """,
                                            str(call.get("id", "")),
                                            str(participant.get("userId", "")),
                                            str(participant.get("emailAddress", "")),
                                            str(participant.get("name", "")),
                                            str(participant.get("company", "")),
                                            str(participant.get("title", "")),
                                            str(participant.get("phoneNumber", "")),
                                            datetime.utcnow(),
                                            datetime.utcnow()
                                        )
                                        storage_results["participants_stored"] += 1
                                    except Exception as e:
                                        storage_results["errors"].append(f"Error storing participant: {str(e)}")
                    
                    except Exception as e:
                        storage_results["errors"].append(f"Error storing call {call.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error storing call: {str(e)}")
            
            await conn.close()
            logger.info("Database connection closed")
            
            storage_results["success"] = True
            storage_results["total_records"] = (
                storage_results["users_stored"] + 
                storage_results["workspaces_stored"] + 
                storage_results["calls_stored"] + 
                storage_results["participants_stored"]
            )
            
            return storage_results
            
        except Exception as e:
            logger.error(f"Error in fix_database_storage: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_stored": 0,
                "workspaces_stored": 0,
                "calls_stored": 0,
                "participants_stored": 0
            }
    
    async def verify_data_storage(self) -> dict:
        """Verify that data was stored correctly"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Count records in each table
            users_count = await conn.fetchval("SELECT COUNT(*) FROM gong_users")
            workspaces_count = await conn.fetchval("SELECT COUNT(*) FROM gong_workspaces")
            calls_count = await conn.fetchval("SELECT COUNT(*) FROM gong_calls")
            participants_count = await conn.fetchval("SELECT COUNT(*) FROM gong_participants")
            
            # Get apartment-relevant data
            apartment_users = await conn.fetchval(
                "SELECT COUNT(*) FROM gong_users WHERE apartment_relevance > 0.5"
            )
            apartment_calls = await conn.fetchval(
                "SELECT COUNT(*) FROM gong_calls WHERE apartment_relevance > 0.5"
            )
            high_value_calls = await conn.fetchval(
                "SELECT COUNT(*) FROM gong_calls WHERE apartment_relevance > 0.8"
            )
            
            # Get sample data for verification
            sample_users = await conn.fetch(
                "SELECT first_name, last_name, company, apartment_relevance FROM gong_users ORDER BY apartment_relevance DESC LIMIT 5"
            )
            
            sample_calls = await conn.fetch(
                "SELECT title, apartment_relevance, sophia_insights FROM gong_calls ORDER BY apartment_relevance DESC LIMIT 5"
            )
            
            await conn.close()
            
            return {
                "success": True,
                "record_counts": {
                    "users": users_count,
                    "workspaces": workspaces_count,
                    "calls": calls_count,
                    "participants": participants_count
                },
                "apartment_intelligence": {
                    "apartment_relevant_users": apartment_users,
                    "apartment_relevant_calls": apartment_calls,
                    "high_value_opportunities": high_value_calls
                },
                "sample_data": {
                    "top_users": [dict(row) for row in sample_users],
                    "top_calls": [dict(row) for row in sample_calls]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

async def main():
    """Main function to fix database storage and verify data"""
    
    fixer = DatabaseStorageFixer()
    
    print("🔧 FIXING DATABASE STORAGE...")
    storage_result = await fixer.fix_database_storage()
    
    if storage_result["success"]:
        print(f"✅ Database storage fixed successfully!")
        print(f"Users stored: {storage_result['users_stored']}")
        print(f"Workspaces stored: {storage_result['workspaces_stored']}")
        print(f"Calls stored: {storage_result['calls_stored']}")
        print(f"Participants stored: {storage_result['participants_stored']}")
        print(f"Total records: {storage_result['total_records']}")
        
        if storage_result["errors"]:
            print(f"⚠️ {len(storage_result['errors'])} errors occurred during storage")
    else:
        print(f"❌ Database storage failed: {storage_result.get('error', 'Unknown error')}")
        return
    
    print("\n🔍 VERIFYING DATA STORAGE...")
    verification_result = await fixer.verify_data_storage()
    
    if verification_result["success"]:
        counts = verification_result["record_counts"]
        intelligence = verification_result["apartment_intelligence"]
        
        print(f"✅ Data verification complete!")
        print(f"📊 RECORD COUNTS:")
        print(f"   Users: {counts['users']}")
        print(f"   Workspaces: {counts['workspaces']}")
        print(f"   Calls: {counts['calls']}")
        print(f"   Participants: {counts['participants']}")
        
        print(f"\n🏢 APARTMENT INTELLIGENCE:")
        print(f"   Apartment-relevant users: {intelligence['apartment_relevant_users']}")
        print(f"   Apartment-relevant calls: {intelligence['apartment_relevant_calls']}")
        print(f"   High-value opportunities: {intelligence['high_value_opportunities']}")
        
        print(f"\n👥 TOP APARTMENT-RELEVANT USERS:")
        for user in verification_result["sample_data"]["top_users"]:
            print(f"   {user['first_name']} {user['last_name']} ({user['company']}) - Relevance: {user['apartment_relevance']:.2f}")
        
        print(f"\n📞 TOP APARTMENT-RELEVANT CALLS:")
        for call in verification_result["sample_data"]["top_calls"]:
            print(f"   {call['title']} - Relevance: {call['apartment_relevance']:.2f}")
    else:
        print(f"❌ Data verification failed: {verification_result.get('error', 'Unknown error')}")
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"database_storage_fixed_{timestamp}.json"
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "storage_result": storage_result,
        "verification_result": verification_result
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())

