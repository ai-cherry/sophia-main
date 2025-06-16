"""
Pay Ready Company Routes
Business intelligence and company performance endpoints for Pay Ready
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

company_bp = Blueprint('company', __name__)
logger = logging.getLogger(__name__)

@company_bp.route('/performance', methods=['GET'])
def get_company_performance():
    """Get Pay Ready company performance metrics"""
    try:
        # Get query parameters
        timeframe = request.args.get('timeframe', 'monthly')
        metrics = request.args.get('metrics', 'all').split(',')
        
        # Mock Pay Ready performance data (replace with actual data integration)
        performance_data = {
            "company": "Pay Ready",
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "revenue": {
                    "current": 1250000,
                    "previous": 1100000,
                    "growth_rate": 13.6,
                    "trend": "increasing"
                },
                "efficiency": {
                    "operational_efficiency": 87.5,
                    "cost_optimization": 92.3,
                    "process_automation": 78.9
                },
                "growth": {
                    "customer_acquisition": 156,
                    "market_expansion": 23.4,
                    "product_development": 89.2
                },
                "team": {
                    "productivity": 94.1,
                    "satisfaction": 88.7,
                    "retention": 96.3
                }
            },
            "insights": [
                "Pay Ready showing strong revenue growth of 13.6% this period",
                "Operational efficiency above industry benchmark",
                "Customer acquisition exceeding targets",
                "Team productivity and satisfaction at excellent levels"
            ],
            "recommendations": [
                "Continue current growth strategies",
                "Invest in process automation to reach 85%+ efficiency",
                "Expand successful customer acquisition channels"
            ]
        }
        
        return jsonify(performance_data)
        
    except Exception as e:
        logger.error(f"Error getting Pay Ready performance: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve Pay Ready performance data",
            "message": str(e)
        }), 500

@company_bp.route('/dashboard', methods=['GET'])
def get_company_dashboard():
    """Get Pay Ready executive dashboard data"""
    try:
        dashboard_data = {
            "company": "Pay Ready",
            "dashboard_type": "executive",
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": {
                "revenue_ytd": 14750000,
                "growth_rate": 18.3,
                "customer_count": 2847,
                "team_size": 47,
                "market_position": "Growing",
                "satisfaction_score": 4.7
            },
            "recent_achievements": [
                "Exceeded Q4 revenue targets by 12%",
                "Launched new product line successfully",
                "Expanded to 3 new markets",
                "Achieved 96% customer satisfaction"
            ],
            "upcoming_milestones": [
                "Q1 strategic planning session",
                "New office expansion",
                "Product roadmap review",
                "Team growth initiatives"
            ],
            "alerts": [
                {
                    "type": "opportunity",
                    "message": "Market expansion opportunity identified in Southeast region",
                    "priority": "high"
                },
                {
                    "type": "performance",
                    "message": "Customer acquisition costs trending down 8%",
                    "priority": "positive"
                }
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting Pay Ready dashboard: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve Pay Ready dashboard",
            "message": str(e)
        }), 500

@company_bp.route('/insights', methods=['POST'])
def generate_company_insights():
    """Generate AI-powered insights for Pay Ready"""
    try:
        data = request.get_json()
        focus_area = data.get('focus_area', 'general')
        depth = data.get('depth', 'standard')
        
        # Use Orchestra AI if available
        if current_app.orchestrator:
            prompt = f"""
            As Sophia, Pay Ready's dedicated company assistant, provide {depth} business insights 
            focusing on {focus_area} for Pay Ready's operations and strategy.
            
            Consider Pay Ready's current performance, market position, and growth objectives.
            Provide actionable recommendations specific to Pay Ready's business context.
            """
            
            try:
                response = current_app.orchestrator.process_request(
                    prompt=prompt,
                    persona="sophia",
                    context={"company": "Pay Ready", "focus": focus_area}
                )
                
                insights = {
                    "company": "Pay Ready",
                    "focus_area": focus_area,
                    "depth": depth,
                    "timestamp": datetime.utcnow().isoformat(),
                    "ai_insights": response.get('response', 'Analysis complete'),
                    "recommendations": response.get('recommendations', []),
                    "confidence": response.get('confidence', 0.85)
                }
                
            except Exception as ai_error:
                logger.warning(f"AI orchestrator error: {ai_error}")
                # Fallback insights
                insights = {
                    "company": "Pay Ready",
                    "focus_area": focus_area,
                    "depth": depth,
                    "timestamp": datetime.utcnow().isoformat(),
                    "ai_insights": f"Pay Ready analysis for {focus_area} shows positive trends with opportunities for optimization.",
                    "recommendations": [
                        "Continue monitoring key performance indicators",
                        "Focus on customer satisfaction and retention",
                        "Explore new market opportunities"
                    ],
                    "confidence": 0.75,
                    "note": "Generated using fallback analysis"
                }
        else:
            # Fallback when Orchestra AI not available
            insights = {
                "company": "Pay Ready",
                "focus_area": focus_area,
                "depth": depth,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_insights": f"Pay Ready {focus_area} analysis shows strong performance with growth opportunities.",
                "recommendations": [
                    "Maintain current successful strategies",
                    "Investigate expansion opportunities",
                    "Optimize operational efficiency"
                ],
                "confidence": 0.70,
                "note": "Orchestra AI not available - using standard analysis"
            }
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error generating Pay Ready insights: {str(e)}")
        return jsonify({
            "error": "Failed to generate Pay Ready insights",
            "message": str(e)
        }), 500

