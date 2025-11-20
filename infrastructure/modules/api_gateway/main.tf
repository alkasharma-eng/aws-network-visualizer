# API Gateway Module
# Creates REST API with Lambda integrations, throttling, and CORS

resource "aws_api_gateway_rest_api" "main" {
  name        = "network-visualizer-api-${var.environment}"
  description = "AWS Network Visualizer REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = "network-visualizer-api-${var.environment}"
    Environment = var.environment
  }
}

# API Gateway Account (for CloudWatch Logs)
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "api-gateway-cloudwatch-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# /topology resource
resource "aws_api_gateway_resource" "topology" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "topology"
}

# /topology/summary
resource "aws_api_gateway_resource" "topology_summary" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.topology.id
  path_part   = "summary"
}

resource "aws_api_gateway_method" "topology_summary_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.topology_summary.id
  http_method   = "GET"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "topology_summary_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.topology_summary.id
  http_method             = aws_api_gateway_method.topology_summary_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# /topology/{region}/{vpcId}
resource "aws_api_gateway_resource" "topology_region" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.topology.id
  path_part   = "{region}"
}

resource "aws_api_gateway_resource" "topology_vpc" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.topology_region.id
  path_part   = "{vpcId}"
}

resource "aws_api_gateway_method" "topology_vpc_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.topology_vpc.id
  http_method   = "GET"
  authorization = "AWS_IAM"

  request_parameters = {
    "method.request.path.region" = true
    "method.request.path.vpcId"  = true
  }
}

resource "aws_api_gateway_integration" "topology_vpc_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.topology_vpc.id
  http_method             = aws_api_gateway_method.topology_vpc_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# /analyses resource
resource "aws_api_gateway_resource" "analyses" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "analyses"
}

# /analyses/latest
resource "aws_api_gateway_resource" "analyses_latest" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.analyses.id
  path_part   = "latest"
}

resource "aws_api_gateway_method" "analyses_latest_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.analyses_latest.id
  http_method   = "GET"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "analyses_latest_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.analyses_latest.id
  http_method             = aws_api_gateway_method.analyses_latest_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.api_lambda_invoke_arn
}

# /discovery/trigger (POST)
resource "aws_api_gateway_resource" "discovery" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "discovery"
}

resource "aws_api_gateway_resource" "discovery_trigger" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.discovery.id
  path_part   = "trigger"
}

resource "aws_api_gateway_method" "discovery_trigger_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.discovery_trigger.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "discovery_trigger_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.discovery_trigger.id
  http_method             = aws_api_gateway_method.discovery_trigger_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.discovery_lambda_invoke_arn
}

# /analysis/trigger (POST)
resource "aws_api_gateway_resource" "analysis" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "analysis"
}

resource "aws_api_gateway_resource" "analysis_trigger" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.analysis.id
  path_part   = "trigger"
}

resource "aws_api_gateway_method" "analysis_trigger_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.analysis_trigger.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "analysis_trigger_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.analysis_trigger.id
  http_method             = aws_api_gateway_method.analysis_trigger_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.analysis_lambda_invoke_arn
}

# CORS Configuration for all resources
module "cors_topology_summary" {
  source = "../api_gateway_cors"

  api_id      = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.topology_summary.id
}

module "cors_topology_vpc" {
  source = "../api_gateway_cors"

  api_id      = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.topology_vpc.id
}

module "cors_analyses_latest" {
  source = "../api_gateway_cors"

  api_id      = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.analyses_latest.id
}

module "cors_discovery_trigger" {
  source = "../api_gateway_cors"

  api_id      = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.discovery_trigger.id
}

module "cors_analysis_trigger" {
  source = "../api_gateway_cors"

  api_id      = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.analysis_trigger.id
}

# Lambda Permissions
resource "aws_lambda_permission" "api_gateway_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.api_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_discovery" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.discovery_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_analysis" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.analysis_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.topology.id,
      aws_api_gateway_resource.analyses.id,
      aws_api_gateway_method.topology_summary_get.id,
      aws_api_gateway_integration.topology_summary_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.topology_summary_get,
    aws_api_gateway_integration.topology_vpc_get,
    aws_api_gateway_integration.analyses_latest_get,
    aws_api_gateway_integration.discovery_trigger_post,
    aws_api_gateway_integration.analysis_trigger_post,
  ]
}

# Stages
resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  xray_tracing_enabled = var.enable_xray

  tags = {
    Name        = "prod"
    Environment = var.environment
  }
}

resource "aws_api_gateway_stage" "staging" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "staging"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
    })
  }

  xray_tracing_enabled = var.enable_xray

  tags = {
    Name        = "staging"
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/network-visualizer-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "api-gateway-logs"
    Environment = var.environment
  }
}

# Method Settings (Throttling & Caching)
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled      = true
    logging_level        = "INFO"
    data_trace_enabled   = true
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
    caching_enabled      = var.enable_caching
    cache_ttl_in_seconds = var.cache_ttl_seconds
  }
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "main" {
  name        = "network-visualizer-usage-plan-${var.environment}"
  description = "Usage plan for Network Visualizer API"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }

  quota_settings {
    limit  = var.quota_limit
    period = "DAY"
  }

  throttle_settings {
    burst_limit = var.throttling_burst_limit
    rate_limit  = var.throttling_rate_limit
  }
}

# API Keys
resource "aws_api_gateway_api_key" "dashboard" {
  name    = "dashboard-api-key-${var.environment}"
  enabled = true
}

resource "aws_api_gateway_usage_plan_key" "dashboard" {
  key_id        = aws_api_gateway_api_key.dashboard.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}

# WAF Web ACL Association (if WAF enabled)
resource "aws_wafv2_web_acl_association" "api_gateway" {
  count = var.enable_waf ? 1 : 0

  resource_arn = aws_api_gateway_stage.prod.arn
  web_acl_arn  = var.waf_web_acl_arn
}
