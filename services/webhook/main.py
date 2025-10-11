"""
DevOps RCA Webhook Service

Lightweight FastAPI service that receives AlertManager webhooks
and triggers the Kagent AI agent for investigation.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import httpx
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevOps RCA Webhook Service",
    version="0.1.0",
    description="Receives AlertManager webhooks and triggers RCA agent"
)

# Configuration
KAGENT_API_URL = os.getenv(
    "KAGENT_API_URL",
    "http://kagent-api.analysis-agent.svc.cluster.local/api/v1/agents/devops-rca-agent/invoke"
)

# Simple in-memory cache for alert deduplication (TTL: 5 minutes)
recent_alerts = {}
ALERT_CACHE_TTL = timedelta(minutes=5)


# Pydantic models for AlertManager webhook format
class Alert(BaseModel):
    """Single alert from AlertManager"""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: str


class AlertManagerWebhook(BaseModel):
    """AlertManager webhook payload"""
    version: str
    groupKey: str
    status: str
    receiver: str
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    alerts: List[Alert]


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "DevOps RCA Webhook Service",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "alertmanager_webhook": "/api/v1/webhook/alertmanager",
            "test_webhook": "/api/v1/webhook/test"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "service": "webhook",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/webhook/alertmanager")
async def receive_alertmanager_webhook(webhook: AlertManagerWebhook):
    """
    Main webhook endpoint for AlertManager

    Receives alerts, deduplicates, and triggers agent investigation
    """
    logger.info(f"Received webhook - GroupKey: {webhook.groupKey}, Status: {webhook.status}")
    logger.info(f"Number of alerts: {len(webhook.alerts)}")

    # Clean expired alerts from cache
    cleanup_alert_cache()

    # Process each alert
    results = []
    for alert in webhook.alerts:
        try:
            # Only process firing alerts
            if alert.status != "firing":
                logger.info(f"Skipping non-firing alert: {alert.fingerprint} (status: {alert.status})")
                continue

            # Check for duplicates
            if is_duplicate_alert(alert.fingerprint):
                logger.info(f"Skipping duplicate alert: {alert.fingerprint}")
                continue

            # Mark alert as processed
            recent_alerts[alert.fingerprint] = datetime.utcnow()

            # Log alert details
            alert_name = alert.labels.get('alertname', 'Unknown')
            severity = alert.labels.get('severity', 'unknown')
            namespace = alert.labels.get('namespace', 'unknown')

            logger.info(f"Processing alert: {alert_name}")
            logger.info(f"  Severity: {severity}")
            logger.info(f"  Namespace: {namespace}")
            logger.info(f"  Fingerprint: {alert.fingerprint}")

            # Trigger agent investigation
            result = await trigger_agent_investigation(alert, webhook)
            results.append({
                "fingerprint": alert.fingerprint,
                "alertname": alert_name,
                "status": "triggered",
                "result": result
            })

        except Exception as e:
            logger.error(f"Error processing alert {alert.fingerprint}: {e}", exc_info=True)
            results.append({
                "fingerprint": alert.fingerprint,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "processed",
        "webhook_group": webhook.groupKey,
        "alerts_received": len(webhook.alerts),
        "alerts_processed": len(results),
        "results": results
    }


@app.post("/api/v1/webhook/test")
async def test_webhook(request: Request):
    """
    Test endpoint for manual webhook submissions

    Useful for testing without AlertManager
    """
    body = await request.json()
    logger.info(f"Test webhook received: {body}")

    return {
        "status": "test_received",
        "timestamp": datetime.utcnow().isoformat(),
        "data": body
    }


async def trigger_agent_investigation(alert: Alert, webhook: AlertManagerWebhook):
    """
    Trigger the Kagent agent to investigate an alert

    Args:
        alert: The alert to investigate
        webhook: Full webhook context

    Returns:
        Response from agent invocation
    """
    # Build detailed investigation prompt for the agent
    prompt = build_investigation_prompt(alert, webhook)

    logger.info(f"Triggering agent investigation for alert: {alert.labels.get('alertname', 'Unknown')}")
    logger.debug(f"Agent prompt length: {len(prompt)} characters")

    try:
        # Call Kagent agent API
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                KAGENT_API_URL,
                json={"prompt": prompt},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info("Agent investigation triggered successfully")
            return response.json()

    except httpx.TimeoutException:
        logger.error("Agent investigation timed out (300s)")
        return {"status": "timeout", "error": "Agent investigation timed out"}

    except httpx.HTTPStatusError as e:
        logger.error(f"Agent API returned error status: {e.response.status_code}")
        logger.error(f"Response: {e.response.text}")
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}",
            "details": e.response.text
        }

    except Exception as e:
        logger.error(f"Failed to invoke agent: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def build_investigation_prompt(alert: Alert, webhook: AlertManagerWebhook) -> str:
    """
    Build a detailed investigation prompt for the agent

    Args:
        alert: The alert details
        webhook: Full webhook context

    Returns:
        Formatted prompt string
    """
    alert_name = alert.labels.get('alertname', 'Unknown')
    severity = alert.labels.get('severity', 'unknown')
    namespace = alert.labels.get('namespace', 'unknown')
    pod = alert.labels.get('pod', 'unknown')

    # Format labels
    labels_str = "\n".join([f"  {k}: {v}" for k, v in alert.labels.items()])

    # Format annotations
    annotations_str = "\n".join([f"  {k}: {v}" for k, v in alert.annotations.items()])

    prompt = f"""ALERT RECEIVED - INVESTIGATE AND ANALYZE

Alert Name: {alert_name}
Severity: {severity}
Status: {alert.status}
Started At: {alert.startsAt}
Fingerprint: {alert.fingerprint}

ALERT LABELS:
{labels_str}

ALERT ANNOTATIONS:
{annotations_str}

GENERATOR URL:
{alert.generatorURL}

CONTEXT:
- Namespace: {namespace}
- Pod: {pod}
- Group Key: {webhook.groupKey}

INSTRUCTIONS FOR MVP PHASE:

1. Read your memory files to understand the cluster context
   - Check discovered-tools.md for known services
   - Review known-issues.md for similar past issues
   - Check namespace-map.md for namespace topology

2. Based on the alert type and your knowledge:
   - Identify the likely cause
   - Suggest investigation commands
   - Recommend immediate actions

3. Provide a clear, concise response with:
   - What you know about this service/namespace
   - Likely root causes based on alert type
   - Specific kubectl commands to investigate further
   - Immediate mitigation suggestions

For this MVP phase, focus on analysis and recommendations.
Full automated investigation will be added in Phase 3.

Begin your analysis now.
"""

    return prompt


def is_duplicate_alert(fingerprint: str) -> bool:
    """
    Check if an alert is a duplicate based on fingerprint

    Args:
        fingerprint: Alert fingerprint from AlertManager

    Returns:
        True if alert was recently processed
    """
    if fingerprint in recent_alerts:
        # Check if alert is still within TTL
        alert_time = recent_alerts[fingerprint]
        if datetime.utcnow() - alert_time < ALERT_CACHE_TTL:
            return True
        else:
            # Expired, remove from cache
            del recent_alerts[fingerprint]

    return False


def cleanup_alert_cache():
    """Remove expired alerts from the cache"""
    now = datetime.utcnow()
    expired = [
        fp for fp, timestamp in recent_alerts.items()
        if now - timestamp >= ALERT_CACHE_TTL
    ]

    for fp in expired:
        del recent_alerts[fp]

    if expired:
        logger.debug(f"Cleaned up {len(expired)} expired alerts from cache")


def format_dict(d: Dict) -> str:
    """
    Format dictionary for readable output

    Args:
        d: Dictionary to format

    Returns:
        Formatted string
    """
    return "\n".join([f"  {k}: {v}" for k, v in d.items()])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))

    logger.info(f"Starting webhook service on port {port}")
    logger.info(f"Kagent API URL: {KAGENT_API_URL}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
