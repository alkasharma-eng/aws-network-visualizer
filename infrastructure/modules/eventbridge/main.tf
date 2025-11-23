# EventBridge Module - Scheduled Discovery

variable "discovery_function_arn" {
  description = "Discovery Lambda function ARN"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule expression (e.g., rate(1 hour))"
  type        = string
  default     = "rate(1 hour)"
}

# EventBridge Rule for Scheduled Discovery
resource "aws_cloudwatch_event_rule" "discovery_schedule" {
  name                = "network-visualizer-discovery-schedule"
  description         = "Triggers network discovery on a schedule"
  schedule_expression = var.schedule_expression
}

# EventBridge Target - Lambda
resource "aws_cloudwatch_event_target" "discovery_lambda" {
  rule      = aws_cloudwatch_event_rule.discovery_schedule.name
  target_id = "DiscoveryLambda"
  arn       = var.discovery_function_arn
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.discovery_function_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.discovery_schedule.arn
}
