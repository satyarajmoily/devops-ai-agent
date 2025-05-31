"""
Pattern Matcher
Historical incident pattern recognition and learning system
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import re

from ..config.universal_config import UniversalConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class PatternMatch:
    """A matched pattern with confidence score"""
    pattern_id: str
    confidence: float
    matched_symptoms: List[str]
    suggested_actions: List[str]
    estimated_resolution_time: float
    pattern_frequency: int
    last_success: Optional[datetime] = None

@dataclass
class ResolutionOutcome:
    """Outcome of a resolution attempt"""
    pattern_id: str
    actions_taken: List[str]
    success: bool
    resolution_time: float
    timestamp: datetime
    lessons_learned: List[str]

class PatternMatcher:
    """
    Advanced pattern recognition system for infrastructure incidents
    Learns from historical data and successful resolutions
    """
    
    def __init__(self, config: UniversalConfigLoader):
        """Initialize pattern matcher"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pattern storage
        self.learned_patterns = {}
        self.resolution_outcomes = []
        self.pattern_success_rates = defaultdict(list)
        
        # Pattern matching configuration
        self.similarity_threshold = 0.7
        self.confidence_threshold = 0.6
        self.max_patterns_to_match = 5
        
        # Load existing patterns
        self._load_existing_patterns()
        
        self.logger.info("Pattern Matcher initialized with learning capabilities")
    
    def _load_existing_patterns(self):
        """Load existing patterns from storage or configuration"""
        # In production, this would load from persistent storage
        # For now, initialize with some basic patterns
        self.learned_patterns = {
            "memory_leak_cascade": {
                "symptoms": ["high_memory_usage", "slow_response_time", "increasing_cpu", "service_restart_failed"],
                "root_causes": ["memory_leak", "insufficient_gc", "resource_exhaustion"],
                "successful_resolutions": [
                    ["restart_service", "check_memory_limits", "investigate_memory_patterns"],
                    ["scale_service", "apply_memory_limits", "monitor_heap_usage"]
                ],
                "frequency": 4,
                "success_rate": 0.85,
                "avg_resolution_time": 420.0,
                "last_updated": datetime.now() - timedelta(days=5)
            },
            "database_connection_exhaustion": {
                "symptoms": ["connection_timeout", "database_errors", "slow_queries", "high_db_cpu"],
                "root_causes": ["connection_pool_exhaustion", "long_running_queries", "missing_indexes"],
                "successful_resolutions": [
                    ["restart_service", "optimize_connection_pool", "kill_long_queries"],
                    ["scale_database", "add_read_replicas", "optimize_queries"]
                ],
                "frequency": 6,
                "success_rate": 0.92,
                "avg_resolution_time": 180.0,
                "last_updated": datetime.now() - timedelta(days=2)
            },
            "external_dependency_timeout": {
                "symptoms": ["timeout_errors", "circuit_breaker_open", "fallback_activated", "response_time_spike"],
                "root_causes": ["external_service_degradation", "network_issues", "rate_limiting"],
                "successful_resolutions": [
                    ["enable_circuit_breaker", "activate_fallback", "monitor_external_service"],
                    ["adjust_timeout_settings", "implement_retry_logic", "contact_external_team"]
                ],
                "frequency": 8,
                "success_rate": 0.78,
                "avg_resolution_time": 90.0,
                "last_updated": datetime.now() - timedelta(days=1)
            }
        }
    
    async def find_matching_patterns(self, incident_context: Dict[str, Any]) -> List[PatternMatch]:
        """
        Find patterns that match the current incident
        
        Args:
            incident_context: Current incident context including symptoms and metrics
        
        Returns:
            List of matching patterns with confidence scores
        """
        incident = incident_context.get("incident", {})
        symptoms = self._extract_symptoms(incident_context)
        
        self.logger.info(f"Searching for patterns matching {len(symptoms)} symptoms")
        
        matches = []
        
        for pattern_id, pattern_data in self.learned_patterns.items():
            # Calculate pattern match confidence
            confidence = self._calculate_pattern_confidence(symptoms, pattern_data)
            
            if confidence >= self.confidence_threshold:
                # Get matched symptoms
                matched_symptoms = self._get_matched_symptoms(symptoms, pattern_data["symptoms"])
                
                # Get suggested actions based on most successful resolutions
                suggested_actions = self._get_suggested_actions(pattern_data)
                
                # Estimate resolution time based on historical data
                estimated_time = self._estimate_resolution_time(pattern_data, confidence)
                
                match = PatternMatch(
                    pattern_id=pattern_id,
                    confidence=confidence,
                    matched_symptoms=matched_symptoms,
                    suggested_actions=suggested_actions,
                    estimated_resolution_time=estimated_time,
                    pattern_frequency=pattern_data["frequency"],
                    last_success=pattern_data.get("last_updated")
                )
                
                matches.append(match)
        
        # Sort by confidence and limit results
        matches.sort(key=lambda m: m.confidence, reverse=True)
        top_matches = matches[:self.max_patterns_to_match]
        
        self.logger.info(f"Found {len(top_matches)} matching patterns with confidence >= {self.confidence_threshold}")
        return top_matches
    
    def _extract_symptoms(self, incident_context: Dict[str, Any]) -> List[str]:
        """Extract normalized symptoms from incident context"""
        symptoms = []
        
        # From explicit symptoms
        incident = incident_context.get("incident", {})
        explicit_symptoms = incident.get("symptoms", [])
        symptoms.extend([self._normalize_symptom(s) for s in explicit_symptoms])
        
        # From alert name
        alert_name = incident.get("alert_name", "")
        alert_symptoms = self._extract_symptoms_from_alert(alert_name)
        symptoms.extend(alert_symptoms)
        
        # From resource metrics (if available)
        resource_context = incident_context.get("resource_metrics", {})
        resource_symptoms = self._extract_symptoms_from_metrics(resource_context)
        symptoms.extend(resource_symptoms)
        
        # From execution insights
        insights = incident_context.get("execution_insights", {})
        if insights.get("success_rate", 1.0) < 0.5:
            symptoms.append("high_operation_failure_rate")
        
        # Remove duplicates and return
        return list(set(symptoms))
    
    def _normalize_symptom(self, symptom: str) -> str:
        """Normalize symptom strings for consistent matching"""
        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', symptom.lower())
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        return normalized.strip('_')
    
    def _extract_symptoms_from_alert(self, alert_name: str) -> List[str]:
        """Extract symptoms from alert name"""
        alert_lower = alert_name.lower()
        symptoms = []
        
        # Define symptom patterns
        symptom_patterns = {
            "high_memory": ["memory", "mem", "oom"],
            "high_cpu": ["cpu", "processor"],
            "high_disk": ["disk", "storage", "space"],
            "slow_response": ["slow", "latency", "timeout"],
            "service_down": ["down", "unavailable", "failed", "crash"],
            "connection_error": ["connection", "connect", "network"],
            "database_error": ["database", "db", "sql", "query"],
            "external_error": ["external", "upstream", "dependency"]
        }
        
        for symptom, keywords in symptom_patterns.items():
            if any(keyword in alert_lower for keyword in keywords):
                symptoms.append(symptom)
        
        return symptoms
    
    def _extract_symptoms_from_metrics(self, metrics: Dict[str, Any]) -> List[str]:
        """Extract symptoms from resource metrics"""
        symptoms = []
        
        # CPU metrics
        cpu_usage = metrics.get("cpu_percent", 0)
        if cpu_usage > 80:
            symptoms.append("high_cpu_usage")
        elif cpu_usage > 60:
            symptoms.append("elevated_cpu_usage")
        
        # Memory metrics
        memory_usage = metrics.get("memory_percent", 0)
        if memory_usage > 90:
            symptoms.append("high_memory_usage")
        elif memory_usage > 70:
            symptoms.append("elevated_memory_usage")
        
        # Response time metrics
        response_time = metrics.get("avg_response_time", 0)
        if response_time > 1000:
            symptoms.append("slow_response_time")
        elif response_time > 500:
            symptoms.append("elevated_response_time")
        
        return symptoms
    
    def _calculate_pattern_confidence(self, incident_symptoms: List[str], pattern_data: Dict[str, Any]) -> float:
        """Calculate confidence score for pattern match"""
        pattern_symptoms = pattern_data["symptoms"]
        
        if not incident_symptoms or not pattern_symptoms:
            return 0.0
        
        # Symptom overlap score (0-0.6)
        common_symptoms = set(incident_symptoms) & set(pattern_symptoms)
        overlap_score = len(common_symptoms) / len(set(incident_symptoms) | set(pattern_symptoms))
        
        # Historical success rate score (0-0.2)
        success_rate_score = pattern_data.get("success_rate", 0.5) * 0.2
        
        # Frequency/recency score (0-0.2)
        frequency = pattern_data.get("frequency", 1)
        last_updated = pattern_data.get("last_updated", datetime.now() - timedelta(days=30))
        days_since = (datetime.now() - last_updated).days
        
        frequency_score = min(frequency / 10, 1.0) * 0.1
        recency_score = max(0, (30 - days_since) / 30) * 0.1
        
        total_confidence = (overlap_score * 0.6) + success_rate_score + frequency_score + recency_score
        
        return min(total_confidence, 1.0)
    
    def _get_matched_symptoms(self, incident_symptoms: List[str], pattern_symptoms: List[str]) -> List[str]:
        """Get list of symptoms that matched between incident and pattern"""
        return list(set(incident_symptoms) & set(pattern_symptoms))
    
    def _get_suggested_actions(self, pattern_data: Dict[str, Any]) -> List[str]:
        """Get suggested actions based on most successful historical resolutions"""
        successful_resolutions = pattern_data.get("successful_resolutions", [])
        
        if not successful_resolutions:
            return []
        
        # If multiple successful resolution paths, choose the most recent/successful
        # For now, return the first one (most successful)
        return successful_resolutions[0] if successful_resolutions else []
    
    def _estimate_resolution_time(self, pattern_data: Dict[str, Any], confidence: float) -> float:
        """Estimate resolution time based on pattern history and confidence"""
        base_time = pattern_data.get("avg_resolution_time", 300.0)
        
        # Adjust based on confidence - lower confidence means might take longer
        confidence_factor = 0.8 + (confidence * 0.4)  # 0.8 to 1.2 multiplier
        
        # Add some uncertainty for lower confidence
        uncertainty_factor = 1.0 + ((1.0 - confidence) * 0.5)
        
        estimated_time = base_time * confidence_factor * uncertainty_factor
        
        return estimated_time
    
    async def learn_from_resolution(self, 
                                  incident_context: Dict[str, Any], 
                                  actions_taken: List[str],
                                  outcome: Dict[str, Any]) -> bool:
        """
        Learn from a resolution attempt to improve future pattern matching
        
        Args:
            incident_context: Original incident context
            actions_taken: List of actions that were taken
            outcome: Resolution outcome with success/failure and timing
        
        Returns:
            True if learning was successful
        """
        try:
            success = outcome.get("success", False)
            resolution_time = outcome.get("duration", 0.0)
            
            # Extract symptoms from incident
            symptoms = self._extract_symptoms(incident_context)
            
            # Record resolution outcome
            resolution_outcome = ResolutionOutcome(
                pattern_id=self._generate_pattern_id(symptoms),
                actions_taken=actions_taken,
                success=success,
                resolution_time=resolution_time,
                timestamp=datetime.now(),
                lessons_learned=outcome.get("lessons_learned", [])
            )
            
            self.resolution_outcomes.append(resolution_outcome)
            
            if success:
                # Update or create pattern based on successful resolution
                await self._update_pattern_from_success(symptoms, actions_taken, resolution_time)
                
                self.logger.info(f"Learned from successful resolution in {resolution_time:.1f}s")
            else:
                # Learn from failure - mark certain action combinations as less effective
                await self._update_pattern_from_failure(symptoms, actions_taken)
                
                self.logger.info("Learned from failed resolution attempt")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to learn from resolution: {e}")
            return False
    
    def _generate_pattern_id(self, symptoms: List[str]) -> str:
        """Generate a pattern ID based on symptom combination"""
        # Sort symptoms for consistent ID generation
        sorted_symptoms = sorted(symptoms)
        
        # Create a shorter, readable ID
        if len(sorted_symptoms) <= 3:
            return "_".join(sorted_symptoms)
        else:
            # For longer symptom lists, use a hash-based approach
            import hashlib
            symptom_string = "_".join(sorted_symptoms)
            hash_suffix = hashlib.md5(symptom_string.encode()).hexdigest()[:8]
            return f"pattern_{hash_suffix}"
    
    async def _update_pattern_from_success(self, symptoms: List[str], actions: List[str], resolution_time: float):
        """Update pattern database with successful resolution"""
        pattern_id = self._generate_pattern_id(symptoms)
        
        if pattern_id in self.learned_patterns:
            # Update existing pattern
            pattern = self.learned_patterns[pattern_id]
            pattern["frequency"] += 1
            pattern["last_updated"] = datetime.now()
            
            # Add to successful resolutions if not already present
            if actions not in pattern["successful_resolutions"]:
                pattern["successful_resolutions"].append(actions)
            
            # Update average resolution time
            current_avg = pattern["avg_resolution_time"]
            pattern["avg_resolution_time"] = (current_avg + resolution_time) / 2
            
            # Update success rate tracking
            self.pattern_success_rates[pattern_id].append(True)
            
        else:
            # Create new pattern
            self.learned_patterns[pattern_id] = {
                "symptoms": symptoms,
                "root_causes": [],  # Will be inferred over time
                "successful_resolutions": [actions],
                "frequency": 1,
                "success_rate": 1.0,
                "avg_resolution_time": resolution_time,
                "last_updated": datetime.now()
            }
            
            self.pattern_success_rates[pattern_id] = [True]
        
        # Recalculate success rate
        self._recalculate_success_rate(pattern_id)
    
    async def _update_pattern_from_failure(self, symptoms: List[str], actions: List[str]):
        """Update pattern database with failed resolution"""
        pattern_id = self._generate_pattern_id(symptoms)
        
        # Record failure in success rate tracking
        self.pattern_success_rates[pattern_id].append(False)
        
        if pattern_id in self.learned_patterns:
            # Update frequency but not successful resolutions
            self.learned_patterns[pattern_id]["frequency"] += 1
            
            # Recalculate success rate
            self._recalculate_success_rate(pattern_id)
    
    def _recalculate_success_rate(self, pattern_id: str):
        """Recalculate success rate for a pattern"""
        success_history = self.pattern_success_rates.get(pattern_id, [])
        
        if success_history:
            success_rate = sum(success_history) / len(success_history)
            if pattern_id in self.learned_patterns:
                self.learned_patterns[pattern_id]["success_rate"] = success_rate
    
    def get_pattern_analytics(self) -> Dict[str, Any]:
        """Get analytics about learned patterns"""
        analytics = {
            "total_patterns": len(self.learned_patterns),
            "total_resolutions": len(self.resolution_outcomes),
            "success_rate": 0.0,
            "pattern_performance": {},
            "top_patterns": [],
            "learning_trends": {}
        }
        
        if self.resolution_outcomes:
            successful_resolutions = [r for r in self.resolution_outcomes if r.success]
            analytics["success_rate"] = len(successful_resolutions) / len(self.resolution_outcomes)
        
        # Pattern performance
        for pattern_id, pattern_data in self.learned_patterns.items():
            analytics["pattern_performance"][pattern_id] = {
                "frequency": pattern_data["frequency"],
                "success_rate": pattern_data["success_rate"],
                "avg_resolution_time": pattern_data["avg_resolution_time"],
                "days_since_update": (datetime.now() - pattern_data["last_updated"]).days
            }
        
        # Top patterns by frequency and success rate
        patterns_by_score = []
        for pattern_id, perf in analytics["pattern_performance"].items():
            score = perf["frequency"] * perf["success_rate"]
            patterns_by_score.append((pattern_id, score, perf))
        
        patterns_by_score.sort(key=lambda x: x[1], reverse=True)
        analytics["top_patterns"] = [
            {"pattern_id": pid, "score": score, "performance": perf}
            for pid, score, perf in patterns_by_score[:5]
        ]
        
        return analytics
    
    def export_patterns(self) -> Dict[str, Any]:
        """Export learned patterns for backup or transfer"""
        export_data = {
            "patterns": {},
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_patterns": len(self.learned_patterns),
                "total_resolutions": len(self.resolution_outcomes)
            }
        }
        
        # Convert patterns to serializable format
        for pattern_id, pattern_data in self.learned_patterns.items():
            pattern_copy = pattern_data.copy()
            # Convert datetime to ISO string
            if isinstance(pattern_copy.get("last_updated"), datetime):
                pattern_copy["last_updated"] = pattern_copy["last_updated"].isoformat()
            
            export_data["patterns"][pattern_id] = pattern_copy
        
        return export_data
    
    def import_patterns(self, pattern_data: Dict[str, Any]) -> bool:
        """Import patterns from backup or external source"""
        try:
            imported_patterns = pattern_data.get("patterns", {})
            
            for pattern_id, pattern_info in imported_patterns.items():
                # Convert ISO string back to datetime
                if isinstance(pattern_info.get("last_updated"), str):
                    pattern_info["last_updated"] = datetime.fromisoformat(pattern_info["last_updated"])
                
                self.learned_patterns[pattern_id] = pattern_info
            
            self.logger.info(f"Imported {len(imported_patterns)} patterns")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import patterns: {e}")
            return False 