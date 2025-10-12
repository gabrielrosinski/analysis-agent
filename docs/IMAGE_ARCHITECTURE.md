# Docker Image Architecture - Separation of Concerns

This document explains how Docker images are managed in this project with clear separation between maintainers and end users.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEPARATION OF CONCERNS                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   MAINTAINERS       │  Build & Publish Images
│   (Once)            │  └─> ghcr.io/your-org/webhook:0.1.0
└──────────┬──────────┘  └─> ghcr.io/your-org/notifier:0.1.0
           │
           │ Published to GHCR
           ▼
┌─────────────────────┐
│   values.yaml       │  Default Image References
│   (Version Control) │  webhook.image.repository: ghcr.io/...
└──────────┬──────────┘  webhook.image.tag: "0.1.0"
           │
           │ Referenced by
           ▼
┌─────────────────────┐
│   Templates         │  Use Values from values.yaml
│   (Helm)            │  image: "{{ .Values.webhook.image.repository }}:..."
└──────────┬──────────┘
           │
           │ Rendered by Helm
           ▼
┌─────────────────────┐
│   END USERS         │  Just: helm install
│   (Zero Config)     │  Images pulled automatically
└─────────────────────┘

           OR

┌─────────────────────┐
│   ADVANCED USERS    │  Override: --set webhook.image.repository=custom
│   (Custom Images)   │  Full control when needed
└─────────────────────┘
```

## Component Responsibilities

### 1. Maintainers (Build & Publish)

**Responsibility**: Build and publish images to public registry

**Location**: `ghcr.io/your-org/` (GitHub Container Registry)

**Tools**: `docs/DOCKER_BUILD.md`

**Workflow**:
```bash
# Build images
docker build -t ghcr.io/your-org/analysis-agent-webhook:0.1.0 services/webhook
docker build -t ghcr.io/your-org/analysis-agent-notifier:0.1.0 services/notifier

# Publish to GHCR
docker push ghcr.io/your-org/analysis-agent-webhook:0.1.0
docker push ghcr.io/your-org/analysis-agent-notifier:0.1.0

# Update values.yaml with new version
# (Done via CI/CD or manually)
```

**Frequency**: On new releases (v0.1.0, v0.2.0, etc.)

---

### 2. Helm Chart Configuration (values.yaml)

**Responsibility**: Define default image references

**Location**: `chart/analysis-agent/values.yaml`

**Configuration**:
```yaml
webhook:
  image:
    # Pre-built image from GitHub Container Registry
    # Default: Uses published image - no need to build yourself!
    # Override: Use --set webhook.image.repository=your-registry/webhook
    repository: ghcr.io/your-org/analysis-agent-webhook
    tag: "0.1.0"
    pullPolicy: IfNotPresent

notifier:
  image:
    # Pre-built image from GitHub Container Registry
    # Default: Uses published image - no need to build yourself!
    # Override: Use --set notifier.image.repository=your-registry/notifier
    repository: ghcr.io/your-org/analysis-agent-notifier
    tag: "0.1.0"
    pullPolicy: IfNotPresent
```

**Purpose**: Single source of truth for image configuration

---

### 3. Helm Templates

**Responsibility**: Reference values from values.yaml

**Location**:
- `chart/analysis-agent/templates/webhook-deployment.yaml`
- `chart/analysis-agent/templates/notifier-deployment.yaml`

**Code**:
```yaml
# webhook-deployment.yaml (line 28)
containers:
- name: webhook
  image: "{{ .Values.webhook.image.repository }}:{{ .Values.webhook.image.tag }}"
  imagePullPolicy: {{ .Values.webhook.image.pullPolicy }}

# notifier-deployment.yaml (line 28)
containers:
- name: notifier
  image: "{{ .Values.notifier.image.repository }}:{{ .Values.notifier.image.tag }}"
  imagePullPolicy: {{ .Values.notifier.image.pullPolicy }}
```

**Purpose**: Render deployment manifests using values

---

### 4. End Users (Zero Configuration)

**Responsibility**: Just install and use

**Command**:
```bash
# Create secrets first
kubectl create secret generic gmail-credentials ...
kubectl create secret generic email-recipients ...

# Install with defaults - images pulled automatically!
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace
```

**What happens**:
1. Helm reads `values.yaml`
2. Finds `repository: ghcr.io/your-org/analysis-agent-webhook`
3. Finds `tag: "0.1.0"`
4. Renders deployment with `image: ghcr.io/your-org/analysis-agent-webhook:0.1.0`
5. Kubernetes pulls image from GHCR
6. Pods start running

**User sees**: Working system with zero image configuration!

---

### 5. Advanced Users (Custom Images)

**Responsibility**: Override defaults when needed

**Use Cases**:
- Using custom-built images
- Testing development versions
- Corporate registry requirements
- Air-gapped environments

**Commands**:

**Option A: Command-line override**
```bash
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace \
  --set webhook.image.repository=my-registry.com/webhook \
  --set webhook.image.tag=custom \
  --set notifier.image.repository=my-registry.com/notifier \
  --set notifier.image.tag=custom
```

**Option B: Custom values file**
```bash
# my-values.yaml
webhook:
  image:
    repository: my-registry.com/webhook
    tag: custom

notifier:
  image:
    repository: my-registry.com/notifier
    tag: custom

# Install
helm install analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  --create-namespace \
  -f my-values.yaml
```

**Option C: Partial override**
```yaml
# Override only what's needed
webhook:
  image:
    tag: "0.2.0-dev"  # Use development version
  # repository stays as ghcr.io/your-org/... (default)
```

---

## Benefits of This Architecture

### ✅ For End Users
1. **Zero configuration**: Just `helm install`
2. **No Docker knowledge required**: Images pre-built and published
3. **Fast installation**: No 15-20 minute build process
4. **Consistent versions**: Everyone gets the same tested images
5. **Easy upgrades**: Just change tag in values.yaml

### ✅ For Maintainers
1. **Single point of truth**: values.yaml defines defaults
2. **CI/CD friendly**: Automate builds and publish
3. **Version control**: Track image versions in Git
4. **Easy releases**: Build once, publish, update values.yaml
5. **Multi-arch support**: Build for amd64 and arm64

### ✅ For Advanced Users
1. **Full control**: Override any image setting
2. **Corporate compliance**: Use internal registries
3. **Custom builds**: Modify services and deploy
4. **Testing**: Use development images
5. **Air-gapped**: Pre-pull to internal registry

---

## Image Naming Convention

### Production Images
```
ghcr.io/your-org/analysis-agent-webhook:0.1.0
ghcr.io/your-org/analysis-agent-webhook:0.2.0
ghcr.io/your-org/analysis-agent-webhook:1.0.0

ghcr.io/your-org/analysis-agent-notifier:0.1.0
ghcr.io/your-org/analysis-agent-notifier:0.2.0
ghcr.io/your-org/analysis-agent-notifier:1.0.0
```

### Latest Tag
```
ghcr.io/your-org/analysis-agent-webhook:latest  → points to newest stable
ghcr.io/your-org/analysis-agent-notifier:latest → points to newest stable
```

### Development Tags
```
ghcr.io/your-org/analysis-agent-webhook:0.2.0-dev
ghcr.io/your-org/analysis-agent-webhook:main-abc123 (commit SHA)
```

---

## Update Workflow

### When Releasing New Version (e.g., v0.2.0)

1. **Maintainer builds and publishes**:
   ```bash
   docker build -t ghcr.io/your-org/analysis-agent-webhook:0.2.0 services/webhook
   docker push ghcr.io/your-org/analysis-agent-webhook:0.2.0

   docker build -t ghcr.io/your-org/analysis-agent-notifier:0.2.0 services/notifier
   docker push ghcr.io/your-org/analysis-agent-notifier:0.2.0
   ```

2. **Update values.yaml**:
   ```yaml
   webhook:
     image:
       tag: "0.2.0"  # Update version

   notifier:
     image:
       tag: "0.2.0"  # Update version
   ```

3. **Commit and tag**:
   ```bash
   git add chart/analysis-agent/values.yaml
   git commit -m "Release v0.2.0"
   git tag v0.2.0
   git push --tags
   ```

4. **Users upgrade**:
   ```bash
   helm upgrade analysis-agent ./chart/analysis-agent
   # Automatically pulls new v0.2.0 images
   ```

---

## Troubleshooting

### Issue: Image Pull Errors

**Symptom**: Pods stuck in `ImagePullBackOff`

**Check**:
```bash
# Check what image is being pulled
kubectl describe pod <pod-name> -n analysis-agent

# Look for Events section:
# "Failed to pull image "ghcr.io/your-org/...": manifest not found"
```

**Solutions**:

1. **Image doesn't exist**: Maintainer hasn't published it yet
   ```bash
   # Verify image exists
   docker pull ghcr.io/your-org/analysis-agent-webhook:0.1.0
   ```

2. **Wrong registry**: values.yaml has incorrect repository
   ```yaml
   # Check values.yaml
   webhook.image.repository: ghcr.io/your-org/... # Correct?
   ```

3. **Private registry auth**: Need imagePullSecrets
   ```bash
   # Create registry secret
   kubectl create secret docker-registry regcred \
     --docker-server=your-registry \
     --docker-username=user \
     --docker-password=pass \
     -n analysis-agent

   # Add to values.yaml
   imagePullSecrets:
     - name: regcred
   ```

---

## Summary

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **Maintainer** | Build & publish images | `ghcr.io/your-org/` |
| **values.yaml** | Define default images | `chart/analysis-agent/values.yaml` |
| **Templates** | Reference values | `chart/analysis-agent/templates/*.yaml` |
| **End Users** | Just `helm install` | Zero configuration needed |
| **Advanced Users** | Override defaults | `--set` or custom values file |

This architecture ensures:
- ✅ End users have zero-config experience
- ✅ Maintainers have simple release process
- ✅ Advanced users have full control
- ✅ Single source of truth (values.yaml)
- ✅ Clear separation of concerns

---

**Last Updated**: 2025-10-12
**Architecture Version**: 1.0
