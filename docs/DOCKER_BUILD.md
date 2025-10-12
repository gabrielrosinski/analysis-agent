# Docker Build Guide

This guide is for **project maintainers** who need to build and publish Docker images for the webhook and notifier services.

**Note**: End users do NOT need to build images. Pre-built images are available and referenced by default in the Helm chart.

## Separation of Concerns

The Helm chart is designed with clear separation:

- **`values.yaml`**: Contains default image references
  ```yaml
  webhook:
    image:
      repository: ghcr.io/your-org/analysis-agent-webhook
      tag: "0.1.0"
  ```

- **Deployment templates**: Reference values from `values.yaml`
  ```yaml
  image: "{{ .Values.webhook.image.repository }}:{{ .Values.webhook.image.tag }}"
  ```

- **End users**: Just run `helm install` - images pulled automatically
- **Custom builds**: Override with `--set webhook.image.repository=custom-registry/webhook`

This means maintainers publish to `ghcr.io/your-org/`, and users get working defaults without any configuration.

---

## Prerequisites

- **Docker**: v24.0+
- **Registry Access**: Push permissions to target registry (Docker Hub, GHCR, ECR, etc.)
- **Repository Cloned**: Local copy of the analysis-agent repository

---

## Build Process

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd analysis-agent
```

### 2. Build Webhook Service

```bash
cd services/webhook

# Build image
docker build -t ghcr.io/your-org/analysis-agent-webhook:v0.1.0 .

# Tag latest
docker tag ghcr.io/your-org/analysis-agent-webhook:v0.1.0 \
           ghcr.io/your-org/analysis-agent-webhook:latest

cd ../..
```

### 3. Build Notifier Service

```bash
cd services/notifier

# Build image
docker build -t ghcr.io/your-org/analysis-agent-notifier:v0.1.0 .

# Tag latest
docker tag ghcr.io/your-org/analysis-agent-notifier:v0.1.0 \
           ghcr.io/your-org/analysis-agent-notifier:latest

cd ../..
```

### 4. Push to Registry

```bash
# Push webhook
docker push ghcr.io/your-org/analysis-agent-webhook:v0.1.0
docker push ghcr.io/your-org/analysis-agent-webhook:latest

# Push notifier
docker push ghcr.io/your-org/analysis-agent-notifier:v0.1.0
docker push ghcr.io/your-org/analysis-agent-notifier:latest
```

---

## Registry Options

### GitHub Container Registry (GHCR) - Recommended

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/your-org/analysis-agent-webhook:v0.1.0 services/webhook
docker push ghcr.io/your-org/analysis-agent-webhook:v0.1.0
```

### Docker Hub

```bash
# Login
docker login

# Build and push
docker build -t your-dockerhub-username/analysis-agent-webhook:v0.1.0 services/webhook
docker push your-dockerhub-username/analysis-agent-webhook:v0.1.0
```

### Private Registry (Harbor, ECR, GCR, ACR)

```bash
# Login to private registry
docker login registry.company.com

# Build and push
docker build -t registry.company.com/analysis-agent/webhook:v0.1.0 services/webhook
docker push registry.company.com/analysis-agent/webhook:v0.1.0
```

---

## Multi-Architecture Builds

For ARM64 and AMD64 support (Apple Silicon, AWS Graviton, etc.):

```bash
# Create buildx builder
docker buildx create --name multiarch --use

# Build and push multi-arch webhook
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/analysis-agent-webhook:v0.1.0 \
  --push \
  services/webhook

# Build and push multi-arch notifier
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/analysis-agent-notifier:v0.1.0 \
  --push \
  services/notifier
```

---

## Automated Builds (CI/CD)

### GitHub Actions Workflow

Create `.github/workflows/build-images.yml`:

```yaml
name: Build and Push Images

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build and push webhook
        uses: docker/build-push-action@v4
        with:
          context: ./services/webhook
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/webhook:${{ steps.version.outputs.VERSION }}
            ghcr.io/${{ github.repository }}/webhook:latest

      - name: Build and push notifier
        uses: docker/build-push-action@v4
        with:
          context: ./services/notifier
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/notifier:${{ steps.version.outputs.VERSION }}
            ghcr.io/${{ github.repository }}/notifier:latest
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - build

build-images:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # Build webhook
    - cd services/webhook
    - docker build -t $CI_REGISTRY/analysis-agent/webhook:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY/analysis-agent/webhook:$CI_COMMIT_TAG

    # Build notifier
    - cd ../notifier
    - docker build -t $CI_REGISTRY/analysis-agent/notifier:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY/analysis-agent/notifier:$CI_COMMIT_TAG
  only:
    - tags
```

---

## Update Helm Chart Defaults

After publishing new images, update `chart/analysis-agent/values.yaml`:

```yaml
webhook:
  image:
    repository: ghcr.io/your-org/analysis-agent-webhook
    tag: "0.1.0"  # Update to new version
    pullPolicy: IfNotPresent

notifier:
  image:
    repository: ghcr.io/your-org/analysis-agent-notifier
    tag: "0.1.0"  # Update to new version
    pullPolicy: IfNotPresent
```

---

## Image Scanning and Security

### Scan with Trivy

```bash
# Install trivy
brew install aquasecurity/trivy/trivy  # macOS
# or apt-get install trivy              # Linux

# Scan webhook image
trivy image ghcr.io/your-org/analysis-agent-webhook:v0.1.0

# Scan notifier image
trivy image ghcr.io/your-org/analysis-agent-notifier:v0.1.0
```

### Sign Images with Cosign

```bash
# Install cosign
brew install cosign  # macOS

# Generate key pair
cosign generate-key-pair

# Sign images
cosign sign --key cosign.key ghcr.io/your-org/analysis-agent-webhook:v0.1.0
cosign sign --key cosign.key ghcr.io/your-org/analysis-agent-notifier:v0.1.0

# Verify signatures
cosign verify --key cosign.pub ghcr.io/your-org/analysis-agent-webhook:v0.1.0
```

---

## Versioning Strategy

### Semantic Versioning

Use semantic versioning for image tags:

- **Major**: Breaking changes (v2.0.0)
- **Minor**: New features, backward compatible (v1.1.0)
- **Patch**: Bug fixes (v1.0.1)

### Tag Conventions

```bash
# Version tag
docker tag webhook:latest webhook:v0.1.0

# Latest tag (always points to newest stable)
docker tag webhook:v0.1.0 webhook:latest

# Branch tags for testing
docker tag webhook:v0.1.0 webhook:dev
docker tag webhook:v0.1.0 webhook:staging
```

---

## Testing Images Locally

Before pushing to registry:

```bash
# Run webhook locally
docker run -p 8080:8080 \
  -e LOG_LEVEL=debug \
  ghcr.io/your-org/analysis-agent-webhook:v0.1.0

# Test health endpoint
curl http://localhost:8080/health

# Run notifier locally
docker run -p 8081:8080 \
  -e SMTP_HOST=smtp.gmail.com \
  -e SMTP_USERNAME=test@gmail.com \
  -e SMTP_PASSWORD=app-password \
  ghcr.io/your-org/analysis-agent-notifier:v0.1.0
```

---

## Image Size Optimization

### Multi-Stage Builds

Both services already use multi-stage builds in their Dockerfiles:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Check Image Size

```bash
docker images | grep analysis-agent

# Expected sizes:
# webhook:  ~150MB
# notifier: ~150MB
```

---

## Troubleshooting

### Build Fails with "No Space Left on Device"

```bash
# Clean up Docker system
docker system prune -a --volumes

# Remove unused images
docker image prune -a
```

### Push Fails with "Unauthorized"

```bash
# Re-authenticate
docker logout ghcr.io
docker login ghcr.io -u USERNAME

# Or use token
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Build is Slow

```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build ...

# Or use buildx
docker buildx build --load -t image:tag .
```

---

## When to Rebuild Images

Rebuild and publish new images when:

1. **Service code changes** (`services/webhook/`, `services/notifier/`)
2. **Dependency updates** (`requirements.txt`)
3. **Security patches** (base image updates)
4. **New features** (API endpoints, email templates)
5. **Bug fixes** (code corrections)

**Do NOT rebuild for:**
- Configuration changes (use Kubernetes secrets/configmaps)
- Email recipient changes (use secrets)
- Kagent agent updates (agent is separate)

---

## Support

- **Main Documentation**: [README.md](../README.md)
- **Installation Guide**: [INSTALLATION.md](./INSTALLATION.md)
- **Issues**: Create an issue in the repository

---

**Last Updated**: 2025-10-12
