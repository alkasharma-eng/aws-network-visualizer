#!/bin/bash
# Verify backup integrity and availability
# Usage: ./scripts/verify-backups.sh <environment>

set -e

ENVIRONMENT=${1:-production}

echo "========================================="
echo "Backup Verification for $ENVIRONMENT"
echo "========================================="

# 1. Check DynamoDB backups
echo "\n1. Checking DynamoDB Backups..."
BACKUP_COUNT=$(aws dynamodb list-backups \
  --table-name network-visualizer-topology \
  --time-range-lower-bound $(date -u -d '7 days ago' +%s) \
  --query 'length(BackupSummaries)' \
  --output text)

echo "  Daily backups (last 7 days): $BACKUP_COUNT"
if [ "$BACKUP_COUNT" -lt 7 ]; then
  echo "  ⚠️  WARNING: Expected at least 7 daily backups, found $BACKUP_COUNT"
else
  echo "  ✅ Daily backups OK"
fi

# 2. Check AWS Backup jobs
echo "\n2. Checking AWS Backup Jobs..."
FAILED_JOBS=$(aws backup list-backup-jobs \
  --by-backup-vault-name network-visualizer-vault-$ENVIRONMENT \
  --by-created-after $(date -u -d '7 days ago' +%Y-%m-%d) \
  --query 'BackupJobs[?State==`FAILED`] | length(@)' \
  --output text)

echo "  Failed backup jobs (last 7 days): $FAILED_JOBS"
if [ "$FAILED_JOBS" -gt 0 ]; then
  echo "  ⚠️  WARNING: $FAILED_JOBS failed backup jobs detected"
else
  echo "  ✅ No failed backup jobs"
fi

# 3. Verify S3 versioning
echo "\n3. Checking S3 Versioning..."
VERSIONING_STATUS=$(aws s3api get-bucket-versioning \
  --bucket network-visualizer-data-$ENVIRONMENT \
  --query 'Status' \
  --output text)

echo "  S3 versioning status: $VERSIONING_STATUS"
if [ "$VERSIONING_STATUS" != "Enabled" ]; then
  echo "  ⚠️  WARNING: S3 versioning not enabled"
else
  echo "  ✅ S3 versioning enabled"
fi

# 4. Check point-in-time recovery
echo "\n4. Checking DynamoDB PITR..."
PITR_STATUS=$(aws dynamodb describe-continuous-backups \
  --table-name network-visualizer-topology \
  --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' \
  --output text)

echo "  PITR status: $PITR_STATUS"
if [ "$PITR_STATUS" != "ENABLED" ]; then
  echo "  ⚠️  WARNING: Point-in-time recovery not enabled"
else
  echo "  ✅ PITR enabled"
fi

echo "\n========================================="
echo "Backup Verification Complete"
echo "========================================="
