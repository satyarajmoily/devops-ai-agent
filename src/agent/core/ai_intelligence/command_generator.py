"""
Creative Command Generator
Enables AI to generate custom diagnostic commands beyond predefined operations
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...config.universal_config import UniversalConfigLoader

logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """Categories of generated commands"""
    DIAGNOSTIC = "diagnostic"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    INVESTIGATION = "investigation"
    VALIDATION = "validation"

@dataclass
class GeneratedCommand:
    """AI-generated command with metadata"""
    command: str
    category: CommandCategory
    purpose: str
    expected_output: str
    risk_level: str  # low, medium, high
    timeout: int
    environment_constraints: List[str]
    fallback_commands: List[str]
    interpretation_hints: List[str]

class CreativeCommandGenerator:
    """
    AI-powered creative command generator
    Generates custom diagnostic commands based on incident context and available operations
    """
    
    def __init__(self, config: UniversalConfigLoader):
        """Initialize creative command generator"""
        self.config = config
        self.llm_config = config.get_llm_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client
        self._initialize_llm_client()
        
        # Load command templates and safety rules
        self.command_templates = self._load_command_templates()
        self.safety_rules = self._load_safety_rules()
        self.environment_constraints = self._load_environment_constraints()
        
        self.logger.info("Creative Command Generator initialized")
    
    def _initialize_llm_client(self):
        """Initialize LLM client from configuration"""
        try:
            import openai
            self.llm_client = openai.AsyncOpenAI(
                api_key=self.llm_config["openai_api_key"]
            )
        except ImportError:
            raise RuntimeError("OpenAI package not available. Install with: pip install openai")
        except KeyError as e:
            raise RuntimeError(f"Missing LLM configuration: {e}")
    
    def _load_command_templates(self) -> Dict[str, Any]:
        """Load command templates for different scenarios"""
        return {
            "network_diagnostics": {
                "docker": [
                    "netstat -tlnp | grep {port}",
                    "ss -tuln | head -20",
                    "ping -c 3 {target_host}",
                    "nslookup {service_name}",
                    "curl -I -m 10 http://localhost:{port}/health"
                ],
                "oci": [
                    "oci network vcn list --compartment-id {compartment_id}",
                    "oci network security-list list --compartment-id {compartment_id}",
                    "oci lb load-balancer list --compartment-id {compartment_id}"
                ]
            },
            "performance_analysis": {
                "docker": [
                    "top -bn1 | head -20",
                    "iostat -x 1 3",
                    "vmstat 1 3",
                    "free -h",
                    "df -h",
                    "ps aux --sort=-%cpu | head -10",
                    "ps aux --sort=-%mem | head -10"
                ],
                "oci": [
                    "oci monitoring metric-data summarize-metrics-data",
                    "oci autoscaling policy list --compartment-id {compartment_id}"
                ]
            },
            "database_diagnostics": {
                "docker": [
                    "mysqladmin -u root processlist",
                    "mysql -e 'SHOW ENGINE INNODB STATUS\\G'",
                    "mysql -e 'SHOW PROCESSLIST'",
                    "mysql -e 'SELECT * FROM information_schema.INNODB_TRX'",
                    "pg_stat_activity query for PostgreSQL"
                ],
                "oci": [
                    "oci db autonomous-database list --compartment-id {compartment_id}",
                    "oci mysql db-system list --compartment-id {compartment_id}"
                ]
            },
            "security_analysis": {
                "docker": [
                    "docker exec {container} ss -tlnp",
                    "docker exec {container} ps aux",
                    "docker inspect {container} | grep -i security",
                    "docker logs {container} | grep -i 'auth\\|login\\|failed'"
                ],
                "oci": [
                    "oci audit event list --compartment-id {compartment_id}",
                    "oci cloud-guard problem list --compartment-id {compartment_id}"
                ]
            }
        }
    
    def _load_safety_rules(self) -> Dict[str, Any]:
        """Load safety rules for command generation"""
        return {
            "forbidden_commands": [
                "rm -rf", "dd if=", "mkfs", "fdisk", "parted",
                "shutdown", "reboot", "halt", "poweroff",
                "passwd", "userdel", "usermod", "groupdel",
                "iptables -F", "ufw --force-enable", "systemctl stop",
                "kill -9", "killall -9", "pkill -9"
            ],
            "forbidden_patterns": [
                r">\s*/dev/sd[a-z]",  # Writing to disk devices
                r">\s*/dev/null",     # Redirecting to null (usually safe but can hide issues)
                r"rm\s+-[rf]+",       # Recursive/force delete
                r"chmod\s+777",       # Dangerous permissions
                r"chown\s+.*:",       # Ownership changes
                r"sudo\s+.*",         # Sudo commands (should be explicit)
            ],
            "risk_indicators": {
                "high": ["delete", "remove", "drop", "truncate", "kill", "stop", "disable"],
                "medium": ["modify", "update", "change", "alter", "restart", "reload"],
                "low": ["show", "list", "get", "describe", "status", "info", "cat", "grep"]
            },
            "max_command_length": 500,
            "max_commands_per_request": 10
        }
    
    def _load_environment_constraints(self) -> Dict[str, Any]:
        """Load environment-specific constraints"""
        return {
            "docker": {
                "required_tools": ["docker", "curl", "netstat", "ps"],
                "optional_tools": ["iostat", "vmstat", "top", "ss"],
                "container_access": True,
                "host_access": False
            },
            "oci": {
                "required_tools": ["oci"],
                "optional_tools": ["curl"],
                "container_access": False,
                "host_access": False,
                "api_access": True
            }
        }
    
    async def generate_custom_commands(self, 
                                     incident_context: Dict[str, Any], 
                                     investigation_focus: str,
                                     max_commands: int = 5) -> List[GeneratedCommand]:
        """
        Generate custom diagnostic commands based on incident context
        
        Args:
            incident_context: Context about the incident
            investigation_focus: What aspect to focus on (network, performance, security, etc.)
            max_commands: Maximum number of commands to generate
        
        Returns:
            List of generated commands with metadata
        """
        self.logger.info(f"Generating custom commands for focus area: {investigation_focus}")
        
        # Build AI prompt for command generation
        prompt = self._build_command_generation_prompt(incident_context, investigation_focus, max_commands)
        
        try:
            # Get AI response
            response = await self.llm_client.chat.completions.create(
                model=self.llm_config["model"],
                temperature=self.llm_config.get("temperature", 0.2),  # Slightly higher for creativity
                max_tokens=self.llm_config.get("max_tokens", 3000),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert systems administrator and SRE who creates safe, effective diagnostic commands. You must follow all safety rules and never generate destructive commands."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            commands = self._parse_ai_command_response(ai_content, incident_context)
            
            # Validate and filter commands
            safe_commands = []
            for command in commands:
                if self._validate_command_safety(command):
                    safe_commands.append(command)
                else:
                    self.logger.warning(f"Filtered unsafe command: {command.command}")
            
            self.logger.info(f"Generated {len(safe_commands)} safe commands (filtered {len(commands) - len(safe_commands)} unsafe)")
            return safe_commands[:max_commands]
            
        except Exception as e:
            self.logger.error(f"AI command generation failed: {e}")
            # Fallback to template-based commands
            return self._generate_template_commands(incident_context, investigation_focus, max_commands)
    
    def _build_command_generation_prompt(self, context: Dict[str, Any], focus: str, max_commands: int) -> str:
        """Build prompt for AI command generation"""
        
        incident = context.get("incident", {})
        environment = context.get("environment", {})
        env_type = environment.get("type", "docker")
        
        # Get environment constraints
        constraints = self.environment_constraints.get(env_type, {})
        available_tools = constraints.get("required_tools", []) + constraints.get("optional_tools", [])
        
        # Get safety rules
        forbidden = self.safety_rules["forbidden_commands"]
        risk_indicators = self.safety_rules["risk_indicators"]
        
        prompt = f"""
CUSTOM DIAGNOSTIC COMMAND GENERATION

## INCIDENT CONTEXT
Service: {incident.get('service', 'unknown')}
Alert: {incident.get('alert_name', 'unknown')}
Severity: {incident.get('severity', 'medium')}
Symptoms: {incident.get('symptoms', [])}
Investigation Focus: {focus}

## ENVIRONMENT CONSTRAINTS
Type: {env_type}
Available Tools: {available_tools}
Container Access: {constraints.get('container_access', False)}
Host Access: {constraints.get('host_access', False)}

## SAFETY RULES (CRITICAL - MUST FOLLOW)
FORBIDDEN COMMANDS: {', '.join(forbidden)}
HIGH RISK INDICATORS: {risk_indicators['high']}
MEDIUM RISK INDICATORS: {risk_indicators['medium']}
LOW RISK INDICATORS: {risk_indicators['low']}

## COMMAND GENERATION GUIDELINES

**For {focus} investigation, generate commands that:**
1. Are SAFE and READ-ONLY when possible
2. Follow environment constraints
3. Provide actionable diagnostic information
4. Have clear expected outputs
5. Include fallback alternatives

**Command Categories:**
- DIAGNOSTIC: Identify problems and bottlenecks
- MONITORING: Track real-time metrics and status
- ANALYSIS: Deep-dive into logs and performance data
- INVESTIGATION: Explore specific issues or patterns
- VALIDATION: Verify system state and configurations

**Environment-Specific Examples:**
{self._get_environment_examples(env_type, focus)}

## OUTPUT FORMAT
Return JSON array with this exact structure:
[
  {{
    "command": "actual_command_to_execute",
    "category": "diagnostic|monitoring|analysis|investigation|validation",
    "purpose": "What this command will investigate or reveal",
    "expected_output": "What kind of output to expect",
    "risk_level": "low|medium|high",
    "timeout": 30,
    "environment_constraints": ["docker_container_required", "requires_network_access"],
    "fallback_commands": ["alternative_command_1", "alternative_command_2"],
    "interpretation_hints": ["How to interpret the output", "What to look for"]
  }}
]

Generate {max_commands} commands focused on {focus} investigation.
Prioritize SAFETY over functionality.
For {env_type} environment with service '{incident.get('service', 'unknown')}'.
"""
        
        return prompt
    
    def _get_environment_examples(self, env_type: str, focus: str) -> str:
        """Get environment-specific command examples"""
        templates = self.command_templates.get(f"{focus}_diagnostics", {})
        env_commands = templates.get(env_type, [])
        
        if env_commands:
            return f"Examples for {env_type}:\n" + "\n".join(f"- {cmd}" for cmd in env_commands[:3])
        else:
            return f"No specific examples for {env_type} + {focus}"
    
    def _parse_ai_command_response(self, ai_content: str, context: Dict[str, Any]) -> List[GeneratedCommand]:
        """Parse AI response into GeneratedCommand objects"""
        try:
            # Extract JSON from response
            json_start = ai_content.find('[')
            json_end = ai_content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in AI response")
            
            json_content = ai_content[json_start:json_end]
            commands_data = json.loads(json_content)
            
            # Convert to GeneratedCommand objects
            commands = []
            for cmd_data in commands_data:
                command = GeneratedCommand(
                    command=cmd_data.get("command", ""),
                    category=CommandCategory(cmd_data.get("category", "diagnostic")),
                    purpose=cmd_data.get("purpose", ""),
                    expected_output=cmd_data.get("expected_output", ""),
                    risk_level=cmd_data.get("risk_level", "medium"),
                    timeout=cmd_data.get("timeout", 30),
                    environment_constraints=cmd_data.get("environment_constraints", []),
                    fallback_commands=cmd_data.get("fallback_commands", []),
                    interpretation_hints=cmd_data.get("interpretation_hints", [])
                )
                commands.append(command)
            
            return commands
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI command response: {e}")
            self.logger.debug(f"AI response content: {ai_content}")
            return []
    
    def _generate_template_commands(self, context: Dict[str, Any], focus: str, max_commands: int) -> List[GeneratedCommand]:
        """Generate commands using templates (fallback)"""
        incident = context.get("incident", {})
        environment = context.get("environment", {})
        env_type = environment.get("type", "docker")
        service = incident.get("service", "unknown")
        
        # Get appropriate template commands
        template_key = f"{focus}_diagnostics"
        templates = self.command_templates.get(template_key, {})
        env_commands = templates.get(env_type, [])
        
        commands = []
        for i, cmd_template in enumerate(env_commands[:max_commands]):
            # Substitute service name and common parameters
            cmd = cmd_template.format(
                service=service,
                container=service,
                port=8080,  # Common default
                target_host="localhost",
                service_name=service,
                compartment_id="ocid1.compartment...."  # OCI placeholder
            )
            
            command = GeneratedCommand(
                command=cmd,
                category=CommandCategory.DIAGNOSTIC,
                purpose=f"Template-based {focus} diagnostic",
                expected_output=f"System information related to {focus}",
                risk_level="low",
                timeout=30,
                environment_constraints=[f"{env_type}_required"],
                fallback_commands=[],
                interpretation_hints=[f"Look for patterns related to {focus}"]
            )
            commands.append(command)
        
        self.logger.info(f"Generated {len(commands)} template-based commands")
        return commands
    
    def _validate_command_safety(self, command: GeneratedCommand) -> bool:
        """Validate that a command is safe to execute"""
        cmd = command.command.lower()
        
        # Check forbidden commands
        for forbidden in self.safety_rules["forbidden_commands"]:
            if forbidden.lower() in cmd:
                self.logger.warning(f"Command contains forbidden term: {forbidden}")
                return False
        
        # Check forbidden patterns
        for pattern in self.safety_rules["forbidden_patterns"]:
            if re.search(pattern, cmd, re.IGNORECASE):
                self.logger.warning(f"Command matches forbidden pattern: {pattern}")
                return False
        
        # Check command length
        if len(command.command) > self.safety_rules["max_command_length"]:
            self.logger.warning(f"Command too long: {len(command.command)} chars")
            return False
        
        # Additional safety checks for high-risk commands
        if command.risk_level == "high":
            # High-risk commands need extra validation
            high_risk_terms = self.safety_rules["risk_indicators"]["high"]
            if any(term.lower() in cmd for term in high_risk_terms):
                self.logger.warning(f"High-risk command not allowed: {command.command}")
                return False
        
        return True
    
    async def optimize_command_parameters(self, 
                                        command: GeneratedCommand, 
                                        execution_history: List[Dict[str, Any]]) -> GeneratedCommand:
        """Optimize command parameters based on execution history"""
        
        # Analyze previous execution results
        similar_commands = [h for h in execution_history 
                          if h.get("operation") == "execute_command" and 
                          command.command.split()[0] in h.get("parameters", {}).get("command", "")]
        
        if not similar_commands:
            return command
        
        # Simple optimization: adjust timeout based on historical performance
        avg_duration = sum(h.get("duration", 30) for h in similar_commands) / len(similar_commands)
        optimized_timeout = max(int(avg_duration * 1.5), command.timeout)
        
        # Create optimized command
        optimized_command = GeneratedCommand(
            command=command.command,
            category=command.category,
            purpose=command.purpose,
            expected_output=command.expected_output,
            risk_level=command.risk_level,
            timeout=optimized_timeout,
            environment_constraints=command.environment_constraints,
            fallback_commands=command.fallback_commands,
            interpretation_hints=command.interpretation_hints + [
                f"Timeout optimized based on {len(similar_commands)} historical executions"
            ]
        )
        
        self.logger.info(f"Optimized command timeout from {command.timeout}s to {optimized_timeout}s")
        return optimized_command
    
    def get_command_explanation(self, command: GeneratedCommand) -> str:
        """Get detailed explanation of what a command does"""
        explanation = f"""
Command: {command.command}
Purpose: {command.purpose}
Category: {command.category.value}
Risk Level: {command.risk_level}
Expected Output: {command.expected_output}

Interpretation Hints:
{chr(10).join(f"• {hint}" for hint in command.interpretation_hints)}

Environment Constraints:
{chr(10).join(f"• {constraint}" for constraint in command.environment_constraints)}
"""
        
        if command.fallback_commands:
            explanation += f"""
Fallback Commands:
{chr(10).join(f"• {fallback}" for fallback in command.fallback_commands)}
"""
        
        return explanation.strip() 