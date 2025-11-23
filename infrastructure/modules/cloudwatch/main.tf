# CloudWatch Module - Monitoring and Alarms

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "discovery_function" {
  description = "Discovery Lambda function name"
  type        = string
}

variable "analysis_function" {
  description = "Analysis Lambda function name"
  type        = string
}

# CloudWatch Alarms for Discovery Function
resource "aws_cloudwatch_metric_alarm" "discovery_errors" {
  alarm_name          = "${var.environment}-discovery-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors discovery lambda errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.discovery_function
  }
}

resource "aws_cloudwatch_metric_alarm" "discovery_duration" {
  alarm_name          = "${var.environment}-discovery-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "600000" # 10 minutes in milliseconds
  alarm_description   = "This metric monitors discovery lambda duration"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.discovery_function
  }
}

# CloudWatch Alarms for Analysis Function
resource "aws_cloudwatch_metric_alarm" "analysis_errors" {
  alarm_name          = "${var.environment}-analysis-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors analysis lambda errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.analysis_function
  }
}
