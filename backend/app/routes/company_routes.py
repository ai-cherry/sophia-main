"""
Sophia AI - Company Routes
Pay Ready specific business intelligence endpoints

This module provides API endpoints for company-specific operations and analytics.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from agents.core.orchestrator import SophiaOrchestrator
from integrations.hubspot.hubspot_integration import HubSpotIntegration
from monitoring.enhanced_monitoring import SophiaMonitoringSystem

logger = logging.getLogger(__name__)

# Create blueprint
company_bp = Blueprint('company', __name__)

# Initialize components
orchestrator = SophiaOrchestrator()
monitoring = SophiaMonitoringSystem()
hubspot = HubSpotIntegration()

@company_bp.route('/overview', methods=['GET'])
@jwt_required()
async def company_overview():
    """Get comprehensive company overview"""
    try:
        # Get current business metrics
        metrics = await monitoring.get_current_metrics()
        business_metrics = metrics.get('business', {})
        
        # Get recent performance
        performance = {
            'revenue': {
                'current_month': business_metrics.get('revenue', {}).get('monthly', 0),
                'growth_rate': business_metrics.get('revenue', {}).get('growth_rate', 0),
                'total': business_metrics.get('revenue', {}).get('total', 0)
            },
            'customers': {
                'total': business_metrics.get('customers', {}).get('total', 0),
                'new_this_month': business_metrics.get('customers', {}).get('new_this_month', 0),
                'churn_rate': business_metrics.get('customers', {}).get('churn_rate', 0)
            },
            'deals': {
                'in_pipeline': business_metrics.get('deals', {}).get('in_pipeline', 0),
                'closed_this_month': business_metrics.get('deals', {}).get('closed_won_this_month', 0),
                'average_size': business_metrics.get('deals', {}).get('average_deal_size', 0)
            }
        }
        
        # Get system health
        health = await monitoring.health_check()
        
        return jsonify({
            'company': settings.company_name,
            'timestamp': datetime.now().isoformat(),
            'performance': performance,
            'system_health': health.get('status'),
            'active_agents': health.get('active_agents', 0),
            'integrations_status': health.get('integrations', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Company overview error: {str(e)}")
        return jsonify({'error': 'Failed to get company overview'}), 500

@company_bp.route('/revenue', methods=['GET'])
@jwt_required()
async def revenue_analysis():
    """Get detailed revenue analysis"""
    try:
        # Get time range from query params
        days = request.args.get('days', 30, type=int)
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        # Get revenue data from HubSpot
        async with hubspot:
            # Get all deals in date range
            deals = await hubspot.search_deals([
                {
                    'propertyName': 'closedate',
                    'operator': 'GTE',
                    'value': from_date.timestamp() * 1000
                }
            ])
            
            # Calculate revenue metrics
            total_revenue = sum(
                float(deal.get('properties', {}).get('amount', 0) or 0)
                for deal in deals
                if deal.get('properties', {}).get('dealstage') == 'closedwon'
            )
            
            # Group by month
            monthly_revenue = {}
            for deal in deals:
                if deal.get('properties', {}).get('dealstage') == 'closedwon':
                    close_date = deal.get('properties', {}).get('closedate')
                    if close_date:
                        month_key = datetime.fromtimestamp(
                            int(close_date) / 1000
                        ).strftime('%Y-%m')
                        amount = float(deal.get('properties', {}).get('amount', 0) or 0)
                        monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + amount
        
        # Calculate growth metrics
        months = sorted(monthly_revenue.keys())
        growth_rate = 0
        if len(months) >= 2:
            current_month = monthly_revenue.get(months[-1], 0)
            previous_month = monthly_revenue.get(months[-2], 0)
            if previous_month > 0:
                growth_rate = ((current_month - previous_month) / previous_month) * 100
        
        return jsonify({
            'period': {
                'from': from_date.isoformat(),
                'to': to_date.isoformat(),
                'days': days
            },
            'total_revenue': total_revenue,
            'monthly_breakdown': monthly_revenue,
            'growth_rate': growth_rate,
            'deals_closed': len([d for d in deals if d.get('properties', {}).get('dealstage') == 'closedwon']),
            'average_deal_size': total_revenue / len(deals) if deals else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Revenue analysis error: {str(e)}")
        return jsonify({'error': 'Failed to analyze revenue'}), 500

@company_bp.route('/customers', methods=['GET'])
@jwt_required()
async def customer_analysis():
    """Get customer analytics and insights"""
    try:
        # Get customer data from HubSpot
        async with hubspot:
            # Get all contacts
            contacts = await hubspot.export_contacts()
            
            # Get recent contacts (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).timestamp() * 1000
            recent_contacts = [
                c for c in contacts
                if int(c.get('properties', {}).get('createdate', 0)) > thirty_days_ago
            ]
            
            # Analyze customer segments
            segments = {
                'lead': 0,
                'marketingqualifiedlead': 0,
                'salesqualifiedlead': 0,
                'opportunity': 0,
                'customer': 0,
                'evangelist': 0
            }
            
            for contact in contacts:
                lifecycle_stage = contact.get('properties', {}).get('lifecyclestage', 'lead')
                if lifecycle_stage in segments:
                    segments[lifecycle_stage] += 1
        
        # Calculate metrics
        total_customers = segments.get('customer', 0) + segments.get('evangelist', 0)
        conversion_rate = (total_customers / len(contacts) * 100) if contacts else 0
        
        return jsonify({
            'total_contacts': len(contacts),
            'total_customers': total_customers,
            'new_contacts_30d': len(recent_contacts),
            'lifecycle_segments': segments,
            'conversion_rate': conversion_rate,
            'analysis_timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Customer analysis error: {str(e)}")
        return jsonify({'error': 'Failed to analyze customers'}), 500

@company_bp.route('/pipeline', methods=['GET'])
@jwt_required()
async def pipeline_analysis():
    """Get sales pipeline analysis"""
    try:
        # Get pipeline data from HubSpot
        async with hubspot:
            pipeline_analytics = await hubspot.get_pipeline_analytics()
        
        # Calculate pipeline velocity
        pipeline_velocity = {
            'average_days_to_close': 0,
            'conversion_rate': pipeline_analytics.get('win_rate', 0) * 100,
            'average_deal_size': pipeline_analytics.get('average_deal_size', 0)
        }
        
        # Calculate stage distribution
        stage_distribution = []
        if pipeline_analytics.get('open_deals_count', 0) > 0:
            # This would be more detailed with actual stage data
            stage_distribution = [
                {
                    'stage': 'Prospecting',
                    'count': int(pipeline_analytics.get('open_deals_count', 0) * 0.3),
                    'value': pipeline_analytics.get('open_deals_value', 0) * 0.2
                },
                {
                    'stage': 'Qualification',
                    'count': int(pipeline_analytics.get('open_deals_count', 0) * 0.25),
                    'value': pipeline_analytics.get('open_deals_value', 0) * 0.25
                },
                {
                    'stage': 'Proposal',
                    'count': int(pipeline_analytics.get('open_deals_count', 0) * 0.25),
                    'value': pipeline_analytics.get('open_deals_value', 0) * 0.3
                },
                {
                    'stage': 'Negotiation',
                    'count': int(pipeline_analytics.get('open_deals_count', 0) * 0.2),
                    'value': pipeline_analytics.get('open_deals_value', 0) * 0.25
                }
            ]
        
        return jsonify({
            'summary': {
                'total_pipeline_value': pipeline_analytics.get('open_deals_value', 0),
                'total_deals': pipeline_analytics.get('open_deals_count', 0),
                'closed_won_value': pipeline_analytics.get('closed_won_value', 0),
                'closed_won_count': pipeline_analytics.get('closed_won_count', 0)
            },
            'velocity': pipeline_velocity,
            'stage_distribution': stage_distribution,
            'win_rate': pipeline_analytics.get('win_rate', 0),
            'analysis_timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Pipeline analysis error: {str(e)}")
        return jsonify({'error': 'Failed to analyze pipeline'}), 500

@company_bp.route('/health-score', methods=['GET'])
@jwt_required()
async def company_health_score():
    """Calculate overall company health score"""
    try:
        # Get various metrics
        metrics = await monitoring.get_current_metrics()
        business_metrics = metrics.get('business', {})
        
        # Calculate health score components
        scores = {
            'revenue_health': 0,
            'customer_health': 0,
            'pipeline_health': 0,
            'operational_health': 0
        }
        
        # Revenue health (based on growth rate)
        growth_rate = business_metrics.get('revenue', {}).get('growth_rate', 0)
        if growth_rate > 20:
            scores['revenue_health'] = 100
        elif growth_rate > 10:
            scores['revenue_health'] = 80
        elif growth_rate > 0:
            scores['revenue_health'] = 60
        else:
            scores['revenue_health'] = 40
        
        # Customer health (based on churn rate)
        churn_rate = business_metrics.get('customers', {}).get('churn_rate', 0)
        if churn_rate < 2:
            scores['customer_health'] = 100
        elif churn_rate < 5:
            scores['customer_health'] = 80
        elif churn_rate < 10:
            scores['customer_health'] = 60
        else:
            scores['customer_health'] = 40
        
        # Pipeline health (based on conversion rate)
        conversion_rate = business_metrics.get('deals', {}).get('conversion_rate', 16)
        if conversion_rate > 25:
            scores['pipeline_health'] = 100
        elif conversion_rate > 15:
            scores['pipeline_health'] = 80
        elif conversion_rate > 10:
            scores['pipeline_health'] = 60
        else:
            scores['pipeline_health'] = 40
        
        # Operational health (based on system metrics)
        system_health = await monitoring.health_check()
        if system_health.get('status') == 'healthy':
            scores['operational_health'] = 100
        else:
            scores['operational_health'] = 70
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine health status
        if overall_score >= 90:
            status = 'Excellent'
        elif overall_score >= 75:
            status = 'Good'
        elif overall_score >= 60:
            status = 'Fair'
        else:
            status = 'Needs Attention'
        
        # Generate recommendations
        recommendations = []
        if scores['revenue_health'] < 80:
            recommendations.append({
                'area': 'Revenue',
                'recommendation': 'Focus on upselling existing customers and accelerating deal velocity'
            })
        if scores['customer_health'] < 80:
            recommendations.append({
                'area': 'Customer Retention',
                'recommendation': 'Implement customer success initiatives to reduce churn'
            })
        if scores['pipeline_health'] < 80:
            recommendations.append({
                'area': 'Sales Pipeline',
                'recommendation': 'Improve lead qualification and sales process efficiency'
            })
        
        return jsonify({
            'overall_score': overall_score,
            'status': status,
            'component_scores': scores,
            'recommendations': recommendations,
            'calculated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health score calculation error: {str(e)}")
        return jsonify({'error': 'Failed to calculate health score'}), 500

@company_bp.route('/alerts', methods=['GET'])
@jwt_required()
async def company_alerts():
    """Get important company alerts and notifications"""
    try:
        # Get recent alerts from monitoring system
        alerts = await monitoring.get_recent_alerts(limit=20)
        
        # Categorize alerts
        categorized_alerts = {
            'urgent': [],
            'warning': [],
            'info': []
        }
        
        for alert in alerts:
            severity = alert.get('severity', 'info')
            if severity == 'critical':
                categorized_alerts['urgent'].append(alert)
            elif severity == 'warning':
                categorized_alerts['warning'].append(alert)
            else:
                categorized_alerts['info'].append(alert)
        
        # Add business-specific alerts
        metrics = await monitoring.get_current_metrics()
        business_metrics = metrics.get('business', {})
        
        # Check for business alerts
        if business_metrics.get('revenue', {}).get('growth_rate', 0) < 0:
            categorized_alerts['warning'].append({
                'type': 'revenue_decline',
                'message': 'Revenue growth is negative this month',
                'timestamp': datetime.now().isoformat()
            })
        
        if business_metrics.get('customers', {}).get('churn_rate', 0) > 10:
            categorized_alerts['urgent'].append({
                'type': 'high_churn',
                'message': 'Customer churn rate exceeds 10%',
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'alerts': categorized_alerts,
            'total_alerts': len(alerts),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Company alerts error: {str(e)}")
        return jsonify({'error': 'Failed to get company alerts'}), 500

@company_bp.route('/insights', methods=['POST'])
@jwt_required()
async def generate_insights():
    """Generate AI-powered business insights"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'general')
        
        # Submit task to orchestrator
        task_id = await orchestrator.submit_task(
            task_type='generate_insights',
            task_data={
                'topic': topic,
                'company': settings.company_name,
                'requester': get_jwt_identity()
            },
            priority=3
        )
        
        # For now, return task ID - in production, this would wait for results
        return jsonify({
            'task_id': task_id,
            'status': 'processing',
            'message': f'Generating insights for topic: {topic}'
        }), 202
        
    except Exception as e:
        logger.error(f"Insights generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate insights'}), 500

# Error handlers
@company_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Company endpoint not found'}), 404

@company_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

