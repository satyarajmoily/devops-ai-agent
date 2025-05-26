"""Core monitoring orchestration for the Market Programmer Agent."""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional

from agent.agents.analyzer import AnalysisAgent, AnalysisResult, MonitoringData
from agent.config.settings import get_settings
from agent.models.health import AgentAction, MonitoringTarget
from agent.services.predictor_client import PredictorClient
from agent.services.recovery_service import RecoveryService


class MonitoringOrchestrator:
    """Orchestrates monitoring activities for target services."""
    
    def __init__(self):
        """Initialize the monitoring orchestrator."""
        self.settings = get_settings()
        self.analysis_agent = AnalysisAgent()
        self.recovery_service = RecoveryService()
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_cycle_time: Optional[datetime] = None
        self.recent_actions: List[AgentAction] = []
        self.monitoring_targets: Dict[str, MonitoringTarget] = {}
        
        # Initialize monitoring targets
        self._initialize_targets()
    
    def _initialize_targets(self):
        """Initialize monitoring targets."""
        # Add Market Predictor as primary target
        self.monitoring_targets["market-predictor"] = MonitoringTarget(
            name="market-predictor",
            url=self.settings.market_predictor_url,
            status="unknown",
            last_check=datetime.utcnow(),
            response_time_ms=None,
            error_message=None
        )
    
    async def start_monitoring(self):
        """Start the monitoring loop."""
        if self.is_running:
            print("Monitoring already running")
            return
        
        self.is_running = True
        print(f"🔍 Starting monitoring loop (interval: {self.settings.monitoring_interval}s)")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        return self.monitoring_task
    
    async def stop_monitoring(self):
        """Stop the monitoring loop."""
        if not self.is_running:
            print("Monitoring not running")
            return
        
        self.is_running = False
        print("🛑 Stopping monitoring loop")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._perform_monitoring_cycle()
                self.last_cycle_time = datetime.utcnow()
                
                # Wait for next cycle
                await asyncio.sleep(self.settings.monitoring_interval)
                
            except asyncio.CancelledError:
                print("Monitoring loop cancelled")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                # Continue monitoring despite errors
                await asyncio.sleep(self.settings.monitoring_interval)
    
    async def _perform_monitoring_cycle(self):
        """Perform a single monitoring cycle."""
        print(f"📊 Performing monitoring cycle at {datetime.utcnow()}")
        
        # Monitor all targets
        for target_name, target in self.monitoring_targets.items():
            try:
                await self._monitor_target(target_name, target)
            except Exception as e:
                print(f"Error monitoring {target_name}: {e}")
                self._update_target_status(target_name, "error", str(e))
    
    async def _monitor_target(self, target_name: str, target: MonitoringTarget):
        """Monitor a specific target service.
        
        Args:
            target_name: Name of the target service
            target: Target monitoring configuration
        """
        if target_name == "market-predictor":
            await self._monitor_market_predictor(target)
        else:
            print(f"Unknown target type: {target_name}")
    
    async def _monitor_market_predictor(self, target: MonitoringTarget):
        """Monitor the Market Predictor service.
        
        Args:
            target: Market predictor monitoring target
        """
        try:
            async with PredictorClient(target.url, self.settings.health_check_timeout) as client:
                # Check connectivity and get basic health
                is_connected, error_msg, response_time = await client.check_connectivity()
                
                if not is_connected:
                    self._update_target_status("market-predictor", "unhealthy", error_msg, response_time)
                    await self._handle_predictor_issue("connectivity", error_msg)
                    return
                
                # Get detailed status
                status_response = await client.get_status()
                
                # Update target status
                self._update_target_status("market-predictor", "healthy", None, response_time)
                
                # Create monitoring data for analysis
                monitoring_data = MonitoringData(
                    service_name="market-predictor",
                    health_status=status_response.status,
                    response_time_ms=response_time,
                    error_count=0,  # Will be enhanced in later phases
                    uptime_seconds=status_response.uptime_seconds,
                    components=status_response.components,
                    metadata=status_response.metadata or {}
                )
                
                # Analyze monitoring data
                if self.analysis_agent.is_available():
                    analysis_result = await self.analysis_agent.analyze_monitoring_data(monitoring_data)
                    await self._handle_analysis_result(analysis_result)
                else:
                    print("⚠️  Analysis agent not available, using basic monitoring")
                
        except Exception as e:
            error_msg = f"Failed to monitor market-predictor: {e}"
            self._update_target_status("market-predictor", "error", error_msg)
            await self._handle_predictor_issue("monitoring_error", error_msg)
    
    def _update_target_status(self, target_name: str, status: str, error_msg: Optional[str] = None, response_time: Optional[float] = None):
        """Update the status of a monitoring target.
        
        Args:
            target_name: Name of the target
            status: New status
            error_msg: Error message if any
            response_time: Response time in milliseconds
        """
        if target_name in self.monitoring_targets:
            target = self.monitoring_targets[target_name]
            target.status = status
            target.last_check = datetime.utcnow()
            target.error_message = error_msg
            target.response_time_ms = response_time
            
            print(f"📊 {target_name}: {status}" + 
                  (f" ({response_time:.1f}ms)" if response_time else "") +
                  (f" - {error_msg}" if error_msg else ""))
    
    async def _handle_analysis_result(self, result: AnalysisResult):
        """Handle the result of monitoring data analysis.
        
        Args:
            result: Analysis result from the AI agent
        """
        if result.issue_detected:
            print(f"🚨 Issue detected: {result.description}")
            print(f"   Severity: {result.severity}")
            print(f"   Type: {result.issue_type}")
            print(f"   Confidence: {result.confidence:.2f}")
            
            if result.recommended_actions:
                print(f"   Recommended actions:")
                for action in result.recommended_actions:
                    print(f"   - {action}")
            
            # In Phase 1.1, we just log the analysis
            # Later phases will implement actual action execution
            action = AgentAction(
                action_id=f"analysis_{int(time.time())}",
                action_type="analysis",
                target_service="market-predictor",
                description=f"Analyzed issue: {result.description}",
                status="completed",
                result=f"Severity: {result.severity}, Confidence: {result.confidence:.2f}"
            )
            
            self._add_recent_action(action)
        else:
            print(f"✅ No issues detected (confidence: {result.confidence:.2f})")
    
    async def _handle_predictor_issue(self, issue_type: str, error_msg: str):
        """Handle issues with the Market Predictor service.
        
        Args:
            issue_type: Type of issue
            error_msg: Error message
        """
        print(f"⚠️  Market Predictor issue ({issue_type}): {error_msg}")
        
        # In Phase 1.1, we just log the issue
        # Later phases will implement automatic recovery actions
        action = AgentAction(
            action_id=f"issue_{int(time.time())}",
            action_type=issue_type,
            target_service="market-predictor",
            description=f"Detected {issue_type}: {error_msg}",
            status="detected"
        )
        
        self._add_recent_action(action)
    
    def _add_recent_action(self, action: AgentAction):
        """Add an action to the recent actions list.
        
        Args:
            action: Action to add
        """
        self.recent_actions.append(action)
        
        # Keep only last 10 actions
        if len(self.recent_actions) > 10:
            self.recent_actions = self.recent_actions[-10:]
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status.
        
        Returns:
            Dictionary with monitoring status information
        """
        return {
            "is_running": self.is_running,
            "last_cycle": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "monitoring_interval": self.settings.monitoring_interval,
            "targets": {
                name: {
                    "status": target.status,
                    "last_check": target.last_check.isoformat(),
                    "response_time_ms": target.response_time_ms,
                    "error_message": target.error_message
                }
                for name, target in self.monitoring_targets.items()
            },
            "recent_actions": [
                {
                    "action_id": action.action_id,
                    "type": action.action_type,
                    "target": action.target_service,
                    "description": action.description,
                    "status": action.status,
                    "timestamp": action.timestamp.isoformat()
                }
                for action in self.recent_actions
            ]
        }
    
    async def handle_alert_webhook(self, alert_data: Dict) -> Dict:
        """Handle incoming alert webhook from Alertmanager.
        
        Args:
            alert_data: Alert data from Alertmanager webhook
            
        Returns:
            Response dictionary with handling results
        """
        try:
            # Log the alert
            alerts = alert_data.get('alerts', [])
            print(f"🚨 Received {len(alerts)} alerts from Alertmanager")
            
            response = {
                'received_alerts': len(alerts),
                'processed_alerts': 0,
                'recovery_results': [],
                'errors': []
            }
            
            for alert in alerts:
                try:
                    alert_name = alert.get('labels', {}).get('alertname', 'unknown')
                    service_name = alert.get('labels', {}).get('service', 'unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    status = alert.get('status', 'unknown')
                    
                    print(f"  🔥 {status.upper()}: {alert_name} - {alert.get('annotations', {}).get('summary', 'No summary')}")
                    
                    # Only process firing alerts
                    if status == 'firing':
                        print(f"  🤖 Triggering recovery for alert: {alert_name}")
                        
                        # Execute recovery using the recovery service
                        recovery_result = await self.recovery_service.execute_recovery(alert_data)
                        
                        # Log recovery result
                        if recovery_result.success:
                            print(f"  ✅ Recovery completed successfully for {alert_name}")
                            print(f"     Duration: {recovery_result.duration_seconds:.1f}s")
                            print(f"     Steps executed: {recovery_result.metrics.get('total_steps', 0)}")
                        else:
                            print(f"  ❌ Recovery failed for {alert_name}")
                            print(f"     Error: {recovery_result.error_message}")
                            
                        # Store result
                        response['recovery_results'].append({
                            'alert_name': alert_name,
                            'service_name': service_name,
                            'success': recovery_result.success,
                            'duration_seconds': recovery_result.duration_seconds,
                            'steps_executed': len(recovery_result.steps_executed),
                            'recommendations': recovery_result.recommendations
                        })
                        
                        # Record action in monitoring history
                        action = AgentAction(
                            action_id=f"recovery_{alert_name}_{int(time.time())}",
                            action_type="automated_recovery",
                            target_service=service_name,
                            description=f"Automated recovery for alert {alert_name}",
                            status="completed" if recovery_result.success else "failed",
                            details={
                                'alert_name': alert_name,
                                'recovery_steps': len(recovery_result.steps_executed),
                                'duration_seconds': recovery_result.duration_seconds,
                                'recommendations': recovery_result.recommendations
                            }
                        )
                        self._add_recent_action(action)
                        
                        response['processed_alerts'] += 1
                        
                    elif status == 'resolved':
                        print(f"  ✅ Alert resolved: {alert_name}")
                        
                        # Record resolution in monitoring history
                        action = AgentAction(
                            action_id=f"resolved_{alert_name}_{int(time.time())}",
                            action_type="alert_resolved",
                            target_service=service_name,
                            description=f"Alert {alert_name} resolved",
                            status="completed"
                        )
                        self._add_recent_action(action)
                        
                except Exception as e:
                    error_msg = f"Error processing alert: {e}"
                    print(f"  ❌ {error_msg}")
                    response['errors'].append(error_msg)
            
            return response
            
        except Exception as e:
            print(f"❌ Error handling alert webhook: {e}")
            return {
                'error': str(e),
                'received_alerts': 0,
                'processed_alerts': 0,
                'recovery_results': [],
                'errors': [str(e)]
            }
    
    async def execute_manual_recovery(self, service_name: str, recovery_type: str = "full") -> Dict:
        """Execute manual recovery for a service.
        
        Args:
            service_name: Name of the service to recover
            recovery_type: Type of recovery (full, restart, logs)
            
        Returns:
            Recovery result dictionary
        """
        try:
            print(f"🔧 Executing manual recovery for {service_name} (type: {recovery_type})")
            
            # Create mock alert data for manual recovery
            mock_alert_data = {
                'alerts': [{
                    'labels': {
                        'alertname': f'Manual{recovery_type.capitalize()}Recovery',
                        'service': service_name,
                        'severity': 'warning'
                    },
                    'annotations': {
                        'summary': f'Manual {recovery_type} recovery requested',
                        'action_required': 'restart_service' if recovery_type in ['full', 'restart'] else 'check_logs'
                    },
                    'status': 'firing'
                }]
            }
            
            # Execute recovery
            recovery_result = await self.recovery_service.execute_recovery(mock_alert_data)
            
            # Record action
            action = AgentAction(
                action_id=f"manual_recovery_{service_name}_{int(time.time())}",
                action_type="manual_recovery",
                target_service=service_name,
                description=f"Manual {recovery_type} recovery for {service_name}",
                status="completed" if recovery_result.success else "failed",
                details={
                    'recovery_type': recovery_type,
                    'steps_executed': len(recovery_result.steps_executed),
                    'duration_seconds': recovery_result.duration_seconds,
                    'recommendations': recovery_result.recommendations
                }
            )
            self._add_recent_action(action)
            
            return {
                'success': recovery_result.success,
                'service_name': service_name,
                'recovery_type': recovery_type,
                'duration_seconds': recovery_result.duration_seconds,
                'steps_executed': len(recovery_result.steps_executed),
                'recommendations': recovery_result.recommendations,
                'error_message': recovery_result.error_message
            }
            
        except Exception as e:
            error_msg = f"Manual recovery failed: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'service_name': service_name,
                'recovery_type': recovery_type,
                'error_message': error_msg
            }
    
    def get_recovery_status(self) -> Dict:
        """Get current recovery service status and capabilities.
        
        Returns:
            Recovery status dictionary
        """
        return {
            'recovery_service_available': True,
            'docker_available': self.recovery_service.docker_manager.is_available(),
            'supported_actions': [
                'restart_service', 'check_logs', 'check_service_health', 
                'investigate_performance', 'check_resource_usage'
            ],
            'recent_recoveries': [
                action for action in self.recent_actions 
                if action.action_type in ['automated_recovery', 'manual_recovery']
            ][-10:]  # Last 10 recovery actions
        }