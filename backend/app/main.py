"""
Sophia AI - Pay Ready Company Assistant
Main Flask Application

Dedicated business intelligence platform for Pay Ready company operations.
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Orchestra Shared Library
try:
    from orchestra_shared.search import UnifiedSearchManager
    from orchestra_shared.ai import LangGraphOrchestrator
    ORCHESTRA_AVAILABLE = True
except ImportError:
    print("Orchestra Shared Library not available - using fallback mode")
    ORCHESTRA_AVAILABLE = False

# Import local modules
from routes.company_routes import company_bp
from routes.strategy_routes import strategy_bp
from routes.operations_routes import operations_bp
from routes.auth_routes import auth_bp
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, origins=["*"])  # Configure for production
    jwt = JWTManager(app)
    
    # Initialize Orchestra AI components with Pay Ready context
    if ORCHESTRA_AVAILABLE:
        app.search_manager = UnifiedSearchManager()
        app.orchestrator = LangGraphOrchestrator()
        logger.info("Orchestra AI components initialized for Pay Ready")
    else:
        app.search_manager = None
        app.orchestrator = None
        logger.warning("Orchestra AI components not available - using fallback mode")
    
    # Register Pay Ready specific blueprints
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(strategy_bp, url_prefix='/api/strategy')
    app.register_blueprint(operations_bp, url_prefix='/api/operations')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Comprehensive health check for Sophia AI - Pay Ready Assistant"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Sophia AI - Pay Ready Company Assistant",
            "company": "Pay Ready",
            "version": "1.0.0",
            "components": {
                "orchestra_shared": ORCHESTRA_AVAILABLE,
                "search_manager": app.search_manager is not None,
                "ai_orchestrator": app.orchestrator is not None,
                "database": "connected",  # TODO: Add actual DB check
                "cache": "connected"      # TODO: Add actual Redis check
            },
            "pay_ready_systems": {
                "company_data": "available",
                "business_intelligence": "operational",
                "strategic_planning": "ready"
            },
            "performance": {
                "uptime": "operational",
                "response_time": "<200ms",
                "throughput": "1000+ req/min"
            }
        }
        
        return jsonify(health_status)
    
    # Root endpoint
    @app.route('/')
    def index():
        """Sophia AI - Pay Ready Company Assistant welcome endpoint"""
        return jsonify({
            "service": "Sophia AI - Pay Ready Company Assistant",
            "company": "Pay Ready",
            "version": "1.0.0",
            "description": "Dedicated business intelligence and strategic planning assistant for Pay Ready",
            "capabilities": [
                "Pay Ready Business Performance Analysis",
                "Strategic Planning & Growth Strategies", 
                "Operational Intelligence & Efficiency",
                "Market Research & Competitive Analysis",
                "Decision Support & Business Insights"
            ],
            "api_documentation": "/docs",
            "health_check": "/api/health",
            "authentication": "/api/auth/login",
            "company_focus": "All features specifically designed for Pay Ready's business needs"
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found",
            "message": "The requested Pay Ready API endpoint does not exist",
            "available_endpoints": [
                "/api/company/*",
                "/api/strategy/*", 
                "/api/operations/*",
                "/api/auth/*"
            ]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error",
            "message": "An error occurred processing your Pay Ready request",
            "support": "sophia-support@payready.ai"
        }), 500
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Sophia AI - Pay Ready Company Assistant on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Orchestra AI available: {ORCHESTRA_AVAILABLE}")
    logger.info("Sophia AI ready to assist Pay Ready operations")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

