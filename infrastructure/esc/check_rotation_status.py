#!/usr/bin/env python3
"""
Sophia AI - Check Secret Rotation Status
This script checks the rotation status of all secrets and generates a report.
"""

import os
import json
import logging
import datetime
import argparse
from typing import Dict, List, Any, Optional
import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RotationStatusChecker:
    """
    Checks the rotation status of all secrets
    """
    
    def __init__(self):
        self.service_registry = self._load_service_registry()
        self.rotation_history = self._load_rotation_history()
    
    def _load_service_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load service registry"""
        try:
            registry_path = os.environ.get(
                "SERVICE_REGISTRY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/service_registry.json"
            )
            
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    registry = json.load(f)
                
                logger.info(f"Loaded service registry with {len(registry)} services")
                return registry
            else:
                logger.warning(f"Service registry not found at {registry_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            return {}
    
    def _load_rotation_history(self) -> Dict[str, Dict[str, Any]]:
        """Load rotation history"""
        try:
            history_path = os.environ.get(
                "ROTATION_HISTORY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/esc/rotation_history.json"
            )
            
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    history = json.load(f)
                
                logger.info(f"Loaded rotation history")
                return history
            else:
                logger.warning(f"Rotation history not found at {history_path}, creating empty history")
                return {"services": {}}
        except Exception as e:
            logger.error(f"Failed to load rotation history: {e}")
            return {"services": {}}
    
    def _save_rotation_history(self, history: Dict[str, Any]):
        """Save rotation history"""
        try:
            history_path = os.environ.get(
                "ROTATION_HISTORY_PATH", 
                "/home/ubuntu/github/sophia-main/infrastructure/esc/rotation_history.json"
            )
            
            with open(history_path, "w") as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved rotation history to {history_path}")
        except Exception as e:
            logger.error(f"Failed to save rotation history: {e}")
    
    def _parse_rotation_schedule(self, schedule: str) -> datetime.timedelta:
        """Parse rotation schedule"""
        if schedule.endswith("d"):
            days = int(schedule[:-1])
            return datetime.timedelta(days=days)
        elif schedule.endswith("h"):
            hours = int(schedule[:-1])
            return datetime.timedelta(hours=hours)
        else:
            # Default to 90 days
            return datetime.timedelta(days=90)
    
    def check_rotation_status(self) -> Dict[str, Any]:
        """Check rotation status of all secrets"""
        now = datetime.datetime.now()
        status = {
            "timestamp": now.isoformat(),
            "services": {}
        }
        
        for service, config in self.service_registry.items():
            service_status = {
                "rotation_schedule": config.get("rotation_schedule", "90d"),
                "secret_keys": config.get("secret_keys", []),
                "secrets": {}
            }
            
            # Get rotation schedule
            rotation_interval = self._parse_rotation_schedule(service_status["rotation_schedule"])
            
            # Get rotation history for this service
            service_history = self.rotation_history.get("services", {}).get(service, {})
            
            # Check each secret
            for key in service_status["secret_keys"]:
                secret_id = f"{service}_{key}"
                
                # Get last rotation time
                last_rotation_str = service_history.get(key, {}).get("last_rotation")
                if last_rotation_str:
                    try:
                        last_rotation = datetime.datetime.fromisoformat(last_rotation_str)
                    except ValueError:
                        last_rotation = None
                else:
                    last_rotation = None
                
                # Calculate next rotation time
                if last_rotation:
                    next_rotation = last_rotation + rotation_interval
                    days_until_rotation = (next_rotation - now).days
                    if days_until_rotation < 0:
                        status_text = "OVERDUE"
                    elif days_until_rotation == 0:
                        status_text = "DUE TODAY"
                    elif days_until_rotation <= 7:
                        status_text = "DUE SOON"
                    else:
                        status_text = "OK"
                else:
                    next_rotation = None
                    days_until_rotation = None
                    status_text = "NEVER ROTATED"
                
                # Store secret status
                service_status["secrets"][key] = {
                    "last_rotation": last_rotation_str,
                    "next_rotation": next_rotation.isoformat() if next_rotation else None,
                    "days_until_rotation": days_until_rotation,
                    "status": status_text
                }
            
            # Store service status
            status["services"][service] = service_status
        
        return status
    
    def generate_report(self, status: Dict[str, Any], format: str = "text") -> str:
        """Generate a report of rotation status"""
        if format == "json":
            return json.dumps(status, indent=2)
        
        # Generate text report
        report = []
        report.append(f"Secret Rotation Status Report - {status['timestamp']}")
        report.append("")
        
        # Generate table data
        table_data = []
        for service, service_status in status["services"].items():
            for key, secret_status in service_status["secrets"].items():
                secret_id = f"{service}_{key}"
                last_rotation = secret_status.get("last_rotation", "Never")
                next_rotation = secret_status.get("next_rotation", "ASAP")
                days_until = secret_status.get("days_until_rotation", "N/A")
                status_text = secret_status.get("status", "UNKNOWN")
                
                table_data.append([
                    service,
                    key,
                    last_rotation,
                    next_rotation,
                    days_until,
                    status_text
                ])
        
        # Sort by status (OVERDUE first, then DUE TODAY, etc.)
        status_order = {"OVERDUE": 0, "DUE TODAY": 1, "DUE SOON": 2, "NEVER ROTATED": 3, "OK": 4, "UNKNOWN": 5}
        table_data.sort(key=lambda x: (status_order.get(x[5], 999), x[0], x[1]))
        
        # Generate table
        headers = ["Service", "Secret", "Last Rotation", "Next Rotation", "Days Until", "Status"]
        table = tabulate.tabulate(table_data, headers=headers, tablefmt="grid")
        
        report.append(table)
        report.append("")
        
        # Generate summary
        overdue = sum(1 for row in table_data if row[5] == "OVERDUE")
        due_today = sum(1 for row in table_data if row[5] == "DUE TODAY")
        due_soon = sum(1 for row in table_data if row[5] == "DUE SOON")
        never_rotated = sum(1 for row in table_data if row[5] == "NEVER ROTATED")
        ok = sum(1 for row in table_data if row[5] == "OK")
        
        report.append(f"Summary:")
        report.append(f"  OVERDUE: {overdue}")
        report.append(f"  DUE TODAY: {due_today}")
        report.append(f"  DUE SOON: {due_soon}")
        report.append(f"  NEVER ROTATED: {never_rotated}")
        report.append(f"  OK: {ok}")
        report.append(f"  Total: {len(table_data)}")
        
        return "\n".join(report)
    
    def update_rotation_history(self, service: str, key: str, timestamp: str = None):
        """Update rotation history for a secret"""
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        # Ensure service exists in history
        if "services" not in self.rotation_history:
            self.rotation_history["services"] = {}
        
        if service not in self.rotation_history["services"]:
            self.rotation_history["services"][service] = {}
        
        # Update last rotation time
        if key not in self.rotation_history["services"][service]:
            self.rotation_history["services"][service][key] = {}
        
        self.rotation_history["services"][service][key]["last_rotation"] = timestamp
        
        # Save history
        self._save_rotation_history(self.rotation_history)
        
        logger.info(f"Updated rotation history for {service}_{key}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check secret rotation status")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--update", "-u", action="store_true", help="Update rotation history for a secret")
    parser.add_argument("--service", "-s", help="Service name (required with --update)")
    parser.add_argument("--key", "-k", help="Secret key (required with --update)")
    parser.add_argument("--timestamp", "-t", help="Timestamp (ISO format, defaults to now)")
    args = parser.parse_args()
    
    try:
        checker = RotationStatusChecker()
        
        if args.update:
            if not args.service or not args.key:
                parser.error("--service and --key are required with --update")
            
            checker.update_rotation_history(args.service, args.key, args.timestamp)
            print(f"Updated rotation history for {args.service}_{args.key}")
        else:
            status = checker.check_rotation_status()
            report = checker.generate_report(status, args.format)
            
            if args.output:
                with open(args.output, "w") as f:
                    f.write(report)
                print(f"Report written to {args.output}")
            else:
                print(report)
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

