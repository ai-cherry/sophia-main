"""
Hugging Face MCP Server Integration for Sophia AI
Provides access to HF models, datasets, and community tools
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HFModel:
    id: str
    name: str
    description: str
    downloads: int
    likes: int
    tags: List[str]
    pipeline_tag: Optional[str] = None
    library_name: Optional[str] = None

@dataclass
class HFDataset:
    id: str
    name: str
    description: str
    downloads: int
    likes: int
    tags: List[str]
    task_categories: List[str]

class HuggingFaceMCPServer:
    """
    Hugging Face MCP Server integration for Sophia AI
    Provides access to models, datasets, and semantic search capabilities
    """
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://huggingface.co/api"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
    async def search_models(self, query: str, limit: int = 10, 
                          filter_tags: Optional[List[str]] = None) -> List[HFModel]:
        """Search for models on Hugging Face Hub"""
        try:
            params = {
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": -1
            }
            
            if filter_tags:
                params["filter"] = ",".join(filter_tags)
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            models_data = response.json()
            models = []
            
            for model_data in models_data:
                model = HFModel(
                    id=model_data.get("id", ""),
                    name=model_data.get("id", "").split("/")[-1],
                    description=model_data.get("description", ""),
                    downloads=model_data.get("downloads", 0),
                    likes=model_data.get("likes", 0),
                    tags=model_data.get("tags", []),
                    pipeline_tag=model_data.get("pipeline_tag"),
                    library_name=model_data.get("library_name")
                )
                models.append(model)
            
            logger.info(f"Found {len(models)} models for query: {query}")
            return models
            
        except Exception as e:
            logger.error(f"Error searching models: {e}")
            return []
    
    async def search_datasets(self, query: str, limit: int = 10,
                            task_categories: Optional[List[str]] = None) -> List[HFDataset]:
        """Search for datasets on Hugging Face Hub"""
        try:
            params = {
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": -1
            }
            
            if task_categories:
                params["filter"] = ",".join(task_categories)
            
            response = requests.get(
                f"{self.base_url}/datasets",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            datasets_data = response.json()
            datasets = []
            
            for dataset_data in datasets_data:
                dataset = HFDataset(
                    id=dataset_data.get("id", ""),
                    name=dataset_data.get("id", "").split("/")[-1],
                    description=dataset_data.get("description", ""),
                    downloads=dataset_data.get("downloads", 0),
                    likes=dataset_data.get("likes", 0),
                    tags=dataset_data.get("tags", []),
                    task_categories=dataset_data.get("task_categories", [])
                )
                datasets.append(dataset)
            
            logger.info(f"Found {len(datasets)} datasets for query: {query}")
            return datasets
            
        except Exception as e:
            logger.error(f"Error searching datasets: {e}")
            return []
    
    async def semantic_search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on research papers"""
        try:
            # This would use HF's semantic search API for papers
            # For now, we'll simulate the response structure
            papers = [
                {
                    "id": f"paper_{i}",
                    "title": f"Research Paper {i}: {query}",
                    "abstract": f"Abstract for paper about {query}...",
                    "authors": ["Author 1", "Author 2"],
                    "published_date": "2024-01-15",
                    "arxiv_id": f"2401.{1000 + i}",
                    "relevance_score": 0.95 - (i * 0.05),
                    "citations": 150 - (i * 10)
                }
                for i in range(min(limit, 5))
            ]
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        try:
            response = requests.get(
                f"{self.base_url}/models/{model_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            model_info = response.json()
            
            # Enhance with additional metadata
            enhanced_info = {
                "id": model_info.get("id"),
                "name": model_info.get("id", "").split("/")[-1],
                "description": model_info.get("description", ""),
                "downloads": model_info.get("downloads", 0),
                "likes": model_info.get("likes", 0),
                "tags": model_info.get("tags", []),
                "pipeline_tag": model_info.get("pipeline_tag"),
                "library_name": model_info.get("library_name"),
                "created_at": model_info.get("createdAt"),
                "last_modified": model_info.get("lastModified"),
                "siblings": model_info.get("siblings", []),
                "config": model_info.get("config", {}),
                "card_data": model_info.get("cardData", {})
            }
            
            return enhanced_info
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_id}: {e}")
            return None
    
    async def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific dataset"""
        try:
            response = requests.get(
                f"{self.base_url}/datasets/{dataset_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            dataset_info = response.json()
            
            # Enhance with additional metadata
            enhanced_info = {
                "id": dataset_info.get("id"),
                "name": dataset_info.get("id", "").split("/")[-1],
                "description": dataset_info.get("description", ""),
                "downloads": dataset_info.get("downloads", 0),
                "likes": dataset_info.get("likes", 0),
                "tags": dataset_info.get("tags", []),
                "task_categories": dataset_info.get("task_categories", []),
                "created_at": dataset_info.get("createdAt"),
                "last_modified": dataset_info.get("lastModified"),
                "siblings": dataset_info.get("siblings", []),
                "card_data": dataset_info.get("cardData", {}),
                "size_categories": dataset_info.get("size_categories", [])
            }
            
            return enhanced_info
            
        except Exception as e:
            logger.error(f"Error getting dataset info for {dataset_id}: {e}")
            return None
    
    async def list_spaces(self, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List Hugging Face Spaces (Gradio apps)"""
        try:
            params = {
                "limit": limit,
                "sort": "likes",
                "direction": -1
            }
            
            if query:
                params["search"] = query
            
            response = requests.get(
                f"{self.base_url}/spaces",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            spaces_data = response.json()
            spaces = []
            
            for space_data in spaces_data:
                space = {
                    "id": space_data.get("id", ""),
                    "name": space_data.get("id", "").split("/")[-1],
                    "description": space_data.get("description", ""),
                    "likes": space_data.get("likes", 0),
                    "tags": space_data.get("tags", []),
                    "sdk": space_data.get("sdk", ""),
                    "runtime": space_data.get("runtime", {}),
                    "created_at": space_data.get("createdAt"),
                    "last_modified": space_data.get("lastModified")
                }
                spaces.append(space)
            
            logger.info(f"Found {len(spaces)} spaces")
            return spaces
            
        except Exception as e:
            logger.error(f"Error listing spaces: {e}")
            return []
    
    async def recommend_models_for_task(self, task: str, business_context: str = "") -> List[HFModel]:
        """Recommend models based on business task and context"""
        try:
            # Map business tasks to HF pipeline tags
            task_mapping = {
                "text_analysis": ["text-classification", "sentiment-analysis"],
                "document_processing": ["document-question-answering", "text-generation"],
                "customer_support": ["conversational", "question-answering"],
                "data_extraction": ["token-classification", "text2text-generation"],
                "content_generation": ["text-generation", "summarization"],
                "translation": ["translation"],
                "speech_processing": ["automatic-speech-recognition", "text-to-speech"]
            }
            
            pipeline_tags = task_mapping.get(task, ["text-generation"])
            
            # Search for models with relevant tags
            all_models = []
            for tag in pipeline_tags:
                models = await self.search_models(
                    query=f"{task} {business_context}",
                    limit=5,
                    filter_tags=[tag]
                )
                all_models.extend(models)
            
            # Remove duplicates and sort by downloads
            unique_models = {}
            for model in all_models:
                if model.id not in unique_models:
                    unique_models[model.id] = model
            
            sorted_models = sorted(
                unique_models.values(),
                key=lambda x: x.downloads,
                reverse=True
            )
            
            return sorted_models[:10]
            
        except Exception as e:
            logger.error(f"Error recommending models for task {task}: {e}")
            return []

class SophiaHFIntegration:
    """
    Integration layer between Sophia AI and Hugging Face MCP Server
    """
    
    def __init__(self, hf_api_token: str):
        self.hf_server = HuggingFaceMCPServer(hf_api_token)
        self.integration_config = {
            "business_tasks": {
                "revenue_analysis": "text_analysis",
                "customer_feedback": "text_analysis", 
                "document_processing": "document_processing",
                "support_automation": "customer_support",
                "content_creation": "content_generation",
                "data_extraction": "data_extraction"
            }
        }
    
    async def enhance_knowledge_base_with_models(self, business_domain: str) -> Dict[str, Any]:
        """Enhance Sophia's knowledge base with relevant HF models"""
        try:
            # Get business-relevant models
            task = self.integration_config["business_tasks"].get(
                business_domain, "text_analysis"
            )
            
            models = await self.hf_server.recommend_models_for_task(
                task=task,
                business_context="business intelligence financial analysis"
            )
            
            # Get relevant datasets
            datasets = await self.hf_server.search_datasets(
                query=f"business {business_domain} financial",
                limit=5
            )
            
            # Get research papers
            papers = await self.hf_server.semantic_search_papers(
                query=f"{business_domain} business intelligence AI",
                limit=5
            )
            
            enhancement_data = {
                "domain": business_domain,
                "recommended_models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "description": model.description,
                        "downloads": model.downloads,
                        "pipeline_tag": model.pipeline_tag,
                        "use_case": f"Sophia AI {business_domain} enhancement"
                    }
                    for model in models
                ],
                "relevant_datasets": [
                    {
                        "id": dataset.id,
                        "name": dataset.name,
                        "description": dataset.description,
                        "task_categories": dataset.task_categories
                    }
                    for dataset in datasets
                ],
                "research_papers": papers,
                "integration_timestamp": datetime.now().isoformat()
            }
            
            return enhancement_data
            
        except Exception as e:
            logger.error(f"Error enhancing knowledge base: {e}")
            return {}
    
    async def get_model_recommendations_for_sophia(self) -> Dict[str, List[HFModel]]:
        """Get model recommendations specifically for Sophia AI capabilities"""
        recommendations = {}
        
        sophia_capabilities = [
            "revenue_analysis",
            "customer_feedback", 
            "document_processing",
            "support_automation",
            "content_creation"
        ]
        
        for capability in sophia_capabilities:
            try:
                models = await self.enhance_knowledge_base_with_models(capability)
                recommendations[capability] = models.get("recommended_models", [])
            except Exception as e:
                logger.error(f"Error getting recommendations for {capability}: {e}")
                recommendations[capability] = []
        
        return recommendations

# Flask API endpoints for HF MCP integration
from flask import Blueprint, request, jsonify

hf_mcp_bp = Blueprint('hf_mcp', __name__, url_prefix='/api/hf-mcp')

# Initialize with environment variable
HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN', '')
sophia_hf = SophiaHFIntegration(HF_API_TOKEN) if HF_API_TOKEN else None

@hf_mcp_bp.route('/search/models')
async def search_models():
    """Search for models on Hugging Face Hub"""
    if not sophia_hf:
        return jsonify({'error': 'HF API token not configured'}), 500
    
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 10))
    tags = request.args.getlist('tags')
    
    models = await sophia_hf.hf_server.search_models(
        query=query,
        limit=limit,
        filter_tags=tags if tags else None
    )
    
    return jsonify({
        'models': [
            {
                'id': model.id,
                'name': model.name,
                'description': model.description,
                'downloads': model.downloads,
                'likes': model.likes,
                'tags': model.tags,
                'pipeline_tag': model.pipeline_tag
            }
            for model in models
        ]
    })

@hf_mcp_bp.route('/search/datasets')
async def search_datasets():
    """Search for datasets on Hugging Face Hub"""
    if not sophia_hf:
        return jsonify({'error': 'HF API token not configured'}), 500
    
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 10))
    
    datasets = await sophia_hf.hf_server.search_datasets(
        query=query,
        limit=limit
    )
    
    return jsonify({
        'datasets': [
            {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'downloads': dataset.downloads,
                'likes': dataset.likes,
                'tags': dataset.tags,
                'task_categories': dataset.task_categories
            }
            for dataset in datasets
        ]
    })

@hf_mcp_bp.route('/recommendations')
async def get_recommendations():
    """Get model recommendations for Sophia AI"""
    if not sophia_hf:
        return jsonify({'error': 'HF API token not configured'}), 500
    
    recommendations = await sophia_hf.get_model_recommendations_for_sophia()
    return jsonify({'recommendations': recommendations})

@hf_mcp_bp.route('/enhance/<domain>')
async def enhance_domain(domain):
    """Enhance knowledge base for specific business domain"""
    if not sophia_hf:
        return jsonify({'error': 'HF API token not configured'}), 500
    
    enhancement_data = await sophia_hf.enhance_knowledge_base_with_models(domain)
    return jsonify(enhancement_data)

# Example usage
async def main():
    """Example usage of HF MCP integration"""
    api_token = os.getenv('HUGGINGFACE_API_TOKEN', 'your_token_here')
    sophia_hf = SophiaHFIntegration(api_token)
    
    # Get recommendations for revenue analysis
    enhancement = await sophia_hf.enhance_knowledge_base_with_models("revenue_analysis")
    print(f"Found {len(enhancement.get('recommended_models', []))} models for revenue analysis")
    
    # Get all recommendations
    recommendations = await sophia_hf.get_model_recommendations_for_sophia()
    print(f"Total recommendations: {sum(len(models) for models in recommendations.values())}")

if __name__ == "__main__":
    asyncio.run(main())

