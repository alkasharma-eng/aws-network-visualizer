output "backup_vault_name" {
  description = "Backup vault name"
  value       = aws_backup_vault.main.name
}

output "backup_vault_arn" {
  description = "Backup vault ARN"
  value       = aws_backup_vault.main.arn
}

output "backup_plan_id" {
  description = "Backup plan ID"
  value       = aws_backup_plan.main.id
}

output "backup_plan_arn" {
  description = "Backup plan ARN"
  value       = aws_backup_plan.main.arn
}
