# Production Deployment Guide

## Overview
Complete guide for deploying the AWS Network Visualizer to production. This platform is production-ready and meets Amazon DevOps standards.

## Prerequisites

### Required Tools
- AWS CLI v2.x configured with appropriate credentials
- Terraform >= 1.5.0
- Docker & Docker Compose
- Node.js 18+ and npm
- Python 3.11+
- Git

### Required AWS Permissions
- Administrator access (for initial setup)
- Or specific IAM permissions for:
  - Lambda, API Gateway, DynamoDB, S3, CloudFront
  - IAM role creation
  - CloudWatch, X-Ray, Secrets Manager
  - Bedrock model access

### Required Secrets
```bash
# Set up AWS Secrets Manager secrets before deployment
aws secretsmanager create-secret \
  --name network-visualizer/api-keys-production \
  --secret-string '{"api_gateway_key":"YOUR_KEY","bedrock_api_key":"YOUR_KEY"}'

aws secretsmanager create-secret \
  --name network-visualizer/integrations-production \
  --secret-string '{"slack_webhook_url":"YOUR_WEBHOOK","pagerduty_api_key":"YOUR_KEY"}'
```

## Quick Start (Development)

```bash
# 1. Clone repository
git clone https://github.com/your-org/aws-network-visualizer.git
cd aws-network-visualizer

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run with Docker Compose
docker-compose up

# 4. Run tests
pytest tests/ -v

# 5. Run CLI
python -m src.cli discover --region us-east-1
```

## Production Deployment

### Step 1: Infrastructure Setup

```bash
cd infrastructure/

# Initialize Terraform
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=network-visualizer/production/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-state-lock"

# Create production workspace
terraform workspace new production

# Review and apply infrastructure
terraform plan \
  -var="environment=production" \
  -var="s3_bucket_name=network-visualizer-data-prod" \
  -var="frontend_bucket_name=network-visualizer-frontend-prod" \
  -var="enable_ai_analysis=true" \
  -var="api_throttling_burst_limit=10000" \
  -var="api_throttling_rate_limit=20000" \
  -out=tfplan

terraform apply tfplan
```

### Step 2: Deploy Application Code

```bash
# Using GitHub Actions (Recommended)
git push origin main  # Triggers deploy-production.yml workflow

# Or manually
./scripts/build-and-push.sh production v1.0.0
```

### Step 3: Deploy Frontend

```bash
cd frontend/

# Build production bundle
npm ci
npm run build

# Deploy to S3
aws s3 sync dist/ s3://network-visualizer-frontend-prod/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

### Step 4: Verify Deployment

```bash
# Run production verification script
./scripts/production-verification.sh

# Check all services
./scripts/health-check.sh production

# Run smoke tests
pytest tests/smoke/ --api-endpoint=https://api.network-visualizer.com
```

## Architecture Overview

```
┌─────────────────┐
│   CloudFront    │ ← Frontend (React + D3.js)
└────────┬────────┘
         │
┌────────▼────────┐
│  API Gateway    │ ← REST API with throttling, caching
└────────┬────────┘
         │
    ┌────▼────┐ ┌──────────┐ ┌──────────┐
    │ Lambda  │ │ Lambda   │ │ Lambda   │
    │Discovery│ │Analysis  │ │   API    │
    └────┬────┘ └────┬─────┘ └────┬─────┘
         │           │             │
    ┌────▼───────────▼─────────────▼────┐
    │          DynamoDB Table            │ ← Topology data
    └────────────────────────────────────┘

    ┌─────────────┐  ┌──────────────┐
    │     S3      │  │   Bedrock    │
    │ Visualizations│  │ (Claude AI)  │
    └─────────────┘  └──────────────┘
```

## Key Features

### 1. API Gateway
- **Endpoint**: https://api.network-visualizer.com
- **Routes**:
  - GET `/topology/summary` - Get topology overview
  - GET `/topology/{region}/{vpcId}` - Get VPC topology
  - GET `/analyses/latest` - Get latest anomalies
  - POST `/discovery/trigger` - Trigger discovery
  - POST `/analysis/trigger` - Trigger analysis
- **Features**: Rate limiting (10K RPS), caching (5 min TTL), CORS enabled

### 2. Lambda Functions
- **Discovery** (15 min timeout, 1024MB): Collects AWS resources
- **Analysis** (15 min timeout, 2048MB): AI-powered anomaly detection
- **API** (30 sec timeout, 512MB): Serves REST API

### 3. Security
- **WAF**: Rate limiting, OWASP rules, IP blocking
- **GuardDuty**: Threat detection with auto-response
- **Secrets Manager**: Encrypted credential storage with rotation
- **VPC Endpoints**: Private AWS service access (no IGW)
- **Encryption**: At rest (AES-256) and in transit (TLS 1.2+)

### 4. Observability
- **X-Ray**: Distributed tracing with subsegments
- **CloudWatch**: Metrics, logs, alarms with 30-day retention
- **Dashboards**: Real-time operational insights
- **Structured Logging**: JSON format with correlation IDs

### 5. Disaster Recovery
- **RTO**: < 1 hour for most scenarios
- **RPO**: < 15 minutes with PITR and replication
- **Backups**: Daily (30d), Weekly (90d), Monthly (1y)
- **Cross-Region**: Optional replication to DR region

### 6. Cost Optimization
- **Budgets**: Monthly ($400), per-service alerts
- **Anomaly Detection**: Automated cost anomaly alerts
- **Right-sizing**: Weekly Lambda memory optimization
- **Target**: $350-500/month for production

## Operational Procedures

### Daily Operations
```bash
# Morning health check (10 min)
./scripts/daily-health-check.sh

# Review critical errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/network-visualizer-api-production \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '24 hours ago' +%s)000
```

### Weekly Maintenance
```bash
# Security review
./scripts/security-scan.sh

# Performance review
./scripts/performance-analysis.sh

# Cost review
./scripts/cost-analysis.sh 7
```

### Monthly Tasks
- [ ] Capacity planning review
- [ ] Cost optimization analysis
- [ ] Security audit
- [ ] DR drill (quarterly)
- [ ] Backup verification

## Incident Response

### P0 - Critical (< 15 min response)
1. Acknowledge alert
2. Create incident channel (#incident-YYYY-MM-DD-desc)
3. Assess impact
4. Follow [Incident Response Runbook](docs/runbooks/INCIDENT_RESPONSE.md)

### Common Scenarios
- **API 5XX Errors**: Check Lambda logs, DynamoDB throttling
- **Frontend Down**: Check CloudFront, S3 bucket
- **High Costs**: Review Lambda invocations, DynamoDB capacity
- **Data Loss**: Restore from backup (see DR runbook)

### Rollback Procedure
```bash
# Automatic rollback via GitHub Actions
gh workflow run rollback.yml \
  -f environment=production \
  -f lambda_version=3
```

## Monitoring & Alerts

### CloudWatch Alarms
- Lambda errors > 10/10min → PagerDuty
- API Gateway 5XX rate > 5% → PagerDuty
- DynamoDB throttling → Email
- Cost > 80% budget → Email
- GuardDuty critical finding → Slack + Email

### SLAs
- **Availability**: 99.9% uptime
- **API Latency**: P95 < 1000ms, P99 < 2000ms
- **Error Rate**: < 0.1%
- **RTO**: < 1 hour
- **RPO**: < 15 minutes

## Performance Testing

```bash
# Run load tests
./scripts/run-load-tests.sh production all

# Locust (interactive)
locust -f tests/load/locustfile.py \
  --host=https://api.network-visualizer.com \
  --users 100 \
  --spawn-rate 10

# Artillery (automated)
artillery run tests/load/artillery.yml
```

## Security

### Compliance
- OWASP Top 10 protection (WAF)
- Encryption at rest and in transit
- Least privilege IAM policies
- Automated vulnerability scanning (Trivy)
- Secrets rotation (30 days)

### Security Scanning
```bash
# Scan for vulnerabilities
docker run --rm -v $(pwd):/src aquasec/trivy fs /src

# Check for secrets in code
git secrets --scan

# Security audit
./scripts/security-audit.sh
```

## Cost Management

### Monthly Cost Breakdown
- Lambda: $50 (10M invocations)
- DynamoDB: $150 (on-demand)
- S3: $25 (100GB)
- CloudFront: $85 (1TB transfer)
- API Gateway: $35 (10M requests)
- Other: $55 (logs, metrics, Bedrock)
- **Total: ~$400/month**

### Cost Optimization
```bash
# Weekly cost optimizer
./scripts/weekly-cost-review.sh

# Get recommendations
aws ce get-rightsizing-recommendation --service Lambda
```

## Troubleshooting

### Quick Diagnostics
```bash
# Full diagnostic
./scripts/diagnostics.sh production

# Check specific component
./scripts/check-component.sh lambda api production
```

### Common Issues
See [Troubleshooting Guide](docs/runbooks/TROUBLESHOOTING.md) for detailed solutions.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Incident Response](docs/runbooks/INCIDENT_RESPONSE.md)
- [Operational Procedures](docs/runbooks/OPERATIONAL_PROCEDURES.md)
- [Disaster Recovery](docs/runbooks/DISASTER_RECOVERY.md)
- [Cost Optimization](docs/COST_OPTIMIZATION.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)

## Support

- **On-Call**: PagerDuty rotation
- **Slack**: #platform-network-visualizer
- **Issues**: https://github.com/your-org/aws-network-visualizer/issues
- **Wiki**: https://wiki.company.com/network-visualizer

## CI/CD

### GitHub Actions Workflows
- **ci.yml**: Runs on PRs (lint, test, security scan)
- **deploy-staging.yml**: Deploys to staging on push to develop
- **deploy-production.yml**: Deploys to production on push to main
- **rollback.yml**: Manual rollback workflow

### Deployment Process
1. Create PR → CI runs automatically
2. Merge to develop → Deploy to staging
3. Test in staging
4. Merge to main → Deploy to production (with approval)
5. Verify production deployment

## License

MIT License - See [LICENSE](LICENSE) file

---

## Quick Reference Commands

```bash
# Infrastructure
terraform plan -out=tfplan
terraform apply tfplan

# Application
docker-compose up
python -m src.cli discover

# Deployment
./scripts/build-and-push.sh production v1.0.0
gh workflow run deploy-production.yml

# Operations
./scripts/health-check.sh production
./scripts/daily-health-check.sh

# Incident Response
gh workflow run rollback.yml -f environment=production

# Testing
pytest tests/ -v
./scripts/run-load-tests.sh production

# Monitoring
aws cloudwatch get-dashboard --dashboard-name network-visualizer-production
```

---

**Last Updated**: 2025-01-18
**Version**: 1.0.0
**Maintainer**: DevOps Team
