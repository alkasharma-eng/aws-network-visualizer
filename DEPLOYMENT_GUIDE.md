# 🚀 AWS Network Visualizer - Complete Deployment Guide

This guide will help you deploy the AWS Network Visualizer as a **production web application** accessible via a custom domain (like `network-visualizer.yourcompany.com`) or CloudFront URL.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Without Custom Domain)](#quick-start-without-custom-domain)
4. [Production Deployment (With Custom Domain)](#production-deployment-with-custom-domain)
5. [Creating a Frontend Web UI](#creating-a-frontend-web-ui)
6. [Testing Your Deployment](#testing-your-deployment)
7. [Creating a Demo for Executives](#creating-a-demo-for-executives)
8. [Ongoing Operations](#ongoing-operations)

---

## 🏗️ Architecture Overview

Your deployment will create a **serverless architecture** on AWS:

```
┌────────────────────────────────────────────────────────────────┐
│                        Internet Users                           │
│           (You, Andy Jassy, or anyone you share with)          │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Route53 DNS │  (Optional: custom domain)
                    └──────┬───────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   CloudFront CDN        │  Global edge locations
              │   (SSL/HTTPS enabled)   │  for fast access worldwide
              └─────┬──────────┬────────┘
                    │          │
        ┌───────────┘          └──────────┐
        ▼                                 ▼
┌───────────────┐                  ┌─────────────┐
│ S3 Frontend   │                  │ API Gateway │
│ (React/HTML)  │                  │ (REST API)  │
└───────────────┘                  └──────┬──────┘
                                          │
                           ┌──────────────┼──────────────┐
                           ▼              ▼              ▼
                    ┌──────────┐   ┌──────────┐  ┌──────────┐
                    │ Lambda   │   │ Lambda   │  │ Lambda   │
                    │Discovery │   │ Analysis │  │   API    │
                    └────┬─────┘   └────┬─────┘  └────┬─────┘
                         │              │             │
                         └──────┬───────┴─────────────┘
                                ▼
                    ┌──────────────────────┐
                    │    DynamoDB          │  Topology data storage
                    │    S3                │  Visualizations & archives
                    │    ElastiCache       │  Caching layer
                    └──────────────────────┘
```

**Key Features:**
- 🌍 **Global CDN**: CloudFront ensures fast loading worldwide
- 🔒 **HTTPS**: Automatic SSL/TLS encryption
- 📊 **Monitoring**: CloudWatch dashboards and X-Ray tracing
- 💰 **Serverless**: Pay only for what you use
- 🔐 **Secure**: WAF, API keys, and IAM policies

---

## ✅ Prerequisites

### Required Tools

1. **AWS Account** with appropriate permissions
2. **Terraform** (v1.0+)
   ```bash
   # Install Terraform
   brew install terraform  # macOS
   # OR download from https://www.terraform.io/downloads
   ```

3. **AWS CLI** configured
   ```bash
   # Install AWS CLI
   brew install awscli  # macOS

   # Configure credentials
   aws configure
   # Enter your AWS Access Key ID, Secret Key, and default region
   ```

4. **Python 3.10+** (for local testing)
   ```bash
   python --version  # Should be 3.10+
   ```

### IAM Permissions Required

Your AWS account needs permissions to create:
- Lambda functions
- API Gateway
- DynamoDB tables
- S3 buckets
- CloudFront distributions
- Route53 records (if using custom domain)
- IAM roles and policies

**Recommended**: Use an IAM user with `AdministratorAccess` for initial deployment.

---

## 🚀 Quick Start (Without Custom Domain)

This gets you up and running in **~15 minutes** with a CloudFront URL.

### Step 1: Configure Terraform Variables

```bash
cd infrastructure

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your settings
nano terraform.tfvars
```

**Minimal Configuration** (edit `terraform.tfvars`):

```hcl
# Basic Settings
aws_region  = "us-east-1"  # Your preferred region
environment = "production"  # or "staging", "dev"

# Application Settings
dynamodb_table_name = "network-visualizer-topology"
s3_bucket_name      = "network-visualizer-data-YOURNAME"  # Must be globally unique
frontend_bucket_name = "network-visualizer-frontend-YOURNAME"  # Must be globally unique

# Regions to scan
aws_regions = ["us-east-1", "us-west-2", "eu-west-1"]

# AI Analysis
enable_ai_analysis = true

# Discovery Schedule (runs automatically)
discovery_schedule = "rate(1 hour)"  # Run every hour

# API Settings (no custom domain yet)
create_dns_records = false
```

### Step 2: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy! (takes ~5-10 minutes)
terraform apply
# Type 'yes' when prompted
```

### Step 3: Note Your URLs

After deployment, Terraform will output:

```
Outputs:

api_endpoint = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"
cloudfront_domain_name = "d1234567890abc.cloudfront.net"
frontend_url = "https://d1234567890abc.cloudfront.net"
```

**Save these URLs!** Your app is now live at the `frontend_url`.

### Step 4: Upload Frontend (if you have one)

```bash
# If you have a React/HTML frontend
cd ../frontend  # (you'll need to create this)

# Build the frontend
npm run build

# Upload to S3
aws s3 sync build/ s3://network-visualizer-frontend-YOURNAME --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID_FROM_OUTPUT> \
  --paths "/*"
```

**🎉 Your app is now live!** Visit the `frontend_url` from Terraform outputs.

---

## 🌐 Production Deployment (With Custom Domain)

Make your app accessible at `network-visualizer.yourcompany.com`

### Step 1: Get a Domain Name

**Option A: Use Existing Domain**
- If you already have a domain in Route53, skip to Step 2

**Option B: Register New Domain**
```bash
# Register via AWS Console
# Go to: Route53 → Registered Domains → Register Domain
# Cost: ~$12/year for .com domains
```

**Option C: Transfer External Domain**
- Transfer your domain from GoDaddy, Namecheap, etc. to Route53
- Follow: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-transfer-to-route-53.html

### Step 2: Request SSL Certificate

**IMPORTANT**: SSL certificate for CloudFront **must** be in `us-east-1`

```bash
# Switch to us-east-1 region
export AWS_DEFAULT_REGION=us-east-1

# Request certificate via AWS Console:
# 1. Go to: AWS Certificate Manager (ACM)
# 2. Click "Request certificate"
# 3. Enter domain: network-visualizer.yourcompany.com
# 4. Choose DNS validation
# 5. Click "Create records in Route53" (if using Route53)
# 6. Wait ~5 minutes for validation
```

Or via CLI:
```bash
aws acm request-certificate \
  --domain-name network-visualizer.yourcompany.com \
  --validation-method DNS \
  --region us-east-1

# Note the CertificateArn from output
```

**Get the certificate ARN:**
```bash
aws acm list-certificates --region us-east-1
# Copy the CertificateArn
```

### Step 3: Update Terraform Configuration

Edit `terraform.tfvars`:

```hcl
# Enable DNS and custom domain
create_dns_records = true
hosted_zone_name   = "yourcompany.com"  # Your Route53 hosted zone
frontend_domain_name = "network-visualizer.yourcompany.com"
frontend_domain_names = ["network-visualizer.yourcompany.com"]

# SSL Certificate ARN (from Step 2)
acm_certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/abc-123-xyz"

# Enable Route53 health checks
enable_route53_health_check = true
```

### Step 4: Redeploy

```bash
cd infrastructure

# Apply changes
terraform apply
# Type 'yes'
```

**🎉 Your app is now at:** `https://network-visualizer.yourcompany.com`

---

## 🎨 Creating a Frontend Web UI

Currently, you have a REST API. Let's add a beautiful web interface!

### Option 1: Quick HTML Dashboard (5 minutes)

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>AWS Network Visualizer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-8">
        <h1 class="text-4xl font-bold mb-8 text-blue-600">
            🌐 AWS Network Visualizer
        </h1>

        <!-- Discovery Section -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-2xl font-semibold mb-4">Start Discovery</h2>
            <div class="flex gap-4">
                <input
                    id="regionInput"
                    type="text"
                    placeholder="Region (e.g., us-east-1)"
                    class="border p-2 rounded flex-1"
                />
                <button
                    onclick="startDiscovery()"
                    class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
                >
                    Start Discovery
                </button>
            </div>
            <div id="discoveryStatus" class="mt-4"></div>
        </div>

        <!-- Topology Visualization -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-2xl font-semibold mb-4">Network Topology</h2>
            <div id="topology" class="border rounded" style="height: 600px;">
                <svg id="topologySvg" width="100%" height="100%"></svg>
            </div>
        </div>

        <!-- Resource List -->
        <div class="bg-white rounded-lg shadow p-6 mt-6">
            <h2 class="text-2xl font-semibold mb-4">Discovered Resources</h2>
            <div id="resourceList" class="overflow-auto"></div>
        </div>
    </div>

    <script>
        // Replace with your API endpoint from Terraform output
        const API_ENDPOINT = 'YOUR_API_ENDPOINT_HERE';

        async function startDiscovery() {
            const region = document.getElementById('regionInput').value;
            const status = document.getElementById('discoveryStatus');

            status.innerHTML = '🔄 Starting discovery...';

            try {
                const response = await fetch(`${API_ENDPOINT}/discover`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ region })
                });

                const data = await response.json();
                status.innerHTML = `✅ Discovery started! Job ID: ${data.jobId}`;

                // Poll for results
                setTimeout(() => loadTopology(region), 5000);
            } catch (error) {
                status.innerHTML = `❌ Error: ${error.message}`;
            }
        }

        async function loadTopology(region, vpcId = 'all') {
            try {
                const response = await fetch(`${API_ENDPOINT}/topology/${region}/${vpcId}`);
                const data = await response.json();

                visualizeTopology(data.topology);
                displayResources(data.topology);
            } catch (error) {
                console.error('Error loading topology:', error);
            }
        }

        function visualizeTopology(topology) {
            // Simple D3.js visualization
            const svg = d3.select('#topologySvg');
            svg.selectAll('*').remove();

            // Add your D3.js visualization here
            // This is a placeholder
            svg.append('text')
                .attr('x', '50%')
                .attr('y', '50%')
                .attr('text-anchor', 'middle')
                .text('Topology visualization will appear here')
                .style('font-size', '20px');
        }

        function displayResources(topology) {
            const resourceList = document.getElementById('resourceList');
            const resources = topology.resources || [];

            const html = resources.map(r => `
                <div class="border-b p-3">
                    <span class="font-semibold">${r.type}</span>: ${r.id}
                    <span class="text-gray-500 text-sm ml-2">${r.region}</span>
                </div>
            `).join('');

            resourceList.innerHTML = html || '<p class="text-gray-500">No resources discovered yet</p>';
        }

        // Check API health on load
        fetch(`${API_ENDPOINT}/health`)
            .then(r => r.json())
            .then(d => console.log('API Status:', d))
            .catch(e => console.error('API unreachable:', e));
    </script>
</body>
</html>
```

**Deploy:**
```bash
# Update the API_ENDPOINT in index.html with your API endpoint
sed -i "s|YOUR_API_ENDPOINT_HERE|$(terraform output -raw api_endpoint)|" frontend/index.html

# Upload to S3
aws s3 cp frontend/index.html s3://network-visualizer-frontend-YOURNAME/ --content-type "text/html"

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Option 2: Full React Application (Production-Ready)

For a complete React application with advanced visualizations:

```bash
# Create React app
npx create-react-app frontend
cd frontend

# Install dependencies
npm install \
  d3 \
  axios \
  react-router-dom \
  @mui/material \
  @emotion/react \
  @emotion/styled

# Create your React components
# (See full React example in separate file)

# Build
npm run build

# Deploy
aws s3 sync build/ s3://network-visualizer-frontend-YOURNAME --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

---

## 🧪 Testing Your Deployment

### Test 1: API Health Check

```bash
curl https://YOUR_CLOUDFRONT_DOMAIN/health
# Expected: {"status":"healthy","request_id":"..."}
```

### Test 2: Trigger Discovery

```bash
curl -X POST https://YOUR_API_ENDPOINT/discover \
  -H "Content-Type: application/json" \
  -d '{"region":"us-east-1"}'
```

### Test 3: Get Topology

```bash
curl https://YOUR_API_ENDPOINT/topology/us-east-1/vpc-12345
```

### Test 4: Frontend Access

Open in browser:
```
https://YOUR_CLOUDFRONT_DOMAIN
# or
https://network-visualizer.yourcompany.com
```

---

## 🎯 Creating a Demo for Executives

### For Andy Jassy or Executive Presentations

**Option 1: Shared CloudFront URL**
```
Share: https://d1234567890abc.cloudfront.net
- No authentication required
- Fast global access
- Professional CloudFront URL
```

**Option 2: Custom Branded Domain**
```
Share: https://network-visualizer.yourcompany.com
- Professional branded domain
- SSL/HTTPS automatically
- Easy to remember
```

**Option 3: Password-Protected Demo**

Add basic auth to CloudFront:

```bash
# Use Lambda@Edge for authentication
# See: infrastructure/modules/cloudfront/auth.tf (create this)
```

### Demo Preparation Checklist

- [ ] Run discovery across key regions
- [ ] Verify visualizations load quickly
- [ ] Test on mobile devices
- [ ] Prepare sample VPCs with interesting topologies
- [ ] Create executive dashboard with key metrics
- [ ] Test from different geographic locations
- [ ] Ensure CloudWatch dashboards are accessible
- [ ] Prepare talking points about enterprise features

---

## 🔧 Ongoing Operations

### Monitoring

**CloudWatch Dashboard:**
```bash
# Get dashboard URL
terraform output cloudwatch_dashboard_url
```

**View Logs:**
```bash
# Lambda logs
aws logs tail /aws/lambda/network-visualizer-discovery --follow

# API Gateway logs
aws logs tail /aws/apigateway/network-visualizer-api --follow
```

### Updating the Application

```bash
# Update code
git pull

# Rebuild Lambda packages
cd lambda_functions
./build.sh  # (create if needed)

# Redeploy with Terraform
cd ../infrastructure
terraform apply
```

### Scaling

The application automatically scales! But you can adjust:

```hcl
# In terraform.tfvars

# API rate limiting
api_throttling_rate_limit = 10000  # requests per second
api_throttling_burst_limit = 5000  # burst capacity

# Lambda concurrency
lambda_reserved_concurrency = 100  # max concurrent executions

# Discovery schedule
discovery_schedule = "rate(30 minutes)"  # more frequent scans
```

### Cost Optimization

Expected monthly costs for enterprise use:

| Service | Est. Cost | Notes |
|---------|-----------|-------|
| Lambda | $20-100 | Based on execution time |
| DynamoDB | $10-50 | On-demand pricing |
| S3 | $5-20 | Storage + requests |
| CloudFront | $10-50 | Data transfer |
| API Gateway | $5-20 | API calls |
| **Total** | **$50-240/mo** | Scales with usage |

**Cost Savings:**
- Use S3 Intelligent-Tiering
- Enable CloudFront caching (included)
- Set DynamoDB auto-scaling
- Use Lambda reserved concurrency limits

---

## 🆘 Troubleshooting

### Issue: Frontend shows CORS errors

**Fix:**
```hcl
# In terraform.tfvars, add your domain:
frontend_cors_origins = [
  "https://network-visualizer.yourcompany.com",
  "http://localhost:3000"  # for local development
]

# Reapply
terraform apply
```

### Issue: API returns 403 Forbidden

**Fix:**
```bash
# Check API key
aws apigateway get-api-keys

# Or disable API key requirement in terraform.tfvars:
api_require_api_key = false
```

### Issue: CloudFront shows 404

**Fix:**
```bash
# Verify files uploaded to S3
aws s3 ls s3://network-visualizer-frontend-YOURNAME/

# Ensure index.html exists
aws s3 cp frontend/index.html s3://network-visualizer-frontend-YOURNAME/

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Issue: DNS not resolving

**Fix:**
```bash
# Check Route53 records
aws route53 list-resource-record-sets \
  --hosted-zone-id $(aws route53 list-hosted-zones --query "HostedZones[?Name=='yourcompany.com.'].Id" --output text)

# Verify nameservers match
dig NS yourcompany.com
```

---

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues
- **AWS Support**: https://console.aws.amazon.com/support

---

## 🎉 Success!

You now have a **production-grade, enterprise-scale AWS Network Visualizer** deployed and accessible worldwide!

**Next Steps:**
1. Share the URL with your team
2. Set up automated discovery schedules
3. Create custom dashboards for different teams
4. Integrate with your CI/CD pipeline
5. Add custom branding to the frontend

**Happy Visualizing! 🚀**
