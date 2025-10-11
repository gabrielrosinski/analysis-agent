# Webhook Service

Lightweight FastAPI service that receives AlertManager webhooks and triggers the Kagent AI agent for root cause analysis.

## Purpose

This service acts as a bridge between Prometheus AlertManager and the Kagent agent:
1. Receives webhook notifications when alerts fire
2. Parses and validates alert data
3. Deduplicates alerts (5-minute TTL)
4. Triggers the Kagent agent with a detailed investigation prompt
5. Returns response to AlertManager

## API Endpoints

### `GET /health`
Health check endpoint for Kubernetes liveness/readiness probes.

### `POST /api/v1/webhook/alertmanager`
Main webhook endpoint for AlertManager. Expects AlertManager v4 webhook format.

### `POST /api/v1/webhook/test`
Test endpoint for manual alert submission without AlertManager.

## Configuration

Environment variables:
- `KAGENT_API_URL` - URL to Kagent agent API (default: internal cluster service)
- `LOG_LEVEL` - Logging level (default: INFO)
- `PORT` - Service port (default: 8080)

## Building

```bash
docker build -t your-dockerhub/analysis-agent-webhook:v0.1.0 .
docker push your-dockerhub/analysis-agent-webhook:v0.1.0
```

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Test endpoint
curl -X POST http://localhost:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "alert"}'
```

## Alert Deduplication

The service maintains an in-memory cache of recent alert fingerprints with a 5-minute TTL to prevent duplicate processing of the same alert.

## Integration with AlertManager

AlertManager should be configured to send webhooks to:
```
http://webhook-service.analysis-agent.svc.cluster.local:8080/api/v1/webhook/alertmanager
```

See `manifests/alertmanager-config.yaml` for configuration example.
