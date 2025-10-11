# Notifier Service

FastAPI-based email notification service for DevOps RCA incident reports. Converts markdown reports to styled HTML emails and sends them via Gmail SMTP with severity-based routing.

## Purpose

This service:
1. Receives incident reports in markdown format via HTTP POST
2. Converts markdown to beautifully styled HTML
3. Routes emails based on severity (critical/warning/info)
4. Sends notifications via Gmail SMTP
5. Provides test endpoints for verification

## Features

- **Markdown to HTML**: Rich formatting with syntax highlighting for code blocks
- **Styled Templates**: Professional email design with severity-based colors
- **Severity Routing**: Different recipients for critical, warning, and info alerts
- **Gmail Integration**: Uses Gmail SMTP with app passwords
- **Health Checks**: Kubernetes-ready liveness/readiness probes
- **Test Endpoint**: Verify email configuration before production
- **HA Ready**: Stateless design supports multiple replicas

## API Endpoints

### `GET /health`
Health check endpoint for Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "service": "notifier",
  "timestamp": "2025-10-11T14:30:00.000Z",
  "smtp_configured": true
}
```

### `POST /api/v1/notify`
Send incident report notification.

**Request:**
```json
{
  "alert_name": "KubePodCrashLooping",
  "severity": "critical",
  "namespace": "production",
  "report_markdown": "# Incident Report\n\n..."
}
```

**Response:**
```json
{
  "success": true,
  "alert_name": "KubePodCrashLooping",
  "severity": "critical",
  "recipients": ["oncall@example.com"],
  "subject": "[CRITICAL] KubePodCrashLooping (production)",
  "timestamp": "2025-10-11T14:30:00.000Z"
}
```

### `POST /api/v1/test-email`
Send test email to verify SMTP configuration.

**Request:**
```json
{
  "recipients": ["your-email@example.com"],
  "test_message": "Testing notifier service"
}
```

**Response:**
```json
{
  "success": true,
  "recipients": ["your-email@example.com"],
  "message": "Test email sent successfully",
  "timestamp": "2025-10-11T14:30:00.000Z"
}
```

### `GET /api/v1/config`
Get current configuration (for debugging).

**Response:**
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your-email@gmail.com",
  "smtp_configured": true,
  "recipients": {
    "critical": ["oncall@example.com"],
    "warning": ["devops@example.com"],
    "info": ["devops-alerts@example.com"]
  },
  "version": "0.1.0"
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SMTP_HOST` | SMTP server hostname | No | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | No | `587` |
| `SMTP_USER` | SMTP username (Gmail address) | Yes | - |
| `SMTP_PASSWORD` | SMTP password (Gmail app password) | Yes | - |
| `SMTP_FROM` | From address for emails | No | Same as `SMTP_USER` |
| `RECIPIENTS_CRITICAL` | Comma-separated critical alert recipients | Yes | - |
| `RECIPIENTS_WARNING` | Comma-separated warning alert recipients | Yes | - |
| `RECIPIENTS_INFO` | Comma-separated info alert recipients | Yes | - |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No | `INFO` |
| `PORT` | Service port | No | `8080` |

### Gmail Setup

**1. Enable 2-Factor Authentication**
- Go to: https://myaccount.google.com/security
- Enable 2FA on your Gmail account

**2. Generate App Password**
- Go to: https://myaccount.google.com/apppasswords
- Select "Mail" and "Other (Custom name)"
- Name it "DevOps RCA Agent"
- Copy the 16-character password

**3. Configure Secret**
Edit `manifests/secrets.yaml`:
```yaml
stringData:
  username: "your-email@gmail.com"
  password: "xxxx xxxx xxxx xxxx"  # App password from step 2
  from-address: "DevOps RCA Agent <your-email@gmail.com>"
```

**4. Apply Secret**
```bash
kubectl apply -f manifests/secrets.yaml
```

## Building

```bash
cd services/notifier

# Build image
docker build -t your-dockerhub/analysis-agent-notifier:v0.1.0 .

# Push to registry
docker push your-dockerhub/analysis-agent-notifier:v0.1.0

# Update deployment manifest
# Edit manifests/deployments/notifier-deployment.yaml
# Change image: your-dockerhub/analysis-agent-notifier:v0.1.0
```

## Testing Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export RECIPIENTS_CRITICAL="oncall@example.com"
export RECIPIENTS_WARNING="devops@example.com"
export RECIPIENTS_INFO="devops-alerts@example.com"
```

### 3. Run Service
```bash
python main.py
```

### 4. Test with curl
```bash
# Test health endpoint
curl http://localhost:8080/health

# Send test email
curl -X POST http://localhost:8080/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["your-test-email@example.com"]}'

# Send mock incident report
curl -X POST http://localhost:8080/api/v1/notify \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "TestAlert",
    "severity": "warning",
    "namespace": "test",
    "report_markdown": "# Test Incident\n\n## Summary\nThis is a test incident report.\n\n## Root Cause\nTesting the notifier service.\n\n## Solutions\n```bash\nkubectl get pods\n```"
  }'
```

## Testing in Kubernetes

### 1. Port Forward
```bash
kubectl port-forward svc/notifier-service 8080:8080 -n analysis-agent
```

### 2. Test Endpoints
```bash
# Health check
curl http://localhost:8080/health

# Configuration check
curl http://localhost:8080/api/v1/config

# Send test email
curl -X POST http://localhost:8080/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["your-email@example.com"]}'
```

### 3. Check Logs
```bash
kubectl logs -f -n analysis-agent -l app=notifier-service
```

## Email Styling

Emails are styled with:
- **Professional Layout**: Clean, centered design with max-width
- **Severity Colors**: Red (critical), Orange (warning), Blue (info)
- **Code Highlighting**: Dark background for code blocks
- **Responsive Design**: Mobile-friendly layout
- **Branded Footer**: DevOps RCA Agent branding

### Example Email

**Subject:** `[CRITICAL] KubePodCrashLooping (production)`

**Body:**
- Executive summary at the top
- Color-coded headings (blue for sections, green for subsections)
- Syntax-highlighted code blocks
- Timeline with bullet points
- Solutions with exact commands
- Professional footer

## Severity Routing

| Severity | Recipients | Use Case |
|----------|-----------|----------|
| **critical** | `RECIPIENTS_CRITICAL` | Production outages, data loss, security incidents |
| **warning** | `RECIPIENTS_WARNING` | Degraded performance, non-critical failures |
| **info** | `RECIPIENTS_INFO` | Informational alerts, resolved incidents |

## Troubleshooting

### Email Not Sending

**Check SMTP Credentials:**
```bash
kubectl get secret gmail-credentials -n analysis-agent -o yaml
kubectl describe secret gmail-credentials -n analysis-agent
```

**Test SMTP Connection:**
```bash
kubectl port-forward svc/notifier-service 8080:8080 -n analysis-agent

curl -X POST http://localhost:8080/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["your-email@example.com"]}'
```

**Check Logs for Errors:**
```bash
kubectl logs -n analysis-agent -l component=notifier-service --tail=100
```

**Common Errors:**

1. **"SMTP authentication failed"**
   - Check app password is correct (not regular Gmail password)
   - Verify 2FA is enabled on Gmail account
   - Regenerate app password

2. **"No recipients configured"**
   - Check `email-recipients` secret is applied
   - Verify recipients are comma-separated
   - Check secret values: `kubectl get secret email-recipients -n analysis-agent -o yaml`

3. **"Failed to connect to SMTP server"**
   - Check network connectivity from pod
   - Verify firewall allows outbound port 587
   - Try alternative SMTP port (465 for SSL)

### Gmail App Password Not Working

1. Ensure 2FA is enabled first
2. Regenerate app password
3. Remove spaces from app password in secret
4. Try using port 465 instead of 587

### No Recipients Configured

Edit `manifests/secrets.yaml` and add recipients:
```yaml
stringData:
  recipients-critical: "oncall@example.com,sre@example.com"
```

Re-apply secret and restart pods:
```bash
kubectl apply -f manifests/secrets.yaml
kubectl rollout restart deployment/notifier-service -n analysis-agent
```

## Security Considerations

- **App Passwords**: Use Gmail app passwords, not regular passwords
- **Secret Management**: Never commit `secrets.yaml` with real credentials to Git
- **RBAC**: Limit access to secrets with Kubernetes RBAC
- **Read-Only Filesystem**: Container runs with read-only root filesystem
- **Non-Root User**: Runs as UID 1000 (notifier user)
- **TLS**: Uses STARTTLS for SMTP encryption

## Alternative SMTP Providers

While this service is configured for Gmail, it works with any SMTP provider:

### SendGrid
```yaml
SMTP_HOST: smtp.sendgrid.net
SMTP_PORT: 587
SMTP_USER: apikey
SMTP_PASSWORD: <sendgrid-api-key>
```

### AWS SES
```yaml
SMTP_HOST: email-smtp.us-east-1.amazonaws.com
SMTP_PORT: 587
SMTP_USER: <aws-smtp-username>
SMTP_PASSWORD: <aws-smtp-password>
```

### Office 365
```yaml
SMTP_HOST: smtp.office365.com
SMTP_PORT: 587
SMTP_USER: your-email@company.com
SMTP_PASSWORD: <password>
```

## Integration with Agent

The agent calls the notifier service after generating a report:

```bash
curl -X POST http://notifier-service.analysis-agent.svc.cluster.local:8080/api/v1/notify \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "<alert_name>",
    "severity": "<severity>",
    "report_markdown": "<full_report>",
    "namespace": "<namespace>"
  }'
```

## Future Enhancements

- **Slack Integration**: Send notifications to Slack channels
- **Microsoft Teams**: Support Teams webhooks
- **PagerDuty**: Integrate with incident management
- **Attachment Support**: Attach logs or metrics graphs
- **Template Customization**: User-configurable email templates
- **Rate Limiting**: Prevent email flooding
- **Retry Logic**: Automatic retries on SMTP failures

---

**Version:** 0.1.0

**Last Updated:** 2025-10-11
