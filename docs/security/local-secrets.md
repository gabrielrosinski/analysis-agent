# Scripts Directory

Utility scripts for the Analysis-Agent project.

---

## Available Scripts

### 🔒 `setup-local-secrets.sh`

**Purpose:** Automated Kubernetes secrets creation from `.env.local` file.

**Quick Start:**
```bash
cp .env.template .env.local # Create a copy of .env.template
nano .env.local  # Add your credentials
./scripts/setup-local-secrets.sh # Run the credential auto init script
```

**Full Documentation:** See [Installation Guide - Step 2](../docs/INSTALLATION.md#step-2-configure-secrets)

---

### 🧠 `init-memory.sh`

**Purpose:** Initialize agent memory templates in PersistentVolume.

```bash
./scripts/init-memory.sh
```

---

### 📋 `verify-agent.sh`

**Purpose:** Verify all analysis-agent components are running correctly.

```bash
./scripts/verify-agent.sh
```

---

### 🧪 `create-test-failure.sh`

**Purpose:** Create test failure scenarios for testing RCA agent.

```bash
./scripts/create-test-failure.sh
```

---

### 📨 `send-test-alert.sh`

**Purpose:** Send test alert to webhook service.

```bash
./scripts/send-test-alert.sh
```

---

## General Notes

- All scripts should be run from **project root directory**
- Requires **kubectl** and **Helm** to be installed
- Scripts use `--dry-run=client` to avoid conflicts (safe to re-run)

---

## Troubleshooting

**Permission denied:**
```bash
chmod +x scripts/*.sh
```

**Script not found:**
```bash
# Ensure you're in project root
cd /path/to/analysis-agent
./scripts/script-name.sh
```

---

## Documentation

For complete installation and usage instructions, see:
- **[Installation Guide](../docs/INSTALLATION.md)** - Full step-by-step setup
- **[SECURITY.md](../docs/SECURITY.md)** - Production secret management with Vault
- **[CLAUDE.md](../CLAUDE.md)** - Development guide for contributors
