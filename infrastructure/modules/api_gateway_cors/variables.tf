variable "api_id" {
  description = "API Gateway REST API ID"
  type        = string
}

variable "resource_id" {
  description = "API Gateway resource ID"
  type        = string
}

variable "allow_origin" {
  description = "CORS allowed origin"
  type        = string
  default     = "'*'"
}
