output "discovery_function_name" {
  description = "Discovery Lambda function name"
  value       = aws_lambda_function.discovery.function_name
}

output "discovery_function_arn" {
  description = "Discovery Lambda function ARN"
  value       = aws_lambda_function.discovery.arn
}

output "discovery_function_invoke_arn" {
  description = "Discovery Lambda function invoke ARN"
  value       = aws_lambda_function.discovery.invoke_arn
}

output "analysis_function_name" {
  description = "Analysis Lambda function name"
  value       = aws_lambda_function.analysis.function_name
}

output "analysis_function_arn" {
  description = "Analysis Lambda function ARN"
  value       = aws_lambda_function.analysis.arn
}

output "analysis_function_invoke_arn" {
  description = "Analysis Lambda function invoke ARN"
  value       = aws_lambda_function.analysis.invoke_arn
}

output "api_function_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "api_function_arn" {
  description = "API Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "api_function_invoke_arn" {
  description = "API Lambda function invoke ARN"
  value       = aws_lambda_function.api.invoke_arn
}
