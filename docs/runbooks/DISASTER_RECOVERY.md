# Disaster Recovery Runbook

## Overview
This runbook provides procedures for recovering from various disaster scenarios.

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Service | RTO | RPO | Strategy |
|---------|-----|-----|----------|
| DynamoDB | < 1 hour | < 15 minutes | Point-in-time recovery + Daily backups |
| S3 | < 30 minutes | < 5 minutes | Cross-region replication + Versioning |
| Lambda | < 15 minutes | 0 (stateless) | Redeploy from source |
| API Gateway | < 15 minutes | 0 (configuration) | Terraform recreation |
| CloudFront | < 30 minutes | 0 (configuration) | Terraform recreation |

## Backup Schedule

- **Daily backups**: 5 AM UTC, retained for 30 days
- **Weekly backups**: 6 AM UTC Sundays, retained for 90 days
- **Monthly backups**: 7 AM UTC 1st of month, retained for 1 year

## Disaster Scenarios

### Scenario 1: Complete DynamoDB Table Loss

**Symptoms**: DynamoDB table deleted or corrupted

**Recovery Steps:**

1. **Identify Latest Backup**
```bash
# List available backups
aws dynamodb list-backups \
  --table-name network-visualizer-topology \
  --time-range-lower-bound $(date -u -d '30 days ago' +%s) \
  --query 'BackupSummaries[*].[BackupName,BackupCreationDateTime,BackupStatus]' \
  --output table

# Get the most recent backup ARN
BACKUP_ARN=$(aws dynamodb list-backups \
  --table-name network-visualizer-topology \
  --query 'BackupSummaries[0].BackupArn' \
  --output text)

echo "Latest backup: $BACKUP_ARN"
```

2. **Restore from Backup**
```bash
# Restore to new table
aws dynamodb restore-table-from-backup \
  --target-table-name network-visualizer-topology-restored \
  --backup-arn $BACKUP_ARN

# Wait for restore to complete
aws dynamodb wait table-exists \
  --table-name network-visualizer-topology-restored

# Check table status
aws dynamodb describe-table \
  --table-name network-visualizer-topology-restored \
  --query 'Table.TableStatus' \
  --output text
```

3. **Update Infrastructure**
```bash
# Update Terraform to use restored table
cd infrastructure/
terraform import aws_dynamodb_table.topology network-visualizer-topology-restored

# Or rename the restored table to original name
aws dynamodb update-table \
  --table-name network-visualizer-topology-restored \
  --attribute-definitions ... # (requires no active connections)
```

4. **Verify Data Integrity**
```bash
# Check item count
aws dynamodb describe-table \
  --table-name network-visualizer-topology-restored \
  --query 'Table.ItemCount' \
  --output text

# Sample data verification
aws dynamodb scan \
  --table-name network-visualizer-topology-restored \
  --limit 10 \
  --query 'Items[*]' \
  --output json
```

5. **Update Lambda Functions**
```bash
# Update environment variables to point to restored table
for func in discovery analysis api; do
  aws lambda update-function-configuration \
    --function-name network-visualizer-$func-production \
    --environment Variables={DYNAMODB_TABLE_NAME=network-visualizer-topology-restored}
done
```

**Expected RTO**: 45-60 minutes
**Expected RPO**: Up to 24 hours (last backup)

---

### Scenario 2: S3 Bucket Data Loss

**Symptoms**: S3 bucket deleted, objects missing, or corrupted

**Recovery Steps:**

1. **Check Versioning**
```bash
# List deleted objects (if versioning enabled)
aws s3api list-object-versions \
  --bucket network-visualizer-data-production \
  --query 'DeleteMarkers[*].[Key,VersionId,LastModified]' \
  --output table

# Restore deleted object
aws s3api delete-object \
  --bucket network-visualizer-data-production \
  --key topologies/us-east-1/vpc-123/2025-01-18.json \
  --version-id <delete-marker-version-id>
```

2. **Restore from Cross-Region Replica** (if enabled)
```bash
# Sync from replica bucket
aws s3 sync \
  s3://network-visualizer-data-production-replica/ \
  s3://network-visualizer-data-production/ \
  --source-region us-west-2 \
  --region us-east-1
```

3. **Restore from AWS Backup** (if enabled)
```bash
# List recovery points
aws backup list-recovery-points-by-backup-vault \
  --backup-vault-name network-visualizer-vault-production \
  --by-resource-arn arn:aws:s3:::network-visualizer-data-production

# Start restore job
aws backup start-restore-job \
  --recovery-point-arn <recovery-point-arn> \
  --iam-role-arn <backup-role-arn> \
  --metadata bucket=network-visualizer-data-production-restored
```

**Expected RTO**: 15-30 minutes
**Expected RPO**: < 5 minutes (with replication)

---

### Scenario 3: Complete Region Failure

**Symptoms**: All services in primary region unavailable

**Recovery Steps:**

1. **Activate DR Region**
```bash
# Set environment to DR region
export AWS_DEFAULT_REGION=us-west-2
export DR_REGION=us-west-2
```

2. **Deploy Infrastructure in DR Region**
```bash
cd infrastructure/
terraform workspace select production-dr || terraform workspace new production-dr

terraform apply \
  -var="aws_region=$DR_REGION" \
  -var="environment=production-dr" \
  -var="s3_bucket_name=network-visualizer-data-production-dr" \
  -var="frontend_bucket_name=network-visualizer-frontend-production-dr" \
  -auto-approve
```

3. **Restore Data**
```bash
# DynamoDB: Use cross-region replica or restore from backup
# S3: Already replicated if enabled

# Point Lambda functions to DR DynamoDB table
for func in discovery analysis api; do
  aws lambda update-function-configuration \
    --function-name network-visualizer-$func-production-dr \
    --region $DR_REGION \
    --environment Variables={DYNAMODB_TABLE_NAME=network-visualizer-topology-dr,AWS_REGION=$DR_REGION}
done
```

4. **Update DNS**
```bash
# Update Route53 to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.network-visualizer.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "<dr-api-gateway-hosted-zone>",
          "DNSName": "<dr-api-gateway-domain>",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'

# Update CloudFront origin
aws cloudfront update-distribution \
  --id $CLOUDFRONT_DIST_ID \
  --distribution-config file://dr-distribution-config.json
```

5. **Verify DR Environment**
```bash
# Run health checks
curl -f https://api.network-visualizer.com/health

# Run smoke tests
pytest tests/smoke/ --api-endpoint=https://api.network-visualizer.com
```

**Expected RTO**: 2-4 hours (full region failover)
**Expected RPO**: 15 minutes (with replication)

---

### Scenario 4: Accidental Lambda Deployment Failure

**Symptoms**: Lambda function not working after deployment, high error rate

**Recovery Steps:**

1. **Identify Last Known Good Version**
```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name network-visualizer-api-production \
  --query 'Versions[*].[Version,LastModified,Description]' \
  --output table

# Get current live alias
aws lambda get-alias \
  --function-name network-visualizer-api-production \
  --name live \
  --query '[FunctionVersion,Description]' \
  --output text
```

2. **Rollback to Previous Version**
```bash
# Update alias to point to previous version
aws lambda update-alias \
  --function-name network-visualizer-api-production \
  --name live \
  --function-version <previous-version>

# Or use GitHub Actions rollback workflow
gh workflow run rollback.yml \
  -f environment=production \
  -f lambda_version=<version-number>
```

3. **Verify Rollback**
```bash
# Check error rate after rollback
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=network-visualizer-api-production \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum
```

**Expected RTO**: 5-10 minutes
**Expected RPO**: 0 (stateless)

---

## DR Testing Schedule

### Quarterly DR Drill

**Schedule**: Every quarter (Jan, Apr, Jul, Oct)

**Procedure:**
```bash
# 1. Announce DR drill
# 2. Simulate failure in staging environment
# 3. Execute recovery procedures
# 4. Document time to recovery
# 5. Identify improvements
# 6. Update runbook
```

**Drill Checklist:**
- [ ] DynamoDB restore test
- [ ] S3 restore test
- [ ] Lambda rollback test
- [ ] Cross-region failover test
- [ ] DNS failover test
- [ ] Verify RTO/RPO targets met
- [ ] Document lessons learned

### Monthly Backup Verification

```bash
#!/bin/bash
# verify-backups.sh

echo "=== Monthly Backup Verification ==="

# 1. Verify DynamoDB backups exist
BACKUP_COUNT=$(aws dynamodb list-backups \
  --table-name network-visualizer-topology \
  --time-range-lower-bound $(date -u -d '7 days ago' +%s) \
  --query 'length(BackupSummaries)' \
  --output text)

echo "DynamoDB backups (last 7 days): $BACKUP_COUNT"
if [ "$BACKUP_COUNT" -lt 7 ]; then
  echo "⚠️  WARNING: Expected at least 7 daily backups"
fi

# 2. Test restore of sample data
aws dynamodb restore-table-from-backup \
  --target-table-name test-restore-$(date +%Y%m%d) \
  --backup-arn $(aws dynamodb list-backups \
    --table-name network-visualizer-topology \
    --query 'BackupSummaries[0].BackupArn' --output text)

# 3. Verify S3 replication lag
if [ "$ENABLE_S3_REPLICATION" = "true" ]; then
  aws s3api get-bucket-replication \
    --bucket network-visualizer-data-production \
    --query 'ReplicationConfiguration.Rules[0].Status'
fi

echo "✅ Backup verification complete"
```

---

## Post-DR Procedures

### 1. Service Restoration Verification
- [ ] All Lambda functions operational
- [ ] DynamoDB responding to queries
- [ ] S3 objects accessible
- [ ] API Gateway returning 200s
- [ ] Frontend loading correctly
- [ ] No active alarms

### 2. Data Integrity Check
```bash
# Run data validation scripts
python scripts/validate-topology-data.py --comprehensive

# Compare record counts pre/post disaster
aws dynamodb describe-table \
  --table-name network-visualizer-topology \
  --query 'Table.ItemCount'
```

### 3. Post-Incident Review
- Schedule PIR within 48 hours
- Document actual RTO/RPO achieved
- Identify process improvements
- Update runbooks
- Update DR plan

---

## Emergency Contacts

- **On-Call Engineer**: PagerDuty rotation
- **DR Coordinator**: [Name, Phone, Email]
- **AWS Support**: 1-877-AWS-SUPPORT (Enterprise)
- **AWS TAM**: [Name, Email] (if applicable)

## Important Links

- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/
- Backup Vault: https://console.aws.amazon.com/backup/
- DR Region Dashboard: https://us-west-2.console.aws.amazon.com/
- Runbook Repository: https://github.com/org/network-visualizer/docs/runbooks
