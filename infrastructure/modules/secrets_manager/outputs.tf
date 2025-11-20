output "api_keys_secret_arn" {
  description = "ARN of API keys secret"
  value       = aws_secretsmanager_secret.api_keys.arn
}

output "database_secret_arn" {
  description = "ARN of database secret"
  value       = aws_secretsmanager_secret.database.arn
}

output "integrations_secret_arn" {
  description = "ARN of integrations secret"
  value       = aws_secretsmanager_secret.integrations.arn
}

output "encryption_keys_secret_arn" {
  description = "ARN of encryption keys secret"
  value       = aws_secretsmanager_secret.encryption_keys.arn
}

output "secret_arns" {
  description = "Map of all secret ARNs"
  value = {
    api_keys      = aws_secretsmanager_secret.api_keys.arn
    database      = aws_secretsmanager_secret.database.arn
    integrations  = aws_secretsmanager_secret.integrations.arn
    encryption    = aws_secretsmanager_secret.encryption_keys.arn
  }
}
