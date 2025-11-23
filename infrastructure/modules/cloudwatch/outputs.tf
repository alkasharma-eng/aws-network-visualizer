# CloudWatch Module Outputs

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${var.environment}-network-visualizer"
}

data "aws_region" "current" {}
