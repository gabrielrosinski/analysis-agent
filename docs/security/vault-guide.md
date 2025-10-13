# Security Guide

This document explains secret management security for the DevOps RCA Agent and production deployment best practices.

---

## ⚠️ Current Security Status (Development/Testing)

**Current Implementation:**
- Secrets stored as Kubernetes Secrets (base64 encoded)
- **NOT SECURE** - base64 is trivially reversible
- Anyone with `kubectl get secrets` permission can decode secrets

**Example of the security issue:**
```bash
# Anyone can decode secrets in plain text
kubectl get secret kagent-anthropic -n kagent -o jsonpath='{.data.ANTHROPIC_API_KEY}' | base64 -d
# Returns: sk-ant-api-YOUR-KEY-HERE (in plain text!)
```

**What's at risk:**
- Anthropic API key (costs real money if leaked)
- Gmail app password (email access)
- GitHub tokens (repository access)
- Email recipient lists

**When this is acceptable:**
- ✅ Local development/testing (like now)
- ✅ Learning and prototyping
- ✅ Environments where cluster access is already highly restricted
- ❌ **NEVER for production!**

---

## 🔒 Production Solution: HashiCorp Vault

**Why HashiCorp Vault:**
- ✅ **Free and open-source** (Community Edition)
- ✅ Industry-standard secret management
- ✅ Dynamic secrets (generated on-demand, automatically rotated)
- ✅ Encryption at rest and in transit
- ✅ Fine-grained access control (per-pod, per-service)
- ✅ Comprehensive audit logging
- ✅ Self-hosted (no external cloud dependencies)
- ✅ Kubernetes-native integration via Agent Injector

---

## 📦 Installing HashiCorp Vault (Community Edition)

### Prerequisites
- Kubernetes cluster (K3s, K8s, etc.)
- Helm 3.12+
- At least 1GB RAM for Vault server

### Step 1: Add Vault Helm Repository

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

### Step 2: Install Vault Server

**Development Mode (for testing):**
```bash
# Quick start - Vault runs in dev mode (data not persisted)
helm install vault hashicorp/vault \
    --namespace vault \
    --create-namespace \
    --set "server.dev.enabled=true"
```

**Production Mode (with persistent storage):**
```bash
# Production-ready Vault with HA and persistent storage
helm install vault hashicorp/vault \
    --namespace vault \
    --create-namespace \
    --set "server.ha.enabled=true" \
    --set "server.ha.replicas=3" \
    --set "server.dataStorage.enabled=true" \
    --set "server.dataStorage.size=10Gi"
```

### Step 3: Initialize Vault (Production Mode Only)

```bash
# Initialize Vault (run once)
kubectl exec -n vault vault-0 -- vault operator init \
    -key-shares=5 \
    -key-threshold=3 \
    -format=json > vault-init.json

# IMPORTANT: Save vault-init.json securely!
# It contains unseal keys and root token

# Unseal Vault (required after every restart)
UNSEAL_KEY_1=$(jq -r '.unseal_keys_b64[0]' vault-init.json)
UNSEAL_KEY_2=$(jq -r '.unseal_keys_b64[1]' vault-init.json)
UNSEAL_KEY_3=$(jq -r '.unseal_keys_b64[2]' vault-init.json)

kubectl exec -n vault vault-0 -- vault operator unseal $UNSEAL_KEY_1
kubectl exec -n vault vault-0 -- vault operator unseal $UNSEAL_KEY_2
kubectl exec -n vault vault-0 -- vault operator unseal $UNSEAL_KEY_3
```

### Step 4: Enable Kubernetes Authentication

```bash
# Port forward to Vault
kubectl port-forward -n vault svc/vault 8200:8200 &

# Login with root token
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=$(jq -r '.root_token' vault-init.json)

# Enable Kubernetes auth
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc:443"
```

### Step 5: Create Secrets in Vault

```bash
# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store Anthropic API key
vault kv put secret/kagent/anthropic \
    api_key="sk-ant-api-YOUR-KEY-HERE"

# Store Gmail credentials
vault kv put secret/kagent/gmail \
    username="your-email@gmail.com" \
    password="your-app-password" \
    from_address="DevOps RCA Agent <your-email@gmail.com>"

# Store email recipients
vault kv put secret/kagent/email-recipients \
    critical="oncall@example.com,sre@example.com" \
    warning="devops@example.com" \
    info="devops-alerts@example.com"

# Store GitHub token (optional)
vault kv put secret/kagent/github \
    token="ghp_YOUR_GITHUB_TOKEN"
```

### Step 6: Create Vault Policies

```bash
# Policy for analysis-agent namespace
vault policy write analysis-agent-policy - <<EOF
# Read-only access to kagent secrets
path "secret/data/kagent/*" {
  capabilities = ["read"]
}
EOF

# Bind policy to Kubernetes service accounts
vault write auth/kubernetes/role/analysis-agent-role \
    bound_service_account_names=webhook-sa,notifier-sa,agent-sa \
    bound_service_account_namespaces=analysis-agent \
    policies=analysis-agent-policy \
    ttl=24h
```

---

## 🔌 Integrating with Analysis-Agent

### Option A: Vault Agent Injector (Recommended)

**How it works:**
- Vault Agent sidecar automatically injected into pods
- Secrets fetched from Vault and written to shared volume
- Application reads secrets from files (not environment variables)

**Enable Vault Agent Injector:**
```bash
helm upgrade vault hashicorp/vault \
    --namespace vault \
    --set "injector.enabled=true"
```

**Update Deployment Manifests:**

**Example: Webhook Service with Vault Injection**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-service
  namespace: analysis-agent
spec:
  template:
    metadata:
      annotations:
        # Enable Vault injection
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "analysis-agent-role"

        # Inject Anthropic API key
        vault.hashicorp.com/agent-inject-secret-anthropic: "secret/data/kagent/anthropic"
        vault.hashicorp.com/agent-inject-template-anthropic: |
          {{- with secret "secret/data/kagent/anthropic" -}}
          export ANTHROPIC_API_KEY="{{ .Data.data.api_key }}"
          {{- end }}
    spec:
      serviceAccountName: webhook-sa
      containers:
      - name: webhook
        image: blaqr/analysis-agent-webhook:0.1.0
        # Source the Vault-injected secret
        command: ["/bin/sh", "-c"]
        args:
          - source /vault/secrets/anthropic && uvicorn main:app --host 0.0.0.0 --port 8080
```

**Example: Notifier Service with Vault Injection**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notifier-service
  namespace: analysis-agent
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "analysis-agent-role"

        # Inject Gmail credentials
        vault.hashicorp.com/agent-inject-secret-gmail: "secret/data/kagent/gmail"
        vault.hashicorp.com/agent-inject-template-gmail: |
          {{- with secret "secret/data/kagent/gmail" -}}
          export SMTP_USER="{{ .Data.data.username }}"
          export SMTP_PASSWORD="{{ .Data.data.password }}"
          export SMTP_FROM="{{ .Data.data.from_address }}"
          {{- end }}

        # Inject email recipients
        vault.hashicorp.com/agent-inject-secret-recipients: "secret/data/kagent/email-recipients"
        vault.hashicorp.com/agent-inject-template-recipients: |
          {{- with secret "secret/data/kagent/email-recipients" -}}
          export RECIPIENTS_CRITICAL="{{ .Data.data.critical }}"
          export RECIPIENTS_WARNING="{{ .Data.data.warning }}"
          export RECIPIENTS_INFO="{{ .Data.data.info }}"
          {{- end }}
    spec:
      serviceAccountName: notifier-sa
      containers:
      - name: notifier
        image: blaqr/analysis-agent-notifier:0.1.0
        command: ["/bin/sh", "-c"]
        args:
          - source /vault/secrets/gmail && source /vault/secrets/recipients && python main.py
```

---

### Option B: Vault CSI Provider (Alternative)

**How it works:**
- Secrets mounted as volumes using Kubernetes CSI driver
- No sidecar containers
- Slightly more complex setup

**Installation:**
```bash
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
    --namespace kube-system

# Install Vault CSI provider
kubectl apply -f https://raw.githubusercontent.com/hashicorp/vault-csi-provider/main/deployment/vault-csi-provider.yaml
```

**Usage Example:**
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-kagent-secrets
  namespace: analysis-agent
spec:
  provider: vault
  parameters:
    vaultAddress: "http://vault.vault:8200"
    roleName: "analysis-agent-role"
    objects: |
      - objectName: "anthropic_api_key"
        secretPath: "secret/data/kagent/anthropic"
        secretKey: "api_key"
```

---

## 🔄 Secret Rotation Strategy

### Automatic Rotation with Vault

**Dynamic Secrets (Best Practice):**
```bash
# Configure dynamic database credentials (example)
vault secrets enable database

vault write database/config/postgresql \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/kagent"

# Create role that generates short-lived credentials
vault write database/roles/kagent-role \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';" \
    default_ttl="1h" \
    max_ttl="24h"
```

**Lease Renewal:**
- Vault Agent automatically renews leases before expiration
- No manual intervention required
- Seamless rotation without pod restarts

---

## 🛡️ Security Best Practices

### 1. Never Store Vault Tokens in Git
```bash
# Add to .gitignore
echo "vault-init.json" >> .gitignore
echo "*.vault-token" >> .gitignore
echo ".vault-token" >> .gitignore
```

### 2. Use Namespace Isolation
```bash
# Limit Vault policies to specific namespaces
vault write auth/kubernetes/role/analysis-agent-role \
    bound_service_account_namespaces=analysis-agent
```

### 3. Enable Audit Logging
```bash
vault audit enable file file_path=/vault/logs/audit.log
```

### 4. Regular Unseal Key Rotation
```bash
# Rotate unseal keys every 90 days
vault operator rekey -init -key-shares=5 -key-threshold=3
```

### 5. Principle of Least Privilege
- Each service account gets its own Vault role
- Only access to secrets it needs
- Short TTLs (1-24 hours)

---

## 📊 Comparison: Secret Management Options

| Feature | Kubernetes Secrets | Sealed Secrets | External Secrets | HashiCorp Vault |
|---------|-------------------|----------------|------------------|-----------------|
| **Cost** | Free | Free | Free* | **Free (OSS)** |
| **Encryption at Rest** | ❌ (base64) | ✅ | ✅ | ✅ |
| **Dynamic Secrets** | ❌ | ❌ | ❌ | ✅ |
| **Automatic Rotation** | ❌ | ❌ | Limited | ✅ |
| **Audit Logging** | Limited | ❌ | Limited | ✅ |
| **GitOps Friendly** | ❌ | ✅ | ⚠️ | ⚠️ |
| **Self-Hosted** | ✅ | ✅ | ✅ | ✅ |
| **Complexity** | Low | Low | Medium | **High** |
| **Production Ready** | ❌ | ⚠️ | ✅ | ✅ |

*External Secrets is free, but requires paid cloud provider secrets service (AWS Secrets Manager, Azure Key Vault)

---

## 🚀 Migration Path

### Phase 1: Development (Current)
```bash
# Use plain Kubernetes secrets
kubectl create secret generic kagent-anthropic -n kagent \
    --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

### Phase 2: Pre-Production
```bash
# Deploy Vault in dev mode
helm install vault hashicorp/vault --set "server.dev.enabled=true"
# Test integration with Agent Injector
```

### Phase 3: Production
```bash
# Deploy Vault with HA + persistent storage
# Enable Kubernetes auth
# Migrate all secrets to Vault
# Update deployment manifests with Vault annotations
# Remove old Kubernetes secrets
```

---

## 📖 Additional Resources

**HashiCorp Vault Documentation:**
- Official Docs: https://developer.hashicorp.com/vault/docs
- Kubernetes Integration: https://developer.hashicorp.com/vault/docs/platform/k8s
- Agent Injector: https://developer.hashicorp.com/vault/docs/platform/k8s/injector

**Vault on Kubernetes Tutorial:**
- https://learn.hashicorp.com/tutorials/vault/kubernetes-sidecar

**Community Support:**
- Vault GitHub: https://github.com/hashicorp/vault
- Vault Forums: https://discuss.hashicorp.com/c/vault

---

## 🔧 Troubleshooting

### Vault Pod Not Starting
```bash
# Check logs
kubectl logs -n vault vault-0

# Common issues:
# - Insufficient resources (increase memory/CPU)
# - Storage class not available (check PVC)
# - Unseal keys required (production mode)
```

### Agent Injection Not Working
```bash
# Check injector logs
kubectl logs -n vault -l app.kubernetes.io/name=vault-agent-injector

# Verify service account has correct role binding
vault read auth/kubernetes/role/analysis-agent-role
```

### Secrets Not Appearing in Pods
```bash
# Check Vault agent logs in pod
kubectl logs -n analysis-agent <pod-name> -c vault-agent

# Verify policy permissions
vault policy read analysis-agent-policy
```

---

## 📝 Security Checklist

Before going to production:

- [ ] Vault installed with HA and persistent storage
- [ ] Unseal keys stored securely (separate from cluster)
- [ ] Root token rotated after initial setup
- [ ] Kubernetes auth configured with namespace isolation
- [ ] Policies follow principle of least privilege
- [ ] Audit logging enabled
- [ ] All secrets migrated from Kubernetes Secrets to Vault
- [ ] Old Kubernetes Secrets deleted
- [ ] Deployment manifests updated with Vault annotations
- [ ] Secret rotation strategy documented
- [ ] Backup and disaster recovery plan in place

---

**Version:** 0.1.0
**Last Updated:** 2025-10-13
**Status:** Production-Ready Architecture Documented
