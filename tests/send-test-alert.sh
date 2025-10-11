#!/bin/bash

# Send Test Alert Script
# Sends a test alert to the webhook service to trigger agent investigation
# This bypasses AlertManager and directly calls the webhook endpoint

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DevOps RCA Agent - Test Alert Sender${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Configuration
NAMESPACE="${NAMESPACE:-analysis-agent}"
WEBHOOK_SERVICE="${WEBHOOK_SERVICE:-webhook-service}"
WEBHOOK_PORT="${WEBHOOK_PORT:-8080}"

# Check if webhook service is available
echo -e "${YELLOW}[1/4]${NC} Checking webhook service..."
if ! kubectl get svc "$WEBHOOK_SERVICE" -n "$NAMESPACE" &>/dev/null; then
    echo -e "${RED}✗ Webhook service not found in namespace '$NAMESPACE'${NC}"
    echo "Deploy the service first: kubectl apply -f manifests/deployments/webhook-deployment.yaml"
    exit 1
fi
echo -e "${GREEN}✓ Webhook service found${NC}"

# Get webhook endpoint
WEBHOOK_URL="http://${WEBHOOK_SERVICE}.${NAMESPACE}.svc.cluster.local:${WEBHOOK_PORT}/api/v1/webhook/test"

# Prompt for alert details
echo ""
echo -e "${YELLOW}[2/4]${NC} Configure test alert..."

# Alert name
read -p "Alert name [KubePodCrashLooping]: " ALERT_NAME
ALERT_NAME="${ALERT_NAME:-KubePodCrashLooping}"

# Severity
echo "Severity options: critical, warning, info"
read -p "Severity [critical]: " SEVERITY
SEVERITY="${SEVERITY:-critical}"

# Namespace
read -p "Affected namespace [production]: " AFFECTED_NS
AFFECTED_NS="${AFFECTED_NS:-production}"

# Pod name
read -p "Pod name [test-app-7d4f8-x9k2m]: " POD_NAME
POD_NAME="${POD_NAME:-test-app-7d4f8-x9k2m}"

# Description
read -p "Description [Pod is crash looping]: " DESCRIPTION
DESCRIPTION="${DESCRIPTION:-Pod is crash looping}"

# Build test alert JSON (AlertManager v4 format)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

TEST_ALERT_JSON=$(cat <<EOF
{
  "version": "4",
  "groupKey": "test-group-key",
  "status": "firing",
  "receiver": "devops-rca-agent",
  "groupLabels": {
    "alertname": "${ALERT_NAME}"
  },
  "commonLabels": {
    "alertname": "${ALERT_NAME}",
    "severity": "${SEVERITY}",
    "namespace": "${AFFECTED_NS}",
    "pod": "${POD_NAME}"
  },
  "commonAnnotations": {
    "description": "${DESCRIPTION}",
    "summary": "Test alert for ${ALERT_NAME}"
  },
  "externalURL": "http://alertmanager:9093",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "${ALERT_NAME}",
        "severity": "${SEVERITY}",
        "namespace": "${AFFECTED_NS}",
        "pod": "${POD_NAME}",
        "job": "kubernetes-pods",
        "instance": "test-instance"
      },
      "annotations": {
        "description": "${DESCRIPTION}",
        "summary": "Test alert for ${ALERT_NAME}",
        "runbook_url": "https://runbooks.example.com/${ALERT_NAME}"
      },
      "startsAt": "${TIMESTAMP}",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph?g0.expr=test",
      "fingerprint": "test-$(date +%s)"
    }
  ]
}
EOF
)

# Display alert summary
echo ""
echo -e "${YELLOW}[3/4]${NC} Alert summary:"
echo -e "  Alert Name:  ${BLUE}${ALERT_NAME}${NC}"
echo -e "  Severity:    ${BLUE}${SEVERITY}${NC}"
echo -e "  Namespace:   ${BLUE}${AFFECTED_NS}${NC}"
echo -e "  Pod:         ${BLUE}${POD_NAME}${NC}"
echo -e "  Description: ${BLUE}${DESCRIPTION}${NC}"
echo ""

# Confirm before sending
read -p "Send this test alert? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

# Send alert to webhook
echo ""
echo -e "${YELLOW}[4/4]${NC} Sending test alert..."

# Create temporary pod to send the request from inside the cluster
TEMP_POD="test-alert-sender-$$"

kubectl run "$TEMP_POD" -n "$NAMESPACE" --rm -i --restart=Never --image=curlimages/curl:latest -- \
    curl -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$TEST_ALERT_JSON" \
    --max-time 10 \
    --silent \
    --show-error \
    --write-out "\nHTTP Status: %{http_code}\n"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Test alert sent successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Monitor webhook logs:"
    echo -e "   ${YELLOW}kubectl logs -f -n $NAMESPACE -l app=webhook-service${NC}"
    echo ""
    echo "2. Check agent is investigating (wait 1-2 minutes):"
    echo -e "   ${YELLOW}kubectl logs -n kagent-system -l app=kagent-operator${NC}"
    echo ""
    echo "3. Check for email notification (if configured)"
    echo ""
    echo "4. View agent memory for saved reports:"
    echo -e "   ${YELLOW}kubectl exec -it -n $NAMESPACE <agent-pod> -- ls -la /agent-memory/reports/${NC}"
else
    echo -e "${RED}✗ Failed to send test alert (exit code: $EXIT_CODE)${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check webhook service is running:"
    echo -e "   ${YELLOW}kubectl get pods -n $NAMESPACE -l app=webhook-service${NC}"
    echo ""
    echo "2. Check webhook logs for errors:"
    echo -e "   ${YELLOW}kubectl logs -n $NAMESPACE -l app=webhook-service --tail=50${NC}"
    echo ""
    echo "3. Verify service endpoint:"
    echo -e "   ${YELLOW}kubectl get svc $WEBHOOK_SERVICE -n $NAMESPACE${NC}"
    exit 1
fi

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
