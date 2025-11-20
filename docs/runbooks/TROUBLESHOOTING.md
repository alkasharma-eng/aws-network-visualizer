# Troubleshooting Guide

## Quick Diagnostics

```bash
# Run full diagnostic
./scripts/diagnostics.sh production

# Check specific component
./scripts/check-component.sh lambda discovery production
```

## Common Issues

### Issue: Lambda Timeout
**Symptoms**: 30-second timeouts in logs
**Solution**: Increase timeout or optimize code
```bash
aws lambda update-function-configuration \
  --function-name network-visualizer-discovery-production \
  --timeout 900
```

### Issue: DynamoDB Throttling
**Symptoms**: ProvisionedThroughputExceededException
**Solution**: Enable on-demand billing
```bash
aws dynamodb update-table \
  --table-name network-visualizer-topology \
  --billing-mode PAY_PER_REQUEST
```

### Issue: High Costs
**Check**: Lambda invocations, DynamoDB reads/writes
**Solution**: Review EventBridge schedules, add caching
```bash
# Check invocation counts
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```
