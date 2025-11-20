# Incident Response Runbook

## Overview
This runbook provides step-by-step procedures for responding to incidents in the AWS Network Visualizer production environment.

## Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| **P0 - Critical** | Complete service outage | < 15 minutes | Immediate |
| **P1 - High** | Major degradation affecting >50% users | < 30 minutes | Within 1 hour |
| **P2 - Medium** | Partial degradation affecting <50% users | < 2 hours | Within 4 hours |
| **P3 - Low** | Minor issues, no user impact | < 8 hours | Next business day |

## Incident Response Team

- **On-Call Engineer**: First responder, incident commander
- **DevOps Lead**: Escalation point for P0/P1 incidents
- **Platform Architect**: Technical escalation for complex issues
- **Product Manager**: Business impact assessment

## Initial Response (First 15 Minutes)

### 1. Acknowledge the Alert
```bash
# Via PagerDuty, Slack, or monitoring dashboard
# Document incident start time
INCIDENT_TIME=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
```

### 2. Create Incident Channel
```bash
# Create dedicated Slack channel
# Format: #incident-YYYY-MM-DD-brief-description
# Example: #incident-2025-01-18-api-gateway-down
```

### 3. Assess Impact
```bash
# Check CloudWatch Dashboard
aws cloudwatch get-dashboard \
  --dashboard-name network-visualizer-production

# Check API health
curl -f https://api.network-visualizer.com/health

# Check error rates
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=network-visualizer-api-production \
  --start-time $(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### 4. Notify Stakeholders
- Post initial update in incident channel
- Page additional team members if P0/P1
- Update status page (if applicable)

## Common Incident Scenarios

## Scenario 1: API Gateway 5XX Errors

### Symptoms
- High 5XX error rate in CloudWatch
- Increased Lambda errors
- User reports of API failures

### Investigation Steps

1. **Check Lambda Function Health**
```bash
# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=network-visualizer-api-production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Check Lambda logs
aws logs tail /aws/lambda/network-visualizer-api-production --follow
```

2. **Check DynamoDB Throttling**
```bash
# Check DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=network-visualizer-topology \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

3. **Check X-Ray Traces**
```bash
# Get trace summaries
aws xray get-trace-summaries \
  --start-time $(date -u -d '15 minutes ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'error = true'
```

### Resolution Steps

**Option A: Lambda Memory/Timeout Issues**
```bash
# Increase Lambda memory
aws lambda update-function-configuration \
  --function-name network-visualizer-api-production \
  --memory-size 1024 \
  --timeout 60
```

**Option B: DynamoDB Throttling**
```bash
# Switch to on-demand billing temporarily
aws dynamodb update-table \
  --table-name network-visualizer-topology \
  --billing-mode PAY_PER_REQUEST
```

**Option C: Rollback Recent Deployment**
```bash
# Rollback to previous Lambda version
cd infrastructure/
terraform workspace select production
terraform plan -var="lambda_version=previous"
terraform apply -auto-approve

# Or use GitHub Actions rollback workflow
gh workflow run rollback.yml \
  -f environment=production \
  -f lambda_version=3
```

### Verification
```bash
# Monitor error rates for 5 minutes
watch -n 10 'aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=network-visualizer-api-production \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum'
```

---

## Scenario 2: Frontend Not Loading

### Symptoms
- Users report blank page or loading errors
- CloudFront errors
- S3 access issues

### Investigation Steps

1. **Check CloudFront Distribution**
```bash
# Get distribution status
aws cloudfront get-distribution \
  --id $CLOUDFRONT_DIST_ID

# Check CloudFront metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 4xxErrorRate \
  --dimensions Name=DistributionId,Value=$CLOUDFRONT_DIST_ID \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

2. **Check S3 Bucket**
```bash
# Verify S3 bucket exists and has content
aws s3 ls s3://network-visualizer-frontend-production/

# Check bucket policy
aws s3api get-bucket-policy --bucket network-visualizer-frontend-production
```

3. **Test Direct S3 Access**
```bash
# Test if index.html exists
aws s3api head-object \
  --bucket network-visualizer-frontend-production \
  --key index.html
```

### Resolution Steps

**Option A: CloudFront Cache Issue**
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DIST_ID \
  --paths "/*"
```

**Option B: Missing Files in S3**
```bash
# Redeploy frontend
cd frontend/
npm run build
aws s3 sync dist/ s3://network-visualizer-frontend-production/ --delete
```

**Option C: Broken CORS Configuration**
```bash
# Update CORS policy
aws s3api put-bucket-cors \
  --bucket network-visualizer-frontend-production \
  --cors-configuration file://cors-config.json
```

---

## Scenario 3: High Lambda Costs

### Symptoms
- Unexpected AWS bill spike
- High Lambda invocation count
- Increased CloudWatch costs

### Investigation Steps

1. **Check Lambda Invocations**
```bash
# Get invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=network-visualizer-discovery-production \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

2. **Check EventBridge Rules**
```bash
# List active rules
aws events list-rules --name-prefix network-visualizer

# Check rule details
aws events describe-rule --name network-visualizer-discovery-schedule-production
```

3. **Review Cost Explorer**
```bash
# Get cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Resolution Steps

**Option A: Disable Excessive Schedules**
```bash
# Disable EventBridge rule
aws events disable-rule --name network-visualizer-discovery-schedule-production
```

**Option B: Adjust Lambda Memory/Timeout**
```bash
# Reduce memory to minimum required
aws lambda update-function-configuration \
  --function-name network-visualizer-discovery-production \
  --memory-size 512 \
  --timeout 300
```

**Option C: Implement Rate Limiting**
```bash
# Update API Gateway throttling
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/throttle/rateLimit,value=100
```

---

## Scenario 4: Data Loss or Corruption

### Symptoms
- Missing topology data
- Incorrect graph relationships
- DynamoDB scan errors

### Investigation Steps

1. **Check DynamoDB Backups**
```bash
# List available backups
aws dynamodb list-backups \
  --table-name network-visualizer-topology

# Describe latest backup
aws dynamodb describe-backup --backup-arn $BACKUP_ARN
```

2. **Check S3 Versioning**
```bash
# List object versions
aws s3api list-object-versions \
  --bucket network-visualizer-data-production \
  --prefix topologies/
```

3. **Verify Data Integrity**
```bash
# Run data validation Lambda
aws lambda invoke \
  --function-name network-visualizer-validate-data-production \
  --payload '{"action": "validate"}' \
  response.json
```

### Resolution Steps

**Option A: Restore from DynamoDB Backup**
```bash
# Restore table from backup
aws dynamodb restore-table-from-backup \
  --target-table-name network-visualizer-topology-restored \
  --backup-arn $BACKUP_ARN

# Wait for restore to complete
aws dynamodb wait table-exists --table-name network-visualizer-topology-restored

# Swap tables (update Terraform)
```

**Option B: Restore from S3**
```bash
# Restore specific version from S3
aws s3api get-object \
  --bucket network-visualizer-data-production \
  --key topologies/us-east-1/vpc-123/2025-01-17.json \
  --version-id $VERSION_ID \
  restored-topology.json

# Re-import to DynamoDB
python scripts/import-topology.py --file restored-topology.json
```

---

## Post-Incident Procedures

### 1. Incident Resolution
- Verify service is fully operational
- Monitor for 30 minutes after resolution
- Clear all alarms

### 2. Communication
```markdown
## Incident Resolved

**Incident**: [Brief description]
**Duration**: [Start time] - [End time]
**Impact**: [User impact description]
**Root Cause**: [Brief root cause]
**Resolution**: [What was done]

Next steps:
- [ ] Post-incident review scheduled
- [ ] Documentation updated
- [ ] Preventive measures identified
```

### 3. Post-Incident Review (Within 48 Hours)
- Schedule PIR meeting with team
- Document timeline of events
- Identify root cause
- Create action items to prevent recurrence
- Update runbooks based on learnings

### PIR Template
```markdown
# Post-Incident Review: [Incident Title]

## Incident Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours
- **Severity**: PX
- **Impact**: [User impact, revenue impact]

## Timeline
- **HH:MM UTC**: Alert triggered
- **HH:MM UTC**: Team acknowledged
- **HH:MM UTC**: Root cause identified
- **HH:MM UTC**: Fix deployed
- **HH:MM UTC**: Service restored

## Root Cause
[Detailed root cause analysis]

## What Went Well
- [Things that worked well]

## What Didn't Go Well
- [Areas for improvement]

## Action Items
- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]
```

## Emergency Contacts

- **On-Call Engineer**: PagerDuty rotation
- **DevOps Lead**: [Contact info]
- **AWS Support**: 1-877-AWS-SUPPORT (Premium Support)
- **Slack Channel**: #platform-incidents

## Useful Commands Reference

### Quick Health Check
```bash
#!/bin/bash
# health-check.sh
echo "=== API Health ==="
curl -sf https://api.network-visualizer.com/health || echo "API DOWN"

echo "=== Lambda Functions ==="
for func in discovery analysis api; do
  aws lambda get-function --function-name network-visualizer-$func-production \
    --query 'Configuration.LastUpdateStatus' --output text
done

echo "=== DynamoDB ==="
aws dynamodb describe-table --table-name network-visualizer-topology \
  --query 'Table.TableStatus' --output text

echo "=== CloudFront ==="
aws cloudfront get-distribution --id $CLOUDFRONT_DIST_ID \
  --query 'Distribution.Status' --output text
```

### Enable Debug Logging
```bash
# Enable debug logs for Lambda function
aws lambda update-function-configuration \
  --function-name network-visualizer-api-production \
  --environment "Variables={LOG_LEVEL=DEBUG}"
```

### Emergency Shutdown
```bash
# Disable all EventBridge rules
for rule in $(aws events list-rules --name-prefix network-visualizer --query 'Rules[].Name' --output text); do
  aws events disable-rule --name $rule
done

# Set API Gateway to maintenance mode
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/throttle/rateLimit,value=0
```
