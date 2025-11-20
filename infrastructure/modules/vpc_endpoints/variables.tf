variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "Existing VPC ID (if not creating new VPC)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_ids" {
  description = "Subnet IDs for interface endpoints"
  type        = list(string)
  default     = []
}

variable "route_table_ids" {
  description = "Route table IDs for gateway endpoints"
  type        = list(string)
  default     = []
}

variable "enable_interface_endpoints" {
  description = "Enable interface VPC endpoints (incurs costs)"
  type        = bool
  default     = false
}
