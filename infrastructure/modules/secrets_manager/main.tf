# AWS Secrets Manager for Sensitive Configuration

# API Keys secret
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "network-visualizer/api-keys-${var.environment}"
  description             = "API keys and secrets for Network Visualizer"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "api-keys-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    api_gateway_key = var.api_gateway_key
    bedrock_api_key = var.bedrock_api_key
  })
}

# Database credentials (if using RDS in future)
resource "aws_secretsmanager_secret" "database" {
  name                    = "network-visualizer/database-${var.environment}"
  description             = "Database credentials for Network Visualizer"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "database-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = var.db_host
    port     = var.db_port
    database = var.db_name
  })
}

# Third-party integrations
resource "aws_secretsmanager_secret" "integrations" {
  name                    = "network-visualizer/integrations-${var.environment}"
  description             = "Third-party integration credentials"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "integrations-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "integrations" {
  secret_id = aws_secretsmanager_secret.integrations.id
  secret_string = jsonencode({
    slack_webhook_url = var.slack_webhook_url
    pagerduty_api_key = var.pagerduty_api_key
    datadog_api_key   = var.datadog_api_key
    github_token      = var.github_token
  })
}

# Encryption key configuration
resource "aws_secretsmanager_secret" "encryption_keys" {
  name                    = "network-visualizer/encryption-keys-${var.environment}"
  description             = "Encryption keys for data at rest"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "encryption-keys-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "encryption_keys" {
  secret_id = aws_secretsmanager_secret.encryption_keys.id
  secret_string = jsonencode({
    master_key = var.master_encryption_key
    salt       = var.encryption_salt
  })
}

# Automatic secret rotation for API keys
resource "aws_lambda_function" "rotate_api_keys" {
  count = var.enable_rotation ? 1 : 0

  filename      = data.archive_file.rotation_lambda[0].output_path
  function_name = "network-visualizer-rotate-api-keys-${var.environment}"
  role          = aws_iam_role.rotation_lambda[0].arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${var.aws_region}.amazonaws.com"
    }
  }
}

resource "aws_iam_role" "rotation_lambda" {
  count = var.enable_rotation ? 1 : 0

  name = "secrets-rotation-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "rotation_lambda" {
  count = var.enable_rotation ? 1 : 0

  name = "secrets-rotation-policy"
  role = aws_iam_role.rotation_lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.api_keys.arn,
          aws_secretsmanager_secret.integrations.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "rotation_lambda" {
  count = var.enable_rotation ? 1 : 0

  type        = "zip"
  output_path = "${path.module}/rotation_lambda.zip"

  source {
    content  = <<-EOT
import json
import boto3
import os

def handler(event, context):
    """Rotate API keys"""
    secret_id = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    client = boto3.client('secretsmanager')

    if step == "createSecret":
        # Generate new API key
        new_secret = {"api_gateway_key": "new-key-" + token[:8]}
        client.put_secret_value(
            SecretId=secret_id,
            ClientRequestToken=token,
            SecretString=json.dumps(new_secret),
            VersionStages=['AWSPENDING']
        )

    elif step == "setSecret":
        # Update the resource with new secret
        pass

    elif step == "testSecret":
        # Test the new secret
        pass

    elif step == "finishSecret":
        # Finalize rotation
        client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage='AWSCURRENT',
            MoveToVersionId=token,
            RemoveFromVersionId=event['PreviousVersionId']
        )

    return {"statusCode": 200}
EOT
    filename = "index.py"
  }
}

# Rotation schedule
resource "aws_secretsmanager_secret_rotation" "api_keys" {
  count = var.enable_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.api_keys.id
  rotation_lambda_arn = aws_lambda_function.rotate_api_keys[0].arn

  rotation_rules {
    automatically_after_days = var.rotation_days
  }
}

resource "aws_lambda_permission" "rotation" {
  count = var.enable_rotation ? 1 : 0

  statement_id  = "AllowSecretsManagerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotate_api_keys[0].function_name
  principal     = "secretsmanager.amazonaws.com"
}

# CloudWatch alarms for secret access
resource "aws_cloudwatch_log_metric_filter" "secret_access" {
  name           = "secret-access-${var.environment}"
  log_group_name = "/aws/lambda/network-visualizer-api-${var.environment}"
  pattern        = "[time, request_id, level, msg = *secret*]"

  metric_transformation {
    name      = "SecretAccessCount"
    namespace = "NetworkVisualizer"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "excessive_secret_access" {
  alarm_name          = "excessive-secret-access-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "SecretAccessCount"
  namespace           = "NetworkVisualizer"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.secret_access_threshold
  alarm_description   = "Excessive secret access detected"
  treat_missing_data  = "notBreaching"
}
