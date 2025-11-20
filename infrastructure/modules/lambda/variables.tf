variable "environment" {
  description = "Environment name"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN"
  type        = string
}

variable "aws_regions" {
  description = "List of AWS regions to scan"
  type        = list(string)
}

variable "enable_ai_analysis" {
  description = "Enable AI-powered analysis"
  type        = bool
}
