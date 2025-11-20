variable "environment" {
  description = "Environment name"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN to backup"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN to backup"
  type        = string
  default     = ""
}

variable "s3_bucket_id" {
  description = "S3 bucket ID for replication"
  type        = string
  default     = ""
}

variable "s3_replica_bucket_arn" {
  description = "S3 replica bucket ARN"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
  description = "KMS key ARN for backup encryption"
  type        = string
  default     = ""
}

variable "enable_s3_backup" {
  description = "Enable S3 backup"
  type        = bool
  default     = false
}

variable "enable_cross_region_replica" {
  description = "Enable cross-region DynamoDB replica"
  type        = bool
  default     = false
}

variable "enable_s3_replication" {
  description = "Enable S3 cross-region replication"
  type        = bool
  default     = false
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for backup alerts"
  type        = string
  default     = ""
}
