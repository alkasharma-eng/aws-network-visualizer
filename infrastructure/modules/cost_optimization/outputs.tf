output "budget_name" {
  description = "Monthly budget name"
  value       = aws_budgets_budget.monthly.name
}

output "cost_anomaly_monitor_arn" {
  description = "Cost anomaly monitor ARN"
  value       = aws_ce_anomaly_monitor.service_monitor.arn
}

output "cost_alerts_topic_arn" {
  description = "SNS topic ARN for cost alerts"
  value       = aws_sns_topic.cost_alerts.arn
}

output "cost_optimizer_function_name" {
  description = "Cost optimizer Lambda function name"
  value       = aws_lambda_function.cost_optimizer.function_name
}
