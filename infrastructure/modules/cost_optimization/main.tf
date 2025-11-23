# AWS Cost Optimization and Monitoring

# AWS Budgets
resource "aws_budgets_budget" "monthly" {
  name         = "network-visualizer-monthly-${var.environment}"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.budget_alert_emails
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["Environment$${var.environment}"]
  }
}

# Service-specific budgets
resource "aws_budgets_budget" "lambda" {
  name         = "network-visualizer-lambda-${var.environment}"
  budget_type  = "COST"
  limit_amount = var.lambda_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  cost_filter {
    name   = "Service"
    values = ["AWS Lambda"]
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["Environment$${var.environment}"]
  }
}

resource "aws_budgets_budget" "dynamodb" {
  name         = "network-visualizer-dynamodb-${var.environment}"
  budget_type  = "COST"
  limit_amount = var.dynamodb_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  cost_filter {
    name   = "Service"
    values = ["Amazon DynamoDB"]
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["Environment$${var.environment}"]
  }
}

# Cost Anomaly Detection
resource "aws_ce_anomaly_monitor" "service_monitor" {
  name              = "network-visualizer-service-monitor-${var.environment}"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  monitor_specification = jsonencode({
    Tags = {
      Key    = "Environment"
      Values = [var.environment]
    }
  })
}

resource "aws_ce_anomaly_subscription" "alerts" {
  name      = "network-visualizer-cost-anomalies-${var.environment}"
  frequency = "DAILY"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.service_monitor.arn
  ]

  subscriber {
    type    = "EMAIL"
    address = var.cost_anomaly_email
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = [var.anomaly_threshold_dollars]
    }
  }
}

# Lambda for cost optimization recommendations
resource "aws_lambda_function" "cost_optimizer" {
  filename      = data.archive_file.cost_optimizer.output_path
  function_name = "network-visualizer-cost-optimizer-${var.environment}"
  role          = aws_iam_role.cost_optimizer.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      SNS_TOPIC_ARN  = aws_sns_topic.cost_alerts.arn
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  tags = {
    Name        = "cost-optimizer-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role" "cost_optimizer" {
  name = "cost-optimizer-${var.environment}"

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

resource "aws_iam_role_policy" "cost_optimizer" {
  name = "cost-optimizer-policy"
  role = aws_iam_role.cost_optimizer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "ce:GetReservationUtilization",
          "ce:GetSavingsPlansUtilization"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:ListFunctions",
          "lambda:GetFunction",
          "dynamodb:DescribeTable",
          "dynamodb:UpdateTable",
          "s3:GetBucketLifecycleConfiguration",
          "s3:PutBucketLifecycleConfiguration"
        ]
        Resource = "*"
      },
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
          "sns:Publish"
        ]
        Resource = aws_sns_topic.cost_alerts.arn
      }
    ]
  })
}

data "archive_file" "cost_optimizer" {
  type        = "zip"
  output_path = "${path.module}/cost_optimizer.zip"

  source {
    content  = <<-EOT
import json
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')
lambda_client = boto3.client('lambda')
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')

def handler(event, context):
    """Analyze costs and provide optimization recommendations"""
    recommendations = []

    # 1. Analyze Lambda memory utilization
    print("Analyzing Lambda functions...")
    lambda_recs = analyze_lambda_functions()
    recommendations.extend(lambda_recs)

    # 2. Analyze DynamoDB capacity
    print("Analyzing DynamoDB capacity...")
    dynamodb_recs = analyze_dynamodb()
    recommendations.extend(dynamodb_recs)

    # 3. Analyze S3 storage classes
    print("Analyzing S3 storage...")
    s3_recs = analyze_s3()
    recommendations.extend(s3_recs)

    # 4. Check for idle resources
    print("Checking for idle resources...")
    idle_recs = check_idle_resources()
    recommendations.extend(idle_recs)

    # 5. Send recommendations
    if recommendations:
        send_recommendations(recommendations)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'recommendations': len(recommendations),
            'potential_savings': sum(r.get('savings', 0) for r in recommendations)
        })
    }

def analyze_lambda_functions():
    """Identify over-provisioned Lambda functions"""
    recommendations = []
    functions = lambda_client.list_functions()

    for func in functions['Functions']:
        # Check if memory is over-provisioned
        # (In production, analyze CloudWatch metrics)
        memory = func['MemorySize']
        if memory > 1024:
            recommendations.append({
                'type': 'lambda_memory',
                'resource': func['FunctionName'],
                'current': f'{memory}MB',
                'recommended': '512MB',
                'savings': 10.0  # Estimate
            })

    return recommendations

def analyze_dynamodb():
    """Check DynamoDB provisioned capacity vs usage"""
    recommendations = []
    # Implementation: Check if on-demand might be cheaper
    return recommendations

def analyze_s3():
    """Check S3 storage classes and lifecycle policies"""
    recommendations = []
    # Implementation: Identify objects that should be moved to IA or Glacier
    return recommendations

def check_idle_resources():
    """Identify unused or idle resources"""
    recommendations = []
    # Implementation: Check Lambda invocations, DynamoDB reads, etc.
    return recommendations

def send_recommendations(recommendations):
    """Send recommendations via SNS"""
    message = "Cost Optimization Recommendations:\n\n"
    total_savings = 0

    for rec in recommendations:
        message += f"- {rec['type']}: {rec['resource']}\n"
        message += f"  Current: {rec['current']}, Recommended: {rec['recommended']}\n"
        message += f"  Potential savings: $${rec['savings']:.2f}/month\n\n"
        total_savings += rec['savings']

    message += f"Total potential savings: $${total_savings:.2f}/month"

    sns.publish(
        TopicArn=context.environment['SNS_TOPIC_ARN'],
        Subject='Cost Optimization Recommendations',
        Message=message
    )
EOT
    filename = "index.py"
  }
}

# SNS topic for cost alerts
resource "aws_sns_topic" "cost_alerts" {
  name = "cost-alerts-${var.environment}"

  tags = {
    Name        = "cost-alerts-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "cost_alerts_email" {
  count = length(var.budget_alert_emails) > 0 ? 1 : 0

  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.budget_alert_emails[0]
}

# EventBridge rule to run cost optimizer weekly
resource "aws_cloudwatch_event_rule" "cost_optimizer_schedule" {
  name                = "cost-optimizer-schedule-${var.environment}"
  description         = "Run cost optimizer weekly"
  schedule_expression = "cron(0 9 ? * MON *)" # Every Monday at 9 AM UTC

  tags = {
    Name        = "cost-optimizer-schedule-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "cost_optimizer" {
  rule      = aws_cloudwatch_event_rule.cost_optimizer_schedule.name
  target_id = "CostOptimizerLambda"
  arn       = aws_lambda_function.cost_optimizer.arn
}

resource "aws_lambda_permission" "cost_optimizer_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_optimizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_optimizer_schedule.arn
}

# CloudWatch dashboard for cost monitoring
resource "aws_cloudwatch_dashboard" "cost_monitoring" {
  dashboard_name = "cost-monitoring-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", { stat = "Maximum", period = 86400 }]
          ]
          period = 86400
          stat   = "Maximum"
          region = "us-east-1"
          title  = "Estimated Monthly Charges"
        }
      }
    ]
  })
}
