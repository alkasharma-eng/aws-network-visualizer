# Lambda Functions for Network Visualizer

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_role" {
  name = "network-visualizer-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for Lambda Functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "network-visualizer-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "elasticloadbalancing:Describe*",
          "rds:Describe*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:*:*:model/anthropic.claude-*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Discovery Lambda Function
resource "aws_lambda_function" "discovery" {
  filename      = data.archive_file.discovery_lambda.output_path
  function_name = "network-visualizer-discovery-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 1024

  source_code_hash = data.archive_file.discovery_lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      S3_BUCKET_NAME      = var.s3_bucket_name
      AWS_REGIONS         = join(",", var.aws_regions)
      ENABLE_AI_ANALYSIS  = tostring(var.enable_ai_analysis)
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.discovery
  ]
}

# Analysis Lambda Function
resource "aws_lambda_function" "analysis" {
  filename      = data.archive_file.analysis_lambda.output_path
  function_name = "network-visualizer-analysis-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 2048

  source_code_hash = data.archive_file.analysis_lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      S3_BUCKET_NAME      = var.s3_bucket_name
      ENABLE_AI_ANALYSIS  = tostring(var.enable_ai_analysis)
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.analysis
  ]
}

# API Lambda Function
resource "aws_lambda_function" "api" {
  filename      = data.archive_file.api_lambda.output_path
  function_name = "network-visualizer-api-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  source_code_hash = data.archive_file.api_lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      S3_BUCKET_NAME      = var.s3_bucket_name
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.api
  ]
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "discovery" {
  name              = "/aws/lambda/network-visualizer-discovery-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "analysis" {
  name              = "/aws/lambda/network-visualizer-analysis-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/network-visualizer-api-${var.environment}"
  retention_in_days = 30
}

# Package Lambda functions
data "archive_file" "discovery_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda_functions/discovery"
  output_path = "${path.module}/discovery.zip"
}

data "archive_file" "analysis_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda_functions/analysis"
  output_path = "${path.module}/analysis.zip"
}

data "archive_file" "api_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda_functions/api"
  output_path = "${path.module}/api.zip"
}

# Outputs
output "discovery_function_name" {
  value = aws_lambda_function.discovery.function_name
}

output "discovery_function_arn" {
  value = aws_lambda_function.discovery.arn
}

output "analysis_function_name" {
  value = aws_lambda_function.analysis.function_name
}

output "analysis_function_arn" {
  value = aws_lambda_function.analysis.arn
}

output "api_function_name" {
  value = aws_lambda_function.api.function_name
}

output "api_function_arn" {
  value = aws_lambda_function.api.arn
}
