# VPC Endpoints for Private AWS Service Access
# Reduces data transfer costs and improves security

resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "network-visualizer-vpc-${var.environment}"
    Environment = var.environment
  }
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  count = var.create_vpc ? 1 : 0

  name        = "vpc-endpoints-${var.environment}"
  description = "Security group for VPC endpoints"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.create_vpc ? aws_vpc.main[0].cidr_block : var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "vpc-endpoints-sg-${var.environment}"
    Environment = var.environment
  }
}

# DynamoDB Gateway Endpoint (no cost)
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = {
    Name        = "dynamodb-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# S3 Gateway Endpoint (no cost)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = {
    Name        = "s3-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# Lambda Interface Endpoint
resource "aws_vpc_endpoint" "lambda" {
  count = var.enable_interface_endpoints ? 1 : 0

  vpc_id              = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.lambda"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "lambda-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# Secrets Manager Interface Endpoint
resource "aws_vpc_endpoint" "secretsmanager" {
  count = var.enable_interface_endpoints ? 1 : 0

  vpc_id              = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "secretsmanager-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# CloudWatch Logs Interface Endpoint
resource "aws_vpc_endpoint" "logs" {
  count = var.enable_interface_endpoints ? 1 : 0

  vpc_id              = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "logs-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# Bedrock Runtime Interface Endpoint
resource "aws_vpc_endpoint" "bedrock_runtime" {
  count = var.enable_interface_endpoints ? 1 : 0

  vpc_id              = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "bedrock-runtime-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# EC2 Interface Endpoint (for resource discovery)
resource "aws_vpc_endpoint" "ec2" {
  count = var.enable_interface_endpoints ? 1 : 0

  vpc_id              = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.ec2"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "ec2-endpoint-${var.environment}"
    Environment = var.environment
  }
}
