output "api_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "API Gateway REST API ARN"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_endpoint" {
  description = "API Gateway invoke URL"
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "api_stage_arn" {
  description = "API Gateway stage ARN"
  value       = aws_api_gateway_stage.prod.arn
}

output "api_key_id" {
  description = "API Key ID for dashboard"
  value       = aws_api_gateway_api_key.dashboard.id
  sensitive   = true
}

output "api_key_value" {
  description = "API Key value for dashboard"
  value       = aws_api_gateway_api_key.dashboard.value
  sensitive   = true
}

output "usage_plan_id" {
  description = "Usage plan ID"
  value       = aws_api_gateway_usage_plan.main.id
}
