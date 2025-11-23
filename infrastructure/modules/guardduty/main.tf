# Amazon GuardDuty for Threat Detection

resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = var.enable_kubernetes_audit_logs
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = var.enable_malware_protection
        }
      }
    }
  }

  finding_publishing_frequency = var.finding_publishing_frequency

  tags = {
    Name        = "network-visualizer-guardduty-${var.environment}"
    Environment = var.environment
  }
}

# GuardDuty Filter for high severity findings
resource "aws_guardduty_filter" "high_severity" {
  name        = "high-severity-findings-${var.environment}"
  action      = "ARCHIVE" # or "NOOP" to keep them
  detector_id = aws_guardduty_detector.main.id
  rank        = 1

  finding_criteria {
    criterion {
      field  = "severity"
      equals = ["8", "9", "10"] # High and Critical
    }
  }
}

# SNS Topic for GuardDuty notifications
resource "aws_sns_topic" "guardduty_alerts" {
  name = "guardduty-alerts-${var.environment}"

  tags = {
    Name        = "guardduty-alerts-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "guardduty_email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.guardduty_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# EventBridge Rule for GuardDuty findings
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "guardduty-findings-${var.environment}"
  description = "Capture GuardDuty findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [
        { numeric = [">=", 7] } # High and Critical only
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "guardduty_sns" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.guardduty_alerts.arn

  input_transformer {
    input_paths = {
      severity    = "$.detail.severity"
      type        = "$.detail.type"
      description = "$.detail.description"
      region      = "$.detail.region"
      accountId   = "$.detail.accountId"
    }

    input_template = <<EOF
"GuardDuty Finding Alert

Severity: <severity>
Type: <type>
Description: <description>
Region: <region>
Account: <accountId>

Please investigate immediately."
EOF
  }
}

# Lambda function for automated response (optional)
resource "aws_lambda_function" "guardduty_responder" {
  count = var.enable_auto_response ? 1 : 0

  filename      = data.archive_file.guardduty_responder[0].output_path
  function_name = "guardduty-responder-${var.environment}"
  role          = aws_iam_role.guardduty_responder[0].arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      SNS_TOPIC_ARN = aws_sns_topic.guardduty_alerts.arn
    }
  }

  tags = {
    Name        = "guardduty-responder-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role" "guardduty_responder" {
  count = var.enable_auto_response ? 1 : 0

  name = "guardduty-responder-${var.environment}"

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

resource "aws_iam_role_policy" "guardduty_responder" {
  count = var.enable_auto_response ? 1 : 0

  name = "guardduty-responder-policy"
  role = aws_iam_role.guardduty_responder[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:StopInstances",
          "ec2:TerminateInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.guardduty_alerts.arn
      }
    ]
  })
}

data "archive_file" "guardduty_responder" {
  count = var.enable_auto_response ? 1 : 0

  type        = "zip"
  output_path = "${path.module}/guardduty_responder.zip"

  source {
    content  = <<-EOT
import json
import boto3
import os

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def handler(event, context):
    """Automated response to GuardDuty findings"""
    detail = event['detail']
    severity = detail['severity']
    finding_type = detail['type']

    print(f"Processing finding: {finding_type} (Severity: {severity})")

    # For critical findings on EC2 instances
    if severity >= 8 and 'UnauthorizedAccess:EC2' in finding_type:
        resource = detail.get('resource', {})
        instance_details = resource.get('instanceDetails', {})
        instance_id = instance_details.get('instanceId')

        if instance_id:
            print(f"CRITICAL: Stopping compromised instance {instance_id}")

            # Stop the instance
            ec2.stop_instances(InstanceIds=[instance_id])

            # Send notification
            sns.publish(
                TopicArn=os.environ['SNS_TOPIC_ARN'],
                Subject=f'CRITICAL: Instance {instance_id} stopped automatically',
                Message=f'Instance {instance_id} was stopped due to GuardDuty finding: {finding_type}'
            )

    return {
        'statusCode': 200,
        'body': json.dumps('Processed GuardDuty finding')
    }
EOT
    filename = "index.py"
  }
}

resource "aws_cloudwatch_event_target" "guardduty_lambda" {
  count = var.enable_auto_response ? 1 : 0

  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "InvokeLambda"
  arn       = aws_lambda_function.guardduty_responder[0].arn
}

resource "aws_lambda_permission" "guardduty_invoke" {
  count = var.enable_auto_response ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.guardduty_responder[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.guardduty_findings.arn
}

# SNS Topic Policy
resource "aws_sns_topic_policy" "guardduty_alerts" {
  arn = aws_sns_topic.guardduty_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action   = "SNS:Publish"
      Resource = aws_sns_topic.guardduty_alerts.arn
    }]
  })
}
