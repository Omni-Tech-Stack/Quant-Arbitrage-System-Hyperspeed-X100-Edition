# Dependency & Supply Chain Security

## Overview

This document outlines procedures for managing dependencies securely, including pinning versions, generating Software Bill of Materials (SBOM), running Software Composition Analysis (SCA), and implementing reproducible builds.

## Table of Contents

1. [Dependency Pinning](#dependency-pinning)
2. [SBOM Generation](#sbom-generation)
3. [Software Composition Analysis](#software-composition-analysis)
4. [Vulnerability Scanning](#vulnerability-scanning)
5. [Reproducible Builds](#reproducible-builds)
6. [Dependency Update Policy](#dependency-update-policy)

## Dependency Pinning

### Python Dependencies

Always pin exact versions in `requirements.txt`:

```txt
# requirements.txt - Pin exact versions for reproducibility
web3==6.11.3
eth-account==0.9.0
eth-utils==2.3.1
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
joblib==1.3.2
aiohttp==3.9.1
python-dotenv==1.0.0
pyyaml==6.0.1
prometheus-client==0.19.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

Generate from current environment:

```bash
# Generate pinned requirements
pip freeze > requirements.txt

# Or use pip-tools for better control
pip install pip-tools
pip-compile requirements.in --generate-hashes
```

### Node.js Dependencies

Use `package-lock.json` (npm) or `yarn.lock` (yarn) to lock versions:

```bash
# Generate lock file
npm install

# Always commit package-lock.json
git add package-lock.json
git commit -m "Lock npm dependencies"
```

For production, use exact versions in `package.json`:

```json
{
  "dependencies": {
    "express": "4.18.2",
    "cors": "2.8.5",
    "ws": "8.14.0",
    "ethers": "6.9.0",
    "web3": "4.3.0"
  }
}
```

### Rust Dependencies (Cargo)

Lock with `Cargo.lock`:

```toml
# Cargo.toml
[dependencies]
tokio = "=1.35.0"  # Use = for exact version
serde = "=1.0.193"
ethers = "=2.0.11"
```

Always commit `Cargo.lock`:

```bash
git add Cargo.lock
git commit -m "Lock Rust dependencies"
```

## SBOM Generation

### Using CycloneDX

#### Python SBOM

```bash
# Install cyclonedx-bom
pip install cyclonedx-bom

# Generate SBOM for Python
cyclonedx-py -r -i requirements.txt -o sbom-python.json

# With vulnerability data
cyclonedx-py -r -i requirements.txt -o sbom-python.json --format json
```

#### Node.js SBOM

```bash
# Install CycloneDX npm plugin
npm install -g @cyclonedx/cyclonedx-npm

# Generate SBOM for Node.js
cyclonedx-npm --output-file sbom-nodejs.json
```

#### Combined SBOM

```bash
# Merge SBOMs
cyclonedx merge \
  --input-files sbom-python.json sbom-nodejs.json \
  --output-file sbom-complete.json
```

### SBOM Validation

```bash
# Validate SBOM format
cyclonedx validate --input-file sbom-complete.json

# Check for required fields
cyclonedx validate --input-file sbom-complete.json --fail-on-errors
```

### Store SBOM in Version Control

```bash
# Create sbom directory
mkdir -p sbom/

# Generate and store
cyclonedx-py -r -i requirements.txt -o sbom/sbom-python-$(date +%Y%m%d).json
cyclonedx-npm --output-file sbom/sbom-nodejs-$(date +%Y%m%d).json

# Add to git
git add sbom/
git commit -m "Add SBOM for supply chain verification"
```

## Software Composition Analysis

### GitHub Dependabot

Enable Dependabot in `.github/dependabot.yml`:

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    
  # Node.js dependencies
  - package-ecosystem: "npm"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "npm"
    directory: "/ultra-fast-arbitrage-engine"
    schedule:
      interval: "weekly"
    
  # Rust dependencies
  - package-ecosystem: "cargo"
    directory: "/ultra-fast-arbitrage-engine/native"
    schedule:
      interval: "weekly"
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Snyk

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test Python dependencies
snyk test --file=requirements.txt

# Test Node.js dependencies
cd backend && snyk test

# Monitor continuously
snyk monitor
```

### OWASP Dependency-Check

```bash
# Install dependency-check
wget https://github.com/jeremylong/DependencyCheck/releases/download/v8.4.0/dependency-check-8.4.0-release.zip
unzip dependency-check-8.4.0-release.zip

# Run scan
./dependency-check/bin/dependency-check.sh \
  --project "Arbitrage System" \
  --scan . \
  --format "HTML" \
  --format "JSON" \
  --out reports/dependency-check

# View report
open reports/dependency-check/dependency-check-report.html
```

### Safety (Python)

```bash
# Install Safety
pip install safety

# Check dependencies
safety check --file requirements.txt

# Generate report
safety check --file requirements.txt --json > reports/safety-report.json

# Check with detailed output
safety check --file requirements.txt --full-report
```

### npm audit

```bash
# Audit Node.js dependencies
cd backend
npm audit

# Audit with JSON output
npm audit --json > ../reports/npm-audit.json

# Fix automatically (use with caution)
npm audit fix

# Fix breaking changes (more aggressive)
npm audit fix --force
```

## Vulnerability Scanning

### Automated Scanning in CI/CD

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  python-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install safety bandit
      
      - name: Safety check
        run: safety check --file requirements.txt --json > safety-report.json
        continue-on-error: true
      
      - name: Bandit security linter
        run: bandit -r . -f json -o bandit-report.json
        continue-on-error: true
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: python-security-reports
          path: |
            safety-report.json
            bandit-report.json
  
  nodejs-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd backend && npm ci
          cd ../ultra-fast-arbitrage-engine && npm ci
      
      - name: npm audit
        run: |
          cd backend && npm audit --json > ../npm-audit-backend.json || true
          cd ../ultra-fast-arbitrage-engine && npm audit --json > ../npm-audit-engine.json || true
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: nodejs-security-reports
          path: |
            npm-audit-backend.json
            npm-audit-engine.json
  
  dependency-review:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/dependency-review-action@v3
        with:
          fail-on-severity: high
```

### Manual Vulnerability Assessment

```bash
#!/bin/bash
# scripts/security-scan.sh

echo "Running comprehensive security scan..."

# Create reports directory
mkdir -p reports/security

# Python dependencies
echo "Scanning Python dependencies..."
safety check --file requirements.txt --json > reports/security/safety.json
bandit -r . -f json -o reports/security/bandit.json

# Node.js dependencies
echo "Scanning Node.js dependencies..."
cd backend && npm audit --json > ../reports/security/npm-audit-backend.json
cd ../ultra-fast-arbitrage-engine && npm audit --json > ../reports/security/npm-audit-engine.json
cd ..

# SBOM generation
echo "Generating SBOM..."
cyclonedx-py -r -i requirements.txt -o reports/security/sbom-python.json
cyclonedx-npm --output-file reports/security/sbom-nodejs.json

# Dependency-Check
echo "Running OWASP Dependency-Check..."
./dependency-check/bin/dependency-check.sh \
  --project "Arbitrage System" \
  --scan . \
  --format "JSON" \
  --out reports/security

echo "Security scan complete. Reports in reports/security/"
```

## Reproducible Builds

### Docker for Reproducibility

```dockerfile
# Dockerfile with pinned base image and dependencies
FROM python:3.11.6-slim@sha256:specific-hash AS python-base

# Pin system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    git=1:2.39.2-1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Set build timestamp for reproducibility
ARG BUILD_DATE
ENV BUILD_DATE=${BUILD_DATE}

# Run application
CMD ["python", "main_quant_hybrid_orchestrator.py"]
```

Build with reproducibility:

```bash
# Build with specific date
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --tag arbitrage-system:v1.0.0 \
  .

# Verify build
docker inspect arbitrage-system:v1.0.0
```

### Hash Verification

```bash
# Generate checksums for dependencies
pip install --no-deps \
  --download /tmp/packages \
  -r requirements.txt

cd /tmp/packages
sha256sum * > checksums.txt

# Verify later
sha256sum -c checksums.txt
```

### Reproducible pip Install

```bash
# requirements.txt with hashes
pip install \
  --require-hashes \
  --no-deps \
  -r requirements-hashes.txt
```

Generate `requirements-hashes.txt`:

```bash
pip-compile requirements.in --generate-hashes
```

## Dependency Update Policy

### Policy Guidelines

1. **Critical Security Updates**: Apply immediately (within 24 hours)
2. **High Security Updates**: Apply within 1 week
3. **Medium Security Updates**: Apply within 2 weeks
4. **Low/Info Updates**: Review during regular maintenance
5. **Feature Updates**: Evaluate during sprint planning

### Update Procedure

```bash
#!/bin/bash
# scripts/update-dependencies.sh

# 1. Check for updates
echo "Checking for Python updates..."
pip list --outdated

echo "Checking for Node.js updates..."
cd backend && npm outdated
cd ../ultra-fast-arbitrage-engine && npm outdated
cd ..

# 2. Run security scans
./scripts/security-scan.sh

# 3. Update in separate branch
git checkout -b dependency-updates-$(date +%Y%m%d)

# 4. Update Python (manually review each)
# pip install --upgrade <package>
# pip freeze > requirements.txt

# 5. Update Node.js
cd backend && npm update
cd ../ultra-fast-arbitrage-engine && npm update
cd ..

# 6. Run tests
npm run test:all

# 7. Commit if tests pass
git add -A
git commit -m "Update dependencies - $(date +%Y-%m-%d)"
git push origin dependency-updates-$(date +%Y%m%d)

# 8. Create PR for review
```

### Monthly Dependency Review

```markdown
# Dependency Review Checklist (Monthly)

- [ ] Run full security scan
- [ ] Review Dependabot PRs
- [ ] Check for deprecated packages
- [ ] Review license changes
- [ ] Update SBOM
- [ ] Test with updated dependencies
- [ ] Update documentation if needed
- [ ] Verify reproducible builds still work
```

## CI/CD Integration

```yaml
# .github/workflows/dependency-management.yml
name: Dependency Management

on:
  schedule:
    # Run weekly on Monday at 9 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch:

jobs:
  generate-sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Generate SBOM
        run: |
          pip install cyclonedx-bom
          npm install -g @cyclonedx/cyclonedx-npm
          
          cyclonedx-py -r -i requirements.txt -o sbom/sbom-python.json
          cyclonedx-npm --output-file sbom/sbom-nodejs.json
      
      - name: Commit SBOM
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add sbom/
          git commit -m "Update SBOM - $(date +%Y-%m-%d)" || echo "No changes"
          git push
  
  check-vulnerabilities:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run security scans
        run: ./scripts/security-scan.sh
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: reports/security/
      
      - name: Check for critical vulnerabilities
        run: |
          # Parse reports and fail if critical vulns found
          python scripts/check-critical-vulns.py reports/security/
```

## Best Practices Summary

1. ✅ **Always pin versions** in production
2. ✅ **Generate and track SBOM** for transparency
3. ✅ **Run automated security scans** in CI/CD
4. ✅ **Review and update dependencies** regularly
5. ✅ **Use lock files** (package-lock.json, Cargo.lock)
6. ✅ **Verify checksums** for critical dependencies
7. ✅ **Monitor security advisories** (GitHub, CVE databases)
8. ✅ **Test updates** in staging before production
9. ✅ **Document dependency choices** and reasons
10. ✅ **Implement reproducible builds** for consistency

## Tools Summary

| Tool | Purpose | Language |
|------|---------|----------|
| CycloneDX | SBOM generation | All |
| Safety | Vulnerability scanning | Python |
| Bandit | Security linting | Python |
| npm audit | Vulnerability scanning | Node.js |
| Snyk | Comprehensive SCA | All |
| OWASP Dependency-Check | Vulnerability scanning | All |
| Dependabot | Automated updates | All |
| pip-audit | Python security | Python |

## References

- [CycloneDX SBOM Standard](https://cyclonedx.org/)
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [Snyk Documentation](https://docs.snyk.io/)
- [GitHub Dependabot](https://docs.github.com/en/code-security/dependabot)
- [NIST Guidelines on SBOM](https://www.ntia.gov/sbom)
