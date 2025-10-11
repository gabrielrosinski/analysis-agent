#!/bin/bash
# Initialize agent memory with template files
# This script copies memory templates to the agent's PersistentVolume

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Agent Memory Initialization"
echo "======================================"
echo ""

# Check if namespace exists, create if not
echo "1. Checking namespace..."
if kubectl get namespace analysis-agent >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Namespace 'analysis-agent' exists"
else
    echo -e "${YELLOW}→${NC} Creating namespace 'analysis-agent'"
    kubectl create namespace analysis-agent
    echo -e "${GREEN}✓${NC} Namespace created"
fi
echo ""

# Apply storage manifest
echo "2. Creating PersistentVolumeClaim..."
kubectl apply -f manifests/storage.yaml
echo ""

# Wait for PVC to be bound
echo "3. Waiting for PVC to be bound..."
kubectl wait --for=condition=Bound pvc/agent-memory-pvc -n analysis-agent --timeout=60s
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PVC is bound"
else
    echo -e "${RED}✗${NC} PVC failed to bind. Check storage class availability."
    exit 1
fi
echo ""

# Create temporary pod to copy files
echo "4. Creating temporary pod for file transfer..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: memory-init
  namespace: analysis-agent
spec:
  volumes:
  - name: memory
    persistentVolumeClaim:
      claimName: agent-memory-pvc
  containers:
  - name: init
    image: busybox:latest
    command: ["sleep", "300"]
    volumeMounts:
    - name: memory
      mountPath: /agent-memory
  restartPolicy: Never
EOF

# Wait for pod to be ready
echo "   Waiting for pod to be ready..."
kubectl wait --for=condition=Ready pod/memory-init -n analysis-agent --timeout=60s
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Temporary pod is ready"
else
    echo -e "${RED}✗${NC} Pod failed to start"
    kubectl delete pod memory-init -n analysis-agent --force 2>/dev/null
    exit 1
fi
echo ""

# Copy template files to PVC
echo "5. Copying memory templates to PVC..."
if [ -d "memory-templates" ]; then
    # Copy all files from memory-templates directory
    for file in memory-templates/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "   Copying $filename..."
            kubectl cp "$file" analysis-agent/memory-init:/agent-memory/"$filename"
        fi
    done

    # Create reports directory
    echo "   Creating reports directory..."
    kubectl exec memory-init -n analysis-agent -- mkdir -p /agent-memory/reports

    echo -e "${GREEN}✓${NC} Memory templates copied successfully"
else
    echo -e "${RED}✗${NC} memory-templates directory not found"
    echo "   Please run this script from the project root directory"
    kubectl delete pod memory-init -n analysis-agent --force 2>/dev/null
    exit 1
fi
echo ""

# Verify files were copied
echo "6. Verifying copied files..."
echo "   Files in /agent-memory:"
kubectl exec memory-init -n analysis-agent -- ls -lh /agent-memory/
echo ""

# Cleanup temporary pod
echo "7. Cleaning up temporary pod..."
kubectl delete pod memory-init -n analysis-agent
echo -e "${GREEN}✓${NC} Cleanup complete"
echo ""

echo "======================================"
echo -e "${GREEN}✓ Memory initialization complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review manifests/rbac.yaml and apply: kubectl apply -f manifests/rbac.yaml"
echo "2. Create agents/devops-rca-agent.yaml"
echo "3. Deploy the agent"
echo ""
