variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "api_lambda_function_name" {
  description = "API Lambda function name"
  type        = string
}

variable "api_lambda_invoke_arn" {
  description = "API Lambda function invoke ARN"
  type        = string
}

variable "discovery_lambda_function_name" {
  description = "Discovery Lambda function name"
  type        = string
}

variable "discovery_lambda_invoke_arn" {
  description = "Discovery Lambda function invoke ARN"
  type        = string
}

variable "analysis_lambda_function_name" {
  description = "Analysis Lambda function name"
  type        = string
}

variable "analysis_lambda_invoke_arn" {
  description = "Analysis Lambda function invoke ARN"
  type        = string
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 5000
}

variable "throttling_rate_limit" {
  description = "API Gateway throttling rate limit"
  type        = number
  default     = 10000
}

variable "enable_caching" {
  description = "Enable API Gateway caching"
  type        = bool
  default     = true
}

variable "cache_ttl_seconds" {
  description = "Cache TTL in seconds"
  type        = number
  default     = 300
}

variable "quota_limit" {
  description = "Daily API quota limit"
  type        = number
  default     = 100000
}

variable "enable_waf" {
  description = "Enable WAF protection"
  type        = bool
  default     = false
}

variable "waf_web_acl_arn" {
  description = "WAF Web ACL ARN (required if enable_waf is true)"
  type        = string
  default     = ""
}
