"""AI-driven action executor for dynamic DevOps operations."""

import asyncio
import logging
import subprocess
import time
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from agent.core.ai_reasoning import AIAction, AIDecision
from agent.services.docker_service import DockerServiceManager
from agent.config.settings import get_settings


class ActionResult(BaseModel):
    """Result of action execution."""
    
    success: bool = Field(..., description="Whether action succeeded")
    action_type: str = Field(..., description="Type of action executed")
    target: str = Field(..., description="Target of the action")
    command: Optional[str] = Field(default=None, description="Command that was executed")
    output: Optional[str] = Field(default=None, description="Output from action")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(..., description="Time taken to execute")
    validation_results: Dict = Field(default_factory=dict, description="Validation check results")
    additional_data: Dict = Field(default_factory=dict, description="Additional data from execution")


class PlanExecutionResult(BaseModel):
    """Result of executing an AI action plan."""
    
    success: bool = Field(..., description="Overall plan success")
    actions_executed: List[ActionResult] = Field(default_factory=list, description="Results of each action")
    total_duration: float = Field(..., description="Total execution time")
    ai_decision: AIDecision = Field(..., description="Original AI decision")
    final_analysis: Optional[Dict] = Field(default=None, description="AI's final analysis of results")
    escalation_required: bool = Field(default=False, description="Whether human escalation is needed")
    lessons_learned: List[str] = Field(default_factory=list, description="Key insights from execution")


class FlexibleActionExecutor:
    """Executes AI-generated actions dynamically without hardcoded patterns."""
    
    def __init__(self):
        """Initialize action executor."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.docker_manager = DockerServiceManager()
    
    async def execute_ai_plan(self, ai_decision: AIDecision, context: Dict) -> PlanExecutionResult:
        """Execute an AI-generated action plan.
        
        Args:
            ai_decision: AI decision with action plan
            context: Current system context
            
        Returns:
            Execution results
        """
        start_time = time.time()
        self.logger.info(f"Executing AI plan with {len(ai_decision.action_plan)} actions")
        self.logger.info(f"AI Analysis: {ai_decision.analysis}")
        self.logger.info(f"Root Cause: {ai_decision.root_cause}")
        self.logger.info(f"AI Decision: {ai_decision.decision}")
        
        executed_actions = []
        overall_success = True
        escalation_required = False
        
        try:
            for i, action in enumerate(ai_decision.action_plan):
                self.logger.info(f"Executing action {i+1}/{len(ai_decision.action_plan)}: {action.action_type}")
                self.logger.info(f"  Target: {action.target}")
                self.logger.info(f"  Reason: {action.reason}")
                self.logger.info(f"  Expected: {action.expected_outcome}")
                
                # Execute the action
                action_result = await self._execute_action(action)
                executed_actions.append(action_result)
                
                self.logger.info(f"Action {i+1} {'✅ SUCCEEDED' if action_result.success else '❌ FAILED'}")
                if action_result.error_message:
                    self.logger.error(f"  Error: {action_result.error_message}")
                if action_result.output:
                    self.logger.info(f"  Output: {action_result.output[:200]}...")
                
                # If action failed, check with AI about next steps
                if not action_result.success:
                    # Import here to avoid circular imports
                    from agent.core.ai_reasoning import AIDevOpsReasoning
                    
                    ai_reasoner = AIDevOpsReasoning()
                    evaluation = await ai_reasoner.evaluate_action_result(action, action_result.dict(), context)
                    
                    self.logger.info(f"AI Evaluation: {evaluation.get('evaluation', 'No evaluation')}")
                    self.logger.info(f"AI Recommendation: {evaluation.get('next_recommendation', 'No recommendation')}")
                    
                    if evaluation.get('escalate', False):
                        self.logger.warning("🚨 AI recommends escalating to human intervention")
                        escalation_required = True
                        overall_success = False
                        break
                    elif not evaluation.get('continue_plan', True):
                        self.logger.warning("⚠️ AI recommends stopping the plan")
                        overall_success = False
                        break
                    elif evaluation.get('alternative_action'):
                        self.logger.info("🔄 AI suggests alternative action - adapting plan")
                        # Could implement dynamic plan modification here
                
                # Brief pause between actions
                await asyncio.sleep(1)
            
            # Calculate final results
            total_duration = time.time() - start_time
            
            return PlanExecutionResult(
                success=overall_success and all(action.success for action in executed_actions),
                actions_executed=executed_actions,
                total_duration=total_duration,
                ai_decision=ai_decision,
                escalation_required=escalation_required,
                lessons_learned=self._extract_lessons_learned(executed_actions, ai_decision)
            )
            
        except Exception as e:
            self.logger.error(f"Critical error executing AI plan: {e}")
            return PlanExecutionResult(
                success=False,
                actions_executed=executed_actions,
                total_duration=time.time() - start_time,
                ai_decision=ai_decision,
                escalation_required=True,
                lessons_learned=[f"Critical execution error: {e}"]
            )
    
    async def _execute_action(self, action: AIAction) -> ActionResult:
        """Execute a single AI-generated action.
        
        Args:
            action: AI action to execute
            
        Returns:
            Action execution result
        """
        start_time = time.time()
        
        try:
            # Route to appropriate execution method based on action type
            if action.action_type in ["restart_service", "restart_container"]:
                result = await self._execute_restart_action(action)
            elif action.action_type in ["check_logs", "analyze_logs"]:
                result = await self._execute_log_action(action)
            elif action.action_type in ["check_health", "verify_service", "validate_service"]:
                result = await self._execute_health_check_action(action)
            elif action.action_type in ["docker_compose_up", "recreate_service", "compose_recreate"]:
                result = await self._execute_compose_action(action)
            elif action.action_type in ["run_command", "execute_command", "shell_command"]:
                result = await self._execute_command_action(action)
            elif action.action_type in ["check_docker", "docker_status", "docker_info"]:
                result = await self._execute_docker_info_action(action)
            elif action.action_type in ["wait", "sleep", "pause"]:
                result = await self._execute_wait_action(action)
            elif action.action_type in ["http_check", "url_check", "endpoint_check"]:
                result = await self._execute_http_check_action(action)
            else:
                # Generic command execution for unknown action types
                result = await self._execute_generic_action(action)
            
            result.duration_seconds = time.time() - start_time
            return result
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                command=action.command,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _execute_restart_action(self, action: AIAction) -> ActionResult:
        """Execute container restart action."""
        self.logger.info(f"Restarting container: {action.target}")
        
        try:
            restart_result = await self.docker_manager.restart_service(
                action.target, 
                action.timeout_seconds
            )
            
            return ActionResult(
                success=restart_result.success,
                action_type=action.action_type,
                target=action.target,
                output=f"Container restart {'succeeded' if restart_result.success else 'failed'}",
                error_message=restart_result.error_message,
                duration_seconds=restart_result.duration_seconds,
                additional_data=restart_result.dict()
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_log_action(self, action: AIAction) -> ActionResult:
        """Execute log checking action."""
        self.logger.info(f"Checking logs for: {action.target}")
        
        try:
            logs = await self.docker_manager.get_service_logs(action.target, lines=50)
            
            if logs:
                # Basic log analysis
                log_lines = logs.split('\n')
                error_count = sum(1 for line in log_lines if 'error' in line.lower())
                warning_count = sum(1 for line in log_lines if 'warning' in line.lower())
                
                output = f"Retrieved {len(log_lines)} log lines. Errors: {error_count}, Warnings: {warning_count}"
                
                return ActionResult(
                    success=True,
                    action_type=action.action_type,
                    target=action.target,
                    output=output,
                    additional_data={
                        "log_lines": len(log_lines),
                        "error_count": error_count,
                        "warning_count": warning_count,
                        "recent_logs": log_lines[-10:] if log_lines else []
                    },
                    duration_seconds=0
                )
            else:
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    target=action.target,
                    error_message="No logs available",
                    duration_seconds=0
                )
                
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_health_check_action(self, action: AIAction) -> ActionResult:
        """Execute health check action."""
        self.logger.info(f"Checking health of: {action.target}")
        
        try:
            # Check container health via Docker
            container_info = await self.docker_manager.get_container_info(action.target)
            
            if container_info:
                is_healthy = container_info.status == "running"
                output = f"Container {action.target}: {container_info.status}"
                
                # Try HTTP health check if it's a web service
                http_result = {}
                if action.target in ["market-predictor", "devops-ai-agent"]:
                    port = "8000" if action.target == "market-predictor" else "8001"
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"http://localhost:{port}/health", 
                                                 timeout=aiohttp.ClientTimeout(total=5)) as response:
                                http_result = {
                                    "http_status": response.status,
                                    "http_healthy": response.status == 200
                                }
                                if response.status == 200:
                                    is_healthy = True
                    except Exception as e:
                        http_result = {"http_error": str(e)}
                
                return ActionResult(
                    success=is_healthy,
                    action_type=action.action_type,
                    target=action.target,
                    output=output,
                    additional_data={
                        "container_status": container_info.status,
                        "container_health": container_info.health,
                        **http_result
                    },
                    duration_seconds=0
                )
            else:
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    target=action.target,
                    error_message="Container not found",
                    duration_seconds=0
                )
                
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_compose_action(self, action: AIAction) -> ActionResult:
        """Execute Docker Compose action."""
        self.logger.info(f"Running Docker Compose action for: {action.target}")
        
        try:
            # Build Docker Compose command
            if action.command:
                command = action.command
            else:
                # Default compose command for service recreation
                command = f"docker-compose up -d --force-recreate {action.target}"
            
            # Execute the command
            result = await self._run_shell_command(command, action.timeout_seconds)
            
            # Wait a moment for service to start
            await asyncio.sleep(3)
            
            # Validate service is running
            container_info = await self.docker_manager.get_container_info(action.target)
            service_running = container_info and container_info.status == "running"
            
            return ActionResult(
                success=result["success"] and service_running,
                action_type=action.action_type,
                target=action.target,
                command=command,
                output=result["output"],
                error_message=result.get("error") if not result["success"] else None,
                additional_data={
                    "service_running": service_running,
                    "container_status": container_info.status if container_info else "not_found"
                },
                duration_seconds=0
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                command=action.command,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_command_action(self, action: AIAction) -> ActionResult:
        """Execute shell command action."""
        self.logger.info(f"Executing command: {action.command}")
        
        if not action.command:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message="No command specified",
                duration_seconds=0
            )
        
        try:
            result = await self._run_shell_command(action.command, action.timeout_seconds)
            
            return ActionResult(
                success=result["success"],
                action_type=action.action_type,
                target=action.target,
                command=action.command,
                output=result["output"],
                error_message=result.get("error") if not result["success"] else None,
                duration_seconds=0
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                command=action.command,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_docker_info_action(self, action: AIAction) -> ActionResult:
        """Execute Docker info action."""
        self.logger.info("Getting Docker system information")
        
        try:
            system_info = await self.docker_manager.get_system_info()
            containers = await self.docker_manager.list_containers()
            
            output = f"Docker available: {system_info.get('available', False)}"
            if system_info.get('available'):
                output += f", Running containers: {system_info.get('containers_running', 0)}"
            
            return ActionResult(
                success=system_info.get('available', False),
                action_type=action.action_type,
                target=action.target,
                output=output,
                additional_data={
                    "system_info": system_info,
                    "container_count": len(containers)
                },
                duration_seconds=0
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_wait_action(self, action: AIAction) -> ActionResult:
        """Execute wait/sleep action."""
        wait_time = action.timeout_seconds if action.timeout_seconds > 0 else 5
        self.logger.info(f"Waiting {wait_time} seconds...")
        
        try:
            await asyncio.sleep(wait_time)
            
            return ActionResult(
                success=True,
                action_type=action.action_type,
                target=action.target,
                output=f"Waited {wait_time} seconds",
                duration_seconds=wait_time
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_http_check_action(self, action: AIAction) -> ActionResult:
        """Execute HTTP endpoint check action."""
        self.logger.info(f"Checking HTTP endpoint for: {action.target}")
        
        try:
            # Determine URL
            if action.command and action.command.startswith("http"):
                url = action.command
            elif action.target == "market-predictor":
                url = "http://localhost:8000/health"
            elif action.target == "devops-ai-agent":
                url = "http://localhost:8001/health"
            else:
                return ActionResult(
                    success=False,
                    action_type=action.action_type,
                    target=action.target,
                    error_message="Unable to determine URL for HTTP check",
                    duration_seconds=0
                )
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=action.timeout_seconds)) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    is_healthy = response.status == 200
                    response_data = ""
                    try:
                        response_data = await response.text()
                    except:
                        pass
                    
                    return ActionResult(
                        success=is_healthy,
                        action_type=action.action_type,
                        target=action.target,
                        command=url,
                        output=f"HTTP {response.status} ({response_time:.1f}ms)",
                        additional_data={
                            "status_code": response.status,
                            "response_time_ms": response_time,
                            "response_data": response_data[:200] if response_data else ""
                        },
                        duration_seconds=0
                    )
                    
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                command=action.command,
                error_message=str(e),
                duration_seconds=0
            )
    
    async def _execute_generic_action(self, action: AIAction) -> ActionResult:
        """Execute generic action by interpreting AI intent."""
        self.logger.info(f"Executing generic action: {action.action_type}")
        
        # Try to infer what the AI wants to do based on action type and command
        if action.command:
            return await self._execute_command_action(action)
        else:
            return ActionResult(
                success=False,
                action_type=action.action_type,
                target=action.target,
                error_message=f"Unknown action type '{action.action_type}' with no command specified",
                duration_seconds=0
            )
    
    async def _run_shell_command(self, command: str, timeout: int = 60) -> Dict:
        """Run shell command with timeout."""
        try:
            # Security: Basic command validation
            dangerous_commands = ["rm -rf", "sudo rm", "format", "del /f"]
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                return {
                    "success": False,
                    "output": "",
                    "error": "Dangerous command rejected for safety"
                }
            
            self.logger.info(f"Running command: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                output = stdout.decode() if stdout else ""
                error = stderr.decode() if stderr else ""
                
                success = process.returncode == 0
                
                return {
                    "success": success,
                    "output": output,
                    "error": error,
                    "return_code": process.returncode
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {timeout} seconds"
                }
                
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def _extract_lessons_learned(self, executed_actions: List[ActionResult], ai_decision: AIDecision) -> List[str]:
        """Extract lessons learned from action execution."""
        lessons = []
        
        # Analyze success/failure patterns
        total_actions = len(executed_actions)
        successful_actions = sum(1 for action in executed_actions if action.success)
        
        if successful_actions == total_actions:
            lessons.append(f"AI plan executed successfully with {total_actions} actions")
        elif successful_actions > 0:
            lessons.append(f"Partial success: {successful_actions}/{total_actions} actions succeeded")
        else:
            lessons.append("AI plan failed completely - all actions failed")
        
        # Analyze action types that worked/failed
        action_types = {}
        for action in executed_actions:
            action_type = action.action_type
            if action_type not in action_types:
                action_types[action_type] = {"success": 0, "failure": 0}
            
            if action.success:
                action_types[action_type]["success"] += 1
            else:
                action_types[action_type]["failure"] += 1
        
        for action_type, results in action_types.items():
            if results["failure"] > 0:
                lessons.append(f"Action type '{action_type}' had {results['failure']} failures")
        
        # AI confidence vs actual results
        if ai_decision.confidence > 0.8 and successful_actions < total_actions:
            lessons.append("AI was overconfident - actual results worse than predicted")
        elif ai_decision.confidence < 0.5 and successful_actions == total_actions:
            lessons.append("AI was underconfident - actual results better than predicted")
        
        return lessons 