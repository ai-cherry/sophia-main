"""
Sophia AI - Dynamic Schema Migration System
Automatically evolves database tables based on incoming data structures
"""

import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib

class SchemaMigrationSystem:
    """
    Dynamic schema migration system for Sophia AI Pay Ready platform.
    Handles automatic table evolution based on incoming data structures.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.setup_migration_tracking()
    
    def setup_logging(self):
        """Setup logging for migration tracking"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def setup_migration_tracking(self):
        """Create migration tracking table if it doesn't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(255) NOT NULL,
                        migration_type VARCHAR(50) NOT NULL,
                        column_changes JSONB,
                        data_sample JSONB,
                        data_quality_score FLOAT,
                        migration_hash VARCHAR(64) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        applied_at TIMESTAMP,
                        rollback_sql TEXT,
                        status VARCHAR(20) DEFAULT 'pending'
                    )
                """)
                conn.commit()
    
    def analyze_data_structure(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze data structure and infer column types"""
        column_types = {}
        
        for key, value in data.items():
            if value is None:
                column_types[key] = 'TEXT'  # Default for null values
            elif isinstance(value, bool):
                column_types[key] = 'BOOLEAN'
            elif isinstance(value, int):
                if -2147483648 <= value <= 2147483647:
                    column_types[key] = 'INTEGER'
                else:
                    column_types[key] = 'BIGINT'
            elif isinstance(value, float):
                column_types[key] = 'DECIMAL(15,4)'
            elif isinstance(value, str):
                if len(value) <= 255:
                    column_types[key] = 'VARCHAR(255)'
                else:
                    column_types[key] = 'TEXT'
            elif isinstance(value, (dict, list)):
                column_types[key] = 'JSONB'
            elif isinstance(value, datetime):
                column_types[key] = 'TIMESTAMP'
            else:
                column_types[key] = 'TEXT'  # Fallback
        
        return column_types
    
    def get_existing_columns(self, table_name: str) -> Dict[str, str]:
        """Get existing columns and their types for a table"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table_name,))
                
                columns = {}
                for row in cursor.fetchall():
                    col_type = row['data_type'].upper()
                    if row['character_maximum_length']:
                        col_type += f"({row['character_maximum_length']})"
                    columns[row['column_name']] = col_type
                
                return columns
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                """, (table_name,))
                return cursor.fetchone()[0]
    
    def create_table(self, table_name: str, column_types: Dict[str, str]) -> str:
        """Create new table with specified columns"""
        columns_sql = []
        for col_name, col_type in column_types.items():
            columns_sql.append(f"{col_name} {col_type}")
        
        # Add standard columns
        columns_sql.extend([
            "id SERIAL PRIMARY KEY",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ])
        
        create_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns_sql)}
            )
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_sql)
                conn.commit()
        
        self.logger.info(f"Created table {table_name} with {len(column_types)} columns")
        return create_sql
    
    def add_columns(self, table_name: str, new_columns: Dict[str, str]) -> List[str]:
        """Add new columns to existing table"""
        alter_statements = []
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for col_name, col_type in new_columns.items():
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    cursor.execute(alter_sql)
                    alter_statements.append(alter_sql)
                    self.logger.info(f"Added column {col_name} ({col_type}) to {table_name}")
                
                conn.commit()
        
        return alter_statements
    
    def calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score based on completeness and consistency"""
        total_fields = len(data)
        if total_fields == 0:
            return 0.0
        
        # Count non-null, non-empty values
        valid_fields = 0
        for value in data.values():
            if value is not None and value != "" and value != []:
                valid_fields += 1
        
        completeness_score = valid_fields / total_fields
        
        # Additional quality checks
        consistency_score = 1.0  # Simplified for now
        
        # Weighted average
        quality_score = (completeness_score * 0.7) + (consistency_score * 0.3)
        return round(quality_score, 3)
    
    def generate_migration_hash(self, table_name: str, changes: Dict) -> str:
        """Generate unique hash for migration"""
        migration_data = {
            'table': table_name,
            'changes': changes,
            'timestamp': datetime.now().isoformat()
        }
        return hashlib.sha256(json.dumps(migration_data, sort_keys=True).encode()).hexdigest()
    
    def record_migration(self, table_name: str, migration_type: str, 
                        column_changes: Dict, data_sample: Dict, 
                        quality_score: float, sql_statements: List[str]) -> str:
        """Record migration in tracking table"""
        migration_hash = self.generate_migration_hash(table_name, column_changes)
        rollback_sql = self.generate_rollback_sql(migration_type, table_name, column_changes)
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO schema_migrations 
                    (table_name, migration_type, column_changes, data_sample, 
                     data_quality_score, migration_hash, applied_at, rollback_sql, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (migration_hash) DO NOTHING
                """, (
                    table_name, migration_type, json.dumps(column_changes),
                    json.dumps(data_sample), quality_score, migration_hash,
                    datetime.now(), '\n'.join(sql_statements), 'completed'
                ))
                conn.commit()
        
        return migration_hash
    
    def generate_rollback_sql(self, migration_type: str, table_name: str, changes: Dict) -> str:
        """Generate rollback SQL for migration"""
        if migration_type == 'create_table':
            return f"DROP TABLE IF EXISTS {table_name};"
        elif migration_type == 'add_columns':
            rollback_statements = []
            for col_name in changes.keys():
                rollback_statements.append(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col_name};")
            return '\n'.join(rollback_statements)
        return ""
    
    def migrate_schema(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to migrate schema based on incoming data
        Returns migration summary
        """
        try:
            # Analyze incoming data structure
            required_columns = self.analyze_data_structure(data)
            quality_score = self.calculate_data_quality_score(data)
            
            migration_summary = {
                'table_name': table_name,
                'data_quality_score': quality_score,
                'migration_type': None,
                'changes': {},
                'sql_statements': [],
                'migration_hash': None
            }
            
            if not self.table_exists(table_name):
                # Create new table
                create_sql = self.create_table(table_name, required_columns)
                migration_summary.update({
                    'migration_type': 'create_table',
                    'changes': required_columns,
                    'sql_statements': [create_sql]
                })
                
            else:
                # Check for new columns
                existing_columns = self.get_existing_columns(table_name)
                new_columns = {}
                
                for col_name, col_type in required_columns.items():
                    if col_name not in existing_columns:
                        new_columns[col_name] = col_type
                
                if new_columns:
                    alter_statements = self.add_columns(table_name, new_columns)
                    migration_summary.update({
                        'migration_type': 'add_columns',
                        'changes': new_columns,
                        'sql_statements': alter_statements
                    })
                else:
                    migration_summary['migration_type'] = 'no_changes'
            
            # Record migration if changes were made
            if migration_summary['migration_type'] != 'no_changes':
                migration_hash = self.record_migration(
                    table_name, migration_summary['migration_type'],
                    migration_summary['changes'], data, quality_score,
                    migration_summary['sql_statements']
                )
                migration_summary['migration_hash'] = migration_hash
            
            return migration_summary
            
        except Exception as e:
            self.logger.error(f"Migration failed for table {table_name}: {str(e)}")
            raise
    
    def rollback_migration(self, migration_hash: str) -> bool:
        """Rollback a specific migration"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get migration details
                    cursor.execute("""
                        SELECT * FROM schema_migrations 
                        WHERE migration_hash = %s AND status = 'completed'
                    """, (migration_hash,))
                    
                    migration = cursor.fetchone()
                    if not migration:
                        self.logger.warning(f"Migration {migration_hash} not found or already rolled back")
                        return False
                    
                    # Execute rollback SQL
                    if migration['rollback_sql']:
                        cursor.execute(migration['rollback_sql'])
                        
                        # Update migration status
                        cursor.execute("""
                            UPDATE schema_migrations 
                            SET status = 'rolled_back' 
                            WHERE migration_hash = %s
                        """, (migration_hash,))
                        
                        conn.commit()
                        self.logger.info(f"Successfully rolled back migration {migration_hash}")
                        return True
                    
        except Exception as e:
            self.logger.error(f"Rollback failed for migration {migration_hash}: {str(e)}")
            return False
    
    def get_migration_history(self, table_name: Optional[str] = None) -> List[Dict]:
        """Get migration history for a table or all tables"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if table_name:
                    cursor.execute("""
                        SELECT * FROM schema_migrations 
                        WHERE table_name = %s 
                        ORDER BY created_at DESC
                    """, (table_name,))
                else:
                    cursor.execute("""
                        SELECT * FROM schema_migrations 
                        ORDER BY created_at DESC
                    """)
                
                return [dict(row) for row in cursor.fetchall()]
    
    def optimize_table_indexes(self, table_name: str, data_sample: Dict[str, Any]):
        """Create optimized indexes based on data patterns"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Create indexes for commonly queried fields
                index_candidates = []
                
                for col_name, value in data_sample.items():
                    # Index timestamp columns
                    if isinstance(value, datetime) or 'date' in col_name.lower() or 'time' in col_name.lower():
                        index_candidates.append(col_name)
                    
                    # Index ID-like columns
                    if col_name.endswith('_id') or col_name == 'id':
                        index_candidates.append(col_name)
                    
                    # Index commonly searched text fields
                    if col_name in ['name', 'email', 'username', 'company', 'title']:
                        index_candidates.append(col_name)
                
                # Create indexes
                for col_name in index_candidates:
                    try:
                        index_name = f"idx_{table_name}_{col_name}"
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name} 
                            ON {table_name} ({col_name})
                        """)
                        self.logger.info(f"Created index {index_name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to create index on {col_name}: {str(e)}")
                
                conn.commit()


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    DATABASE_URL = "postgresql://sophia_admin:simple123@150.136.94.139/sophia_payready"
    
    # Initialize migration system
    migration_system = SchemaMigrationSystem(DATABASE_URL)
    
    # Example data structures for testing
    company_data = {
        "company_name": "Pay Ready Inc",
        "revenue": 1250000.50,
        "employees": 45,
        "founded_date": datetime(2020, 1, 15),
        "is_public": False,
        "metadata": {"industry": "fintech", "stage": "series_a"}
    }
    
    customer_data = {
        "customer_id": "cust_12345",
        "email": "john@example.com",
        "signup_date": datetime.now(),
        "lifetime_value": 2500.00,
        "is_active": True,
        "preferences": {"notifications": True, "marketing": False}
    }
    
    # Test migrations
    try:
        # Migrate company data
        result1 = migration_system.migrate_schema("companies", company_data)
        print("Company migration result:", result1)
        
        # Migrate customer data
        result2 = migration_system.migrate_schema("customers", customer_data)
        print("Customer migration result:", result2)
        
        # Get migration history
        history = migration_system.get_migration_history()
        print(f"Total migrations: {len(history)}")
        
    except Exception as e:
        print(f"Migration test failed: {e}")

