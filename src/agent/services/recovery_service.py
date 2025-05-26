"""Recovery service for automated system recovery operations."""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from agent.services.docker_service import DockerServiceManager, ServiceRestartResult
from agent.config.settings import get_settings


class RecoveryAction(str, Enum):
    """Available recovery actions."""
    
    RESTART_SERVICE = "restart_service"
    CHECK_LOGS = "check_logs"
    CHECK_SERVICE_HEALTH = "check_service_health"
    INVESTIGATE_PERFORMANCE = "investigate_performance"
    CHECK_RESOURCE_USAGE = "check_resource_usage"
    CLEANUP_DISK_SPACE = "cleanup_disk_space"
    EMERGENCY_CLEANUP = "emergency_cleanup"
    INVESTIGATE_CONTAINER_ISSUES = "investigate_container_issues"
    RESTART_CONTAINER = "restart_container"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class RecoveryStep(BaseModel):
    """Individual recovery step."""
    
    action: RecoveryAction = Field(..., description="Recovery action to take")
    target: str = Field(..., description="Target service/component")
    timeout_seconds: int = Field(default=30, description="Timeout for this step")
    retry_count: int = Field(default=3, description="Number of retries")
    prerequisite_checks: List[str] = Field(default_factory=list, description="Prerequisites")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")


class RecoveryResult(BaseModel):
    """Result of recovery operation."""
    
    success: bool = Field(..., description="Overall success status")
    alert_name: str = Field(..., description="Alert that triggered recovery")
    service_name: str = Field(..., description="Target service")
    steps_executed: List[Dict] = Field(default_factory=list, description="Steps executed")
    duration_seconds: float = Field(..., description="Total duration")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    recommendations: List[str] = Field(default_factory=list, description="Next steps")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Recovery metrics")


class LogAnalysisResult(BaseModel):
    """Result of log analysis."""
    
    error_patterns: List[str] = Field(default_factory=list, description="Detected error patterns")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    startup_issues: List[str] = Field(default_factory=list, description="Startup-related issues")
    connectivity_issues: List[str] = Field(default_factory=list, description="Network issues")
    resource_issues: List[str] = Field(default_factory=list, description="Resource problems")
    recommendations: List[str] = Field(default_factory=list, description="Analysis recommendations")


class RecoveryService:
    """Service for automated system recovery operations."""
    
    def __init__(self):
        """Initialize recovery service."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.docker_manager = DockerServiceManager()
        
        # Recovery patterns and strategies
        self._initialize_recovery_patterns()
    
    def _initialize_recovery_patterns(self):
        """Initialize recovery patterns and strategies."""
        
        # Error patterns for log analysis
        self.error_patterns = {
            'connection_refused': [
                r'Connection refused',
                r'connect.*refused',
                r'No route to host',
                r'Network unreachable'
            ],
            'timeout': [
                r'timeout',
                r'timed out',
                r'operation timeout'
            ],
            'memory_error': [
                r'OutOfMemoryError',
                r'MemoryError',
                r'Cannot allocate memory',
                r'memory.*exhausted'
            ],
            'port_binding': [
                r'Port.*already in use',
                r'Address already in use',
                r'bind.*address already in use'
            ],
            'dependency_missing': [
                r'ModuleNotFoundError',
                r'ImportError',
                r'No module named',
                r'dependency.*not found'
            ],
            'permission_denied': [
                r'Permission denied',
                r'Access denied',
                r'Forbidden'
            ],
            'file_not_found': [
                r'No such file or directory',
                r'FileNotFoundError',
                r'File not found'
            ]
        }
        
        # Recovery strategies by alert type
        self.recovery_strategies = {
            'MarketPredictorDown': [
                RecoveryStep(
                    action=RecoveryAction.CHECK_LOGS,
                    target="market-predictor",
                    timeout_seconds=10
                ),
                RecoveryStep(
                    action=RecoveryAction.RESTART_SERVICE,
                    target="market-predictor",
                    timeout_seconds=60,
                    success_criteria=["service_running", "health_check_passed"]
                ),
                RecoveryStep(
                    action=RecoveryAction.CHECK_SERVICE_HEALTH,
                    target="market-predictor",
                    timeout_seconds=30
                )
            ],
            'MarketProgrammerAgentDown': [
                RecoveryStep(
                    action=RecoveryAction.CHECK_LOGS,
                    target="market-programmer-agent",
                    timeout_seconds=10
                ),
                RecoveryStep(
                    action=RecoveryAction.RESTART_SERVICE,
                    target="market-programmer-agent",
                    timeout_seconds=60
                )
            ],
            'HighMemoryUsage': [
                RecoveryStep(
                    action=RecoveryAction.CHECK_RESOURCE_USAGE,
                    target="system",
                    timeout_seconds=15
                ),
                RecoveryStep(
                    action=RecoveryAction.CHECK_LOGS,
                    target="all",
                    timeout_seconds=10
                )
            ],
            'CriticalMemoryUsage': [
                RecoveryStep(
                    action=RecoveryAction.RESTART_SERVICE,
                    target="market-predictor",
                    timeout_seconds=60
                )
            ],
            'ServiceDown': [
                RecoveryStep(
                    action=RecoveryAction.CHECK_LOGS,
                    target="service_name",  # Will be replaced with actual service name
                    timeout_seconds=10
                ),
                RecoveryStep(
                    action=RecoveryAction.RESTART_SERVICE,
                    target="service_name",  # Will be replaced with actual service name
                    timeout_seconds=60,
                    success_criteria=["service_running", "health_check_passed"]
                ),
                RecoveryStep(
                    action=RecoveryAction.CHECK_SERVICE_HEALTH,
                    target="service_name",  # Will be replaced with actual service name
                    timeout_seconds=30
                )
            ]
        }
    
    async def execute_recovery(self, alert_data: Dict) -> RecoveryResult:
        """Execute recovery operation based on alert data."""
        start_time = datetime.utcnow()
        
        # Extract alert information
        alert_name = self._extract_alert_name(alert_data)
        service_name = self._extract_service_name(alert_data)
        severity = self._extract_severity(alert_data)
        action_required = self._extract_action_required(alert_data)
        
        self.logger.info(f"Starting recovery for alert {alert_name}, service: {service_name}")
        
        try:
            # Determine recovery strategy
            recovery_steps = self._get_recovery_strategy(alert_name, action_required)
            
            if not recovery_steps:
                return RecoveryResult(
                    success=False,
                    alert_name=alert_name,
                    service_name=service_name,
                    duration_seconds=0.0,
                    error_message=f"No recovery strategy found for alert {alert_name}",
                    recommendations=["Manual investigation required"]
                )
            
            # Replace service_name placeholders in recovery steps
            for step in recovery_steps:
                if step.target == "service_name":
                    step.target = service_name
            
            # Execute recovery steps
            executed_steps = []
            overall_success = True
            
            for step in recovery_steps:
                step_result = await self._execute_recovery_step(step, service_name)
                executed_steps.append(step_result)
                
                # Stop on critical failure
                if not step_result.get('success', False) and step.action == RecoveryAction.RESTART_SERVICE:
                    overall_success = False
                    break
            
            # Calculate metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics = await self._calculate_recovery_metrics(executed_steps, service_name)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                executed_steps, overall_success, alert_name, service_name
            )
            
            return RecoveryResult(
                success=overall_success,
                alert_name=alert_name,
                service_name=service_name,
                steps_executed=executed_steps,
                duration_seconds=duration,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Recovery execution failed: {e}")
            
            return RecoveryResult(
                success=False,
                alert_name=alert_name,
                service_name=service_name,
                duration_seconds=duration,
                error_message=str(e),
                recommendations=["Manual investigation required", "Check agent logs for details"]
            )
    
    def _extract_alert_name(self, alert_data: Dict) -> str:
        """Extract alert name from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            return alerts[0].get('labels', {}).get('alertname', 'unknown')
        return 'unknown'
    
    def _extract_service_name(self, alert_data: Dict) -> str:
        """Extract service name from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            labels = alerts[0].get('labels', {})
            # Try 'service' first, then 'job', then 'container'
            service_name = labels.get('service') or labels.get('job') or labels.get('container', 'unknown')
            self.logger.info(f"Extracted service name: '{service_name}' from labels: {labels}")
            return service_name
        self.logger.warning("No alerts found in alert_data")
        return 'unknown'
    
    def _extract_severity(self, alert_data: Dict) -> str:
        """Extract severity from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            return alerts[0].get('labels', {}).get('severity', 'unknown')
        return 'unknown'
    
    def _extract_action_required(self, alert_data: Dict) -> Optional[str]:
        """Extract required action from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            return alerts[0].get('annotations', {}).get('action_required')
        return None 
    
    async def _execute_recovery_step(self, step: RecoveryStep, service_name: str) -> Dict:
        """Execute a single recovery step."""
        step_start = datetime.utcnow()
        step_result = {
            'action': step.action.value,
            'target': step.target,
            'success': False,
            'duration_seconds': 0.0,
            'output': None,
            'error_message': None
        }
        
        try:
            target = step.target if step.target != "all" else service_name
            
            if step.action == RecoveryAction.RESTART_SERVICE:
                result = await self.docker_manager.restart_service(target, step.timeout_seconds)
                step_result.update({
                    'success': result.success,
                    'output': result.dict(),
                    'error_message': result.error_message
                })
                
            elif step.action == RecoveryAction.CHECK_LOGS:
                logs = await self.docker_manager.get_service_logs(target, lines=50)
                log_analysis = await self._analyze_logs(logs) if logs else None
                step_result.update({
                    'success': logs is not None,
                    'output': {
                        'logs_available': logs is not None,
                        'log_analysis': log_analysis.dict() if log_analysis else None
                    },
                    'error_message': "No logs available" if not logs else None
                })
                
            elif step.action == RecoveryAction.CHECK_SERVICE_HEALTH:
                container_info = await self.docker_manager.get_container_info(target)
                health_status = self._check_container_health(container_info)
                step_result.update({
                    'success': health_status['healthy'],
                    'output': health_status
                })
                
            elif step.action == RecoveryAction.CHECK_RESOURCE_USAGE:
                system_info = await self.docker_manager.get_system_info()
                containers = await self.docker_manager.list_containers()
                resource_status = self._analyze_resource_usage(system_info, containers)
                step_result.update({
                    'success': True,
                    'output': resource_status
                })
                
            else:
                step_result.update({
                    'success': False,
                    'error_message': f"Recovery action {step.action} not implemented"
                })
                
        except Exception as e:
            step_result.update({
                'success': False,
                'error_message': str(e)
            })
            
        finally:
            step_result['duration_seconds'] = (datetime.utcnow() - step_start).total_seconds()
            
        return step_result
    
    async def _analyze_logs(self, logs: str) -> LogAnalysisResult:
        """Analyze service logs for issues."""
        analysis = LogAnalysisResult()
        
        if not logs:
            return analysis
        
        log_lines = logs.split('\n')
        
        for line in log_lines:
            line_lower = line.lower()
            
            # Check for error patterns
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        analysis.error_patterns.append(f"{error_type}: {line.strip()}")
                        break
            
            # Check for warnings
            if any(word in line_lower for word in ['warn', 'warning']):
                analysis.warnings.append(line.strip())
            
            # Check for startup issues
            if any(word in line_lower for word in ['startup', 'initialization', 'failed to start']):
                analysis.startup_issues.append(line.strip())
            
            # Check for connectivity issues
            if any(word in line_lower for word in ['connection', 'network', 'unreachable']):
                analysis.connectivity_issues.append(line.strip())
            
            # Check for resource issues
            if any(word in line_lower for word in ['memory', 'disk', 'cpu', 'resource']):
                analysis.resource_issues.append(line.strip())
        
        # Generate recommendations based on analysis
        analysis.recommendations = self._generate_log_recommendations(analysis)
        
        return analysis
    
    def _generate_log_recommendations(self, analysis: LogAnalysisResult) -> List[str]:
        """Generate recommendations based on log analysis."""
        recommendations = []
        
        if analysis.error_patterns:
            recommendations.append("Investigate error patterns in logs")
            
            if any('connection' in pattern.lower() for pattern in analysis.error_patterns):
                recommendations.append("Check network connectivity and service dependencies")
                
            if any('memory' in pattern.lower() for pattern in analysis.error_patterns):
                recommendations.append("Review memory usage and consider increasing resource limits")
                
            if any('port' in pattern.lower() for pattern in analysis.error_patterns):
                recommendations.append("Check for port conflicts and ensure services are properly configured")
        
        if analysis.startup_issues:
            recommendations.append("Review service startup configuration and dependencies")
        
        if len(analysis.warnings) > 5:
            recommendations.append("High number of warnings detected - review service configuration")
        
        if not recommendations:
            recommendations.append("No significant issues detected in logs")
        
        return recommendations
    
    def _check_container_health(self, container_info) -> Dict:
        """Check container health status."""
        if not container_info:
            return {
                'healthy': False,
                'status': 'not_found',
                'message': 'Container not found'
            }
        
        healthy = container_info.status == 'running'
        
        return {
            'healthy': healthy,
            'status': container_info.status,
            'container_id': container_info.id,
            'started': container_info.started.isoformat() if container_info.started else None,
            'health_status': container_info.health,
            'message': f"Container is {container_info.status}"
        }
    
    def _analyze_resource_usage(self, system_info: Dict, containers: List) -> Dict:
        """Analyze system resource usage."""
        analysis = {
            'docker_available': system_info.get('available', False),
            'containers_running': system_info.get('containers_running', 0),
            'containers_stopped': system_info.get('containers_stopped', 0),
            'total_containers': len(containers),
            'issues': [],
            'recommendations': []
        }
        
        # Check for resource issues
        if analysis['containers_stopped'] > 0:
            analysis['issues'].append(f"{analysis['containers_stopped']} containers are stopped")
            analysis['recommendations'].append("Investigate stopped containers")
        
        if analysis['containers_running'] == 0:
            analysis['issues'].append("No containers are running")
            analysis['recommendations'].append("Check Docker Compose services")
        
        return analysis
    
    def _get_recovery_strategy(self, alert_name: str, action_required: Optional[str]) -> List[RecoveryStep]:
        """Get recovery strategy for alert."""
        # Check for specific alert strategy
        if alert_name in self.recovery_strategies:
            return self.recovery_strategies[alert_name]
        
        # Check for action-based strategy
        if action_required:
            if action_required == "restart_service":
                return [
                    RecoveryStep(
                        action=RecoveryAction.CHECK_LOGS,
                        target="unknown",
                        timeout_seconds=10
                    ),
                    RecoveryStep(
                        action=RecoveryAction.RESTART_SERVICE,
                        target="unknown",
                        timeout_seconds=60
                    )
                ]
            elif action_required == "check_logs":
                return [
                    RecoveryStep(
                        action=RecoveryAction.CHECK_LOGS,
                        target="unknown",
                        timeout_seconds=10
                    )
                ]
        
        # Default strategy
        return [
            RecoveryStep(
                action=RecoveryAction.CHECK_SERVICE_HEALTH,
                target="unknown",
                timeout_seconds=30
            )
        ]
    
    async def _calculate_recovery_metrics(self, executed_steps: List[Dict], service_name: str) -> Dict:
        """Calculate recovery operation metrics."""
        metrics = {
            'total_steps': len(executed_steps),
            'successful_steps': sum(1 for step in executed_steps if step.get('success', False)),
            'failed_steps': sum(1 for step in executed_steps if not step.get('success', False)),
            'total_duration': sum(step.get('duration_seconds', 0) for step in executed_steps),
            'restart_attempted': any(step.get('action') == 'restart_service' for step in executed_steps),
            'logs_analyzed': any(step.get('action') == 'check_logs' for step in executed_steps),
            'service_healthy_after_recovery': False
        }
        
        # Check final service health
        try:
            container_info = await self.docker_manager.get_container_info(service_name)
            metrics['service_healthy_after_recovery'] = (
                container_info and container_info.status == 'running'
            )
        except Exception:
            pass
        
        return metrics
    
    def _generate_recommendations(self, executed_steps: List[Dict], overall_success: bool, 
                                alert_name: str, service_name: str) -> List[str]:
        """Generate recommendations based on recovery results."""
        recommendations = []
        
        if overall_success:
            recommendations.append("Recovery completed successfully")
            recommendations.append("Continue monitoring service health")
        else:
            recommendations.append("Automatic recovery failed")
            recommendations.append("Manual investigation required")
            
            # Specific recommendations based on failures
            restart_failed = any(
                step.get('action') == 'restart_service' and not step.get('success', False)
                for step in executed_steps
            )
            
            if restart_failed:
                recommendations.append("Service restart failed - check Docker status and logs")
                recommendations.append("Consider manual container restart or Docker Compose recreation")
        
        # Alert-specific recommendations
        if 'Down' in alert_name:
            recommendations.append("Verify service dependencies are healthy")
            recommendations.append("Check network connectivity and port availability")
        
        if 'Memory' in alert_name:
            recommendations.append("Review application memory usage patterns")
            recommendations.append("Consider increasing container memory limits")
        
        return recommendations 