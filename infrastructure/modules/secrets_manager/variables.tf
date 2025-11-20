variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "recovery_window_days" {
  description = "Number of days to retain deleted secrets"
  type        = number
  default     = 30

  validation {
    condition     = var.recovery_window_days >= 7 && var.recovery_window_days <= 30
    error_message = "Recovery window must be between 7 and 30 days."
  }
}

# API Keys
variable "api_gateway_key" {
  description = "API Gateway key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "bedrock_api_key" {
  description = "Bedrock API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Database credentials
variable "db_username" {
  description = "Database username"
  type        = string
  default     = ""
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_host" {
  description = "Database host"
  type        = string
  default     = ""
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = ""
}

# Third-party integrations
variable "slack_webhook_url" {
  description = "Slack webhook URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "pagerduty_api_key" {
  description = "PagerDuty API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_token" {
  description = "GitHub token"
  type        = string
  sensitive   = true
  default     = ""
}

# Encryption
variable "master_encryption_key" {
  description = "Master encryption key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "encryption_salt" {
  description = "Encryption salt"
  type        = string
  sensitive   = true
  default     = ""
}

# Rotation
variable "enable_rotation" {
  description = "Enable automatic secret rotation"
  type        = bool
  default     = false
}

variable "rotation_days" {
  description = "Days between automatic rotations"
  type        = number
  default     = 30
}

variable "secret_access_threshold" {
  description = "Threshold for secret access alarm"
  type        = number
  default     = 100
}
