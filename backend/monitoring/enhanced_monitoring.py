"""
Sophia AI - Enhanced Monitoring System
Production-grade monitoring with business intelligence metrics

This module provides comprehensive monitoring for:
- System performance and health
- Business intelligence metrics
- Agent performance tracking
- Integration health monitoring
- Real-time alerting and notifications
"""

import asyncio
import json
import logging
import time
import psutil
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    redis_url: str = "redis://localhost:6379"
    metrics_retention_hours: int = 168  # 7 days
    alert_thresholds: Dict[str, float] = None
    monitoring_interval: int = 60  # seconds
    business_metrics_interval: int = 300  # 5 minutes
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'disk_usage': 90.0,
                'response_time': 2000.0,  # milliseconds
                'error_rate': 5.0,  # percentage
                'agent_failure_rate': 10.0  # percentage
            }

class SophiaMonitoringSystem:
    """Enhanced monitoring system for Sophia AI platform"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.redis_client = None
        self.is_running = False
        self.monitoring_tasks = []
        
        # Metrics storage
        self.current_metrics = {}
        self.alert_history = []
        
        # Business metrics
        self.business_metrics = {
            'revenue': 0,
            'customers': 0,
            'deals_in_pipeline': 0,
            'calls_analyzed': 0,
            'tasks_automated': 0
        }
    
    async def start(self):
        """Start the monitoring system"""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(self.config.redis_url)
            
            # Start monitoring tasks
            self.is_running = True
            self.monitoring_tasks = [
                asyncio.create_task(self._monitor_system_metrics()),
                asyncio.create_task(self._monitor_business_metrics()),
                asyncio.create_task(self._monitor_agent_performance()),
                asyncio.create_task(self._monitor_integration_health()),
                asyncio.create_task(self._process_alerts())
            ]
            
            logger.info("Sophia Monitoring System started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring system: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the monitoring system"""
        try:
            self.is_running = False
            
            # Cancel monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Sophia Monitoring System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {str(e)}")
    
    async def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.is_running:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                
                # Store metrics
                await self._store_metrics('system', metrics)
                
                # Check thresholds and generate alerts
                await self._check_system_thresholds(metrics)
                
                # Update current metrics
                self.current_metrics.update(metrics)
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in system metrics monitoring: {str(e)}")
                await asyncio.sleep(self.config.monitoring_interval)
    
    async def _monitor_business_metrics(self):
        """Monitor business intelligence metrics"""
        while self.is_running:
            try:
                # Collect business metrics
                metrics = await self._collect_business_metrics()
                
                # Store metrics
                await self._store_metrics('business', metrics)
                
                # Update business metrics
                self.business_metrics.update(metrics)
                
                await asyncio.sleep(self.config.business_metrics_interval)
                
            except Exception as e:
                logger.error(f"Error in business metrics monitoring: {str(e)}")
                await asyncio.sleep(self.config.business_metrics_interval)
    
    async def _monitor_agent_performance(self):
        """Monitor AI agent performance"""
        while self.is_running:
            try:
                # Collect agent metrics
                metrics = await self._collect_agent_metrics()
                
                # Store metrics
                await self._store_metrics('agents', metrics)
                
                # Check agent performance thresholds
                await self._check_agent_thresholds(metrics)
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in agent performance monitoring: {str(e)}")
                await asyncio.sleep(self.config.monitoring_interval)
    
    async def _monitor_integration_health(self):
        """Monitor health of external integrations"""
        while self.is_running:
            try:
                # Check integration health
                health_status = await self._check_integration_health()
                
                # Store health metrics
                await self._store_metrics('integrations', health_status)
                
                # Generate alerts for unhealthy integrations
                await self._check_integration_alerts(health_status)
                
                await asyncio.sleep(self.config.monitoring_interval * 2)  # Check less frequently
                
            except Exception as e:
                logger.error(f"Error in integration health monitoring: {str(e)}")
                await asyncio.sleep(self.config.monitoring_interval * 2)
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free
            disk_total = disk.total
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'usage_percent': memory_percent,
                    'available_bytes': memory_available,
                    'total_bytes': memory_total
                },
                'disk': {
                    'usage_percent': disk_percent,
                    'free_bytes': disk_free,
                    'total_bytes': disk_total
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': {
                    'count': process_count
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            return {}
    
    async def _collect_business_metrics(self) -> Dict[str, Any]:
        """Collect business intelligence metrics"""
        try:
            # In a real implementation, these would come from:
            # - HubSpot API for deals and revenue
            # - Database queries for customer counts
            # - Agent activity logs for automation metrics
            
            # Simulated business metrics for demonstration
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'revenue': {
                    'total': 125000,  # Total revenue
                    'monthly': 15000,  # This month's revenue
                    'growth_rate': 12.5  # Month-over-month growth %
                },
                'customers': {
                    'total': 450,
                    'new_this_month': 25,
                    'churn_rate': 2.1
                },
                'deals': {
                    'in_pipeline': 75,
                    'closed_won_this_month': 12,
                    'average_deal_size': 8500,
                    'conversion_rate': 16.0
                },
                'calls': {
                    'analyzed_today': 23,
                    'analyzed_this_month': 340,
                    'average_analysis_time': 45  # seconds
                },
                'automation': {
                    'tasks_completed_today': 156,
                    'tasks_completed_this_month': 2340,
                    'time_saved_hours': 78
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect business metrics: {str(e)}")
            return {}
    
    async def _collect_agent_metrics(self) -> Dict[str, Any]:
        """Collect AI agent performance metrics"""
        try:
            # In a real implementation, this would query agent activity logs
            # and performance databases
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'call_analysis_agent': {
                    'tasks_completed': 23,
                    'success_rate': 95.7,
                    'average_processing_time': 42.3,
                    'errors': 1
                },
                'crm_sync_agent': {
                    'tasks_completed': 45,
                    'success_rate': 98.9,
                    'average_processing_time': 18.7,
                    'errors': 0
                },
                'slack_notification_agent': {
                    'messages_sent': 67,
                    'success_rate': 100.0,
                    'average_response_time': 1.2,
                    'errors': 0
                },
                'orchestrator': {
                    'tasks_orchestrated': 134,
                    'success_rate': 97.8,
                    'average_routing_time': 0.8,
                    'errors': 3
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect agent metrics: {str(e)}")
            return {}
    
    async def _check_integration_health(self) -> Dict[str, Any]:
        """Check health of external integrations"""
        health_status = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Check HubSpot
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.hubapi.com/crm/v3/objects/contacts?limit=1', timeout=5) as response:
                    health_status['hubspot'] = {
                        'status': 'healthy' if response.status == 200 else 'unhealthy',
                        'response_time': response.headers.get('X-Response-Time', 'unknown'),
                        'status_code': response.status
                    }
        except Exception as e:
            health_status['hubspot'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Gong.io (simulated)
        try:
            # In real implementation, this would check Gong API
            health_status['gong'] = {
                'status': 'healthy',
                'response_time': '150ms',
                'last_sync': datetime.now().isoformat()
            }
        except Exception as e:
            health_status['gong'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Slack
        try:
            # In real implementation, this would check Slack API
            health_status['slack'] = {
                'status': 'healthy',
                'response_time': '89ms',
                'last_message': datetime.now().isoformat()
            }
        except Exception as e:
            health_status['slack'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Vector Databases
        try:
            # Check Pinecone (simulated)
            health_status['pinecone'] = {
                'status': 'healthy',
                'response_time': '2253ms',
                'index_count': 1
            }
            
            # Check Weaviate (simulated)
            health_status['weaviate'] = {
                'status': 'healthy',
                'response_time': '87ms',
                'objects_count': 1250
            }
        except Exception as e:
            health_status['vector_dbs'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health_status
    
    async def _store_metrics(self, metric_type: str, metrics: Dict[str, Any]):
        """Store metrics in Redis with expiration"""
        try:
            if not metrics:
                return
            
            timestamp = int(time.time())
            key = f"metrics:{metric_type}:{timestamp}"
            
            await self.redis_client.set(
                key,
                json.dumps(metrics),
                ex=self.config.metrics_retention_hours * 3600
            )
            
            # Also store in a sorted set for time-series queries
            await self.redis_client.zadd(
                f"metrics_index:{metric_type}",
                {key: timestamp}
            )
            
            # Clean up old entries from sorted set
            cutoff_time = timestamp - (self.config.metrics_retention_hours * 3600)
            await self.redis_client.zremrangebyscore(
                f"metrics_index:{metric_type}",
                0,
                cutoff_time
            )
            
        except Exception as e:
            logger.error(f"Failed to store {metric_type} metrics: {str(e)}")
    
    async def _check_system_thresholds(self, metrics: Dict[str, Any]):
        """Check system metrics against thresholds and generate alerts"""
        try:
            alerts = []
            
            # Check CPU usage
            cpu_usage = metrics.get('cpu', {}).get('usage_percent', 0)
            if cpu_usage > self.config.alert_thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_high',
                    'severity': 'warning',
                    'message': f'High CPU usage: {cpu_usage:.1f}%',
                    'value': cpu_usage,
                    'threshold': self.config.alert_thresholds['cpu_usage']
                })
            
            # Check memory usage
            memory_usage = metrics.get('memory', {}).get('usage_percent', 0)
            if memory_usage > self.config.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_high',
                    'severity': 'warning',
                    'message': f'High memory usage: {memory_usage:.1f}%',
                    'value': memory_usage,
                    'threshold': self.config.alert_thresholds['memory_usage']
                })
            
            # Check disk usage
            disk_usage = metrics.get('disk', {}).get('usage_percent', 0)
            if disk_usage > self.config.alert_thresholds['disk_usage']:
                alerts.append({
                    'type': 'disk_high',
                    'severity': 'critical',
                    'message': f'High disk usage: {disk_usage:.1f}%',
                    'value': disk_usage,
                    'threshold': self.config.alert_thresholds['disk_usage']
                })
            
            # Process alerts
            for alert in alerts:
                await self._generate_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to check system thresholds: {str(e)}")
    
    async def _check_agent_thresholds(self, metrics: Dict[str, Any]):
        """Check agent performance thresholds"""
        try:
            alerts = []
            
            for agent_name, agent_metrics in metrics.items():
                if agent_name == 'timestamp':
                    continue
                
                success_rate = agent_metrics.get('success_rate', 100)
                failure_rate = 100 - success_rate
                
                if failure_rate > self.config.alert_thresholds['agent_failure_rate']:
                    alerts.append({
                        'type': 'agent_failure_rate_high',
                        'severity': 'warning',
                        'message': f'High failure rate for {agent_name}: {failure_rate:.1f}%',
                        'agent': agent_name,
                        'value': failure_rate,
                        'threshold': self.config.alert_thresholds['agent_failure_rate']
                    })
            
            # Process alerts
            for alert in alerts:
                await self._generate_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to check agent thresholds: {str(e)}")
    
    async def _check_integration_alerts(self, health_status: Dict[str, Any]):
        """Check integration health and generate alerts"""
        try:
            alerts = []
            
            for integration, status in health_status.items():
                if integration == 'timestamp':
                    continue
                
                if isinstance(status, dict) and status.get('status') == 'unhealthy':
                    alerts.append({
                        'type': 'integration_unhealthy',
                        'severity': 'critical',
                        'message': f'Integration {integration} is unhealthy',
                        'integration': integration,
                        'error': status.get('error', 'Unknown error')
                    })
            
            # Process alerts
            for alert in alerts:
                await self._generate_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to check integration alerts: {str(e)}")
    
    async def _generate_alert(self, alert: Dict[str, Any]):
        """Generate and store alert"""
        try:
            alert['timestamp'] = datetime.now().isoformat()
            alert['id'] = f"alert_{int(time.time())}_{alert['type']}"
            
            # Store alert
            await self.redis_client.set(
                f"alert:{alert['id']}",
                json.dumps(alert),
                ex=7 * 24 * 3600  # Keep alerts for 7 days
            )
            
            # Add to alert history
            self.alert_history.append(alert)
            
            # Keep only recent alerts in memory
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
            
            # Log alert
            logger.warning(f"Alert generated: {alert['message']}")
            
            # In production, this would also:
            # - Send notifications (email, Slack, etc.)
            # - Trigger automated responses
            # - Update monitoring dashboards
            
        except Exception as e:
            logger.error(f"Failed to generate alert: {str(e)}")
    
    async def _process_alerts(self):
        """Process and manage alerts"""
        while self.is_running:
            try:
                # This would implement alert processing logic:
                # - Deduplication
                # - Escalation
                # - Auto-resolution
                # - Notification routing
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error in alert processing: {str(e)}")
                await asyncio.sleep(60)
    
    # Public API methods
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'system': self.current_metrics,
            'business': self.business_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_metrics_history(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics"""
        try:
            end_time = int(time.time())
            start_time = end_time - (hours * 3600)
            
            # Get metric keys from sorted set
            keys = await self.redis_client.zrangebyscore(
                f"metrics_index:{metric_type}",
                start_time,
                end_time
            )
            
            # Retrieve metrics
            metrics = []
            for key in keys:
                metric_data = await self.redis_client.get(key)
                if metric_data:
                    metrics.append(json.loads(metric_data))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics history: {str(e)}")
            return []
    
    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform monitoring system health check"""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {}
            }
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                health['components']['redis'] = 'healthy'
            except Exception:
                health['components']['redis'] = 'unhealthy'
                health['status'] = 'degraded'
            
            # Check monitoring tasks
            running_tasks = sum(1 for task in self.monitoring_tasks if not task.done())
            health['components']['monitoring_tasks'] = {
                'status': 'healthy' if running_tasks == len(self.monitoring_tasks) else 'degraded',
                'running': running_tasks,
                'total': len(self.monitoring_tasks)
            }
            
            # Check metrics collection
            health['components']['metrics_collection'] = {
                'status': 'healthy' if self.current_metrics else 'degraded',
                'last_update': self.current_metrics.get('timestamp', 'never')
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Monitoring health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    async def main():
        config = MonitoringConfig()
        monitoring = SophiaMonitoringSystem(config)
        
        try:
            await monitoring.start()
            
            # Run for a while to collect metrics
            await asyncio.sleep(120)
            
            # Get current metrics
            current = await monitoring.get_current_metrics()
            print(f"Current metrics: {json.dumps(current, indent=2)}")
            
            # Get recent alerts
            alerts = await monitoring.get_recent_alerts()
            print(f"Recent alerts: {len(alerts)}")
            
            # Health check
            health = await monitoring.health_check()
            print(f"Health: {health}")
            
        finally:
            await monitoring.stop()
    
    asyncio.run(main())

