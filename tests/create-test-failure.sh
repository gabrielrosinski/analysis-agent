#!/bin/bash

# Create Test Failure Script
# Deploys test failure scenarios to trigger AlertManager alerts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DevOps RCA Agent - Test Failure Creator${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Configuration
TEST_NAMESPACE="${TEST_NAMESPACE:-test-failures}"

# Check kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl not found${NC}"
    echo "Install kubectl first"
    exit 1
fi

# Create test namespace if it doesn't exist
echo -e "${YELLOW}[1/3]${NC} Preparing test namespace..."
if ! kubectl get namespace "$TEST_NAMESPACE" &>/dev/null; then
    kubectl create namespace "$TEST_NAMESPACE"
    kubectl label namespace "$TEST_NAMESPACE" monitoring=enabled
    echo -e "${GREEN}✓ Created namespace: $TEST_NAMESPACE${NC}"
else
    echo -e "${GREEN}✓ Namespace exists: $TEST_NAMESPACE${NC}"
fi
echo ""

# Display available scenarios
echo -e "${YELLOW}[2/3]${NC} Available test scenarios:"
echo ""
echo "1. CrashLoop - Pod that crashes immediately (simulates database connection failure)"
echo "2. OOMKilled - Pod that exceeds memory limits"
echo "3. ImagePullBackOff - Pod with non-existent image"
echo "4. All scenarios - Deploy all test failures"
echo "5. Cleanup - Remove all test failures"
echo ""

# Prompt for scenario selection
read -p "Select scenario (1-5): " SCENARIO

case $SCENARIO in
    1)
        SCENARIO_NAME="crashloop"
        SCENARIO_DESC="CrashLoop"
        ;;
    2)
        SCENARIO_NAME="oom"
        SCENARIO_DESC="OOMKilled"
        ;;
    3)
        SCENARIO_NAME="imagepull"
        SCENARIO_DESC="ImagePullBackOff"
        ;;
    4)
        SCENARIO_NAME="all"
        SCENARIO_DESC="All scenarios"
        ;;
    5)
        # Cleanup
        echo ""
        echo -e "${YELLOW}Cleaning up test failures...${NC}"
        kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true
        echo -e "${GREEN}✓ Cleanup complete${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}✗ Invalid selection${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}[3/3]${NC} Deploying $SCENARIO_DESC scenario..."
echo ""

# Deploy scenario(s)
deploy_scenario() {
    local scenario=$1
    local examples_dir="../examples/${scenario}-scenario"

    if [ ! -d "$examples_dir" ]; then
        echo -e "${RED}✗ Scenario directory not found: $examples_dir${NC}"
        return 1
    fi

    echo -e "${BLUE}Deploying $scenario scenario...${NC}"
    kubectl apply -f "$examples_dir/" -n "$TEST_NAMESPACE"
    echo -e "${GREEN}✓ Deployed $scenario${NC}"
    echo ""
}

if [ "$SCENARIO_NAME" = "all" ]; then
    deploy_scenario "crashloop"
    deploy_scenario "oom"
    deploy_scenario "imagepull"
else
    deploy_scenario "$SCENARIO_NAME"
fi

# Show deployed resources
echo -e "${BLUE}Deployed resources in namespace '$TEST_NAMESPACE':${NC}"
kubectl get pods,deployments -n "$TEST_NAMESPACE"
echo ""

# Instructions
echo -e "${GREEN}✓ Test failure(s) deployed successfully!${NC}"
echo ""
echo -e "${BLUE}What happens next:${NC}"
echo "1. Pods will start failing (30 seconds - 2 minutes)"
echo "2. Prometheus detects the failure"
echo "3. AlertManager fires alert (after evaluation period)"
echo "4. Webhook receives alert and triggers agent"
echo "5. Agent investigates and sends email report"
echo ""
echo -e "${BLUE}Monitor progress:${NC}"
echo ""
echo "Watch pods (should see CrashLoopBackOff, OOMKilled, etc.):"
echo -e "  ${YELLOW}kubectl get pods -n $TEST_NAMESPACE --watch${NC}"
echo ""
echo "Check AlertManager for firing alerts:"
echo -e "  ${YELLOW}kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093${NC}"
echo -e "  ${YELLOW}# Then visit: http://localhost:9093/#/alerts${NC}"
echo ""
echo "Monitor webhook service:"
echo -e "  ${YELLOW}kubectl logs -f -n analysis-agent -l app=webhook-service${NC}"
echo ""
echo "Check agent activity:"
echo -e "  ${YELLOW}kubectl logs -f -n kagent-system -l app=kagent-operator${NC}"
echo ""
echo "View investigation reports (after alert fires):"
echo -e "  ${YELLOW}kubectl exec -it -n analysis-agent <agent-pod> -- ls -la /agent-memory/reports/${NC}"
echo ""
echo -e "${BLUE}Cleanup when done:${NC}"
echo -e "  ${YELLOW}$0  # Select option 5 (Cleanup)${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
