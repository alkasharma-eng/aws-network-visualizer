# Cost Optimization Guide

## Overview
This guide provides strategies and best practices for optimizing AWS costs for the Network Visualizer platform.

## Current Cost Structure

### Typical Monthly Costs (Production)

| Service | Usage | Estimated Cost |
|---------|-------|----------------|
| Lambda | 10M invocations, 1GB-sec | $50 |
| DynamoDB | On-demand, 1M reads, 500K writes | $150 |
| S3 | 100GB storage, 1M requests | $25 |
| CloudFront | 1TB transfer | $85 |
| API Gateway | 10M requests | $35 |
| CloudWatch | Logs, metrics, alarms | $30 |
| Bedrock (Claude) | 1M tokens | $15 |
| **Total** | | **~$390/month** |

## Cost Optimization Strategies

### 1. Lambda Optimization

**Right-size Memory Allocation**
```bash
# Analyze Lambda memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name MemoryUtilization \
  --dimensions Name=FunctionName,Value=network-visualizer-api-production \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average \
  --output table
```

**Recommendation**: If memory utilization < 50%, reduce memory:
```bash
aws lambda update-function-configuration \
  --function-name network-visualizer-api-production \
  --memory-size 512  # Down from 1024
```

**Estimated Savings**: $10-15/month per function

**Reduce Execution Duration**
- Optimize code (use caching, reduce loops)
- Use Lambda layers for shared dependencies
- Implement connection pooling for DynamoDB

### 2. DynamoDB Optimization

**Use On-Demand vs Provisioned**

Check current usage pattern:
```python
# analyze_dynamodb_usage.py
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')

# Get read/write metrics for last 30 days
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/DynamoDB',
    MetricName='ConsumedReadCapacityUnits',
    Dimensions=[{'Name': 'TableName', 'Value': 'network-visualizer-topology'}],
    StartTime=datetime.utcnow() - timedelta(days=30),
    EndTime=datetime.utcnow(),
    Period=86400,
    Statistics=['Sum', 'Average']
)

# If traffic is predictable and steady, use provisioned
# If traffic is spiky or unpredictable, use on-demand
```

**Enable Auto Scaling** (if using provisioned):
```bash
# Configure auto scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/network-visualizer-topology \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100

aws application-autoscaling put-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/network-visualizer-topology \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --policy-name DynamoDBReadAutoScaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

**Estimated Savings**: $30-50/month with proper capacity planning

**Use DAX for Caching** (for high-read workloads):
- Reduces DynamoDB read costs by 80%+
- Cost: $0.04/hour for cache.t3.small (~$30/month)
- Break-even at ~750K reads/month

### 3. S3 Cost Optimization

**Implement Intelligent-Tiering**
```bash
# Enable intelligent tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket network-visualizer-data-production \
  --id IntelligentTieringConfig \
  --intelligent-tiering-configuration file://intelligent-tiering.json
```

intelligent-tiering.json:
```json
{
  "Id": "IntelligentTieringConfig",
  "Status": "Enabled",
  "Tierings": [
    {
      "Days": 90,
      "AccessTier": "ARCHIVE_ACCESS"
    },
    {
      "Days": 180,
      "AccessTier": "DEEP_ARCHIVE_ACCESS"
    }
  ]
}
```

**Optimize S3 Request Costs**
- Use batch operations instead of individual requests
- Implement S3 Select for filtering data server-side
- Use CloudFront for frequently accessed objects

**Estimated Savings**: $10-15/month on storage

### 4. CloudFront Optimization

**Use Cache Effectively**
```javascript
// CloudFront function for better caching
function handler(event) {
    var request = event.request;
    var headers = request.headers;

    // Add cache headers
    headers['cache-control'] = { value: 'public, max-age=86400' };

    return request;
}
```

**Price Class Optimization**
```bash
# Use PriceClass_100 (US, Canada, Europe) instead of PriceClass_All
# Saves ~30% on data transfer if users are mainly in these regions
```

**Estimated Savings**: $20-30/month

### 5. API Gateway Optimization

**Use Caching**
```bash
# Enable API Gateway caching (0.5GB cache)
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5
```

Cache cost: $0.02/hour (~$14.40/month)
Breaks even at ~400K requests/month saved

**Use HTTP API instead of REST API** (if possible):
- 71% cheaper ($1.00 vs $3.50 per million requests)
- Migration effort required

**Estimated Savings**: $10-20/month

### 6. CloudWatch Optimization

**Reduce Log Retention**
```bash
# Set log retention to 30 days instead of forever
for log_group in $(aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text); do
  aws logs put-retention-policy \
    --log-group-name $log_group \
    --retention-in-days 30
done
```

**Use Metric Filters Efficiently**
- Avoid logging everything in production
- Use sampling for high-volume logs
- Filter logs before sending to CloudWatch

**Estimated Savings**: $5-10/month

### 7. Bedrock (AI) Optimization

**Optimize Prompts**
- Keep prompts concise
- Use system prompts instead of repeating context
- Cache frequently used analysis results

**Use Batch Processing**
```python
# Batch analyze multiple VPCs instead of individual calls
def batch_analyze_vpcs(vpc_list):
    prompt = f"Analyze these {len(vpc_list)} VPCs for anomalies:\n"
    for vpc in vpc_list:
        prompt += f"- {vpc['id']}: {vpc['config']}\n"

    # Single Bedrock call instead of N calls
    return bedrock_client.invoke_model(prompt=prompt)
```

**Estimated Savings**: $5-10/month

## Automated Cost Optimization

### Weekly Cost Review Script

```bash
#!/bin/bash
# weekly-cost-review.sh

# Get last week's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --output table

# Check for cost anomalies
aws ce get-anomalies \
  --date-interval Start=$(date -u -d '7 days ago' +%Y-%m-%d) \
  --max-results 10

# Get recommendations
aws ce get-rightsizing-recommendation \
  --service Lambda

aws ce get-reservation-purchase-recommendation \
  --service DynamoDB \
  --lookback-period SIXTY_DAYS
```

### Monthly Cost Optimization Checklist

- [ ] Review Lambda memory allocation
- [ ] Check DynamoDB capacity mode (on-demand vs provisioned)
- [ ] Analyze S3 storage classes
- [ ] Review CloudFront price class
- [ ] Check for unused resources (idle Lambdas, old S3 objects)
- [ ] Review CloudWatch log retention
- [ ] Analyze Bedrock token usage
- [ ] Check for reserved capacity opportunities
- [ ] Review budget alerts and adjust thresholds

## Cost Allocation Tags

Ensure all resources are tagged:
```bash
# Tag resources for cost allocation
aws resourcegroupstaggingapi tag-resources \
  --resource-arn-list \
    arn:aws:lambda:us-east-1:123456789012:function:network-visualizer-api-production \
  --tags \
    Environment=production \
    Project=network-visualizer \
    CostCenter=engineering \
    Owner=devops-team
```

Enable cost allocation tags in AWS Billing:
```bash
# List available tags
aws ce list-cost-allocation-tags

# Activate tags
aws ce update-cost-allocation-tags-status \
  --cost-allocation-tags-status \
    TagKey=Environment,Status=Active \
    TagKey=Project,Status=Active
```

## Reserved Capacity & Savings Plans

### When to Consider

**Compute Savings Plans** (Lambda):
- If monthly Lambda costs > $100
- Potential savings: 17% (1-year) or 28% (3-year)

**DynamoDB Reserved Capacity**:
- If using provisioned mode consistently
- Potential savings: 50-75% vs on-demand

**S3 Storage Savings** (via Intelligent Tiering):
- Automatic, no commitment required
- Potential savings: 40-95% for infrequently accessed data

## Monitoring Cost Efficiency

### Key Metrics to Track

```bash
# Cost per API request
MONTHLY_API_COST=$(aws ce get-cost-and-usage --time-period Start=$(date -u -d '30 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) --metrics BlendedCost --filter '{"Dimensions":{"Key":"SERVICE","Values":["AWS Lambda","Amazon API Gateway"]}}' --query 'ResultsByTime[*].Total.BlendedCost.Amount' --output text | awk '{s+=$1} END {print s}')

MONTHLY_REQUESTS=$(aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name Count --start-time $(date -u -d '30 days ago' +%Y-%m-%dT00:00:00) --end-time $(date -u +%Y-%m-%dT00:00:00) --period 2592000 --statistics Sum --query 'Datapoints[0].Sum' --output text)

COST_PER_REQUEST=$(echo "scale=6; $MONTHLY_API_COST / $MONTHLY_REQUESTS" | bc)
echo "Cost per API request: \$$COST_PER_REQUEST"
```

**Target**: < $0.0001 per request

### Cost Efficiency Dashboard

Create custom CloudWatch dashboard:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", { "stat": "Average" }],
          [".", "Invocations", { "stat": "Sum" }],
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { "stat": "Sum" }]
        ],
        "title": "Cost Drivers"
      }
    }
  ]
}
```

## Target Monthly Costs by Environment

| Environment | Target | Acceptable Range |
|-------------|--------|------------------|
| Development | $50 | $30-70 |
| Staging | $100 | $80-150 |
| Production | $400 | $350-500 |

**Alert thresholds**: 80% (warning), 100% (critical), 90% forecasted (proactive)
