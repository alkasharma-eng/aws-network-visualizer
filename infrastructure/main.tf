# AWS Network Visualizer - Terraform Infrastructure
#
# This module deploys the complete AWS Network Visualizer infrastructure
# including Lambda functions, DynamoDB, S3, and CloudWatch resources.

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  # Uncomment for remote state
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "network-visualizer/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "aws-network-visualizer"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Modules
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name  = var.dynamodb_table_name
  environment = var.environment
}

module "s3" {
  source = "./modules/s3"

  bucket_name = var.s3_bucket_name
  environment = var.environment
}

module "lambda" {
  source = "./modules/lambda"

  environment          = var.environment
  dynamodb_table_name  = module.dynamodb.table_name
  dynamodb_table_arn   = module.dynamodb.table_arn
  s3_bucket_name       = module.s3.bucket_name
  s3_bucket_arn        = module.s3.bucket_arn
  aws_regions          = var.aws_regions
  enable_ai_analysis   = var.enable_ai_analysis
}

module "api_gateway" {
  source = "./modules/api_gateway"

  environment                    = var.environment
  api_lambda_function_name       = module.lambda.api_function_name
  api_lambda_invoke_arn          = module.lambda.api_function_invoke_arn
  discovery_lambda_function_name = module.lambda.discovery_function_name
  discovery_lambda_invoke_arn    = module.lambda.discovery_function_invoke_arn
  analysis_lambda_function_name  = module.lambda.analysis_function_name
  analysis_lambda_invoke_arn     = module.lambda.analysis_function_invoke_arn
  enable_xray                    = var.enable_xray
  throttling_burst_limit         = var.api_throttling_burst_limit
  throttling_rate_limit          = var.api_throttling_rate_limit
  enable_caching                 = var.api_enable_caching
  quota_limit                    = var.api_quota_limit
}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment         = var.environment
  discovery_function  = module.lambda.discovery_function_name
  analysis_function   = module.lambda.analysis_function_name
}

module "eventbridge" {
  source = "./modules/eventbridge"

  discovery_function_arn = module.lambda.discovery_function_arn
  schedule_expression    = var.discovery_schedule
}

module "frontend_s3" {
  source = "./modules/frontend_s3"

  environment         = var.environment
  bucket_name         = var.frontend_bucket_name
  cors_allowed_origins = var.frontend_cors_origins
  log_retention_days  = var.cloudwatch_log_retention_days
}

module "cloudfront" {
  source = "./modules/cloudfront"

  environment                     = var.environment
  s3_bucket_name                  = module.frontend_s3.bucket_name
  s3_bucket_id                    = module.frontend_s3.bucket_id
  s3_bucket_arn                   = module.frontend_s3.bucket_arn
  s3_bucket_regional_domain_name  = module.frontend_s3.bucket_regional_domain_name
  api_gateway_domain_name         = replace(module.api_gateway.api_endpoint, "https://", "")
  domain_names                    = var.frontend_domain_names
  acm_certificate_arn             = var.acm_certificate_arn
  price_class                     = var.cloudfront_price_class
  geo_restriction_type            = var.cloudfront_geo_restriction_type
  geo_restriction_locations       = var.cloudfront_geo_restriction_locations
  logging_bucket                  = module.frontend_s3.logging_bucket
}

module "route53" {
  source = "./modules/route53"

  environment                = var.environment
  create_dns_records         = var.create_dns_records
  hosted_zone_name           = var.hosted_zone_name
  domain_name                = var.frontend_domain_name
  cloudfront_domain_name     = module.cloudfront.distribution_domain_name
  cloudfront_hosted_zone_id  = module.cloudfront.distribution_hosted_zone_id
  enable_health_check        = var.enable_route53_health_check
}

# Outputs
output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.s3.bucket_name
}

output "discovery_function_name" {
  description = "Discovery Lambda function name"
  value       = module.lambda.discovery_function_name
}

output "analysis_function_name" {
  description = "Analysis Lambda function name"
  value       = module.lambda.analysis_function_name
}

output "api_function_name" {
  description = "API Lambda function name"
  value       = module.lambda.api_function_name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.cloudwatch.dashboard_url
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_key_id" {
  description = "API Key ID (retrieve value from AWS Console or CLI)"
  value       = module.api_gateway.api_key_id
  sensitive   = true
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain_name
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name"
  value       = module.frontend_s3.bucket_name
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = var.create_dns_records ? "https://${var.frontend_domain_name}" : "https://${module.cloudfront.distribution_domain_name}"
}
