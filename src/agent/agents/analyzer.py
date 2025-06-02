"""LangChain-based analysis agent for monitoring data analysis."""

import json
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agent.config.settings import get_settings


class AnalysisResult(BaseModel):
    """Result of monitoring data analysis."""
    
    issue_detected: bool = Field(..., description="Whether an issue was detected")
    severity: str = Field(..., description="Issue severity: low, medium, high, critical")
    issue_type: str = Field(..., description="Type of issue detected")
    description: str = Field(..., description="Human-readable description of the issue")
    root_cause: Optional[str] = Field(default=None, description="Suspected root cause")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    confidence: float = Field(..., description="Confidence in analysis (0-1)")
    requires_immediate_action: bool = Field(default=False, description="Whether immediate action is required")


class MonitoringData(BaseModel):
    """Structure for monitoring data input."""
    
    service_name: str = Field(..., description="Name of the service being monitored")
    health_status: str = Field(..., description="Current health status")
    response_time_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    error_count: int = Field(default=0, description="Number of recent errors")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisAgent:
    """LangChain-powered agent for analyzing monitoring data."""
    
    def __init__(self):
        """Initialize the analysis agent."""
        self.settings = get_settings()
        self.llm = self._create_llm()
        self.agent_executor = self._create_agent()
    
    def _create_llm(self) -> ChatOpenAI:
        """Create LLM instance with proper configuration.
        
        Returns:
            Configured ChatOpenAI instance
        """
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required for analysis agent")
        
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            api_key=self.settings.openai_api_key,
            timeout=self.settings.llm_timeout
        )
    
    def _create_analysis_prompt(self) -> ChatPromptTemplate:
        """Create the analysis prompt template.
        
        Returns:
            ChatPromptTemplate for analysis
        """
        system_prompt = """You are an expert system administrator and DevOps engineer analyzing monitoring data for issues.

Your task is to analyze the provided monitoring data and determine:
1. Whether there are any issues or anomalies
2. The severity and type of any issues found
3. The likely root cause
4. Recommended actions to resolve the issues

Guidelines:
- Be conservative in your analysis - don't flag normal variations as issues
- Focus on clear indicators of problems: service unavailability, high error rates, significant performance degradation
- Provide specific, actionable recommendations
- Consider the service's normal operating parameters
- Rate severity as: low (minor issues), medium (noticeable impact), high (significant impact), critical (service down/major failure)

Respond with a JSON object that matches this structure:
{{
    "issue_detected": boolean,
    "severity": "low|medium|high|critical",
    "issue_type": "connectivity|performance|errors|availability|configuration",
    "description": "Clear description of the issue",
    "root_cause": "Suspected root cause or null",
    "recommended_actions": ["action1", "action2"],
    "confidence": 0.0-1.0,
    "requires_immediate_action": boolean
}}

Only respond with valid JSON - no additional text or explanations."""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Analyze this monitoring data:\n\n{monitoring_data}")
        ])
    
    def _create_agent(self) -> Optional[AgentExecutor]:
        """Create the LangChain agent executor.
        
        Returns:
            AgentExecutor or None if LLM is not available
        """
        try:
            # For Phase 1.1, we'll use a simple prompt-based approach
            # Later phases will add more sophisticated tools and agent patterns
            return None  # Will use direct LLM calls for now
        except Exception as e:
            print(f"Warning: Could not create agent executor: {e}")
            return None
    
    async def analyze_monitoring_data(self, monitoring_data: MonitoringData) -> AnalysisResult:
        """Analyze monitoring data for issues.
        
        Args:
            monitoring_data: Monitoring data to analyze
            
        Returns:
            Analysis result with recommendations
            
        Raises:
            ValueError: If analysis fails
        """
        try:
            # Create the prompt
            prompt = self._create_analysis_prompt()
            
            # Format monitoring data as JSON string
            data_json = monitoring_data.model_dump_json(indent=2)
            
            # Create messages
            messages = prompt.format_messages(monitoring_data=data_json)
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            try:
                result_dict = json.loads(response.content)
                return AnalysisResult(**result_dict)
            except json.JSONDecodeError as e:
                # Check if fallback is enabled for malformed JSON
                if not self.settings.fallback_enabled:
                    raise ValueError(f"AI analysis returned malformed JSON and fallback is disabled: {e}")
                
                # Fallback for malformed JSON
                return AnalysisResult(
                    issue_detected=False,
                    severity="low",
                    issue_type="analysis_error",
                    description=f"Failed to parse analysis result: {e}",
                    confidence=0.0
                )
        
        except Exception as e:
            # Check if fallback is enabled
            if not self.settings.fallback_enabled:
                # No fallback allowed - raise the error
                raise ValueError(f"AI analysis failed and fallback is disabled: {e}")
            
            # Fallback analysis for LLM failures
            return self._fallback_analysis(monitoring_data, str(e))
    
    def _fallback_analysis(self, monitoring_data: MonitoringData, error: str) -> AnalysisResult:
        """Provide fallback analysis when LLM is unavailable.
        
        Args:
            monitoring_data: Monitoring data to analyze
            error: Error message from LLM
            
        Returns:
            Basic rule-based analysis result
        """
        # Simple rule-based analysis as fallback
        issue_detected = False
        severity = "low"
        issue_type = "unknown"
        description = "Service monitoring active"
        recommended_actions = []
        
        # Basic health checks
        if monitoring_data.health_status != "healthy":
            issue_detected = True
            severity = "high"
            issue_type = "availability"
            description = f"Service health status is {monitoring_data.health_status}"
            recommended_actions.append("Check service logs")
            recommended_actions.append("Restart service if necessary")
        
        # Response time checks
        if monitoring_data.response_time_ms and monitoring_data.response_time_ms > 5000:
            issue_detected = True
            severity = "medium" if severity == "low" else severity
            issue_type = "performance"
            description += f" High response time: {monitoring_data.response_time_ms}ms"
            recommended_actions.append("Investigate performance bottlenecks")
        
        # Error count checks
        if monitoring_data.error_count > 0:
            issue_detected = True
            severity = "medium" if severity == "low" else severity
            issue_type = "errors"
            description += f" {monitoring_data.error_count} recent errors detected"
            recommended_actions.append("Review error logs")
        
        return AnalysisResult(
            issue_detected=issue_detected,
            severity=severity,
            issue_type=issue_type,
            description=description,
            root_cause=f"LLM analysis unavailable: {error}",
            recommended_actions=recommended_actions or ["Monitor service status"],
            confidence=0.3,  # Low confidence for rule-based analysis
            requires_immediate_action=severity in ["high", "critical"]
        )
    
    def is_available(self) -> bool:
        """Check if the analysis agent is available.
        
        Returns:
            True if LLM is configured and available
        """
        return bool(self.settings.openai_api_key and self.llm)