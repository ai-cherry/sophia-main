"""
Sophia AI Knowledge Base Implementation
Contained Company Knowledge Base System for Pay Ready
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pinecone
import weaviate
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

Base = declarative_base()


class ContentType(Enum):
    """Types of content in the knowledge base"""
    COMPANY_CORE = "company_core"
    PRODUCTS_SERVICES = "products_services"
    OPERATIONS = "operations"
    DATA_DICTIONARY = "data_dictionary"
    SALES_MARKETING = "sales_marketing"
    CUSTOMER_SUCCESS = "customer_success"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    TECHNOLOGY = "technology"
    VENDORS_PARTNERS = "vendors_partners"


class ContentStatus(Enum):
    """Status of content in the knowledge base"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class KnowledgeDocument:
    """Represents a document in the knowledge base"""
    id: str
    title: str
    content: str
    content_type: ContentType
    status: ContentStatus
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    tags: List[str]
    metadata: Dict[str, Any]
    embedding_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            **asdict(self),
            'content_type': self.content_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class KnowledgeBaseDocument(Base):
    """SQLAlchemy model for knowledge base documents"""
    __tablename__ = 'knowledge_documents'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=False)
    tags = Column(JSON)
    metadata = Column(JSON)
    embedding_id = Column(String)
    content_hash = Column(String)  # For change detection


class SophiaKnowledgeBase:
    """
    Contained Company Knowledge Base for Sophia AI
    Manages curated company knowledge with vector search capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the knowledge base with configuration"""
        self.config = config
        self.db_engine = create_engine(config['database_url'])
        self.Session = sessionmaker(bind=self.db_engine)
        
        # Initialize vector databases
        self._init_pinecone()
        self._init_weaviate()
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create tables
        Base.metadata.create_all(self.db_engine)
        
        logger.info("Sophia Knowledge Base initialized")
    
    def _init_pinecone(self):
        """Initialize Pinecone vector database"""
        try:
            pinecone.init(
                api_key=self.config['pinecone_api_key'],
                environment=self.config.get('pinecone_environment', 'us-west1-gcp')
            )
            
            index_name = "sophia-knowledge-base"
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric='cosine'
                )
            
            self.pinecone_index = pinecone.Index(index_name)
            logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.pinecone_index = None
    
    def _init_weaviate(self):
        """Initialize Weaviate vector database"""
        try:
            self.weaviate_client = weaviate.Client(
                url=self.config['weaviate_url'],
                auth_client_secret=weaviate.AuthApiKey(
                    api_key=self.config['weaviate_api_key']
                )
            )
            
            # Create schema if it doesn't exist
            self._create_weaviate_schema()
            logger.info("Weaviate initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate: {e}")
            self.weaviate_client = None
    
    def _create_weaviate_schema(self):
        """Create Weaviate schema for knowledge documents"""
        schema = {
            "class": "KnowledgeDocument",
            "description": "Pay Ready company knowledge documents",
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "contentType",
                    "dataType": ["string"],
                    "description": "Type of content"
                },
                {
                    "name": "tags",
                    "dataType": ["string[]"],
                    "description": "Document tags"
                },
                {
                    "name": "createdAt",
                    "dataType": ["date"],
                    "description": "Creation timestamp"
                }
            ]
        }
        
        try:
            if not self.weaviate_client.schema.exists("KnowledgeDocument"):
                self.weaviate_client.schema.create_class(schema)
        except Exception as e:
            logger.warning(f"Schema creation warning: {e}")
    
    def add_document(self, document: KnowledgeDocument) -> bool:
        """
        Add a new document to the knowledge base
        
        Args:
            document: KnowledgeDocument to add
            
        Returns:
            bool: Success status
        """
        try:
            session = self.Session()
            
            # Generate content hash for change detection
            content_hash = hashlib.sha256(document.content.encode()).hexdigest()
            
            # Create database record
            db_doc = KnowledgeBaseDocument(
                id=document.id,
                title=document.title,
                content=document.content,
                content_type=document.content_type.value,
                status=document.status.value,
                version=document.version,
                created_by=document.created_by,
                tags=document.tags,
                metadata=document.metadata,
                content_hash=content_hash
            )
            
            session.add(db_doc)
            
            # Generate and store embeddings
            embedding_id = self._store_embeddings(document)
            if embedding_id:
                db_doc.embedding_id = embedding_id
            
            session.commit()
            session.close()
            
            logger.info(f"Added document: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            session.rollback()
            session.close()
            return False
    
    def _store_embeddings(self, document: KnowledgeDocument) -> Optional[str]:
        """Store document embeddings in vector databases"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(
                f"{document.title} {document.content}"
            ).tolist()
            
            embedding_id = f"doc_{document.id}"
            
            # Store in Pinecone
            if self.pinecone_index:
                self.pinecone_index.upsert([
                    (embedding_id, embedding, {
                        'title': document.title,
                        'content_type': document.content_type.value,
                        'tags': ','.join(document.tags)
                    })
                ])
            
            # Store in Weaviate
            if self.weaviate_client:
                self.weaviate_client.data_object.create(
                    data_object={
                        'title': document.title,
                        'content': document.content,
                        'contentType': document.content_type.value,
                        'tags': document.tags,
                        'createdAt': document.created_at.isoformat()
                    },
                    class_name="KnowledgeDocument",
                    uuid=embedding_id,
                    vector=embedding
                )
            
            return embedding_id
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            return None
    
    def search_documents(self, 
                        query: str, 
                        content_types: Optional[List[ContentType]] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity
        
        Args:
            query: Search query
            content_types: Filter by content types
            limit: Maximum number of results
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            results = []
            
            # Search Pinecone
            if self.pinecone_index:
                pinecone_results = self.pinecone_index.query(
                    vector=query_embedding,
                    top_k=limit,
                    include_metadata=True
                )
                
                for match in pinecone_results['matches']:
                    doc_id = match['id'].replace('doc_', '')
                    results.append({
                        'document_id': doc_id,
                        'score': match['score'],
                        'source': 'pinecone',
                        'metadata': match.get('metadata', {})
                    })
            
            # Get full document details from database
            session = self.Session()
            enriched_results = []
            
            for result in results:
                doc = session.query(KnowledgeBaseDocument).filter_by(
                    id=result['document_id']
                ).first()
                
                if doc and (not content_types or 
                           ContentType(doc.content_type) in content_types):
                    enriched_results.append({
                        'id': doc.id,
                        'title': doc.title,
                        'content': doc.content[:500] + '...' if len(doc.content) > 500 else doc.content,
                        'content_type': doc.content_type,
                        'tags': doc.tags,
                        'score': result['score'],
                        'created_at': doc.created_at.isoformat()
                    })
            
            session.close()
            
            # Sort by score and return top results
            enriched_results.sort(key=lambda x: x['score'], reverse=True)
            return enriched_results[:limit]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Get a specific document by ID"""
        try:
            session = self.Session()
            doc = session.query(KnowledgeBaseDocument).filter_by(id=document_id).first()
            session.close()
            
            if doc:
                return KnowledgeDocument(
                    id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    content_type=ContentType(doc.content_type),
                    status=ContentStatus(doc.status),
                    version=doc.version,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    created_by=doc.created_by,
                    tags=doc.tags or [],
                    metadata=doc.metadata or {},
                    embedding_id=doc.embedding_id
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def update_document(self, document: KnowledgeDocument) -> bool:
        """Update an existing document"""
        try:
            session = self.Session()
            
            # Get existing document
            existing = session.query(KnowledgeBaseDocument).filter_by(id=document.id).first()
            if not existing:
                session.close()
                return False
            
            # Check if content changed
            new_hash = hashlib.sha256(document.content.encode()).hexdigest()
            content_changed = existing.content_hash != new_hash
            
            # Update database record
            existing.title = document.title
            existing.content = document.content
            existing.content_type = document.content_type.value
            existing.status = document.status.value
            existing.tags = document.tags
            existing.metadata = document.metadata
            existing.updated_at = datetime.utcnow()
            existing.content_hash = new_hash
            
            if content_changed:
                existing.version += 1
                # Update embeddings
                embedding_id = self._store_embeddings(document)
                if embedding_id:
                    existing.embedding_id = embedding_id
            
            session.commit()
            session.close()
            
            logger.info(f"Updated document: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base content"""
        try:
            session = self.Session()
            
            total_docs = session.query(KnowledgeBaseDocument).count()
            
            # Count by content type
            type_counts = {}
            for content_type in ContentType:
                count = session.query(KnowledgeBaseDocument).filter_by(
                    content_type=content_type.value
                ).count()
                type_counts[content_type.value] = count
            
            # Count by status
            status_counts = {}
            for status in ContentStatus:
                count = session.query(KnowledgeBaseDocument).filter_by(
                    status=status.value
                ).count()
                status_counts[status.value] = count
            
            session.close()
            
            return {
                'total_documents': total_docs,
                'by_content_type': type_counts,
                'by_status': status_counts,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def bulk_import_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk import documents from a list of dictionaries
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Dictionary with import statistics
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for doc_data in documents:
            try:
                # Create KnowledgeDocument from dictionary
                document = KnowledgeDocument(
                    id=doc_data.get('id', f"doc_{datetime.utcnow().timestamp()}"),
                    title=doc_data['title'],
                    content=doc_data['content'],
                    content_type=ContentType(doc_data['content_type']),
                    status=ContentStatus(doc_data.get('status', 'draft')),
                    version=doc_data.get('version', 1),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    created_by=doc_data.get('created_by', 'system'),
                    tags=doc_data.get('tags', []),
                    metadata=doc_data.get('metadata', {})
                )
                
                if self.add_document(document):
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to import document: {e}")
                stats['failed'] += 1
        
        logger.info(f"Bulk import completed: {stats}")
        return stats


# Example usage and initialization
def initialize_sophia_knowledge_base(config: Dict[str, Any]) -> SophiaKnowledgeBase:
    """Initialize Sophia's knowledge base with Pay Ready configuration"""
    
    # Default configuration
    default_config = {
        'database_url': os.getenv('POSTGRES_URL', 'postgresql://sophia:sophia_pass@localhost:5432/sophia_payready'),
        'pinecone_api_key': os.getenv('PINECONE_API_KEY'),
        'pinecone_environment': 'us-west1-gcp',
        'weaviate_url': os.getenv('WEAVIATE_URL'),
        'weaviate_api_key': os.getenv('WEAVIATE_API_KEY')
    }
    
    # Merge with provided config
    final_config = {**default_config, **config}
    
    return SophiaKnowledgeBase(final_config)


# Sample data for initial knowledge base population
SAMPLE_PAY_READY_DOCUMENTS = [
    {
        'id': 'company_mission',
        'title': 'Pay Ready Mission Statement',
        'content': '''Pay Ready is dedicated to revolutionizing payment processing and financial technology solutions. Our mission is to provide businesses with seamless, secure, and intelligent payment systems that drive growth and enhance customer experiences.

Core Values:
- Innovation: Continuously advancing payment technology
- Security: Protecting customer data and transactions
- Reliability: Ensuring 99.9% uptime and consistent service
- Customer Success: Partnering with businesses for mutual growth''',
        'content_type': 'company_core',
        'status': 'published',
        'tags': ['mission', 'values', 'company'],
        'created_by': 'admin'
    },
    {
        'id': 'data_dictionary_kpis',
        'title': 'Key Performance Indicators (KPIs) Dictionary',
        'content': '''Pay Ready KPI Definitions:

Customer Acquisition Cost (CAC): Total cost of acquiring a new customer, including marketing and sales expenses.

Monthly Recurring Revenue (MRR): Predictable revenue generated each month from subscription customers.

Customer Lifetime Value (CLV): Total revenue expected from a customer over their entire relationship with Pay Ready.

Churn Rate: Percentage of customers who cancel their service within a given period.

Transaction Volume: Total dollar amount of payments processed through our platform.

Processing Success Rate: Percentage of transactions successfully completed without errors.

Average Transaction Size: Mean dollar amount per transaction processed.

Time to First Transaction: Average time from customer signup to their first processed payment.''',
        'content_type': 'data_dictionary',
        'status': 'published',
        'tags': ['kpis', 'metrics', 'definitions'],
        'created_by': 'admin'
    }
]


if __name__ == "__main__":
    # Example initialization and usage
    config = {
        'pinecone_api_key': 'your-pinecone-key',
        'weaviate_url': 'your-weaviate-url',
        'weaviate_api_key': 'your-weaviate-key'
    }
    
    kb = initialize_sophia_knowledge_base(config)
    
    # Import sample documents
    stats = kb.bulk_import_documents(SAMPLE_PAY_READY_DOCUMENTS)
    print(f"Import statistics: {stats}")
    
    # Test search
    results = kb.search_documents("What is Pay Ready's mission?")
    print(f"Search results: {len(results)} documents found")
    
    # Get statistics
    stats = kb.get_content_statistics()
    print(f"Knowledge base statistics: {stats}")

