"""
Notifier Service for Kagent DevOps RCA Agent

Receives incident reports and sends styled HTML email notifications via Gmail SMTP.
Routes emails based on alert severity (critical, warning, info).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import markdown
from markdown.extensions import fenced_code, tables, nl2br

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="DevOps RCA Notifier Service",
    description="Email notification service for incident reports",
    version="0.1.0"
)


# Request models
class NotifyRequest(BaseModel):
    """Request model for sending incident notifications."""
    alert_name: str = Field(..., description="Name of the alert")
    severity: str = Field(..., description="Alert severity: critical, warning, or info")
    report_markdown: str = Field(..., description="Incident report in markdown format")
    namespace: Optional[str] = Field(None, description="Kubernetes namespace")


class TestEmailRequest(BaseModel):
    """Request model for testing email functionality."""
    recipients: List[str] = Field(..., description="List of recipient email addresses")
    test_message: Optional[str] = Field("Test email from DevOps RCA Notifier", description="Test message")


# Configuration from environment
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', SMTP_USER)

# Recipient configuration based on severity
RECIPIENTS_CRITICAL = os.environ.get('RECIPIENTS_CRITICAL', '').split(',')
RECIPIENTS_WARNING = os.environ.get('RECIPIENTS_WARNING', '').split(',')
RECIPIENTS_INFO = os.environ.get('RECIPIENTS_INFO', '').split(',')

# Filter empty strings from recipient lists
RECIPIENTS_CRITICAL = [r.strip() for r in RECIPIENTS_CRITICAL if r.strip()]
RECIPIENTS_WARNING = [r.strip() for r in RECIPIENTS_WARNING if r.strip()]
RECIPIENTS_INFO = [r.strip() for r in RECIPIENTS_INFO if r.strip()]


def get_recipients_for_severity(severity: str) -> List[str]:
    """
    Get email recipients based on alert severity.

    Args:
        severity: Alert severity (critical, warning, info)

    Returns:
        List of recipient email addresses
    """
    severity_lower = severity.lower()

    if severity_lower == 'critical':
        return RECIPIENTS_CRITICAL
    elif severity_lower == 'warning':
        return RECIPIENTS_WARNING
    elif severity_lower == 'info':
        return RECIPIENTS_INFO
    else:
        logger.warning(f"Unknown severity '{severity}', using WARNING recipients")
        return RECIPIENTS_WARNING


def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to styled HTML for email.

    Args:
        markdown_text: Markdown content

    Returns:
        Styled HTML string
    """
    # Convert markdown to HTML with extensions
    html_content = markdown.markdown(
        markdown_text,
        extensions=['fenced_code', 'tables', 'nl2br']
    )

    # Wrap in styled HTML template
    styled_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incident Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #d32f2f;
            border-bottom: 3px solid #d32f2f;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #1976d2;
            border-bottom: 2px solid #1976d2;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #388e3c;
            margin-top: 20px;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #d32f2f;
        }}
        pre {{
            background-color: #263238;
            color: #aed581;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border-left: 4px solid #1976d2;
        }}
        pre code {{
            background-color: transparent;
            color: #aed581;
            padding: 0;
        }}
        ul, ol {{
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        strong {{
            color: #1976d2;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #e0e0e0;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #1976d2;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f5f5f5;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        .severity-critical {{
            background-color: #d32f2f;
            color: white;
        }}
        .severity-warning {{
            background-color: #f57c00;
            color: white;
        }}
        .severity-info {{
            background-color: #1976d2;
            color: white;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #757575;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <div class="footer">
            <p>Generated by DevOps RCA Agent | Kagent Framework</p>
            <p>This is an automated incident report. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    return styled_html


def send_email(recipients: List[str], subject: str, html_content: str) -> None:
    """
    Send HTML email via SMTP.

    Args:
        recipients: List of recipient email addresses
        subject: Email subject line
        html_content: HTML content for email body

    Raises:
        Exception: If email sending fails
    """
    if not recipients:
        raise ValueError("No recipients specified")

    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP credentials not configured (SMTP_USER and SMTP_PASSWORD required)")

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = ', '.join(recipients)

    # Attach HTML content
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)

    # Send email
    try:
        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            logger.info(f"Logging in as {SMTP_USER}")
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info(f"Sending email to {len(recipients)} recipient(s)")
            server.send_message(msg)
            logger.info("Email sent successfully")
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed - check credentials")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {
        "status": "healthy",
        "service": "notifier",
        "timestamp": datetime.utcnow().isoformat(),
        "smtp_configured": bool(SMTP_USER and SMTP_PASSWORD)
    }


@app.post("/api/v1/notify")
async def send_notification(request: NotifyRequest):
    """
    Send incident report notification via email.

    Args:
        request: Notification request with alert details and markdown report

    Returns:
        Success response with sent details
    """
    logger.info(f"Received notification request for alert: {request.alert_name}")
    logger.info(f"Severity: {request.severity}, Namespace: {request.namespace}")

    # Get recipients based on severity
    recipients = get_recipients_for_severity(request.severity)

    if not recipients:
        logger.error(f"No recipients configured for severity: {request.severity}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No recipients configured for severity '{request.severity}'"
        )

    # Build email subject
    severity_upper = request.severity.upper()
    namespace_str = f" ({request.namespace})" if request.namespace else ""
    subject = f"[{severity_upper}] {request.alert_name}{namespace_str}"

    # Convert markdown to HTML
    try:
        html_content = markdown_to_html(request.report_markdown)
    except Exception as e:
        logger.error(f"Failed to convert markdown to HTML: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process report: {e}"
        )

    # Send email
    try:
        send_email(recipients, subject, html_content)
        logger.info(f"Notification sent successfully to {len(recipients)} recipient(s)")

        return {
            "success": True,
            "alert_name": request.alert_name,
            "severity": request.severity,
            "recipients": recipients,
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@app.post("/api/v1/test-email")
async def send_test_email(request: TestEmailRequest):
    """
    Send a test email to verify SMTP configuration.

    Args:
        request: Test email request with recipients

    Returns:
        Success response
    """
    logger.info(f"Sending test email to {len(request.recipients)} recipient(s)")

    # Build test email content
    test_markdown = f"""
# Test Email

{request.test_message}

## Configuration Test

This is a test email from the DevOps RCA Notifier Service.

**Timestamp:** {datetime.utcnow().isoformat()}

**Recipients:** {', '.join(request.recipients)}

**SMTP Server:** {SMTP_HOST}:{SMTP_PORT}

**From:** {SMTP_FROM}

---

If you received this email, your notifier service is configured correctly!

## Sample Incident Report Format

### Executive Summary
This is what a real incident report would look like.

### Timeline
- 14:00 - Event 1
- 14:01 - Event 2
- 14:02 - Alert fired

### Root Cause
**Primary Cause:** Test scenario

### Solutions

#### Immediate Fix
```bash
kubectl get pods
```

#### Root Fix
1. Step one
2. Step two

---

**Generated by:** DevOps RCA Notifier Service v0.1.0
"""

    html_content = markdown_to_html(test_markdown)

    try:
        send_email(request.recipients, "[TEST] DevOps RCA Notifier", html_content)
        logger.info("Test email sent successfully")

        return {
            "success": True,
            "recipients": request.recipients,
            "message": "Test email sent successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )


@app.get("/api/v1/config")
async def get_config():
    """
    Get notifier service configuration (for debugging).

    Returns:
        Current configuration (without sensitive data)
    """
    return {
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER,
        "smtp_from": SMTP_FROM,
        "smtp_configured": bool(SMTP_USER and SMTP_PASSWORD),
        "recipients": {
            "critical": RECIPIENTS_CRITICAL if RECIPIENTS_CRITICAL else ["Not configured"],
            "warning": RECIPIENTS_WARNING if RECIPIENTS_WARNING else ["Not configured"],
            "info": RECIPIENTS_INFO if RECIPIENTS_INFO else ["Not configured"]
        },
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn

    # Validate configuration
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured! Service will start but emails will fail.")
        logger.warning("Set SMTP_USER and SMTP_PASSWORD environment variables.")

    if not any([RECIPIENTS_CRITICAL, RECIPIENTS_WARNING, RECIPIENTS_INFO]):
        logger.warning("No recipients configured! Set RECIPIENTS_CRITICAL, RECIPIENTS_WARNING, or RECIPIENTS_INFO.")

    # Run server
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting notifier service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
