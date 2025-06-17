"""
Real-Time Business Intelligence Engine for Pay Ready
Advanced analytics and metrics processing for B2B operations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of business metrics"""
    REVENUE = "revenue"
    CLIENT_HEALTH = "client_health"
    SALES_PERFORMANCE = "sales_performance"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    MARKET_INTELLIGENCE = "market_intelligence"
    COMPLIANCE_STATUS = "compliance_status"
    INFRASTRUCTURE_PERFORMANCE = "infrastructure_performance"


class TimeGranularity(Enum):
    """Time granularity for metrics"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class BusinessMetric:
    """Represents a business metric"""
    metric_id: str
    metric_type: MetricType
    name: str
    value: Union[float, int, str]
    unit: str
    timestamp: datetime
    granularity: TimeGranularity
    metadata: Dict[str, Any]
    trend: Optional[str] = None
    target: Optional[Union[float, int]] = None
    variance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'metric_type': self.metric_type.value,
            'granularity': self.granularity.value,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BusinessInsight:
    """Represents a business insight"""
    insight_id: str
    title: str
    description: str
    impact_level: str  # high, medium, low
    category: str
    metrics_involved: List[str]
    recommendations: List[str]
    confidence_score: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class RealTimeBusinessIntelligence:
    """
    Real-time business intelligence engine for Pay Ready
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_engine = create_engine(config['database_url'])
        self.Session = sessionmaker(bind=self.db_engine)
        
        # Redis for real-time caching
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            decode_responses=True
        )
        
        # Metric cache
        self.metric_cache = {}
        self.insight_cache = {}
        
        # Performance tracking
        self.last_update = datetime.utcnow()
        self.update_frequency = timedelta(minutes=5)  # Update every 5 minutes
        
        logger.info("Real-Time Business Intelligence Engine initialized")
    
    async def get_business_dashboard(self, time_period: str = "30_days") -> Dict[str, Any]:
        """Get comprehensive business dashboard data"""
        dashboard_data = {
            'revenue_metrics': await self._get_revenue_metrics(time_period),
            'client_metrics': await self._get_client_metrics(time_period),
            'sales_metrics': await self._get_sales_metrics(time_period),
            'operational_metrics': await self._get_operational_metrics(time_period),
            'infrastructure_metrics': await self._get_infrastructure_metrics(),
            'key_insights': await self._get_key_insights(time_period),
            'alerts': await self._get_active_alerts(),
            'trends': await self._get_trend_analysis(time_period),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return dashboard_data
    
    async def _get_revenue_metrics(self, time_period: str) -> Dict[str, Any]:
        """Get revenue-related metrics"""
        session = self.Session()
        
        try:
            # Calculate time range
            end_date = datetime.utcnow()
            if time_period == "30_days":
                start_date = end_date - timedelta(days=30)
            elif time_period == "90_days":
                start_date = end_date - timedelta(days=90)
            elif time_period == "1_year":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Revenue query
            revenue_query = text("""
                SELECT 
                    DATE(payment_date) as date,
                    SUM(amount) as daily_revenue,
                    COUNT(DISTINCT client_id) as paying_clients,
                    AVG(amount) as avg_payment_size
                FROM payments 
                WHERE payment_date >= :start_date 
                AND payment_date <= :end_date
                AND status = 'completed'
                GROUP BY DATE(payment_date)
                ORDER BY date
            """)
            
            revenue_df = pd.read_sql(
                revenue_query, 
                session.bind, 
                params={'start_date': start_date, 'end_date': end_date}
            )
            
            # Calculate metrics
            total_revenue = revenue_df['daily_revenue'].sum()
            avg_daily_revenue = revenue_df['daily_revenue'].mean()
            revenue_growth = self._calculate_growth_rate(revenue_df['daily_revenue'])
            
            # Monthly recurring revenue (MRR)
            mrr_query = text("""
                SELECT 
                    SUM(monthly_value) as mrr,
                    COUNT(*) as active_subscriptions,
                    AVG(monthly_value) as avg_subscription_value
                FROM subscriptions 
                WHERE status = 'active'
                AND created_date <= :end_date
            """)
            
            mrr_result = session.execute(mrr_query, {'end_date': end_date}).fetchone()
            
            return {
                'total_revenue': float(total_revenue) if total_revenue else 0,
                'avg_daily_revenue': float(avg_daily_revenue) if avg_daily_revenue else 0,
                'revenue_growth_rate': revenue_growth,
                'mrr': float(mrr_result.mrr) if mrr_result.mrr else 0,
                'active_subscriptions': int(mrr_result.active_subscriptions) if mrr_result.active_subscriptions else 0,
                'avg_subscription_value': float(mrr_result.avg_subscription_value) if mrr_result.avg_subscription_value else 0,
                'revenue_trend': revenue_df[['date', 'daily_revenue']].to_dict('records'),
                'target_achievement': self._calculate_target_achievement(total_revenue, time_period)
            }
            
        finally:
            session.close()
    
    async def _get_client_metrics(self, time_period: str) -> Dict[str, Any]:
        """Get client-related metrics"""
        session = self.Session()
        
        try:
            # Client health metrics
            client_query = text("""
                SELECT 
                    COUNT(*) as total_clients,
                    COUNT(CASE WHEN usage_score > 0.7 THEN 1 END) as healthy_clients,
                    COUNT(CASE WHEN usage_score < 0.4 THEN 1 END) as at_risk_clients,
                    COUNT(CASE WHEN last_login >= NOW() - INTERVAL '7 days' THEN 1 END) as active_clients,
                    AVG(usage_score) as avg_usage_score,
                    AVG(satisfaction_score) as avg_satisfaction_score,
                    SUM(monthly_revenue) as total_client_revenue
                FROM client_metrics 
                WHERE active = true
            """)
            
            client_result = session.execute(client_query).fetchone()
            
            # Churn analysis
            churn_query = text("""
                SELECT 
                    COUNT(*) as churned_clients,
                    AVG(DATEDIFF(churn_date, signup_date)) as avg_lifetime_days,
                    SUM(lifetime_value) as churned_revenue
                FROM client_metrics 
                WHERE churn_date >= NOW() - INTERVAL 30 DAY
            """)
            
            churn_result = session.execute(churn_query).fetchone()
            
            # Expansion opportunities
            expansion_query = text("""
                SELECT 
                    COUNT(*) as expansion_ready,
                    SUM(potential_expansion_revenue) as expansion_potential
                FROM client_metrics 
                WHERE usage_score > 0.8 
                AND feature_adoption_rate > 0.9
                AND active = true
            """)
            
            expansion_result = session.execute(expansion_query).fetchone()
            
            return {
                'total_clients': int(client_result.total_clients) if client_result.total_clients else 0,
                'healthy_clients': int(client_result.healthy_clients) if client_result.healthy_clients else 0,
                'at_risk_clients': int(client_result.at_risk_clients) if client_result.at_risk_clients else 0,
                'active_clients': int(client_result.active_clients) if client_result.active_clients else 0,
                'avg_usage_score': float(client_result.avg_usage_score) if client_result.avg_usage_score else 0,
                'avg_satisfaction_score': float(client_result.avg_satisfaction_score) if client_result.avg_satisfaction_score else 0,
                'total_client_revenue': float(client_result.total_client_revenue) if client_result.total_client_revenue else 0,
                'churned_clients_30d': int(churn_result.churned_clients) if churn_result.churned_clients else 0,
                'avg_client_lifetime_days': float(churn_result.avg_lifetime_days) if churn_result.avg_lifetime_days else 0,
                'expansion_ready_clients': int(expansion_result.expansion_ready) if expansion_result.expansion_ready else 0,
                'expansion_potential_revenue': float(expansion_result.expansion_potential) if expansion_result.expansion_potential else 0,
                'client_health_score': self._calculate_client_health_score(client_result),
                'churn_rate': self._calculate_churn_rate(client_result, churn_result)
            }
            
        finally:
            session.close()
    
    async def _get_sales_metrics(self, time_period: str) -> Dict[str, Any]:
        """Get sales performance metrics"""
        session = self.Session()
        
        try:
            # Sales pipeline metrics
            pipeline_query = text("""
                SELECT 
                    COUNT(*) as total_opportunities,
                    SUM(value) as total_pipeline_value,
                    COUNT(CASE WHEN stage = 'closed_won' THEN 1 END) as won_deals,
                    COUNT(CASE WHEN stage = 'closed_lost' THEN 1 END) as lost_deals,
                    AVG(value) as avg_deal_size,
                    AVG(days_in_pipeline) as avg_sales_cycle,
                    SUM(CASE WHEN stage = 'closed_won' THEN value ELSE 0 END) as won_revenue
                FROM opportunities 
                WHERE created_date >= NOW() - INTERVAL 90 DAY
            """)
            
            pipeline_result = session.execute(pipeline_query).fetchone()
            
            # Sales rep performance
            rep_query = text("""
                SELECT 
                    sales_rep_id,
                    sales_rep_name,
                    COUNT(o.id) as total_deals,
                    COUNT(CASE WHEN o.stage = 'closed_won' THEN 1 END) as won_deals,
                    SUM(CASE WHEN o.stage = 'closed_won' THEN o.value ELSE 0 END) as revenue,
                    AVG(o.demo_score) as avg_demo_score
                FROM sales_reps sr
                LEFT JOIN opportunities o ON sr.sales_rep_id = o.assigned_rep
                WHERE o.created_date >= NOW() - INTERVAL 90 DAY
                GROUP BY sales_rep_id, sales_rep_name
                ORDER BY revenue DESC
            """)
            
            rep_df = pd.read_sql(rep_query, session.bind)
            
            # Calculate metrics
            close_rate = (
                pipeline_result.won_deals / (pipeline_result.won_deals + pipeline_result.lost_deals)
                if (pipeline_result.won_deals + pipeline_result.lost_deals) > 0 else 0
            )
            
            return {
                'total_opportunities': int(pipeline_result.total_opportunities) if pipeline_result.total_opportunities else 0,
                'total_pipeline_value': float(pipeline_result.total_pipeline_value) if pipeline_result.total_pipeline_value else 0,
                'won_deals': int(pipeline_result.won_deals) if pipeline_result.won_deals else 0,
                'lost_deals': int(pipeline_result.lost_deals) if pipeline_result.lost_deals else 0,
                'close_rate': float(close_rate),
                'avg_deal_size': float(pipeline_result.avg_deal_size) if pipeline_result.avg_deal_size else 0,
                'avg_sales_cycle_days': float(pipeline_result.avg_sales_cycle) if pipeline_result.avg_sales_cycle else 0,
                'won_revenue': float(pipeline_result.won_revenue) if pipeline_result.won_revenue else 0,
                'sales_rep_performance': rep_df.to_dict('records'),
                'top_performer': rep_df.iloc[0].to_dict() if len(rep_df) > 0 else None,
                'pipeline_velocity': self._calculate_pipeline_velocity(pipeline_result)
            }
            
        finally:
            session.close()
    
    async def _get_operational_metrics(self, time_period: str) -> Dict[str, Any]:
        """Get operational efficiency metrics"""
        session = self.Session()
        
        try:
            # Support metrics
            support_query = text("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
                    AVG(resolution_time_hours) as avg_resolution_time,
                    AVG(satisfaction_rating) as avg_satisfaction_rating
                FROM support_tickets 
                WHERE created_date >= NOW() - INTERVAL 30 DAY
            """)
            
            support_result = session.execute(support_query).fetchone()
            
            # System performance metrics
            system_query = text("""
                SELECT 
                    AVG(response_time_ms) as avg_response_time,
                    (COUNT(CASE WHEN status_code = 200 THEN 1 END) * 100.0 / COUNT(*)) as uptime_percentage,
                    COUNT(*) as total_requests
                FROM system_logs 
                WHERE timestamp >= NOW() - INTERVAL 24 HOUR
            """)
            
            system_result = session.execute(system_query).fetchone()
            
            return {
                'total_support_tickets': int(support_result.total_tickets) if support_result.total_tickets else 0,
                'resolved_tickets': int(support_result.resolved_tickets) if support_result.resolved_tickets else 0,
                'ticket_resolution_rate': (
                    support_result.resolved_tickets / support_result.total_tickets
                    if support_result.total_tickets > 0 else 0
                ),
                'avg_resolution_time_hours': float(support_result.avg_resolution_time) if support_result.avg_resolution_time else 0,
                'support_satisfaction': float(support_result.avg_satisfaction_rating) if support_result.avg_satisfaction_rating else 0,
                'system_uptime_percentage': float(system_result.uptime_percentage) if system_result.uptime_percentage else 0,
                'avg_response_time_ms': float(system_result.avg_response_time) if system_result.avg_response_time else 0,
                'total_api_requests': int(system_result.total_requests) if system_result.total_requests else 0
            }
            
        finally:
            session.close()
    
    async def _get_infrastructure_metrics(self) -> Dict[str, Any]:
        """Get infrastructure performance metrics"""
        # This would integrate with Lambda Labs API and monitoring systems
        # For now, return simulated real-time data
        return {
            'lambda_labs_instances': {
                'active_instances': 2,
                'total_cost_per_hour': 4.80,
                'gpu_utilization': 78.5,
                'cpu_utilization': 65.2,
                'memory_utilization': 82.1
            },
            'database_performance': {
                'postgresql_connections': 45,
                'postgresql_max_connections': 100,
                'redis_memory_usage': 1.2,
                'redis_max_memory': 4.0,
                'query_performance_ms': 23.4
            },
            'api_gateway_metrics': {
                'requests_per_minute': 1247,
                'success_rate': 99.2,
                'avg_latency_ms': 156,
                'cache_hit_rate': 94.2
            }
        }
    
    async def _get_key_insights(self, time_period: str) -> List[BusinessInsight]:
        """Generate key business insights"""
        insights = []
        
        # Revenue insights
        revenue_metrics = await self._get_revenue_metrics(time_period)
        if revenue_metrics['revenue_growth_rate'] > 0.2:
            insights.append(BusinessInsight(
                insight_id="revenue_growth_strong",
                title="Strong Revenue Growth",
                description=f"Revenue is growing at {revenue_metrics['revenue_growth_rate']:.1%}, significantly above industry average",
                impact_level="high",
                category="revenue",
                metrics_involved=["total_revenue", "revenue_growth_rate"],
                recommendations=[
                    "Scale successful client acquisition strategies",
                    "Invest in customer success to maintain growth",
                    "Consider expanding to adjacent markets"
                ],
                confidence_score=0.9,
                timestamp=datetime.utcnow()
            ))
        
        # Client health insights
        client_metrics = await self._get_client_metrics(time_period)
        if client_metrics['at_risk_clients'] > 5:
            insights.append(BusinessInsight(
                insight_id="client_churn_risk",
                title="Client Churn Risk Detected",
                description=f"{client_metrics['at_risk_clients']} clients are at high risk of churning",
                impact_level="high",
                category="client_health",
                metrics_involved=["at_risk_clients", "avg_usage_score"],
                recommendations=[
                    "Implement immediate client success interventions",
                    "Analyze common patterns among at-risk clients",
                    "Develop retention campaigns"
                ],
                confidence_score=0.85,
                timestamp=datetime.utcnow()
            ))
        
        # Sales insights
        sales_metrics = await self._get_sales_metrics(time_period)
        if sales_metrics['close_rate'] > 0.3:
            insights.append(BusinessInsight(
                insight_id="sales_performance_strong",
                title="Excellent Sales Performance",
                description=f"Close rate of {sales_metrics['close_rate']:.1%} exceeds industry benchmarks",
                impact_level="medium",
                category="sales",
                metrics_involved=["close_rate", "avg_deal_size"],
                recommendations=[
                    "Document successful sales processes",
                    "Scale winning strategies across team",
                    "Increase sales team capacity"
                ],
                confidence_score=0.8,
                timestamp=datetime.utcnow()
            ))
        
        return insights
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system and business alerts"""
        alerts = []
        
        # Check for critical metrics
        client_metrics = await self._get_client_metrics("30_days")
        
        if client_metrics['churn_rate'] > 0.05:  # 5% monthly churn
            alerts.append({
                'id': 'high_churn_rate',
                'severity': 'high',
                'title': 'High Churn Rate Alert',
                'message': f"Monthly churn rate is {client_metrics['churn_rate']:.1%}, above acceptable threshold",
                'timestamp': datetime.utcnow().isoformat(),
                'category': 'client_health'
            })
        
        if client_metrics['avg_usage_score'] < 0.6:
            alerts.append({
                'id': 'low_usage_score',
                'severity': 'medium',
                'title': 'Low Client Engagement',
                'message': f"Average usage score is {client_metrics['avg_usage_score']:.2f}, indicating low engagement",
                'timestamp': datetime.utcnow().isoformat(),
                'category': 'client_health'
            })
        
        return alerts
    
    async def _get_trend_analysis(self, time_period: str) -> Dict[str, Any]:
        """Analyze trends across key metrics"""
        session = self.Session()
        
        try:
            # Revenue trend
            revenue_trend_query = text("""
                SELECT 
                    DATE(payment_date) as date,
                    SUM(amount) as daily_revenue
                FROM payments 
                WHERE payment_date >= NOW() - INTERVAL 90 DAY
                AND status = 'completed'
                GROUP BY DATE(payment_date)
                ORDER BY date
            """)
            
            revenue_trend_df = pd.read_sql(revenue_trend_query, session.bind)
            
            # Client acquisition trend
            client_trend_query = text("""
                SELECT 
                    DATE(signup_date) as date,
                    COUNT(*) as new_clients
                FROM client_metrics 
                WHERE signup_date >= NOW() - INTERVAL 90 DAY
                GROUP BY DATE(signup_date)
                ORDER BY date
            """)
            
            client_trend_df = pd.read_sql(client_trend_query, session.bind)
            
            return {
                'revenue_trend': {
                    'data': revenue_trend_df.to_dict('records'),
                    'direction': self._calculate_trend_direction(revenue_trend_df['daily_revenue']),
                    'volatility': self._calculate_volatility(revenue_trend_df['daily_revenue'])
                },
                'client_acquisition_trend': {
                    'data': client_trend_df.to_dict('records'),
                    'direction': self._calculate_trend_direction(client_trend_df['new_clients']),
                    'volatility': self._calculate_volatility(client_trend_df['new_clients'])
                }
            }
            
        finally:
            session.close()
    
    def _calculate_growth_rate(self, values: pd.Series) -> float:
        """Calculate growth rate from a series of values"""
        if len(values) < 2:
            return 0.0
        
        first_half = values[:len(values)//2].mean()
        second_half = values[len(values)//2:].mean()
        
        if first_half == 0:
            return 0.0
        
        return (second_half - first_half) / first_half
    
    def _calculate_target_achievement(self, actual_value: float, time_period: str) -> float:
        """Calculate target achievement percentage"""
        # Define targets based on time period
        targets = {
            "30_days": 500000,  # $500K monthly target
            "90_days": 1500000,  # $1.5M quarterly target
            "1_year": 6000000   # $6M annual target
        }
        
        target = targets.get(time_period, 500000)
        return actual_value / target if target > 0 else 0
    
    def _calculate_client_health_score(self, client_result) -> float:
        """Calculate overall client health score"""
        if not client_result.total_clients:
            return 0.0
        
        healthy_ratio = client_result.healthy_clients / client_result.total_clients
        usage_score = client_result.avg_usage_score or 0
        satisfaction_score = client_result.avg_satisfaction_score or 0
        
        return (healthy_ratio * 0.4 + usage_score * 0.3 + satisfaction_score * 0.3)
    
    def _calculate_churn_rate(self, client_result, churn_result) -> float:
        """Calculate monthly churn rate"""
        if not client_result.total_clients:
            return 0.0
        
        return (churn_result.churned_clients or 0) / client_result.total_clients
    
    def _calculate_pipeline_velocity(self, pipeline_result) -> float:
        """Calculate sales pipeline velocity"""
        if not pipeline_result.avg_sales_cycle:
            return 0.0
        
        avg_deal_size = pipeline_result.avg_deal_size or 0
        close_rate = (
            pipeline_result.won_deals / (pipeline_result.won_deals + pipeline_result.lost_deals)
            if (pipeline_result.won_deals + pipeline_result.lost_deals) > 0 else 0
        )
        
        return (avg_deal_size * close_rate) / pipeline_result.avg_sales_cycle
    
    def _calculate_trend_direction(self, values: pd.Series) -> str:
        """Calculate trend direction (up, down, stable)"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.05:
            return "up"
        elif slope < -0.05:
            return "down"
        else:
            return "stable"
    
    def _calculate_volatility(self, values: pd.Series) -> float:
        """Calculate volatility (coefficient of variation)"""
        if len(values) < 2 or values.mean() == 0:
            return 0.0
        
        return values.std() / values.mean()
    
    async def generate_executive_report(self, time_period: str = "30_days") -> Dict[str, Any]:
        """Generate executive summary report"""
        dashboard_data = await self.get_business_dashboard(time_period)
        
        executive_summary = {
            'period': time_period,
            'generated_at': datetime.utcnow().isoformat(),
            'key_metrics': {
                'total_revenue': dashboard_data['revenue_metrics']['total_revenue'],
                'revenue_growth': dashboard_data['revenue_metrics']['revenue_growth_rate'],
                'total_clients': dashboard_data['client_metrics']['total_clients'],
                'client_health_score': dashboard_data['client_metrics']['client_health_score'],
                'sales_close_rate': dashboard_data['sales_metrics']['close_rate'],
                'system_uptime': dashboard_data['operational_metrics']['system_uptime_percentage']
            },
            'highlights': [
                f"Revenue: ${dashboard_data['revenue_metrics']['total_revenue']:,.0f}",
                f"Growth: {dashboard_data['revenue_metrics']['revenue_growth_rate']:.1%}",
                f"Clients: {dashboard_data['client_metrics']['total_clients']}",
                f"Close Rate: {dashboard_data['sales_metrics']['close_rate']:.1%}"
            ],
            'top_insights': dashboard_data['key_insights'][:3],
            'critical_alerts': [alert for alert in dashboard_data['alerts'] if alert['severity'] == 'high'],
            'recommendations': self._generate_executive_recommendations(dashboard_data)
        }
        
        return executive_summary
    
    def _generate_executive_recommendations(self, dashboard_data: Dict[str, Any]) -> List[str]:
        """Generate executive-level recommendations"""
        recommendations = []
        
        revenue_growth = dashboard_data['revenue_metrics']['revenue_growth_rate']
        if revenue_growth > 0.2:
            recommendations.append("Scale successful growth strategies and consider market expansion")
        elif revenue_growth < 0.05:
            recommendations.append("Focus on revenue optimization and client retention initiatives")
        
        churn_rate = dashboard_data['client_metrics']['churn_rate']
        if churn_rate > 0.05:
            recommendations.append("Implement immediate churn reduction strategies and client success programs")
        
        close_rate = dashboard_data['sales_metrics']['close_rate']
        if close_rate > 0.3:
            recommendations.append("Invest in sales team expansion to capitalize on strong performance")
        elif close_rate < 0.15:
            recommendations.append("Review and optimize sales processes and training programs")
        
        return recommendations

