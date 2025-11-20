variable "environment" {
  description = "Environment name"
  type        = string
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 1000
}

variable "lambda_budget_limit" {
  description = "Lambda monthly budget limit in USD"
  type        = number
  default     = 200
}

variable "dynamodb_budget_limit" {
  description = "DynamoDB monthly budget limit in USD"
  type        = number
  default     = 200
}

variable "budget_alert_emails" {
  description = "Email addresses for budget alerts"
  type        = list(string)
  default     = []
}

variable "cost_anomaly_email" {
  description = "Email address for cost anomaly alerts"
  type        = string
  default     = ""
}

variable "anomaly_threshold_dollars" {
  description = "Threshold for cost anomaly alerts in dollars"
  type        = string
  default     = "50"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for cost analysis"
  type        = string
  default     = ""
}
