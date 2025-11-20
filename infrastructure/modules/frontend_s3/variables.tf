variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for frontend"
  type        = string
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "log_retention_days" {
  description = "Number of days to retain access logs"
  type        = number
  default     = 90
}
