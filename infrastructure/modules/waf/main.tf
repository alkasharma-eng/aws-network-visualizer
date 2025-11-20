# AWS WAF Web ACL for API Gateway and CloudFront

resource "aws_wafv2_web_acl" "main" {
  name  = "network-visualizer-waf-${var.environment}"
  scope = var.scope  # CLOUDFRONT or REGIONAL

  default_action {
    allow {}
  }

  # Rule 1: Rate limiting
  rule {
    name     = "rate-limit-rule"
    priority = 1

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
      }
    }

    action {
      block {
        custom_response {
          response_code = 429
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: AWS Managed Rules - Core Rule Set
  rule {
    name     = "aws-managed-rules-core"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"

        # Exclude rules that cause false positives (adjust as needed)
        excluded_rule {
          name = "SizeRestrictions_BODY"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCore"
      sampled_requests_enabled   = true
    }
  }

  # Rule 3: AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "aws-managed-rules-bad-inputs"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesBadInputs"
      sampled_requests_enabled   = true
    }
  }

  # Rule 4: AWS Managed Rules - SQL Injection
  rule {
    name     = "aws-managed-rules-sqli"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLi"
      sampled_requests_enabled   = true
    }
  }

  # Rule 5: Block requests from known bad IPs
  rule {
    name     = "block-bad-ips"
    priority = 5

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.blocked_ips.arn
      }
    }

    action {
      block {
        custom_response {
          response_code = 403
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockBadIPs"
      sampled_requests_enabled   = true
    }
  }

  # Rule 6: Geo-blocking (if enabled)
  dynamic "rule" {
    for_each = var.enable_geo_blocking ? [1] : []

    content {
      name     = "geo-blocking"
      priority = 6

      statement {
        not_statement {
          statement {
            geo_match_statement {
              country_codes = var.allowed_countries
            }
          }
        }
      }

      action {
        block {
          custom_response {
            response_code = 403
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "GeoBlocking"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "NetworkVisualizerWAF"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "network-visualizer-waf-${var.environment}"
    Environment = var.environment
  }
}

# IP Set for blocked IPs
resource "aws_wafv2_ip_set" "blocked_ips" {
  name               = "blocked-ips-${var.environment}"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_ips

  tags = {
    Name        = "blocked-ips-${var.environment}"
    Environment = var.environment
  }
}

# CloudWatch Log Group for WAF logs
resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/waf/network-visualizer-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "waf-logs-${var.environment}"
    Environment = var.environment
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "x-api-key"
    }
  }
}

# CloudWatch Alarms for WAF
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "waf-high-blocked-requests-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.blocked_requests_threshold
  alarm_description   = "High number of blocked requests detected"
  treat_missing_data  = "notBreaching"

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.name
    Region = var.aws_region
    Rule   = "ALL"
  }
}
