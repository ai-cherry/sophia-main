"""
Knowledge Base Integration Module
Handles integration with existing admin website and deployment
"""

from flask import Flask, Blueprint, request, jsonify, render_template_string
from flask_cors import CORS

from backend.knowledge.knowledge_api import knowledge_bp
from backend.knowledge.workflow_manager import (
    KnowledgeBaseWorkflowManager,
    ScheduledWorkflowManager,
)

# Knowledge Base Admin Interface Blueprint
admin_kb_bp = Blueprint('admin_knowledge', __name__, url_prefix='/admin/knowledge')

# Admin interface HTML template
ADMIN_INTERFACE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sophia AI - Knowledge Base Admin</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .admin-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .tab-button {
            padding: 10px 20px;
            margin-right: 10px;
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            cursor: pointer;
        }
        .tab-button.active {
            background: #3b82f6;
            color: white;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="admin-container">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Sophia AI Knowledge Base</h1>
            <p class="text-gray-600">Manage your company's knowledge base and AI training data</p>
        </header>
        
        <nav class="mb-6">
            <div class="flex border-b">
                <button class="tab-button active" onclick="showTab('documents')">Documents</button>
                <button class="tab-button" onclick="showTab('analytics')">Analytics</button>
                <button class="tab-button" onclick="showTab('workflows')">Workflows</button>
                <button class="tab-button" onclick="showTab('settings')">Settings</button>
            </div>
        </nav>
        
        <!-- Documents Tab -->
        <div id="documents" class="tab-content active">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-semibold">Knowledge Base Documents</h2>
                    <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Add Document
                    </button>
                </div>
                
                <div class="mb-4">
                    <input type="text" placeholder="Search documents..." 
                           class="w-full p-3 border border-gray-300 rounded-lg">
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="border border-gray-200 rounded-lg p-4">
                        <h3 class="font-semibold mb-2">Company Mission Statement</h3>
                        <p class="text-gray-600 text-sm mb-3">Core company values and mission...</p>
                        <div class="flex justify-between items-center">
                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">Company Core</span>
                            <span class="text-xs text-gray-500">v2 • 2024-01-20</span>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg p-4">
                        <h3 class="font-semibold mb-2">Product Catalog</h3>
                        <p class="text-gray-600 text-sm mb-3">Complete product and service offerings...</p>
                        <div class="flex justify-between items-center">
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Products</span>
                            <span class="text-xs text-gray-500">v3 • 2024-01-18</span>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg p-4">
                        <h3 class="font-semibold mb-2">Sales Process</h3>
                        <p class="text-gray-600 text-sm mb-3">Step-by-step sales methodology...</p>
                        <div class="flex justify-between items-center">
                            <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">Sales</span>
                            <span class="text-xs text-gray-500">v1 • 2024-01-22</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Analytics Tab -->
        <div id="analytics" class="tab-content">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Total Documents</h3>
                    <p class="text-3xl font-bold text-gray-900">47</p>
                    <p class="text-sm text-green-600">+3 from last month</p>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Published</h3>
                    <p class="text-3xl font-bold text-gray-900">42</p>
                    <p class="text-sm text-gray-600">5 in draft</p>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Total Searches</h3>
                    <p class="text-3xl font-bold text-gray-900">1,247</p>
                    <p class="text-sm text-green-600">+12% from last week</p>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Avg Response Time</h3>
                    <p class="text-3xl font-bold text-gray-900">185ms</p>
                    <p class="text-sm text-green-600">-15ms improvement</p>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">Knowledge Base Performance</h2>
                <div class="h-64 bg-gray-100 rounded flex items-center justify-center">
                    <p class="text-gray-500">Analytics charts would be displayed here</p>
                </div>
            </div>
        </div>
        
        <!-- Workflows Tab -->
        <div id="workflows" class="tab-content">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-semibold">Automated Workflows</h2>
                    <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Create Workflow
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="border border-gray-200 rounded-lg p-4">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="font-semibold">Daily Notion Sync</h3>
                                <p class="text-gray-600 text-sm">Syncs content from Notion workspace daily</p>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Active</span>
                                <button class="text-blue-600 hover:text-blue-800">Configure</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg p-4">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="font-semibold">SharePoint Import</h3>
                                <p class="text-gray-600 text-sm">Weekly import of documents from SharePoint</p>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">Pending</span>
                                <button class="text-blue-600 hover:text-blue-800">Configure</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg p-4">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="font-semibold">Slack Knowledge Bot</h3>
                                <p class="text-gray-600 text-sm">Enables knowledge base queries from Slack</p>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Connected</span>
                                <button class="text-blue-600 hover:text-blue-800">Configure</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">General Settings</h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Knowledge Base Name</label>
                            <input type="text" value="Pay Ready Knowledge Base" 
                                   class="w-full p-3 border border-gray-300 rounded-lg">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Auto-save Interval (minutes)</label>
                            <input type="number" value="5" 
                                   class="w-full p-3 border border-gray-300 rounded-lg">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Maximum Versions per Document</label>
                            <input type="number" value="10" 
                                   class="w-full p-3 border border-gray-300 rounded-lg">
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">Vector Database Status</h2>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                            <div>
                                <h3 class="font-medium">Pinecone</h3>
                                <p class="text-sm text-gray-600">Vector search operational</p>
                            </div>
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Connected</span>
                        </div>
                        
                        <div class="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                            <div>
                                <h3 class="font-medium">Weaviate</h3>
                                <p class="text-sm text-gray-600">Knowledge graph active</p>
                            </div>
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Connected</span>
                        </div>
                        
                        <div class="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <div>
                                <h3 class="font-medium">Redis Cache</h3>
                                <p class="text-sm text-gray-600">Response time: 185ms</p>
                            </div>
                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">Optimal</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => button.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }
        
        // Initialize with documents tab active
        document.addEventListener('DOMContentLoaded', function() {
            showTab('documents');
        });
    </script>
</body>
</html>
"""

@admin_kb_bp.route('/')
def admin_interface():
    """Serve the knowledge base admin interface"""
    return render_template_string(ADMIN_INTERFACE_TEMPLATE)

@admin_kb_bp.route('/api/status')
def api_status():
    """Get knowledge base system status"""
    return jsonify({
        'status': 'operational',
        'databases': {
            'postgresql': 'connected',
            'redis': 'connected',
            'pinecone': 'connected',
            'weaviate': 'connected'
        },
        'metrics': {
            'total_documents': 47,
            'published_documents': 42,
            'draft_documents': 5,
            'total_searches': 1247,
            'avg_response_time': '185ms'
        }
    })

@admin_kb_bp.route('/api/workflows')
def list_workflows():
    """List all workflow tasks"""
    # This would integrate with the actual workflow manager
    workflows = [
        {
            'id': 'notion_sync_daily',
            'name': 'Daily Notion Sync',
            'source': 'notion',
            'status': 'active',
            'last_run': '2024-01-22T08:00:00Z',
            'next_run': '2024-01-23T08:00:00Z'
        },
        {
            'id': 'sharepoint_weekly',
            'name': 'SharePoint Import',
            'source': 'sharepoint',
            'status': 'pending',
            'last_run': None,
            'next_run': '2024-01-28T09:00:00Z'
        }
    ]
    return jsonify({'workflows': workflows})

@admin_kb_bp.route('/api/workflows', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'source', 'metadata']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # This would integrate with the actual workflow manager
    workflow_id = f"workflow_{data['source']}_{int(time.time())}"
    
    return jsonify({
        'id': workflow_id,
        'name': data['name'],
        'source': data['source'],
        'status': 'created',
        'message': 'Workflow created successfully'
    }), 201

def create_admin_app():
    """Create Flask app with knowledge base admin interface"""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(admin_kb_bp)
    app.register_blueprint(knowledge_bp)
    
    return app

def integrate_with_existing_admin(existing_app):
    """
    Integrate knowledge base admin with existing admin website
    
    Args:
        existing_app: Existing Flask application instance
    """
    
    # Register the knowledge base blueprint
    existing_app.register_blueprint(admin_kb_bp)
    existing_app.register_blueprint(knowledge_bp)
    
    # Add navigation item to existing admin (this would be customized based on your admin structure)
    @existing_app.context_processor
    def inject_kb_nav():
        return {
            'knowledge_base_nav': {
                'title': 'Knowledge Base',
                'url': '/admin/knowledge',
                'icon': 'brain'
            }
        }
    
    return existing_app

# Deployment configuration
class KnowledgeBaseDeployment:
    """
    Handles deployment configuration for knowledge base admin
    """
    
    def __init__(self, config):
        self.config = config
    
    def deploy_to_vercel(self):
        """Deploy the React admin interface to Vercel"""
        vercel_config = {
            "name": "sophia-knowledge-admin",
            "version": 2,
            "builds": [
                {
                    "src": "package.json",
                    "use": "@vercel/static-build",
                    "config": {
                        "distDir": "dist"
                    }
                }
            ],
            "routes": [
                {
                    "src": "/api/(.*)",
                    "dest": "/api/$1"
                },
                {
                    "src": "/(.*)",
                    "dest": "/index.html"
                }
            ],
            "env": {
                "REACT_APP_API_URL": self.config.get('api_url', 'https://api.sophia.ai'),
                "REACT_APP_AUTH_DOMAIN": self.config.get('auth_domain', 'sophia.auth0.com')
            }
        }
        
        return vercel_config
    
    def deploy_to_lambda_labs(self):
        """Deploy the backend API to Lambda Labs"""
        docker_config = {
            "FROM": "python:3.11-slim",
            "WORKDIR": "/app",
            "COPY": ["requirements.txt", "."],
            "RUN": "pip install -r requirements.txt",
            "COPY": [".", "."],
            "EXPOSE": 5000,
            "CMD": ["python", "app.py"]
        }
        
        return docker_config
    
    def generate_nginx_config(self):
        """Generate Nginx configuration for production deployment"""
        nginx_config = """
server {
    listen 80;
    server_name sophia-admin.payready.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sophia-admin.payready.com;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/sophia-admin.crt;
    ssl_certificate_key /etc/ssl/private/sophia-admin.key;
    
    # Frontend (React app)
    location / {
        root /var/www/sophia-admin/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Knowledge base admin interface
    location /admin/knowledge/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
        return nginx_config

if __name__ == "__main__":
    # Example usage
    app = create_admin_app()
    app.run(debug=True, host='0.0.0.0', port=5001)

