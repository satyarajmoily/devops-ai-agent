"""
Context Enricher
Enhanced AI context building with service architecture understanding and historical patterns
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from ...config.universal_config import UniversalConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class ServiceDependency:
    """Service dependency information"""
    service_name: str
    dependency_type: str  # upstream, downstream, database, cache, etc.
    criticality: str  # critical, important, optional
    health_endpoint: Optional[str] = None
    typical_response_time: Optional[float] = None

@dataclass
class PerformanceBaseline:
    """Performance baseline for service metrics"""
    metric_name: str
    normal_range: Tuple[float, float]
    warning_threshold: float
    critical_threshold: float
    trend_direction: str  # stable, increasing, decreasing
    last_updated: datetime

@dataclass
class IncidentPattern:
    """Historical incident pattern"""
    pattern_id: str
    symptoms: List[str]
    root_causes: List[str]
    resolution_steps: List[str]
    frequency: int
    last_occurrence: datetime
    avg_resolution_time: float

class ContextEnricher:
    """
    Enhanced AI context builder
    Provides rich context with service architecture, baselines, and historical patterns
    """
    
    def __init__(self, config: UniversalConfigLoader):
        """Initialize context enricher"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load service architecture and dependencies
        self.service_dependencies = self._load_service_dependencies()
        self.performance_baselines = self._load_performance_baselines()
        self.incident_patterns = self._load_incident_patterns()
        
        # Initialize execution history tracking
        self.execution_history = []
        self.incident_history = []
        
        self.logger.info("Context Enricher initialized with service architecture awareness")
    
    def _load_service_dependencies(self) -> Dict[str, List[ServiceDependency]]:
        """Load service dependency mappings"""
        # In production, this would come from service mesh, configuration files, or discovery service
        return {
            "market-predictor": [
                ServiceDependency("postgres", "database", "critical", "/health", 50.0),
                ServiceDependency("redis", "cache", "important", "/ping", 10.0),
                ServiceDependency("external-api", "upstream", "important", None, 200.0)
            ],
            "devops-ai-agent": [
                ServiceDependency("docker", "infrastructure", "critical", None, None),
                ServiceDependency("prometheus", "monitoring", "important", "/metrics", 100.0),
                ServiceDependency("openai-api", "upstream", "critical", None, 1000.0)
            ],
            "coding-ai-agent": [
                ServiceDependency("file-system", "infrastructure", "critical", None, None),
                ServiceDependency("openai-api", "upstream", "critical", None, 1000.0)
            ]
        }
    
    def _load_performance_baselines(self) -> Dict[str, Dict[str, PerformanceBaseline]]:
        """Load performance baselines for services and metrics"""
        return {
            "market-predictor": {
                "cpu": PerformanceBaseline("cpu", (10.0, 40.0), 60.0, 80.0, "stable", datetime.now()),
                "memory": PerformanceBaseline("memory", (200.0, 800.0), 1000.0, 1200.0, "stable", datetime.now()),
                "response_time": PerformanceBaseline("response_time", (50.0, 200.0), 500.0, 1000.0, "stable", datetime.now()),
                "error_rate": PerformanceBaseline("error_rate", (0.0, 1.0), 5.0, 10.0, "stable", datetime.now())
            },
            "devops-ai-agent": {
                "cpu": PerformanceBaseline("cpu", (5.0, 25.0), 50.0, 70.0, "stable", datetime.now()),
                "memory": PerformanceBaseline("memory", (100.0, 400.0), 600.0, 800.0, "stable", datetime.now()),
                "operations_per_minute": PerformanceBaseline("operations_per_minute", (1.0, 10.0), 20.0, 50.0, "stable", datetime.now())
            },
            "coding-ai-agent": {
                "cpu": PerformanceBaseline("cpu", (5.0, 30.0), 60.0, 80.0, "stable", datetime.now()),
                "memory": PerformanceBaseline("memory", (100.0, 500.0), 800.0, 1000.0, "stable", datetime.now())
            }
        }
    
    def _load_incident_patterns(self) -> Dict[str, List[IncidentPattern]]:
        """Load historical incident patterns"""
        return {
            "service_down": [
                IncidentPattern(
                    "memory_leak_pattern",
                    ["high_memory", "slow_response", "eventual_crash"],
                    ["memory_leak", "insufficient_garbage_collection"],
                    ["restart_service", "investigate_memory_usage", "apply_memory_limits"],
                    frequency=3,
                    last_occurrence=datetime.now() - timedelta(days=15),
                    avg_resolution_time=300.0
                ),
                IncidentPattern(
                    "dependency_failure_pattern",
                    ["connection_errors", "timeout_errors", "cascade_failures"],
                    ["external_service_down", "network_partition", "rate_limiting"],
                    ["check_dependencies", "implement_circuit_breaker", "enable_fallback"],
                    frequency=5,
                    last_occurrence=datetime.now() - timedelta(days=7),
                    avg_resolution_time=180.0
                )
            ],
            "high_latency": [
                IncidentPattern(
                    "database_bottleneck_pattern",
                    ["slow_queries", "connection_pool_exhaustion", "lock_contention"],
                    ["unoptimized_queries", "database_overload", "missing_indexes"],
                    ["optimize_queries", "scale_database", "add_indexes"],
                    frequency=2,
                    last_occurrence=datetime.now() - timedelta(days=30),
                    avg_resolution_time=600.0
                )
            ]
        }
    
    async def enrich_incident_context(self, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich incident context with additional intelligence
        
        Args:
            base_context: Basic incident context from universal interface
        
        Returns:
            Enhanced context with service architecture, baselines, and patterns
        """
        incident = base_context.get("incident", {})
        service = incident.get("service", "unknown")
        
        self.logger.info(f"Enriching context for service: {service}")
        
        # Start with base context
        enriched_context = {**base_context}
        
        # Add service architecture context
        enriched_context["service_architecture"] = await self._get_service_architecture_context(service)
        
        # Add performance baselines
        enriched_context["performance_baselines"] = self._get_performance_baselines_context(service)
        
        # Add historical patterns
        enriched_context["historical_patterns"] = self._get_historical_patterns_context(incident)
        
        # Add dependency health status
        enriched_context["dependency_health"] = await self._get_dependency_health_context(service)
        
        # Add execution history insights
        enriched_context["execution_insights"] = self._get_execution_insights_context(service)
        
        # Add incident correlation
        enriched_context["incident_correlation"] = self._get_incident_correlation_context(incident)
        
        # Add environmental factors
        enriched_context["environmental_factors"] = await self._get_environmental_factors_context()
        
        # Calculate context confidence score
        enriched_context["context_confidence"] = self._calculate_context_confidence(enriched_context)
        
        self.logger.info(f"Context enriched with {len(enriched_context)} sections")
        return enriched_context
    
    async def _get_service_architecture_context(self, service: str) -> Dict[str, Any]:
        """Get service architecture and dependency context"""
        dependencies = self.service_dependencies.get(service, [])
        
        architecture_context = {
            "service_name": service,
            "dependency_count": len(dependencies),
            "critical_dependencies": [dep for dep in dependencies if dep.criticality == "critical"],
            "upstream_services": [dep for dep in dependencies if dep.dependency_type == "upstream"],
            "downstream_services": [dep for dep in dependencies if dep.dependency_type == "downstream"],
            "infrastructure_dependencies": [dep for dep in dependencies if dep.dependency_type == "infrastructure"],
            "data_dependencies": [dep for dep in dependencies if dep.dependency_type in ["database", "cache"]],
            "dependency_map": {
                dep.service_name: {
                    "type": dep.dependency_type,
                    "criticality": dep.criticality,
                    "health_endpoint": dep.health_endpoint,
                    "typical_response_time": dep.typical_response_time
                } for dep in dependencies
            }
        }
        
        # Add service topology insights
        if dependencies:
            critical_count = len(architecture_context["critical_dependencies"])
            total_count = len(dependencies)
            architecture_context["risk_assessment"] = {
                "dependency_risk": "high" if critical_count > 3 else "medium" if critical_count > 1 else "low",
                "complexity_score": total_count * 0.1,
                "single_points_of_failure": [dep.service_name for dep in dependencies if dep.criticality == "critical"]
            }
        
        return architecture_context
    
    def _get_performance_baselines_context(self, service: str) -> Dict[str, Any]:
        """Get performance baselines and threshold context"""
        baselines = self.performance_baselines.get(service, {})
        
        baseline_context = {
            "service": service,
            "has_baselines": len(baselines) > 0,
            "baseline_count": len(baselines),
            "metrics": {}
        }
        
        for metric_name, baseline in baselines.items():
            baseline_context["metrics"][metric_name] = {
                "normal_range": {
                    "min": baseline.normal_range[0],
                    "max": baseline.normal_range[1]
                },
                "thresholds": {
                    "warning": baseline.warning_threshold,
                    "critical": baseline.critical_threshold
                },
                "trend": baseline.trend_direction,
                "last_updated": baseline.last_updated.isoformat(),
                "baseline_age_days": (datetime.now() - baseline.last_updated).days
            }
        
        # Add baseline health assessment
        if baselines:
            stale_baselines = [name for name, baseline in baselines.items() 
                             if (datetime.now() - baseline.last_updated).days > 7]
            baseline_context["baseline_health"] = {
                "stale_count": len(stale_baselines),
                "stale_baselines": stale_baselines,
                "freshness": "good" if len(stale_baselines) == 0 else "stale"
            }
        
        return baseline_context
    
    def _get_historical_patterns_context(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical incident patterns context"""
        alert_name = incident.get("alert_name", "").lower()
        symptoms = incident.get("symptoms", [])
        
        # Classify incident type for pattern matching
        incident_type = self._classify_incident_for_patterns(alert_name, symptoms)
        
        relevant_patterns = self.incident_patterns.get(incident_type, [])
        
        pattern_context = {
            "incident_type": incident_type,
            "pattern_count": len(relevant_patterns),
            "patterns": []
        }
        
        for pattern in relevant_patterns:
            # Calculate pattern relevance
            relevance_score = self._calculate_pattern_relevance(incident, pattern)
            
            pattern_info = {
                "pattern_id": pattern.pattern_id,
                "symptoms": pattern.symptoms,
                "root_causes": pattern.root_causes,
                "resolution_steps": pattern.resolution_steps,
                "frequency": pattern.frequency,
                "last_occurrence": pattern.last_occurrence.isoformat(),
                "days_since_last": (datetime.now() - pattern.last_occurrence).days,
                "avg_resolution_time_minutes": pattern.avg_resolution_time / 60,
                "relevance_score": relevance_score,
                "recommended": relevance_score > 0.7
            }
            pattern_context["patterns"].append(pattern_info)
        
        # Sort patterns by relevance
        pattern_context["patterns"].sort(key=lambda p: p["relevance_score"], reverse=True)
        
        return pattern_context
    
    def _classify_incident_for_patterns(self, alert_name: str, symptoms: List[str]) -> str:
        """Classify incident type for pattern matching"""
        alert_lower = alert_name.lower()
        symptoms_lower = [s.lower() for s in symptoms]
        
        if any(keyword in alert_lower for keyword in ["down", "unavailable", "failed"]):
            return "service_down"
        elif any(keyword in alert_lower for keyword in ["slow", "latency", "timeout"]):
            return "high_latency"
        elif any(keyword in alert_lower for keyword in ["memory", "cpu", "resource"]):
            return "resource_exhaustion"
        else:
            return "service_down"  # Default
    
    def _calculate_pattern_relevance(self, incident: Dict[str, Any], pattern: IncidentPattern) -> float:
        """Calculate how relevant a historical pattern is to current incident"""
        relevance = 0.0
        
        incident_symptoms = [s.lower() for s in incident.get("symptoms", [])]
        pattern_symptoms = [s.lower() for s in pattern.symptoms]
        
        # Symptom overlap score (0-0.4)
        if incident_symptoms and pattern_symptoms:
            overlap = len(set(incident_symptoms) & set(pattern_symptoms))
            max_possible = max(len(incident_symptoms), len(pattern_symptoms))
            relevance += (overlap / max_possible) * 0.4
        
        # Frequency score (0-0.3) - more frequent patterns are more relevant
        frequency_score = min(pattern.frequency / 10.0, 1.0) * 0.3
        relevance += frequency_score
        
        # Recency score (0-0.3) - more recent patterns are more relevant
        days_since = (datetime.now() - pattern.last_occurrence).days
        recency_score = max(0, (30 - days_since) / 30) * 0.3
        relevance += recency_score
        
        return min(relevance, 1.0)
    
    async def _get_dependency_health_context(self, service: str) -> Dict[str, Any]:
        """Get dependency health status context"""
        dependencies = self.service_dependencies.get(service, [])
        
        health_context = {
            "total_dependencies": len(dependencies),
            "health_checks_available": 0,
            "dependency_status": {},
            "critical_dependencies_healthy": True,
            "health_summary": "unknown"
        }
        
        if not dependencies:
            health_context["health_summary"] = "no_dependencies"
            return health_context
        
        # In production, this would actually check health endpoints
        # For now, simulate health checks
        for dep in dependencies:
            dep_health = {
                "criticality": dep.criticality,
                "has_health_endpoint": dep.health_endpoint is not None,
                "status": "unknown",
                "response_time": None,
                "last_checked": None
            }
            
            if dep.health_endpoint:
                health_context["health_checks_available"] += 1
                # Simulate health check (in production, would make actual HTTP calls)
                dep_health.update({
                    "status": "healthy",  # Would be determined by actual check
                    "response_time": dep.typical_response_time,
                    "last_checked": datetime.now().isoformat()
                })
            
            health_context["dependency_status"][dep.service_name] = dep_health
            
            # Check if critical dependencies are healthy
            if dep.criticality == "critical" and dep_health["status"] != "healthy":
                health_context["critical_dependencies_healthy"] = False
        
        # Determine overall health summary
        if health_context["critical_dependencies_healthy"]:
            health_context["health_summary"] = "healthy"
        else:
            health_context["health_summary"] = "degraded"
        
        return health_context
    
    def _get_execution_insights_context(self, service: str) -> Dict[str, Any]:
        """Get insights from recent operation executions"""
        # Filter execution history for this service
        service_executions = [
            exec_record for exec_record in self.execution_history
            if exec_record.get("service") == service
        ]
        
        insights_context = {
            "total_executions": len(service_executions),
            "success_rate": 0.0,
            "avg_execution_time": 0.0,
            "common_operations": {},
            "recent_failures": [],
            "performance_trends": {}
        }
        
        if not service_executions:
            return insights_context
        
        # Calculate success rate
        successful = [e for e in service_executions if e.get("success", False)]
        insights_context["success_rate"] = len(successful) / len(service_executions)
        
        # Calculate average execution time
        durations = [e.get("duration", 0) for e in service_executions if e.get("duration")]
        if durations:
            insights_context["avg_execution_time"] = sum(durations) / len(durations)
        
        # Find common operations
        operation_counts = defaultdict(int)
        for execution in service_executions:
            operation = execution.get("operation", "unknown")
            operation_counts[operation] += 1
        
        insights_context["common_operations"] = dict(operation_counts)
        
        # Recent failures
        failures = [e for e in service_executions if not e.get("success", True)]
        insights_context["recent_failures"] = failures[-5:]  # Last 5 failures
        
        return insights_context
    
    def _get_incident_correlation_context(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Get incident correlation and clustering context"""
        alert_name = incident.get("alert_name", "")
        service = incident.get("service", "")
        
        correlation_context = {
            "related_incidents": [],
            "correlation_score": 0.0,
            "incident_clustering": "isolated",
            "time_correlation": []
        }
        
        # Find related incidents from history
        for hist_incident in self.incident_history:
            if hist_incident.get("service") == service:
                # Calculate time correlation
                time_diff = abs((datetime.now() - hist_incident.get("timestamp", datetime.now())).total_seconds())
                if time_diff < 3600:  # Within last hour
                    correlation_context["related_incidents"].append({
                        "alert": hist_incident.get("alert_name", ""),
                        "time_ago_minutes": time_diff / 60,
                        "correlation": "temporal"
                    })
        
        # Determine clustering
        if len(correlation_context["related_incidents"]) > 2:
            correlation_context["incident_clustering"] = "cluster"
        elif len(correlation_context["related_incidents"]) > 0:
            correlation_context["incident_clustering"] = "related"
        
        return correlation_context
    
    async def _get_environmental_factors_context(self) -> Dict[str, Any]:
        """Get environmental factors that might affect incidents"""
        env_context = {
            "deployment_info": {
                "recent_deployments": [],
                "deployment_frequency": "unknown",
                "last_deployment": None
            },
            "resource_pressure": {
                "cluster_utilization": "unknown",
                "available_capacity": "unknown",
                "resource_trends": []
            },
            "external_factors": {
                "network_conditions": "unknown",
                "external_service_status": "unknown",
                "scheduled_maintenance": []
            }
        }
        
        # In production, this would integrate with:
        # - CI/CD systems for deployment info
        # - Cluster monitoring for resource pressure
        # - External status pages for service health
        # - Maintenance scheduling systems
        
        return env_context
    
    def _calculate_context_confidence(self, enriched_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence score for the enriched context"""
        confidence_factors = {
            "service_architecture": 0.8 if enriched_context.get("service_architecture", {}).get("dependency_count", 0) > 0 else 0.2,
            "performance_baselines": 0.9 if enriched_context.get("performance_baselines", {}).get("has_baselines", False) else 0.1,
            "historical_patterns": 0.7 if enriched_context.get("historical_patterns", {}).get("pattern_count", 0) > 0 else 0.3,
            "dependency_health": 0.6,  # Always available but might be simulated
            "execution_insights": 0.8 if enriched_context.get("execution_insights", {}).get("total_executions", 0) > 0 else 0.2
        }
        
        overall_confidence = sum(confidence_factors.values()) / len(confidence_factors)
        
        return {
            "overall_confidence": overall_confidence,
            "confidence_factors": confidence_factors,
            "confidence_level": "high" if overall_confidence > 0.7 else "medium" if overall_confidence > 0.4 else "low",
            "recommendations": self._get_confidence_recommendations(confidence_factors)
        }
    
    def _get_confidence_recommendations(self, confidence_factors: Dict[str, float]) -> List[str]:
        """Get recommendations to improve context confidence"""
        recommendations = []
        
        if confidence_factors["performance_baselines"] < 0.5:
            recommendations.append("Establish performance baselines for better incident detection")
        
        if confidence_factors["historical_patterns"] < 0.5:
            recommendations.append("Build incident pattern database from historical data")
        
        if confidence_factors["execution_insights"] < 0.5:
            recommendations.append("Increase operation execution to build insights")
        
        return recommendations
    
    def record_execution(self, execution_record: Dict[str, Any]):
        """Record an operation execution for future insights"""
        execution_record["timestamp"] = datetime.now()
        self.execution_history.append(execution_record)
        
        # Keep only recent history (last 1000 executions)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def record_incident(self, incident_record: Dict[str, Any]):
        """Record an incident for correlation analysis"""
        incident_record["timestamp"] = datetime.now()
        self.incident_history.append(incident_record)
        
        # Keep only recent history (last 500 incidents)
        if len(self.incident_history) > 500:
            self.incident_history = self.incident_history[-500:] 