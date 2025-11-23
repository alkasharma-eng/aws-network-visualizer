# DynamoDB Table for Network Topology Storage

resource "aws_dynamodb_table" "topology" {
  name             = var.table_name
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "PK"
  range_key        = "SK"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "N"
  }

  attribute {
    name = "region"
    type = "S"
  }

  global_secondary_index {
    name            = "RegionIndex"
    hash_key        = "region"
    range_key       = "SK"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "production"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = var.table_name
    Environment = var.environment
  }
}

# Auto Scaling for DynamoDB (if using provisioned mode)
# Uncomment if switching to provisioned billing mode

# resource "aws_appautoscaling_target" "table_read" {
#   max_capacity       = 100
#   min_capacity       = 5
#   resource_id        = "table/${aws_dynamodb_table.topology.name}"
#   scalable_dimension = "dynamodb:table:ReadCapacityUnits"
#   service_namespace  = "dynamodb"
# }

# resource "aws_appautoscaling_policy" "table_read_policy" {
#   name               = "${var.table_name}-read-scaling-policy"
#   policy_type        = "TargetTrackingScaling"
#   resource_id        = aws_appautoscaling_target.table_read.resource_id
#   scalable_dimension = aws_appautoscaling_target.table_read.scalable_dimension
#   service_namespace  = aws_appautoscaling_target.table_read.service_namespace

#   target_tracking_scaling_policy_configuration {
#     predefined_metric_specification {
#       predefined_metric_type = "DynamoDBReadCapacityUtilization"
#     }
#     target_value = 70.0
#   }
# }

output "table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.topology.name
}

output "table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.topology.arn
}

output "table_stream_arn" {
  description = "DynamoDB table stream ARN"
  value       = aws_dynamodb_table.topology.stream_arn
}
