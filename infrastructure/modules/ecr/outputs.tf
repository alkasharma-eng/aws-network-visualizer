output "app_repository_url" {
  description = "Application ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "app_repository_arn" {
  description = "Application ECR repository ARN"
  value       = aws_ecr_repository.app.arn
}

output "lambda_repository_url" {
  description = "Lambda ECR repository URL"
  value       = aws_ecr_repository.lambda.repository_url
}

output "lambda_repository_arn" {
  description = "Lambda ECR repository ARN"
  value       = aws_ecr_repository.lambda.arn
}

output "frontend_repository_url" {
  description = "Frontend ECR repository URL"
  value       = aws_ecr_repository.frontend.repository_url
}

output "frontend_repository_arn" {
  description = "Frontend ECR repository ARN"
  value       = aws_ecr_repository.frontend.arn
}
