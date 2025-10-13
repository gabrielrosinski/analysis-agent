#!/bin/bash
# Setup Local Secrets Script
# Creates Kubernetes secrets from .env.local file (gitignored)
# SAFE: Secrets stay local, never committed to git

set -e

echo "========================================="
echo "  Analysis-Agent Local Secrets Setup"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${RED}ERROR: .env.local file not found!${NC}"
    echo ""
    echo "Please create it from the template:"
    echo "  cp .env.template .env.local"
    echo "  # Edit .env.local with your actual credentials"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Load environment variables from .env.local
echo -e "${GREEN}✓${NC} Loading credentials from .env.local"
export $(grep -v '^#' .env.local | xargs)

# Validate required variables
MISSING_VARS=()

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-api-YOUR-KEY-HERE" ]; then
    MISSING_VARS+=("ANTHROPIC_API_KEY")
fi

if [ -z "$GMAIL_USERNAME" ] || [ "$GMAIL_USERNAME" = "your-email@gmail.com" ]; then
    MISSING_VARS+=("GMAIL_USERNAME")
fi

if [ -z "$GMAIL_APP_PASSWORD" ] || [ "$GMAIL_APP_PASSWORD" = "your-16-char-app-password-here" ]; then
    MISSING_VARS+=("GMAIL_APP_PASSWORD")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Missing or template values detected:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please edit .env.local and add your actual credentials."
    exit 1
fi

echo -e "${GREEN}✓${NC} All required credentials present"
echo ""

# Create kagent namespace if not exists
echo "Creating namespaces..."
kubectl create namespace kagent --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace analysis-agent --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓${NC} Namespaces created"
echo ""

# Create Anthropic API key secret
echo "Creating Anthropic API key secret..."
kubectl create secret generic kagent-anthropic \
    -n kagent \
    --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓${NC} Anthropic secret created in kagent namespace"

# Create Gmail credentials secret
echo "Creating Gmail credentials secret..."
kubectl create secret generic gmail-credentials \
    -n analysis-agent \
    --from-literal=username="$GMAIL_USERNAME" \
    --from-literal=password="$GMAIL_APP_PASSWORD" \
    --from-literal=from-address="$GMAIL_FROM_ADDRESS" \
    --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓${NC} Gmail credentials created"

# Create email recipients secret
echo "Creating email recipients secret..."
kubectl create secret generic email-recipients \
    -n analysis-agent \
    --from-literal=recipients-critical="$RECIPIENTS_CRITICAL" \
    --from-literal=recipients-warning="$RECIPIENTS_WARNING" \
    --from-literal=recipients-info="$RECIPIENTS_INFO" \
    --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓${NC} Email recipients configured"

# Create GitHub token secret (if provided)
if [ -n "$GITHUB_TOKEN" ] && [ "$GITHUB_TOKEN" != "ghp_YOUR_GITHUB_TOKEN_HERE" ]; then
    echo "Creating GitHub token secret..."
    kubectl create secret generic github-credentials \
        -n analysis-agent \
        --from-literal=token="$GITHUB_TOKEN" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✓${NC} GitHub token created"
else
    echo -e "${YELLOW}⚠${NC}  GitHub token not provided (optional - skipping)"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✓ All secrets created successfully!${NC}"
echo "========================================="
echo ""
echo "Your secrets are stored:"
echo "  - In Kubernetes cluster (base64 encoded)"
echo "  - Locally in .env.local (gitignored)"
echo ""
echo "To view secrets:"
echo "  kubectl get secrets -n kagent"
echo "  kubectl get secrets -n analysis-agent"
echo ""
echo "Next steps:"
echo "  1. Install Kagent operator (see docs/INSTALLATION.md Step 1.3)"
echo "  2. Deploy analysis-agent with Helm"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC} Never commit .env.local to git!"
echo ""
