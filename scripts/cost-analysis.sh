#!/bin/bash
# Comprehensive cost analysis script
# Usage: ./scripts/cost-analysis.sh [days] [output-file]

DAYS=${1:-30}
OUTPUT_FILE=${2:-cost-analysis-$(date +%Y%m%d).txt}

echo "Analyzing AWS costs for last $DAYS days..."
echo "Results will be saved to: $OUTPUT_FILE"

{
  echo "========================================="
  echo "AWS Cost Analysis Report"
  echo "Period: Last $DAYS days"
  echo "Generated: $(date)"
  echo "========================================="

  # 1. Total costs
  echo "\n1. TOTAL COSTS"
  aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "$DAYS days ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --output table

  # 2. Cost by service
  echo "\n2. COST BY SERVICE"
  aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "$DAYS days ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=SERVICE \
    --output table

  # 3. Daily cost trend
  echo "\n3. DAILY COST TREND"
  aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "$DAYS days ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity DAILY \
    --metrics BlendedCost \
    --output table

  # 4. Cost by tag (Environment)
  echo "\n4. COST BY ENVIRONMENT"
  aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "$DAYS days ago" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=TAG,Key=Environment \
    --output table

  # 5. Cost anomalies
  echo "\n5. COST ANOMALIES"
  aws ce get-anomalies \
    --date-interval Start=$(date -u -d "$DAYS days ago" +%Y-%m-%d) \
    --max-results 10 \
    --output table

  # 6. Cost forecast
  echo "\n6. COST FORECAST (Next 30 days)"
  aws ce get-cost-forecast \
    --time-period Start=$(date -u +%Y-%m-%d),End=$(date -u -d '30 days' +%Y-%m-%d) \
    --metric BLENDED_COST \
    --granularity MONTHLY \
    --output table

  # 7. Recommendations
  echo "\n7. RIGHTSIZING RECOMMENDATIONS"
  aws ce get-rightsizing-recommendation \
    --service Lambda \
    --output table || echo "  No recommendations available"

  echo "\n8. SAVINGS PLANS RECOMMENDATIONS"
  aws ce get-savings-plans-purchase-recommendation \
    --lookback-period-in-days SIXTY_DAYS \
    --payment-option NO_UPFRONT \
    --savings-plans-type COMPUTE_SP \
    --term-in-years ONE_YEAR \
    --output table || echo "  No recommendations available"

  echo "\n========================================="
  echo "Cost Analysis Complete"
  echo "========================================="

} | tee $OUTPUT_FILE

echo "\nReport saved to: $OUTPUT_FILE"
