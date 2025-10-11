#!/bin/bash

# Verify Agent Installation Script
# Checks all components of the DevOps RCA system are deployed and healthy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Configuration
NAMESPACE="${NAMESPACE:-analysis-agent}"
KAGENT_NAMESPACE="${KAGENT_NAMESPACE:-kagent-system}"

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DevOps RCA Agent - System Verification${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Helper functions
check_passed() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_failed() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((CHECKS_WARNING++))
}

# 1. Check namespace exists
echo -e "${BLUE}[1] Checking namespace...${NC}"
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    check_passed "Namespace '$NAMESPACE' exists"
else
    check_failed "Namespace '$NAMESPACE' not found"
    echo "   Create with: kubectl apply -f manifests/namespace.yaml"
fi
echo ""

# 2. Check RBAC resources
echo -e "${BLUE}[2] Checking RBAC resources...${NC}"
if kubectl get serviceaccount webhook-sa -n "$NAMESPACE" &>/dev/null; then
    check_passed "ServiceAccount 'webhook-sa' exists"
else
    check_failed "ServiceAccount 'webhook-sa' not found"
fi

if kubectl get serviceaccount notifier-sa -n "$NAMESPACE" &>/dev/null; then
    check_passed "ServiceAccount 'notifier-sa' exists"
else
    check_failed "ServiceAccount 'notifier-sa' not found"
fi

if kubectl get serviceaccount agent-sa -n "$NAMESPACE" &>/dev/null; then
    check_passed "ServiceAccount 'agent-sa' exists"
else
    check_failed "ServiceAccount 'agent-sa' not found"
fi

if kubectl get clusterrole devops-rca-agent-role &>/dev/null; then
    check_passed "ClusterRole 'devops-rca-agent-role' exists"
else
    check_failed "ClusterRole 'devops-rca-agent-role' not found"
fi

if kubectl get clusterrolebinding devops-rca-agent-binding &>/dev/null; then
    check_passed "ClusterRoleBinding exists"
else
    check_failed "ClusterRoleBinding not found"
fi
echo ""

# 3. Check storage
echo -e "${BLUE}[3] Checking persistent storage...${NC}"
if kubectl get pvc agent-memory-pvc -n "$NAMESPACE" &>/dev/null; then
    PVC_STATUS=$(kubectl get pvc agent-memory-pvc -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    if [ "$PVC_STATUS" = "Bound" ]; then
        check_passed "PVC 'agent-memory-pvc' is Bound"
    else
        check_warning "PVC 'agent-memory-pvc' exists but status is: $PVC_STATUS"
    fi
else
    check_failed "PVC 'agent-memory-pvc' not found"
fi
echo ""

# 4. Check secrets
echo -e "${BLUE}[4] Checking secrets...${NC}"
if kubectl get secret gmail-credentials -n "$NAMESPACE" &>/dev/null; then
    check_passed "Secret 'gmail-credentials' exists"
    # Check if it has the required keys
    if kubectl get secret gmail-credentials -n "$NAMESPACE" -o jsonpath='{.data.username}' &>/dev/null && \
       kubectl get secret gmail-credentials -n "$NAMESPACE" -o jsonpath='{.data.password}' &>/dev/null; then
        check_passed "Gmail credentials have required keys"
    else
        check_warning "Gmail credentials missing some keys"
    fi
else
    check_warning "Secret 'gmail-credentials' not found (emails will not work)"
fi

if kubectl get secret email-recipients -n "$NAMESPACE" &>/dev/null; then
    check_passed "Secret 'email-recipients' exists"
else
    check_warning "Secret 'email-recipients' not found (emails will not work)"
fi

if kubectl get secret github-credentials -n "$NAMESPACE" &>/dev/null; then
    check_passed "Secret 'github-credentials' exists (optional)"
else
    check_warning "Secret 'github-credentials' not found (optional - GitHub integration disabled)"
fi
echo ""

# 5. Check webhook service
echo -e "${BLUE}[5] Checking webhook service...${NC}"
if kubectl get deployment webhook-service -n "$NAMESPACE" &>/dev/null; then
    check_passed "Deployment 'webhook-service' exists"

    DESIRED=$(kubectl get deployment webhook-service -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment webhook-service -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    READY=${READY:-0}

    if [ "$READY" -eq "$DESIRED" ]; then
        check_passed "Webhook service is ready ($READY/$DESIRED replicas)"
    else
        check_failed "Webhook service not ready ($READY/$DESIRED replicas)"
    fi
else
    check_failed "Deployment 'webhook-service' not found"
fi

if kubectl get svc webhook-service -n "$NAMESPACE" &>/dev/null; then
    check_passed "Service 'webhook-service' exists"
else
    check_failed "Service 'webhook-service' not found"
fi
echo ""

# 6. Check notifier service
echo -e "${BLUE}[6] Checking notifier service...${NC}"
if kubectl get deployment notifier-service -n "$NAMESPACE" &>/dev/null; then
    check_passed "Deployment 'notifier-service' exists"

    DESIRED=$(kubectl get deployment notifier-service -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment notifier-service -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    READY=${READY:-0}

    if [ "$READY" -eq "$DESIRED" ]; then
        check_passed "Notifier service is ready ($READY/$DESIRED replicas)"
    else
        check_failed "Notifier service not ready ($READY/$DESIRED replicas)"
    fi
else
    check_failed "Deployment 'notifier-service' not found"
fi

if kubectl get svc notifier-service -n "$NAMESPACE" &>/dev/null; then
    check_passed "Service 'notifier-service' exists"
else
    check_failed "Service 'notifier-service' not found"
fi
echo ""

# 7. Check Kagent operator
echo -e "${BLUE}[7] Checking Kagent operator...${NC}"
if kubectl get namespace "$KAGENT_NAMESPACE" &>/dev/null; then
    check_passed "Kagent namespace exists"

    if kubectl get pods -n "$KAGENT_NAMESPACE" -l app=kagent-operator &>/dev/null; then
        OPERATOR_PODS=$(kubectl get pods -n "$KAGENT_NAMESPACE" -l app=kagent-operator --no-headers 2>/dev/null | wc -l)
        if [ "$OPERATOR_PODS" -gt 0 ]; then
            check_passed "Kagent operator is running ($OPERATOR_PODS pod(s))"
        else
            check_failed "Kagent operator not running"
        fi
    else
        check_failed "Kagent operator pods not found"
    fi
else
    check_failed "Kagent namespace not found - Install Kagent operator first"
fi
echo ""

# 8. Check agent resource
echo -e "${BLUE}[8] Checking agent...${NC}"
if kubectl get agent devops-rca-agent -n "$NAMESPACE" &>/dev/null; then
    check_passed "Agent 'devops-rca-agent' resource exists"

    # Check agent status (if available)
    AGENT_STATUS=$(kubectl get agent devops-rca-agent -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    if [ "$AGENT_STATUS" = "Running" ]; then
        check_passed "Agent status: Running"
    elif [ "$AGENT_STATUS" = "Unknown" ]; then
        check_warning "Agent status unknown (might be initializing)"
    else
        check_warning "Agent status: $AGENT_STATUS"
    fi
else
    check_failed "Agent 'devops-rca-agent' resource not found"
fi
echo ""

# 9. Check AlertManager integration (optional)
echo -e "${BLUE}[9] Checking AlertManager integration (optional)...${NC}"
if kubectl get namespace monitoring &>/dev/null; then
    check_passed "Monitoring namespace exists"

    if kubectl get statefulset -n monitoring -l app.kubernetes.io/name=alertmanager &>/dev/null; then
        check_passed "AlertManager found in monitoring namespace"
    else
        check_warning "AlertManager not found (optional)"
    fi
else
    check_warning "Monitoring namespace not found (optional)"
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Passed:${NC}   $CHECKS_PASSED"
echo -e "${RED}Failed:${NC}   $CHECKS_FAILED"
echo -e "${YELLOW}Warnings:${NC} $CHECKS_WARNING"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ System verification complete - All critical checks passed!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Initialize agent memory:"
    echo -e "   ${YELLOW}./scripts/init-memory.sh${NC}"
    echo ""
    echo "2. Send a test alert:"
    echo -e "   ${YELLOW}./tests/send-test-alert.sh${NC}"
    echo ""
    echo "3. Monitor webhook logs:"
    echo -e "   ${YELLOW}kubectl logs -f -n $NAMESPACE -l app=webhook-service${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ System verification failed - Fix the errors above${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Missing manifests - Apply all manifests:"
    echo -e "   ${YELLOW}kubectl apply -f manifests/${NC}"
    echo ""
    echo "2. Kagent operator not installed - See docs/KAGENT_INSTALLATION.md"
    echo ""
    echo "3. Services not ready - Check pod logs:"
    echo -e "   ${YELLOW}kubectl logs -n $NAMESPACE -l app=devops-rca${NC}"
    echo ""
    exit 1
fi
