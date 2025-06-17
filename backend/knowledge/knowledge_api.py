"""
Knowledge Base Management API for Sophia AI
RESTful endpoints for managing Pay Ready company knowledge
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, List, Any
import logging

from backend.knowledge.knowledge_base import (
    SophiaKnowledgeBase, 
    KnowledgeDocument, 
    ContentType, 
    ContentStatus,
    initialize_sophia_knowledge_base
)
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Create Blueprint
knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

# Initialize knowledge base
try:
    kb_config = {
        'database_url': settings.database.url,
        'pinecone_api_key': settings.api_keys.pinecone_api_key,
        'weaviate_url': settings.api_keys.weaviate_url,
        'weaviate_api_key': settings.api_keys.weaviate_api_key
    }
    knowledge_base = initialize_sophia_knowledge_base(kb_config)
    logger.info("Knowledge base initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize knowledge base: {e}")
    knowledge_base = None


@knowledge_bp.route('/search', methods=['POST'])
@jwt_required()
def search_knowledge():
    """
    Search the knowledge base using semantic similarity
    
    POST /api/knowledge/search
    {
        "query": "What is Pay Ready's mission?",
        "content_types": ["company_core", "data_dictionary"],
        "limit": 10
    }
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        data = request.get_json()
        query = data.get('query', '')
        content_types_str = data.get('content_types', [])
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Convert content type strings to enums
        content_types = []
        for ct_str in content_types_str:
            try:
                content_types.append(ContentType(ct_str))
            except ValueError:
                logger.warning(f"Invalid content type: {ct_str}")
        
        # Perform search
        results = knowledge_base.search_documents(
            query=query,
            content_types=content_types if content_types else None,
            limit=limit
        )
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@knowledge_bp.route('/documents', methods=['GET'])
@jwt_required()
def list_documents():
    """
    List all documents in the knowledge base
    
    GET /api/knowledge/documents?content_type=company_core&status=published&limit=50
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        # Get query parameters
        content_type = request.args.get('content_type')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        # This would require additional implementation in the knowledge base class
        # For now, return statistics
        stats = knowledge_base.get_content_statistics()
        
        return jsonify({
            'message': 'Document listing not yet implemented',
            'statistics': stats,
            'filters': {
                'content_type': content_type,
                'status': status,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return jsonify({'error': 'Failed to list documents'}), 500


@knowledge_bp.route('/documents/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id: str):
    """
    Get a specific document by ID
    
    GET /api/knowledge/documents/company_mission
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        document = knowledge_base.get_document(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'document': document.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return jsonify({'error': 'Failed to get document'}), 500


@knowledge_bp.route('/documents', methods=['POST'])
@jwt_required()
def create_document():
    """
    Create a new document in the knowledge base
    
    POST /api/knowledge/documents
    {
        "title": "New Company Policy",
        "content": "Policy content here...",
        "content_type": "operations",
        "tags": ["policy", "operations"],
        "metadata": {"department": "HR"}
    }
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['title', 'content', 'content_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create document
        from datetime import datetime
        import uuid
        
        document = KnowledgeDocument(
            id=data.get('id', str(uuid.uuid4())),
            title=data['title'],
            content=data['content'],
            content_type=ContentType(data['content_type']),
            status=ContentStatus(data.get('status', 'draft')),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=user_id,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
        
        success = knowledge_base.add_document(document)
        
        if success:
            return jsonify({
                'message': 'Document created successfully',
                'document_id': document.id
            }), 201
        else:
            return jsonify({'error': 'Failed to create document'}), 500
        
    except ValueError as e:
        return jsonify({'error': f'Invalid content type or status: {e}'}), 400
    except Exception as e:
        logger.error(f"Create document error: {e}")
        return jsonify({'error': 'Failed to create document'}), 500


@knowledge_bp.route('/documents/<document_id>', methods=['PUT'])
@jwt_required()
def update_document(document_id: str):
    """
    Update an existing document
    
    PUT /api/knowledge/documents/company_mission
    {
        "title": "Updated Mission Statement",
        "content": "Updated content...",
        "status": "published"
    }
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        # Get existing document
        existing_doc = knowledge_base.get_document(document_id)
        if not existing_doc:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Update document fields
        from datetime import datetime
        
        updated_doc = KnowledgeDocument(
            id=existing_doc.id,
            title=data.get('title', existing_doc.title),
            content=data.get('content', existing_doc.content),
            content_type=ContentType(data.get('content_type', existing_doc.content_type.value)),
            status=ContentStatus(data.get('status', existing_doc.status.value)),
            version=existing_doc.version,
            created_at=existing_doc.created_at,
            updated_at=datetime.utcnow(),
            created_by=existing_doc.created_by,
            tags=data.get('tags', existing_doc.tags),
            metadata=data.get('metadata', existing_doc.metadata)
        )
        
        success = knowledge_base.update_document(updated_doc)
        
        if success:
            return jsonify({
                'message': 'Document updated successfully',
                'document_id': document_id
            })
        else:
            return jsonify({'error': 'Failed to update document'}), 500
        
    except ValueError as e:
        return jsonify({'error': f'Invalid content type or status: {e}'}), 400
    except Exception as e:
        logger.error(f"Update document error: {e}")
        return jsonify({'error': 'Failed to update document'}), 500


@knowledge_bp.route('/bulk-import', methods=['POST'])
@jwt_required()
def bulk_import():
    """
    Bulk import documents from JSON
    
    POST /api/knowledge/bulk-import
    {
        "documents": [
            {
                "title": "Document 1",
                "content": "Content 1",
                "content_type": "company_core",
                "tags": ["tag1"]
            },
            ...
        ]
    }
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        data = request.get_json()
        documents = data.get('documents', [])
        
        if not documents:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Add created_by to all documents
        user_id = get_jwt_identity()
        for doc in documents:
            doc['created_by'] = user_id
        
        # Perform bulk import
        stats = knowledge_base.bulk_import_documents(documents)
        
        return jsonify({
            'message': 'Bulk import completed',
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Bulk import error: {e}")
        return jsonify({'error': 'Bulk import failed'}), 500


@knowledge_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    Get knowledge base statistics
    
    GET /api/knowledge/statistics
    """
    try:
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not available'}), 503
        
        stats = knowledge_base.get_content_statistics()
        
        return jsonify({
            'statistics': stats,
            'content_types': [ct.value for ct in ContentType],
            'status_types': [st.value for st in ContentStatus]
        })
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@knowledge_bp.route('/content-types', methods=['GET'])
def get_content_types():
    """
    Get available content types
    
    GET /api/knowledge/content-types
    """
    return jsonify({
        'content_types': [
            {
                'value': ct.value,
                'name': ct.name,
                'description': _get_content_type_description(ct)
            }
            for ct in ContentType
        ]
    })


def _get_content_type_description(content_type: ContentType) -> str:
    """Get human-readable description for content types"""
    descriptions = {
        ContentType.COMPANY_CORE: "Mission, vision, values, and organizational information",
        ContentType.PRODUCTS_SERVICES: "Product descriptions, features, and service offerings",
        ContentType.OPERATIONS: "Standard operating procedures and workflow documentation",
        ContentType.DATA_DICTIONARY: "Business terminology, KPI definitions, and data standards",
        ContentType.SALES_MARKETING: "Sales processes, marketing strategies, and customer personas",
        ContentType.CUSTOMER_SUCCESS: "Support procedures, onboarding, and success metrics",
        ContentType.FINANCIAL: "Revenue models, cost structures, and financial processes",
        ContentType.STRATEGIC: "Business goals, market analysis, and growth strategies",
        ContentType.TECHNOLOGY: "System architecture, integrations, and technical documentation",
        ContentType.VENDORS_PARTNERS: "Partner information, vendor relationships, and contracts"
    }
    return descriptions.get(content_type, "No description available")


# Health check endpoint
@knowledge_bp.route('/health', methods=['GET'])
def health_check():
    """Knowledge base health check"""
    try:
        if not knowledge_base:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Knowledge base not initialized'
            }), 503
        
        # Test basic functionality
        stats = knowledge_base.get_content_statistics()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Knowledge base operational',
            'document_count': stats.get('total_documents', 0)
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check failed: {e}'
        }), 503

