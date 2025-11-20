output "dns_name" {
  description = "DNS name for the frontend"
  value       = var.create_dns_records ? aws_route53_record.frontend[0].fqdn : null
}

output "health_check_id" {
  description = "Route53 health check ID"
  value       = var.create_dns_records && var.enable_health_check ? aws_route53_health_check.frontend[0].id : null
}
