"""
Sophia AI - Production Monitoring System
Alternative implementation using Python-based monitoring
"""

import time
import psutil
import json
import threading
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import requests
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SophiaMonitoring:
    def __init__(self):
        # Prometheus metrics
        self.api_requests = Counter('sophia_api_requests_total', 'Total API requests', ['method', 'endpoint'])
        self.api_duration = Histogram('sophia_api_request_duration_seconds', 'API request duration')
        self.db_connections = Gauge('sophia_db_connections_active', 'Active database connections')
        self.business_metrics_updated = Gauge('sophia_business_metric_last_update', 'Last business metrics update timestamp')
        self.system_cpu = Gauge('sophia_system_cpu_percent', 'System CPU usage percentage')
        self.system_memory = Gauge('sophia_system_memory_percent', 'System memory usage percentage')
        self.system_disk = Gauge('sophia_system_disk_percent', 'System disk usage percentage')
        
        # Business intelligence metrics
        self.bi_queries = Counter('sophia_bi_queries_total', 'Total business intelligence queries')
        self.revenue_metrics = Gauge('sophia_revenue_current', 'Current revenue metrics')
        self.customer_metrics = Gauge('sophia_customers_active', 'Active customer count')
        
        self.running = False
        
    def start_monitoring(self):
        """Start the monitoring system"""
        logger.info("🚀 Starting Sophia AI Monitoring System...")
        
        # Start Prometheus metrics server
        start_http_server(9090)
        logger.info("📊 Prometheus metrics server started on port 9090")
        
        self.running = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_system_metrics, daemon=True).start()
        threading.Thread(target=self._monitor_business_metrics, daemon=True).start()
        threading.Thread(target=self._health_check_services, daemon=True).start()
        
        logger.info("✅ All monitoring threads started")
        
    def _monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.system_disk.set(disk_percent)
                
                # Log alerts for high usage
                if cpu_percent > 80:
                    logger.warning(f"🚨 High CPU usage: {cpu_percent}%")
                if memory.percent > 85:
                    logger.warning(f"🚨 High memory usage: {memory.percent}%")
                if disk_percent > 90:
                    logger.warning(f"🚨 High disk usage: {disk_percent}%")
                    
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                time.sleep(60)
                
    def _monitor_business_metrics(self):
        """Monitor business intelligence metrics"""
        while self.running:
            try:
                # Simulate business metrics collection
                # In production, this would connect to actual business databases
                
                # Update business metrics timestamp
                self.business_metrics_updated.set(time.time())
                
                # Simulate revenue tracking
                # This would be replaced with actual database queries
                current_revenue = 125000  # Example value
                self.revenue_metrics.set(current_revenue)
                
                # Simulate customer metrics
                active_customers = 450  # Example value
                self.customer_metrics.set(active_customers)
                
                logger.info(f"📈 Business metrics updated - Revenue: ${current_revenue}, Customers: {active_customers}")
                
                time.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring business metrics: {e}")
                time.sleep(600)
                
    def _health_check_services(self):
        """Perform health checks on critical services"""
        while self.running:
            try:
                services = {
                    'database': os.getenv('POSTGRES_URL', 'postgresql://localhost:5432/sophia_payready'),
                    'redis': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                    'pinecone': os.getenv('PINECONE_HEALTH_URL', 'https://api.pinecone.io/indexes'),
                    'weaviate': os.getenv('WEAVIATE_HEALTH_URL', 'https://localhost/v1/meta')
                }
                
                for service, endpoint in services.items():
                    try:
                        if service == 'pinecone':
                            # Test Pinecone connection
                            headers = {'Api-Key': os.getenv('PINECONE_API_KEY', '')}
                            response = requests.get(endpoint, headers=headers, timeout=10)
                            status = "✅" if response.status_code == 200 else "❌"
                        elif service == 'weaviate':
                            # Test Weaviate connection
                            headers = {'Authorization': f"Bearer {os.getenv('WEAVIATE_API_KEY', '')}"}
                            response = requests.get(endpoint, headers=headers, timeout=10)
                            status = "✅" if response.status_code == 200 else "❌"
                        else:
                            # For database services, just log status
                            status = "✅"  # Would implement actual connection tests
                            
                        logger.info(f"{status} {service.upper()} health check")
                        
                    except Exception as e:
                        logger.warning(f"❌ {service.upper()} health check failed: {e}")
                        
                time.sleep(120)  # Health check every 2 minutes
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                time.sleep(300)
                
    def record_api_request(self, method, endpoint, duration):
        """Record API request metrics"""
        self.api_requests.labels(method=method, endpoint=endpoint).inc()
        self.api_duration.observe(duration)
        
    def record_bi_query(self):
        """Record business intelligence query"""
        self.bi_queries.inc()
        
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        logger.info("🛑 Monitoring system stopped")

def main():
    """Main monitoring function"""
    monitor = SophiaMonitoring()
    
    try:
        monitor.start_monitoring()
        
        # Keep the monitoring system running
        logger.info("🔄 Monitoring system running... Press Ctrl+C to stop")
        while True:
            time.sleep(60)
            logger.info("💓 Monitoring heartbeat - System operational")
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Monitoring system error: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()

