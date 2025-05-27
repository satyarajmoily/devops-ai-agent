"""Agent orchestrator for handling alerts and recovery actions."""

import time
from datetime import datetime
from typing import Dict, Any, List
from agent.services.docker_service import DockerService


class AgentOrchestrator:
    """Main orchestrator for handling agent actions and recovery."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.docker_service = DockerService()
        self.actions_taken: List[Dict[str, Any]] = []
        self.alerts_received: List[Dict[str, Any]] = []
        
        # Set up logging (simplified for now)
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def handle_alert_webhook(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming alert webhook from Alertmanager.
        
        Args:
            alert_data: Alert data from Alertmanager webhook
            
        Returns:
            Response dictionary with handling results
        """
        # Store the alert
        self.alerts_received.append({
            "timestamp": datetime.utcnow().isoformat(),
            "alert_data": alert_data
        })
        
        # Process alerts
        alerts = alert_data.get('alerts', [])
        self.logger.info(f"Received {len(alerts)} alerts from Alertmanager")
        
        response = {
            'received_alerts': len(alerts),
            'processed_alerts': 0,
            'recovery_actions': [],
            'errors': []
        }
        
        for alert in alerts:
            try:
                # Only process firing alerts
                if alert.get('status') == 'firing':
                    action_id = await self._attempt_recovery(alert)
                    response['recovery_actions'].append(action_id)
                    response['processed_alerts'] += 1
                    
            except Exception as e:
                error_msg = f"Error processing alert: {e}"
                self.logger.error(error_msg)
                response['errors'].append(error_msg)
        
        return response
    
    async def _attempt_recovery(self, alert_details: Dict[str, Any]) -> str:
        """Attempt recovery action based on alert details.
        
        Args:
            alert_details: Alert information containing service details
            
        Returns:
            Recovery action ID for tracking
        """
        action_id = f"recovery_{alert_details.get('alertname', 'Unknown')}_{int(time.time())}"
        
        self.logger.info(f"Starting recovery action {action_id} for alert: {alert_details}")
        
        # Extract service information
        labels = alert_details.get('labels', {})
        service_name = labels.get('job', labels.get('service', 'unknown'))
        container_name = labels.get('container', service_name)
        
        # For common services, map to actual container names
        if service_name == 'market-predictor':
            container_name = 'market-predictor'
        elif service_name == 'devops-ai-agent':
            container_name = 'devops-ai-agent'
        
        self.logger.info(f"Attempting to recover service: {service_name}, container: {container_name}")
        
        try:
            # Attempt restart
            restart_success = await self.docker_service.restart_container(container_name)
            
            action = {
                "id": action_id,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_details": alert_details,
                "service_name": service_name,
                "container_name": container_name,
                "action_type": "container_restart",
                "success": restart_success,
                "error": None if restart_success else "Container restart failed"
            }
            
            if restart_success:
                self.logger.info(f"Recovery action {action_id} completed successfully")
            else:
                self.logger.error(f"Recovery action {action_id} failed to restart container {container_name}")
            
        except Exception as e:
            error_msg = f"Unexpected error during recovery: {type(e).__name__}: {str(e)}"
            self.logger.error(f"Recovery action {action_id} failed with error: {error_msg}")
            
            action = {
                "id": action_id,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_details": alert_details,
                "service_name": service_name,
                "container_name": container_name,
                "action_type": "container_restart",
                "success": False,
                "error": error_msg
            }
        
        # Record the action
        self.actions_taken.append(action)
        
        return action_id
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the orchestrator.
        
        Returns:
            Current status including actions taken and alerts received
        """
        return {
            "orchestrator_active": True,
            "docker_available": self.docker_service.is_available(),
            "alerts_received_count": len(self.alerts_received),
            "actions_taken_count": len(self.actions_taken),
            "recent_alerts": self.alerts_received[-5:],  # Last 5 alerts
            "recent_actions": self.actions_taken[-5:],   # Last 5 actions
            "status": "active"
        } 