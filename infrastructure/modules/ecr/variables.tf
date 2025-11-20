variable "environment" {
  description = "Environment name"
  type        = string
}

variable "allowed_account_ids" {
  description = "AWS account IDs allowed to pull images"
  type        = list(string)
  default     = []
}
