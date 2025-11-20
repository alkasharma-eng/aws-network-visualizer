output "vpc_id" {
  description = "VPC ID"
  value       = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
}

output "dynamodb_endpoint_id" {
  description = "DynamoDB VPC endpoint ID"
  value       = aws_vpc_endpoint.dynamodb.id
}

output "s3_endpoint_id" {
  description = "S3 VPC endpoint ID"
  value       = aws_vpc_endpoint.s3.id
}

output "lambda_endpoint_id" {
  description = "Lambda VPC endpoint ID"
  value       = var.enable_interface_endpoints ? aws_vpc_endpoint.lambda[0].id : null
}

output "secretsmanager_endpoint_id" {
  description = "Secrets Manager VPC endpoint ID"
  value       = var.enable_interface_endpoints ? aws_vpc_endpoint.secretsmanager[0].id : null
}
