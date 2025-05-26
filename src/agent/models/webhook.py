"""Webhook models for receiving alerts from Alertmanager."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class AlertLabel(BaseModel):
    """Alert labels from Prometheus/Alertmanager."""
    
    alertname: str = Field(..., description="Name of the alert")
    instance: Optional[str] = Field(None, description="Instance that triggered the alert")
    job: Optional[str] = Field(None, description="Job name")
    severity: Optional[str] = Field(None, description="Alert severity")
    service: Optional[str] = Field(None, description="Service name")


class AlertAnnotation(BaseModel):
    """Alert annotations from Prometheus/Alertmanager."""
    
    summary: Optional[str] = Field(None, description="Alert summary")
    description: Optional[str] = Field(None, description="Alert description")
    runbook_url: Optional[str] = Field(None, description="Runbook URL")


class Alert(BaseModel):
    """Individual alert from Alertmanager."""
    
    status: str = Field(..., description="Alert status (firing/resolved)")
    labels: Dict[str, Any] = Field(..., description="Alert labels")
    annotations: Dict[str, Any] = Field(default_factory=dict, description="Alert annotations")
    starts_at: datetime = Field(..., alias="startsAt", description="Alert start time")
    ends_at: Optional[datetime] = Field(None, alias="endsAt", description="Alert end time")
    generator_url: Optional[str] = Field(None, alias="generatorURL", description="Generator URL")
    fingerprint: Optional[str] = Field(None, description="Alert fingerprint")


class AlertmanagerWebhook(BaseModel):
    """Alertmanager webhook payload."""
    
    version: str = Field(..., description="Webhook version")
    group_key: str = Field(..., alias="groupKey", description="Group key")
    truncated_alerts: Optional[int] = Field(None, alias="truncatedAlerts", description="Number of truncated alerts")
    status: str = Field(..., description="Group status")
    receiver: str = Field(..., description="Receiver name")
    group_labels: Dict[str, Any] = Field(..., alias="groupLabels", description="Group labels")
    common_labels: Dict[str, Any] = Field(..., alias="commonLabels", description="Common labels")
    common_annotations: Dict[str, Any] = Field(..., alias="commonAnnotations", description="Common annotations")
    external_url: str = Field(..., alias="externalURL", description="External URL")
    alerts: List[Alert] = Field(..., description="List of alerts")


class WebhookResponse(BaseModel):
    """Response to webhook requests."""
    
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Response message")
    alerts_processed: int = Field(..., description="Number of alerts processed")
    actions_triggered: int = Field(default=0, description="Number of actions triggered")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp") 