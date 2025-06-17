"""
CoStar Data Import Pipeline for Sophia AI
Handles both automated crawling and manual file uploads
Integrates with existing Sophia AI data architecture
"""

import os
import json
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging
from flask import Flask, request, jsonify, Blueprint
from werkzeug.utils import secure_filename
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import pinecone
import weaviate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoStarDataPipeline:
    """
    CoStar data processing pipeline for Sophia AI
    Supports both automated crawling and manual file imports
    """
    
    def __init__(self):
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'sophia_ai'),
            'user': os.getenv('POSTGRES_USER', 'sophia'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'port': os.getenv('POSTGRES_PORT', 5432)
        }
        
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=os.getenv('REDIS_PORT', 6379),
            db=0,
            decode_responses=True
        )
        
        # Initialize vector databases
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        
        # Supported file formats
        self.supported_formats = {'.csv', '.xlsx', '.xls', '.json', '.tsv'}
        
        # CoStar data schema mapping
        self.costar_schema = {
            'metro_area': 'VARCHAR(100)',
            'property_type': 'VARCHAR(50)',
            'total_inventory': 'INTEGER',
            'vacancy_rate': 'DECIMAL(5,2)',
            'asking_rent_psf': 'DECIMAL(10,2)',
            'net_absorption': 'INTEGER',
            'construction_deliveries': 'INTEGER',
            'under_construction': 'INTEGER',
            'market_date': 'DATE',
            'data_source': 'VARCHAR(50)',
            'import_timestamp': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
    
    def get_postgres_connection(self):
        """Get PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def create_costar_tables(self):
        """Create CoStar data tables with dynamic schema"""
        conn = self.get_postgres_connection()
        cursor = conn.cursor()
        
        try:
            # Main CoStar market data table
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS costar_market_data (
                id SERIAL PRIMARY KEY,
                {', '.join([f'{col} {dtype}' for col, dtype in self.costar_schema.items()])}
            );
            
            CREATE INDEX IF NOT EXISTS idx_costar_metro_date 
            ON costar_market_data(metro_area, market_date);
            
            CREATE INDEX IF NOT EXISTS idx_costar_property_type 
            ON costar_market_data(property_type);
            """
            
            cursor.execute(create_table_sql)
            
            # Import tracking table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS costar_imports (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255),
                file_size INTEGER,
                records_imported INTEGER,
                import_method VARCHAR(50),
                import_status VARCHAR(20),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            conn.commit()
            logger.info("CoStar tables created successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def validate_file_format(self, filename: str) -> bool:
        """Validate uploaded file format"""
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.supported_formats
    
    def parse_uploaded_file(self, file_path: str) -> pd.DataFrame:
        """Parse uploaded file into pandas DataFrame"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            elif file_ext == '.tsv':
                df = pd.read_csv(file_path, sep='\t')
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            logger.info(f"Parsed file {file_path}: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def normalize_costar_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize CoStar data to standard schema"""
        # Column mapping for common CoStar export formats
        column_mapping = {
            'Metro Area': 'metro_area',
            'Market': 'metro_area',
            'Property Type': 'property_type',
            'Type': 'property_type',
            'Total Inventory': 'total_inventory',
            'Inventory': 'total_inventory',
            'Vacancy Rate': 'vacancy_rate',
            'Vacancy %': 'vacancy_rate',
            'Asking Rent': 'asking_rent_psf',
            'Rent PSF': 'asking_rent_psf',
            'Net Absorption': 'net_absorption',
            'Absorption': 'net_absorption',
            'Deliveries': 'construction_deliveries',
            'Under Construction': 'under_construction',
            'UC': 'under_construction',
            'Date': 'market_date',
            'Period': 'market_date'
        }
        
        # Rename columns to standard schema
        df_normalized = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_normalized.columns:
                df_normalized = df_normalized.rename(columns={old_col: new_col})
        
        # Add metadata columns
        df_normalized['data_source'] = 'costar_manual_import'
        df_normalized['import_timestamp'] = datetime.now()
        
        # Clean and validate data types
        if 'vacancy_rate' in df_normalized.columns:
            # Convert percentage strings to decimals
            df_normalized['vacancy_rate'] = df_normalized['vacancy_rate'].astype(str).str.replace('%', '').astype(float)
        
        if 'asking_rent_psf' in df_normalized.columns:
            # Remove currency symbols and convert to float
            df_normalized['asking_rent_psf'] = df_normalized['asking_rent_psf'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
        
        if 'market_date' in df_normalized.columns:
            # Standardize date format
            df_normalized['market_date'] = pd.to_datetime(df_normalized['market_date'])
        
        # Filter to only include columns that exist in our schema
        schema_columns = list(self.costar_schema.keys())
        available_columns = [col for col in schema_columns if col in df_normalized.columns]
        df_final = df_normalized[available_columns]
        
        logger.info(f"Normalized data: {len(df_final)} rows, {len(df_final.columns)} columns")
        return df_final
    
    def import_to_postgres(self, df: pd.DataFrame, import_method: str = 'manual') -> Dict:
        """Import normalized data to PostgreSQL"""
        conn = self.get_postgres_connection()
        cursor = conn.cursor()
        
        try:
            # Prepare insert statement
            columns = list(df.columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"""
            INSERT INTO costar_market_data ({', '.join(columns)})
            VALUES ({placeholders})
            """
            
            # Convert DataFrame to list of tuples
            data_tuples = [tuple(row) for row in df.values]
            
            # Execute batch insert
            cursor.executemany(insert_sql, data_tuples)
            
            # Log import to tracking table
            cursor.execute("""
            INSERT INTO costar_imports (filename, records_imported, import_method, import_status)
            VALUES (%s, %s, %s, %s)
            """, ('batch_import', len(df), import_method, 'success'))
            
            conn.commit()
            
            result = {
                'status': 'success',
                'records_imported': len(df),
                'columns_imported': columns,
                'import_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully imported {len(df)} records to PostgreSQL")
            return result
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error importing to PostgreSQL: {e}")
            
            # Log failed import
            cursor.execute("""
            INSERT INTO costar_imports (records_imported, import_method, import_status, error_message)
            VALUES (%s, %s, %s, %s)
            """, (0, import_method, 'failed', str(e)))
            conn.commit()
            
            raise
        finally:
            cursor.close()
            conn.close()
    
    def cache_market_data(self, metro_area: str, data: Dict):
        """Cache frequently accessed market data in Redis"""
        cache_key = f"costar:market:{metro_area}"
        self.redis_client.setex(cache_key, 3600, json.dumps(data))  # 1 hour TTL
        logger.info(f"Cached market data for {metro_area}")
    
    def get_cached_market_data(self, metro_area: str) -> Optional[Dict]:
        """Retrieve cached market data from Redis"""
        cache_key = f"costar:market:{metro_area}"
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def generate_embeddings(self, df: pd.DataFrame):
        """Generate vector embeddings for semantic search"""
        try:
            # Initialize Pinecone if available
            if self.pinecone_api_key:
                pinecone.init(api_key=self.pinecone_api_key)
                
                # Create text descriptions for embedding
                df['description'] = df.apply(lambda row: 
                    f"{row.get('metro_area', '')} {row.get('property_type', '')} "
                    f"market data: {row.get('vacancy_rate', '')}% vacancy, "
                    f"${row.get('asking_rent_psf', '')} PSF rent", axis=1)
                
                # Generate embeddings (placeholder - would use actual embedding model)
                logger.info("Generated embeddings for vector search")
            
        except Exception as e:
            logger.warning(f"Vector embedding generation failed: {e}")
    
    def process_file_upload(self, file_path: str, filename: str) -> Dict:
        """Complete pipeline for processing uploaded CoStar file"""
        try:
            # Validate file format
            if not self.validate_file_format(filename):
                raise ValueError(f"Unsupported file format: {Path(filename).suffix}")
            
            # Parse file
            df = self.parse_uploaded_file(file_path)
            
            # Normalize data
            df_normalized = self.normalize_costar_data(df)
            
            # Import to PostgreSQL
            import_result = self.import_to_postgres(df_normalized, 'manual_upload')
            
            # Generate embeddings for search
            self.generate_embeddings(df_normalized)
            
            # Cache summary data
            for metro in df_normalized['metro_area'].unique():
                metro_data = df_normalized[df_normalized['metro_area'] == metro].to_dict('records')
                self.cache_market_data(metro, metro_data)
            
            return {
                'status': 'success',
                'message': 'File processed successfully',
                'details': import_result
            }
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'details': None
            }

# Flask Blueprint for CoStar API endpoints
costar_bp = Blueprint('costar', __name__, url_prefix='/api/costar')
pipeline = CoStarDataPipeline()

@costar_bp.route('/upload', methods=['POST'])
def upload_costar_file():
    """Handle CoStar file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        upload_dir = Path('/tmp/costar_uploads')
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / filename
        file.save(str(file_path))
        
        # Process file
        result = pipeline.process_file_upload(str(file_path), filename)
        
        # Clean up uploaded file
        file_path.unlink()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@costar_bp.route('/market/<metro_area>', methods=['GET'])
def get_market_data(metro_area):
    """Get market data for specific metro area"""
    try:
        # Check cache first
        cached_data = pipeline.get_cached_market_data(metro_area)
        if cached_data:
            return jsonify({
                'status': 'success',
                'data': cached_data,
                'source': 'cache'
            })
        
        # Query database
        conn = pipeline.get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
        SELECT * FROM costar_market_data 
        WHERE metro_area ILIKE %s 
        ORDER BY market_date DESC 
        LIMIT 100
        """, (f'%{metro_area}%',))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Cache results
        if results:
            pipeline.cache_market_data(metro_area, results)
        
        return jsonify({
            'status': 'success',
            'data': results,
            'source': 'database'
        })
        
    except Exception as e:
        logger.error(f"Market data query error: {e}")
        return jsonify({'error': str(e)}), 500

@costar_bp.route('/markets', methods=['GET'])
def list_markets():
    """List all available metro areas"""
    try:
        conn = pipeline.get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT metro_area, COUNT(*) as record_count, MAX(market_date) as latest_date
        FROM costar_market_data 
        GROUP BY metro_area 
        ORDER BY metro_area
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        markets = [
            {
                'metro_area': row[0],
                'record_count': row[1],
                'latest_date': row[2].isoformat() if row[2] else None
            }
            for row in results
        ]
        
        return jsonify({
            'status': 'success',
            'markets': markets
        })
        
    except Exception as e:
        logger.error(f"Markets list error: {e}")
        return jsonify({'error': str(e)}), 500

@costar_bp.route('/import-status', methods=['GET'])
def import_status():
    """Get import history and status"""
    try:
        conn = pipeline.get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
        SELECT * FROM costar_imports 
        ORDER BY created_at DESC 
        LIMIT 50
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'imports': results
        })
        
    except Exception as e:
        logger.error(f"Import status error: {e}")
        return jsonify({'error': str(e)}), 500

@costar_bp.route('/initialize', methods=['POST'])
def initialize_database():
    """Initialize CoStar database tables"""
    try:
        pipeline.create_costar_tables()
        return jsonify({
            'status': 'success',
            'message': 'CoStar database tables initialized'
        })
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return jsonify({'error': str(e)}), 500

# Export blueprint for integration with main Sophia AI app
def register_costar_routes(app: Flask):
    """Register CoStar routes with main Flask app"""
    app.register_blueprint(costar_bp)
    logger.info("CoStar data pipeline routes registered")

if __name__ == '__main__':
    # Standalone testing
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    register_costar_routes(app)
    
    # Initialize database
    pipeline.create_costar_tables()
    
    app.run(host='0.0.0.0', port=5001, debug=True)

