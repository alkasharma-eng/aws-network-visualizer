#!/bin/bash
# Run comprehensive load tests
# Usage: ./scripts/run-load-tests.sh <environment> <test-type>

set -e

ENVIRONMENT=${1:-staging}
TEST_TYPE=${2:-all}

echo "========================================="
echo "Running Load Tests"
echo "Environment: $ENVIRONMENT"
echo "Test Type: $TEST_TYPE"
echo "========================================="

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
  export $(cat .env.$ENVIRONMENT | grep -v '#' | xargs)
fi

# Get API endpoint
if [ "$ENVIRONMENT" == "production" ]; then
  export API_ENDPOINT="https://api.network-visualizer.com"
else
  export API_ENDPOINT="https://api-$ENVIRONMENT.network-visualizer.com"
fi

echo "API Endpoint: $API_ENDPOINT"

# Create results directory
RESULTS_DIR="test-results/load/$(date +%Y%m%d-%H%M%S)"
mkdir -p $RESULTS_DIR

# Run Locust tests
if [ "$TEST_TYPE" == "all" ] || [ "$TEST_TYPE" == "locust" ]; then
  echo "\n=== Running Locust Load Tests ==="
  locust -f tests/load/locustfile.py \
    --host=$API_ENDPOINT \
    --api-key=$API_KEY \
    --users 100 \
    --spawn-rate 10 \
    --run-time 10m \
    --headless \
    --html=$RESULTS_DIR/locust-report.html \
    --csv=$RESULTS_DIR/locust
fi

# Run Artillery tests
if [ "$TEST_TYPE" == "all" ] || [ "$TEST_TYPE" == "artillery" ]; then
  echo "\n=== Running Artillery Load Tests ==="
  artillery run tests/load/artillery.yml \
    --output $RESULTS_DIR/artillery-results.json

  # Generate HTML report
  artillery report $RESULTS_DIR/artillery-results.json \
    --output $RESULTS_DIR/artillery-report.html
fi

# Run performance tests
if [ "$TEST_TYPE" == "all" ] || [ "$TEST_TYPE" == "performance" ]; then
  echo "\n=== Running Performance Tests ==="
  pytest tests/performance/ \
    --api-endpoint=$API_ENDPOINT \
    --api-key=$API_KEY \
    -v \
    --junitxml=$RESULTS_DIR/performance-results.xml \
    --html=$RESULTS_DIR/performance-report.html
fi

# Run stress tests (optional, more aggressive)
if [ "$TEST_TYPE" == "stress" ]; then
  echo "\n=== Running Stress Tests ==="
  locust -f tests/load/locustfile.py \
    --host=$API_ENDPOINT \
    --api-key=$API_KEY \
    --users 500 \
    --spawn-rate 50 \
    --run-time 5m \
    --headless \
    --html=$RESULTS_DIR/stress-test-report.html
fi

echo "\n========================================="
echo "Load Tests Complete"
echo "Results saved to: $RESULTS_DIR"
echo "========================================="

# Upload results to S3 (optional)
if [ ! -z "$S3_RESULTS_BUCKET" ]; then
  echo "Uploading results to S3..."
  aws s3 sync $RESULTS_DIR s3://$S3_RESULTS_BUCKET/load-tests/$(basename $RESULTS_DIR)/
fi

# Analyze results and check against SLAs
echo "\n=== SLA Compliance Check ==="
python scripts/analyze-load-test-results.py $RESULTS_DIR
