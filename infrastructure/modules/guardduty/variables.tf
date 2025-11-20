variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_kubernetes_audit_logs" {
  description = "Enable Kubernetes audit logs in GuardDuty"
  type        = bool
  default     = false
}

variable "enable_malware_protection" {
  description = "Enable malware protection for EC2"
  type        = bool
  default     = true
}

variable "finding_publishing_frequency" {
  description = "Finding publishing frequency"
  type        = string
  default     = "FIFTEEN_MINUTES"

  validation {
    condition     = contains(["FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"], var.finding_publishing_frequency)
    error_message = "Must be FIFTEEN_MINUTES, ONE_HOUR, or SIX_HOURS."
  }
}

variable "alert_email" {
  description = "Email address for GuardDuty alerts"
  type        = string
  default     = ""
}

variable "enable_auto_response" {
  description = "Enable automated response to critical findings"
  type        = bool
  default     = false
}
