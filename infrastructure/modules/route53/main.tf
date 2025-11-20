# Route53 DNS Configuration

data "aws_route53_zone" "main" {
  count = var.create_dns_records ? 1 : 0

  name         = var.hosted_zone_name
  private_zone = false
}

# A record for CloudFront distribution
resource "aws_route53_record" "frontend" {
  count = var.create_dns_records ? 1 : 0

  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# AAAA record for IPv6 support
resource "aws_route53_record" "frontend_ipv6" {
  count = var.create_dns_records ? 1 : 0

  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# Health check for the frontend
resource "aws_route53_health_check" "frontend" {
  count = var.create_dns_records && var.enable_health_check ? 1 : 0

  fqdn              = var.domain_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/index.html"
  failure_threshold = "3"
  request_interval  = "30"

  tags = {
    Name        = "frontend-health-check-${var.environment}"
    Environment = var.environment
  }
}

# CloudWatch alarm for health check
resource "aws_cloudwatch_metric_alarm" "health_check" {
  count = var.create_dns_records && var.enable_health_check ? 1 : 0

  alarm_name          = "route53-health-check-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Route53 health check failed"
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.frontend[0].id
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}
