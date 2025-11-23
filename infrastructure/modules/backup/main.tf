# AWS Backup for Automated Backups

# Backup vault
resource "aws_backup_vault" "main" {
  name        = "network-visualizer-vault-${var.environment}"
  kms_key_arn = var.kms_key_arn

  tags = {
    Name        = "network-visualizer-vault-${var.environment}"
    Environment = var.environment
  }
}

# Backup plan
resource "aws_backup_plan" "main" {
  name = "network-visualizer-backup-${var.environment}"

  # Daily backups with 30-day retention
  rule {
    rule_name         = "daily_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 * * ? *)" # 5 AM UTC daily

    lifecycle {
      delete_after = 30
    }

    recovery_point_tags = {
      Type        = "Daily"
      Environment = var.environment
    }
  }

  # Weekly backups with 90-day retention
  rule {
    rule_name         = "weekly_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 6 ? * SUN *)" # 6 AM UTC on Sundays

    lifecycle {
      delete_after = 90
    }

    recovery_point_tags = {
      Type        = "Weekly"
      Environment = var.environment
    }
  }

  # Monthly backups with 1-year retention
  rule {
    rule_name         = "monthly_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 7 1 * ? *)" # 7 AM UTC on 1st of month

    lifecycle {
      delete_after = 365
    }

    recovery_point_tags = {
      Type        = "Monthly"
      Environment = var.environment
    }
  }

  tags = {
    Name        = "network-visualizer-backup-plan-${var.environment}"
    Environment = var.environment
  }
}

# IAM role for AWS Backup
resource "aws_iam_role" "backup" {
  name = "aws-backup-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "backup.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# Backup selection for DynamoDB table
resource "aws_backup_selection" "dynamodb" {
  name         = "dynamodb-backup-selection-${var.environment}"
  plan_id      = aws_backup_plan.main.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    var.dynamodb_table_arn
  ]

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupEnabled"
      value = "true"
    }
  }
}

# Backup selection for S3 bucket (if enabled)
resource "aws_backup_selection" "s3" {
  count = var.enable_s3_backup ? 1 : 0

  name         = "s3-backup-selection-${var.environment}"
  plan_id      = aws_backup_plan.main.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    var.s3_bucket_arn
  ]
}

# CloudWatch alarm for backup failures
resource "aws_cloudwatch_metric_alarm" "backup_job_failed" {
  alarm_name          = "backup-job-failed-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfBackupJobsFailed"
  namespace           = "AWS/Backup"
  period              = "3600"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Backup job failed"
  treat_missing_data  = "notBreaching"

  dimensions = {
    BackupVaultName = aws_backup_vault.main.name
  }

  alarm_actions = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []
}

# Point-in-time recovery for DynamoDB (separate from AWS Backup)
resource "aws_dynamodb_table_replica" "cross_region" {
  count = var.enable_cross_region_replica ? 1 : 0

  global_table_arn = var.dynamodb_table_arn

  tags = {
    Name        = "network-visualizer-dynamodb-replica-${var.environment}"
    Environment = var.environment
  }
}

# S3 Cross-Region Replication for disaster recovery
resource "aws_s3_bucket_replication_configuration" "disaster_recovery" {
  count = var.enable_s3_replication ? 1 : 0

  role   = aws_iam_role.s3_replication[0].arn
  bucket = var.s3_bucket_id

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = var.s3_replica_bucket_arn
      storage_class = "STANDARD_IA"

      replication_time {
        status = "Enabled"
        time {
          minutes = 15
        }
      }

      metrics {
        status = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }
  }
}

resource "aws_iam_role" "s3_replication" {
  count = var.enable_s3_replication ? 1 : 0

  name = "s3-replication-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "s3_replication" {
  count = var.enable_s3_replication ? 1 : 0

  name = "s3-replication-policy"
  role = aws_iam_role.s3_replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete"
        ]
        Resource = "${var.s3_replica_bucket_arn}/*"
      }
    ]
  })
}
