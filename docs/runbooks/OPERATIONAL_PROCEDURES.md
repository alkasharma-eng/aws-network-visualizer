# Operational Procedures

## Table of Contents
1. [Daily Operations](#daily-operations)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Reviews](#monthly-reviews)
4. [Deployment Procedures](#deployment-procedures)
5. [Backup and Recovery](#backup-and-recovery)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Scaling Procedures](#scaling-procedures)

---

## Daily Operations

### Morning Health Check (10 minutes)

```bash
#!/bin/bash
# daily-health-check.sh

echo "========================================="
echo "Daily Health Check - $(date)"
echo "========================================="

# 1. Check all Lambda functions
echo "\n1. Lambda Function Status:"
for func in discovery analysis api; do
  status=$(aws lambda get-function \
    --function-name network-visualizer-$func-production \
    --query 'Configuration.LastUpdateStatus' --output text)
  echo "  - $func: $status"
done

# 2. Check DynamoDB table
echo "\n2. DynamoDB Status:"
aws dynamodb describe-table \
  --table-name network-visualizer-topology \
  --query 'Table.[TableStatus,ItemCount,TableSizeBytes]' \
  --output text

# 3. Check CloudWatch Alarms
echo "\n3. Active Alarms:"
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --query 'MetricAlarms[].AlarmName' \
  --output table

# 4. Check API Gateway health
echo "\n4. API Gateway:"
http_code=$(curl -s -o /dev/null -w "%{http_code}" https://api.network-visualizer.com/health)
if [ $http_code -eq 200 ]; then
  echo "  ✓ API Gateway healthy (HTTP $http_code)"
else
  echo "  ✗ API Gateway unhealthy (HTTP $http_code)"
fi

# 5. Check CloudFront distribution
echo "\n5. CloudFront Status:"
aws cloudfront get-distribution \
  --id $CLOUDFRONT_DIST_ID \
  --query 'Distribution.Status' \
  --output text

# 6. Check yesterday's error rate
echo "\n6. Yesterday's Error Rate:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text

echo "\n========================================="
echo "Health check complete"
echo "=========================================\n"
```

### Log Review (15 minutes)

```bash
# Review critical errors from last 24 hours
aws logs filter-log-events \
  --log-group-name /aws/lambda/network-visualizer-api-production \
  --start-time $(date -u -d '24 hours ago' +%s)000 \
  --filter-pattern "ERROR" \
  --query 'events[*].[timestamp,message]' \
  --output table | head -50
```

---

## Weekly Maintenance

### Security Review (30 minutes)

1. **Review IAM Access**
```bash
# Check for unused IAM roles
aws iam generate-credential-report
sleep 10
aws iam get-credential-report --query 'Content' --output text | base64 -d > credentials.csv

# Review for:
# - Unused access keys (>90 days)
# - Inactive users
# - Overly permissive policies
```

2. **Check for Security Vulnerabilities**
```bash
# Run Trivy scan on Lambda functions
docker run --rm -v $(pwd):/src aquasec/trivy fs /src

# Check ECR scan results
aws ecr describe-image-scan-findings \
  --repository-name network-visualizer-app-production \
  --image-id imageTag=latest
```

3. **Review CloudTrail Logs**
```bash
# Check for suspicious API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteBucket \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 50
```

### Performance Review (20 minutes)

1. **Lambda Performance**
```bash
# Check Lambda duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=network-visualizer-discovery-production \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average,Maximum \
  --query 'Datapoints' \
  --output table
```

2. **DynamoDB Performance**
```bash
# Check read/write capacity utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=network-visualizer-topology \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --output table
```

3. **API Response Times**
```bash
# Check P95 latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=network-visualizer-api-production \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --extended-statistics p95 \
  --output table
```

### Cost Review (15 minutes)

```bash
# Get weekly cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --output table

# Check for cost anomalies
aws ce get-anomalies \
  --date-interval Start=$(date -u -d '7 days ago' +%Y-%m-%d) \
  --max-results 10
```

---

## Monthly Reviews

### 1. Capacity Planning (1 hour)

**Review growth trends:**
```python
# capacity-review.py
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')

# Get 30-day trends
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

metrics = [
    ('AWS/Lambda', 'Invocations'),
    ('AWS/DynamoDB', 'ConsumedReadCapacityUnits'),
    ('AWS/S3', 'NumberOfObjects'),
    ('AWS/ApiGateway', 'Count')
]

for namespace, metric_name in metrics:
    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,
        Statistics=['Sum']
    )
    print(f"{namespace}/{metric_name}:")
    print(f"  Average: {sum(d['Sum'] for d in response['Datapoints']) / len(response['Datapoints'])}")
    print(f"  Max: {max(d['Sum'] for d in response['Datapoints'])}")
```

### 2. Cost Optimization (1 hour)

```bash
# Identify underutilized resources
# 1. Low Lambda invocation counts
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 2592000 \
  --statistics Sum \
  --output table

# 2. Check for old S3 objects
aws s3api list-objects-v2 \
  --bucket network-visualizer-data-production \
  --query 'Contents[?LastModified<`2024-01-01`].[Key,Size,LastModified]' \
  --output table

# 3. Review Reserved Capacity opportunities
aws ce get-reservation-purchase-recommendation \
  --service DynamoDB \
  --lookback-period THIRTY_DAYS
```

### 3. Security Audit (1 hour)

```bash
# Run AWS Trusted Advisor checks
aws support describe-trusted-advisor-checks \
  --language en \
  --query 'checks[?category==`security`].id' \
  --output text | \
while read check_id; do
  aws support describe-trusted-advisor-check-result --check-id $check_id
done

# Check for public S3 buckets
aws s3api list-buckets --query 'Buckets[].Name' --output text | \
while read bucket; do
  echo "Checking $bucket..."
  aws s3api get-bucket-policy-status --bucket $bucket 2>/dev/null || echo "  No policy"
done
```

---

## Deployment Procedures

### Standard Deployment (Non-Production)

```bash
# 1. Run pre-deployment checks
./scripts/pre-deployment-checks.sh staging

# 2. Deploy infrastructure
cd infrastructure/
terraform workspace select staging
terraform plan -out=tfplan
terraform apply tfplan

# 3. Deploy application code
gh workflow run deploy-staging.yml

# 4. Run smoke tests
pytest tests/smoke/ --env=staging

# 5. Monitor for 15 minutes
watch -n 30 './scripts/health-check.sh staging'
```

### Production Deployment (High Risk)

**Requires:**
- [ ] Change request approved
- [ ] Code review completed
- [ ] Tests passed in staging
- [ ] Rollback plan documented
- [ ] On-call engineer notified

```bash
# 1. Pre-deployment announcement
# Post in #platform-deployments Slack channel

# 2. Take pre-deployment snapshot
aws dynamodb create-backup \
  --table-name network-visualizer-topology \
  --backup-name pre-deployment-$(date +%Y%m%d-%H%M%S)

# 3. Deploy with gradual rollout
# Phase 1: Deploy to 10% of traffic
gh workflow run deploy-production.yml -f traffic_percentage=10

# Wait 30 minutes, monitor error rates

# Phase 2: Deploy to 50% of traffic
gh workflow run deploy-production.yml -f traffic_percentage=50

# Wait 30 minutes, monitor error rates

# Phase 3: Deploy to 100% of traffic
gh workflow run deploy-production.yml -f traffic_percentage=100

# 4. Post-deployment verification
./scripts/production-verification.sh

# 5. Post-deployment announcement
# Update #platform-deployments with results
```

---

## Backup and Recovery

### Daily Backups

**Automated via Lambda (verify):**
```bash
# Check backup schedule
aws events list-rules --name-prefix network-visualizer-backup

# Verify latest backup
aws dynamodb list-backups \
  --table-name network-visualizer-topology \
  --time-range-lower-bound $(date -u -d '48 hours ago' +%s) \
  --query 'BackupSummaries[0].[BackupName,BackupCreationDateTime,BackupStatus]' \
  --output table
```

### Manual Backup (Before Major Changes)

```bash
# DynamoDB backup
aws dynamodb create-backup \
  --table-name network-visualizer-topology \
  --backup-name manual-backup-$(date +%Y%m%d-%H%M%S)

# S3 backup (entire bucket)
aws s3 sync s3://network-visualizer-data-production \
  s3://network-visualizer-data-production-backup/$(date +%Y%m%d)/ \
  --storage-class GLACIER
```

### Recovery Testing (Monthly)

```bash
# Test restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name network-visualizer-topology-test-restore \
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/network-visualizer-topology/backup/01234567890123-abc123

# Verify data integrity
python scripts/verify-restore.py --table network-visualizer-topology-test-restore

# Clean up test table
aws dynamodb delete-table --table-name network-visualizer-topology-test-restore
```

---

## Monitoring and Alerting

### CloudWatch Dashboard Setup

```bash
# Create production dashboard
aws cloudwatch put-dashboard \
  --dashboard-name network-visualizer-production \
  --dashboard-body file://monitoring/cloudwatch_dashboard.json
```

### Alert Tuning

**Review alert thresholds monthly:**
```bash
# Get alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name network-visualizer-high-error-rate \
  --start-date $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --history-item-type StateUpdate \
  --query 'AlarmHistoryItems[*].[Timestamp,HistorySummary]' \
  --output table

# Adjust if too noisy or not sensitive enough
```

---

## Scaling Procedures

### Vertical Scaling (Lambda)

```bash
# Increase Lambda memory/timeout
aws lambda update-function-configuration \
  --function-name network-visualizer-discovery-production \
  --memory-size 2048 \
  --timeout 900
```

### Horizontal Scaling (DynamoDB)

```bash
# Switch to on-demand (automatic scaling)
aws dynamodb update-table \
  --table-name network-visualizer-topology \
  --billing-mode PAY_PER_REQUEST

# Or increase provisioned capacity
aws dynamodb update-table \
  --table-name network-visualizer-topology \
  --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=50
```

### API Gateway Throttling

```bash
# Increase rate limits
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/throttle/burstLimit,value=10000 \
    op=replace,path=/throttle/rateLimit,value=20000
```

---

## Useful Scripts

### scripts/pre-deployment-checks.sh
```bash
#!/bin/bash
# Pre-deployment validation

ENVIRONMENT=$1

echo "Running pre-deployment checks for $ENVIRONMENT..."

# 1. Verify all tests pass
pytest tests/ || exit 1

# 2. Check Terraform syntax
terraform fmt -check -recursive infrastructure/ || exit 1
cd infrastructure && terraform validate || exit 1

# 3. Check for secrets in code
git secrets --scan || exit 1

# 4. Verify Docker images build
docker build -t test-build . || exit 1

echo "✓ All pre-deployment checks passed"
```

### scripts/production-verification.sh
```bash
#!/bin/bash
# Post-deployment verification

echo "Running production verification..."

# Check API health
if ! curl -sf https://api.network-visualizer.com/health; then
  echo "✗ API health check failed"
  exit 1
fi

# Check error rates
ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 600 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text)

if [ "$ERROR_COUNT" != "None" ] && [ "$ERROR_COUNT" -gt 10 ]; then
  echo "✗ High error count: $ERROR_COUNT"
  exit 1
fi

echo "✓ Production verification passed"
```
