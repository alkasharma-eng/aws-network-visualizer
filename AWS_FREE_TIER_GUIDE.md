# 🆓 AWS Free Tier Deployment Guide

Deploy the AWS Network Visualizer using **100% AWS Free Tier** services - **$0/month** for your first year!

---

## 💰 Free Tier Services Used

| Service | Free Tier Limit | Our Usage | Cost |
|---------|----------------|-----------|------|
| Lambda | 1M requests/month | ~100K/month | $0 ✅ |
| DynamoDB | 25GB storage | ~1GB | $0 ✅ |
| S3 | 5GB storage | ~2GB | $0 ✅ |
| CloudFront | 1TB data transfer | ~10GB | $0 ✅ |
| API Gateway | 1M requests/month | ~100K/month | $0 ✅ |
| **Total** | **First 12 months** | **All included** | **$0** ✅ |

**After Free Tier expires**: ~$10-30/month depending on usage

---

## 🚀 Quick Deploy (15 Minutes)

### Prerequisites

```bash
# 1. AWS Account (create at aws.amazon.com)
# 2. AWS CLI installed and configured
aws --version  # Should show v2.x

# 3. Terraform installed
terraform --version  # Should show v1.0+

# 4. Git repository cloned
cd aws-network-visualizer
```

### Step 1: Configure for Free Tier

Edit `infrastructure/terraform.tfvars`:

```hcl
# Minimal Free Tier Configuration
aws_region = "us-east-1"  # Free tier is best in us-east-1
environment = "development"

# Storage (Free Tier limits)
dynamodb_table_name = "network-viz-free-tier"
dynamodb_billing_mode = "PAY_PER_REQUEST"  # No provisioned capacity
s3_bucket_name = "network-viz-free-YOURNAME"  # Must be unique
frontend_bucket_name = "network-viz-frontend-YOURNAME"  # Must be unique

# Regions (limit to 1-2 to stay in free tier)
aws_regions = ["us-east-1"]  # Just one region

# Lambda (Free tier: 1M requests, 400,000 GB-seconds)
lambda_memory_size = 512  # Lower memory = more free tier usage
lambda_timeout = 300  # 5 minutes (vs 15 min default)

# Discovery Schedule (less frequent = lower costs)
discovery_schedule = "rate(6 hours)"  # Every 6 hours vs every hour

# API Gateway (Free tier: 1M requests/month)
api_throttling_rate_limit = 100  # Lower to conserve free tier
api_enable_caching = false  # Caching costs extra

# CloudFront (Free tier: 1TB transfer/month)
cloudfront_price_class = "PriceClass_100"  # US/Europe only

# Disable paid features
enable_ai_analysis = false  # Bedrock costs extra
enable_elasticache = false  # No free tier
enable_waf = false  # Costs extra
enable_backup = false  # Costs extra
enable_guardduty = false  # Costs extra

# Custom domain (optional, costs $12/year)
create_dns_records = false  # Use CloudFront URL instead
```

### Step 2: Deploy Infrastructure

```bash
cd infrastructure

# Initialize
terraform init

# Deploy
terraform apply

# Type 'yes' when prompted
```

**Wait 5-10 minutes for deployment...**

### Step 3: Get Your Free URLs

```bash
# After deployment completes:
terraform output

# You'll get:
# api_endpoint = "https://abc123.execute-api.us-east-1.amazonaws.com/prod"
# cloudfront_domain_name = "d1234567890.cloudfront.net"
# frontend_url = "https://d1234567890.cloudfront.net"
```

**Save these URLs!** Your app is live at the frontend_url.

### Step 4: Deploy Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Configure API endpoint (use your api_endpoint from above)
echo "VITE_API_BASE_URL=https://YOUR_API_ENDPOINT" > .env.local

# Build
npm run build

# Deploy to S3 (use your frontend bucket name)
aws s3 sync dist/ s3://network-viz-frontend-YOURNAME/ --delete

# Get your CloudFront distribution ID
DIST_ID=$(cd ../infrastructure && terraform output -raw cloudfront_distribution_id)

# Invalidate cache
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

**Done!** Visit your frontend_url to see the app live! 🎉

---

## 🧪 LocalStack - 100% Free Local Testing

Test everything locally before deploying to AWS. **$0 cost, no AWS account needed!**

### Install LocalStack

```bash
# Option 1: Docker (recommended)
docker pull localstack/localstack

# Option 2: pip
pip install localstack

# Option 3: Homebrew (macOS)
brew install localstack/tap/localstack-cli
```

### Start LocalStack

```bash
# Start all AWS services locally
localstack start

# Or with Docker
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -p 4571:4571 \
  -e SERVICES="lambda,dynamodb,s3,apigateway,cloudfront" \
  localstack/localstack

# Verify it's running
curl http://localhost:4566/_localstack/health
```

### Configure for LocalStack

```bash
# Set AWS CLI to use LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Test it
aws --endpoint-url=http://localhost:4566 s3 ls
```

### Deploy to LocalStack

```bash
# Create Terraform config for LocalStack
cat > infrastructure/localstack.tfvars << 'EOF'
# LocalStack configuration
aws_region = "us-east-1"
environment = "local"

# Use local endpoint
aws_endpoint = "http://localhost:4566"

# Storage
dynamodb_table_name = "network-viz-local"
s3_bucket_name = "network-viz-local"
frontend_bucket_name = "network-viz-frontend-local"

# Minimal config
aws_regions = ["us-east-1"]
enable_ai_analysis = false
enable_xray = false
EOF

# Deploy to LocalStack
terraform init
terraform apply -var-file="localstack.tfvars"
```

### Test Locally

```bash
# Trigger discovery
curl -X POST http://localhost:4566/discover \
  -H "Content-Type: application/json" \
  -d '{"region":"us-east-1"}'

# Get topology
curl http://localhost:4566/topology/us-east-1/vpc-12345

# Check DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb scan \
  --table-name network-viz-local

# List S3 files
aws --endpoint-url=http://localhost:4566 s3 ls s3://network-viz-local/
```

---

## 💡 Free Tier Optimization Tips

### 1. Reduce Lambda Invocations

```hcl
# Run discovery less frequently
discovery_schedule = "rate(12 hours)"  # vs every hour

# Lower memory = more free tier compute
lambda_memory_size = 512  # vs 3008 MB
```

**Savings**: Use 8x more of free tier

### 2. Limit Regions

```hcl
# Scan fewer regions
aws_regions = ["us-east-1"]  # vs 8 regions
```

**Savings**: 8x fewer API calls

### 3. Disable AI Analysis

```hcl
# Bedrock not in free tier
enable_ai_analysis = false
```

**Savings**: ~$20/month

### 4. Use CloudFront URL (No Custom Domain)

```hcl
create_dns_records = false
```

**Savings**: $12/year for domain

### 5. Manual Discovery Triggers

```bash
# Don't use scheduled discovery
# Trigger manually when needed:
curl -X POST https://YOUR_API/discover
```

**Savings**: 90% fewer Lambda invocations

---

## 📊 Monitor Free Tier Usage

### Check Your Usage

```bash
# AWS Console
# → Billing Dashboard
# → Free Tier
# → See all service usage

# Or use AWS CLI
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

### Set Up Billing Alerts

```bash
# Create budget alert
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget '{
    "BudgetName": "NetworkVisualizerBudget",
    "BudgetLimit": {
      "Amount": "5",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'

# Get email when you exceed $5/month
```

---

## 🎯 Expected Free Tier Usage

### Monthly Usage (Development)

| Service | Usage | Free Tier Limit | Status |
|---------|-------|-----------------|--------|
| Lambda Requests | 50K | 1M | ✅ 5% |
| Lambda Compute | 20K GB-sec | 400K GB-sec | ✅ 5% |
| DynamoDB Read | 100K | 25 units/sec | ✅ 1% |
| DynamoDB Write | 25K | 25 units/sec | ✅ 1% |
| S3 Storage | 0.5GB | 5GB | ✅ 10% |
| S3 Requests | 10K | 20K GET, 2K PUT | ✅ 50% |
| CloudFront | 5GB | 1TB | ✅ 0.5% |
| API Gateway | 50K | 1M | ✅ 5% |

**Total Cost**: $0.00 ✅

### Monthly Usage (Production - Small Team)

| Service | Usage | Free Tier | Overage | Cost |
|---------|-------|-----------|---------|------|
| Lambda | 200K req | 1M free | 0 | $0.00 |
| DynamoDB | 500MB | 25GB free | 0 | $0.00 |
| S3 | 2GB | 5GB free | 0 | $0.00 |
| CloudFront | 50GB | 1TB free | 0 | $0.00 |
| **Total** | | | | **$0.00** |

**Still 100% free!** ✅

---

## 🚨 Avoiding Unexpected Charges

### 1. Enable Cost Alerts

```bash
# Set billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "NetworkViz-BillingAlert" \
  --alarm-description "Alert when bill exceeds $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### 2. Review Before Deploying

```bash
# Preview what will be created
terraform plan

# Look for expensive resources:
# ❌ NAT Gateway ($32/month)
# ❌ Reserved concurrency ($6/month)
# ❌ Provisioned DynamoDB ($?)
```

### 3. Auto-Shutdown After Free Tier

```bash
# Add this to your calendar:
# 11 months after creating AWS account
# → Review and delete unused resources
# → Or accept $10-30/month cost
```

### 4. Use Tags for Cost Tracking

```hcl
# In terraform.tfvars
common_tags = {
  Project = "NetworkVisualizer"
  Environment = "FreeTier"
  Owner = "YourName"
}
```

Then filter billing by tag.

---

## 🔄 Upgrade Path (After Free Tier)

### Year 2+ Pricing

**Option A: Stay Free with LocalStack**
- Use LocalStack for development
- Only deploy to AWS for demos
- Cost: $0/month ✅

**Option B: Minimal AWS ($10/month)**
```hcl
# Keep using free tier where possible
# Pay only for:
# - DynamoDB: $2.50/month (1M reads)
# - S3: $0.50/month (20GB)
# - Lambda: $2/month (extra invocations)
# - CloudFront: $1/month (extra transfer)
# - API Gateway: $3.50/month (extra requests)
# Total: ~$10/month
```

**Option C: Full Production ($50/month)**
```hcl
# Enable all features:
enable_ai_analysis = true  # +$20/month
enable_waf = true  # +$5/month
enable_backup = true  # +$3/month
enable_elasticache = true  # +$15/month
# Total: ~$50/month
```

---

## 📝 Free Tier Checklist

Before deploying, verify:

- [ ] Using `PAY_PER_REQUEST` for DynamoDB (not provisioned)
- [ ] Lambda memory ≤ 512MB (use more free tier)
- [ ] Discovery schedule ≤ every 6 hours (not every hour)
- [ ] Scanning ≤ 2 regions (not all 16)
- [ ] AI analysis disabled (Bedrock costs extra)
- [ ] ElastiCache disabled (no free tier)
- [ ] WAF disabled (costs extra)
- [ ] Using CloudFront URL (no Route53 domain)
- [ ] Billing alerts configured
- [ ] Budget set to $5/month

---

## 🎉 Success!

You now have a **production-grade AWS Network Visualizer** running on:
- ✅ **$0/month** for first 12 months
- ✅ **100% Free Tier** services
- ✅ **Professional UI** at CloudFront URL
- ✅ **Enterprise features** (minus AI)
- ✅ **Scalable architecture**

**LocalStack for development, AWS for production!** 🚀

---

## 🆘 Troubleshooting

### "Free tier limit exceeded"

Check usage:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE
```

### "Unexpected charges"

1. Go to AWS Billing Dashboard
2. Click "Bills" → see breakdown
3. Common culprits:
   - NAT Gateway ($32/month) - delete if created
   - Data transfer between regions
   - Reserved Lambda concurrency

### LocalStack not working

```bash
# Restart LocalStack
docker restart localstack

# Check logs
docker logs localstack

# Verify services
curl http://localhost:4566/_localstack/health
```

---

## 📚 Additional Resources

- **AWS Free Tier**: https://aws.amazon.com/free/
- **LocalStack Docs**: https://docs.localstack.cloud/
- **AWS Pricing Calculator**: https://calculator.aws/
- **This Project**: See `DEPLOYMENT_GUIDE.md`

**Enjoy your free AWS infrastructure visualization!** 💰✨
