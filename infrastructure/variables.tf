# Infrastructure variables

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for topology data"
  type        = string
  default     = "network-visualizer-topology"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for visualizations and archives"
  type        = string
}

variable "aws_regions" {
  description = "List of AWS regions to scan"
  type        = list(string)
  default     = ["us-east-1"]
}

variable "enable_ai_analysis" {
  description = "Enable AI-powered analysis with Bedrock"
  type        = bool
  default     = true
}

variable "discovery_schedule" {
  description = "EventBridge schedule expression for discovery"
  type        = string
  default     = "rate(1 day)"
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 1024

  validation {
    condition     = var.lambda_memory_size >= 512 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory must be between 512 MB and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 900

  validation {
    condition     = var.lambda_timeout >= 60 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 60 and 900 seconds."
  }
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180,
      365, 400, 545, 731, 1827, 3653
    ], var.cloudwatch_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch Logs retention period."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# API Gateway Variables
variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 5000

  validation {
    condition     = var.api_throttling_burst_limit >= 0 && var.api_throttling_burst_limit <= 10000
    error_message = "Burst limit must be between 0 and 10000."
  }
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 10000

  validation {
    condition     = var.api_throttling_rate_limit >= 0 && var.api_throttling_rate_limit <= 20000
    error_message = "Rate limit must be between 0 and 20000."
  }
}

variable "api_enable_caching" {
  description = "Enable API Gateway caching"
  type        = bool
  default     = true
}

variable "api_quota_limit" {
  description = "Daily API quota limit"
  type        = number
  default     = 100000

  validation {
    condition     = var.api_quota_limit > 0
    error_message = "Quota limit must be greater than 0."
  }
}

# Frontend Variables
variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend"
  type        = string
}

variable "frontend_cors_origins" {
  description = "CORS allowed origins for frontend"
  type        = list(string)
  default     = ["*"]
}

variable "frontend_domain_names" {
  description = "Custom domain names for CloudFront"
  type        = list(string)
  default     = []
}

variable "frontend_domain_name" {
  description = "Primary domain name for frontend"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS (must be in us-east-1)"
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "cloudfront_geo_restriction_type" {
  description = "CloudFront geo restriction type"
  type        = string
  default     = "none"
}

variable "cloudfront_geo_restriction_locations" {
  description = "CloudFront geo restriction locations"
  type        = list(string)
  default     = []
}

# Route53 Variables
variable "create_dns_records" {
  description = "Create Route53 DNS records"
  type        = bool
  default     = false
}

variable "hosted_zone_name" {
  description = "Route53 hosted zone name"
  type        = string
  default     = ""
}

variable "enable_route53_health_check" {
  description = "Enable Route53 health check"
  type        = bool
  default     = true
}
