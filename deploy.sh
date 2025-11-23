#!/bin/bash
# AWS Network Visualizer - Quick Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 AWS Network Visualizer - Deployment Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    echo "   Install: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI installed${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install it first.${NC}"
    echo "   Install: https://www.terraform.io/downloads"
    exit 1
fi
echo -e "${GREEN}✅ Terraform installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured.${NC}"
    echo "   Run: aws configure"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials configured${NC}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}   AWS Account: ${ACCOUNT_ID}${NC}"

echo ""
echo "=============================================="
echo ""

# Prompt for deployment type
echo "Select deployment type:"
echo "1) Quick Start (CloudFront URL, no custom domain)"
echo "2) Production (Custom domain with SSL)"
read -p "Enter choice (1 or 2): " DEPLOY_TYPE

cd infrastructure

# Check if terraform.tfvars exists
if [ ! -f terraform.tfvars ]; then
    echo ""
    echo -e "${YELLOW}⚠️  terraform.tfvars not found${NC}"
    read -p "Create from example? (y/n): " CREATE_VARS

    if [ "$CREATE_VARS" = "y" ]; then
        cp terraform.tfvars.example terraform.tfvars

        # Generate unique bucket names
        RANDOM_SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 8)

        echo ""
        echo "Please provide some information:"
        read -p "AWS Region (default: us-east-1): " AWS_REGION
        AWS_REGION=${AWS_REGION:-us-east-1}

        read -p "Environment (default: production): " ENVIRONMENT
        ENVIRONMENT=${ENVIRONMENT:-production}

        read -p "Company/Project name (for bucket naming): " COMPANY_NAME
        COMPANY_NAME=${COMPANY_NAME:-mycompany}

        # Update terraform.tfvars
        sed -i.bak "s/aws_region = \"us-east-1\"/aws_region = \"$AWS_REGION\"/" terraform.tfvars
        sed -i.bak "s/environment = \"production\"/environment = \"$ENVIRONMENT\"/" terraform.tfvars
        sed -i.bak "s/yourcompany-12345/$COMPANY_NAME-$RANDOM_SUFFIX/g" terraform.tfvars

        if [ "$DEPLOY_TYPE" = "1" ]; then
            sed -i.bak "s/create_dns_records = true/create_dns_records = false/" terraform.tfvars
        else
            echo ""
            read -p "Your domain (e.g., yourcompany.com): " DOMAIN
            read -p "Subdomain (e.g., network-visualizer): " SUBDOMAIN
            read -p "ACM Certificate ARN (us-east-1 only!): " CERT_ARN

            sed -i.bak "s/create_dns_records = false/create_dns_records = true/" terraform.tfvars
            sed -i.bak "s/# hosted_zone_name = \"yourcompany.com\"/hosted_zone_name = \"$DOMAIN\"/" terraform.tfvars
            sed -i.bak "s/# frontend_domain_name = \"network-visualizer.yourcompany.com\"/frontend_domain_name = \"$SUBDOMAIN.$DOMAIN\"/" terraform.tfvars
            sed -i.bak "s|# acm_certificate_arn = \"arn:aws:acm:us-east-1:123456789012:certificate/abc-123-xyz\"|acm_certificate_arn = \"$CERT_ARN\"|" terraform.tfvars
        fi

        rm -f terraform.tfvars.bak

        echo -e "${GREEN}✅ Created terraform.tfvars${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Please review terraform.tfvars before continuing${NC}"
        read -p "Continue with deployment? (y/n): " CONTINUE

        if [ "$CONTINUE" != "y" ]; then
            echo "Exiting. Run this script again when ready."
            exit 0
        fi
    else
        echo "Please create terraform.tfvars manually and run this script again."
        exit 0
    fi
fi

echo ""
echo "=============================================="
echo "🏗️  Starting Terraform Deployment"
echo "=============================================="
echo ""

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

echo ""
echo "=============================================="
echo "📋 Planning Deployment"
echo "=============================================="
echo ""

# Plan
terraform plan -out=tfplan

echo ""
echo "=============================================="
read -p "Deploy infrastructure? (y/n): " DEPLOY

if [ "$DEPLOY" != "y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "🚀 Deploying infrastructure (this may take 5-10 minutes)..."
echo ""

# Apply
terraform apply tfplan

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""

# Get outputs
API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null || echo "N/A")
CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain_name 2>/dev/null || echo "N/A")
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "N/A")
CLOUDFRONT_DIST_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "N/A")
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "N/A")

echo "📊 Deployment Information:"
echo ""
echo "🌐 Frontend URL:     $FRONTEND_URL"
echo "🔗 API Endpoint:     $API_ENDPOINT"
echo "☁️  CloudFront URL:   https://$CLOUDFRONT_URL"
echo "📦 Frontend Bucket:  $FRONTEND_BUCKET"
echo "🆔 Distribution ID:  $CLOUDFRONT_DIST_ID"
echo ""

# Save outputs
cat > ../deployment-info.txt << EOF
AWS Network Visualizer - Deployment Information
Generated: $(date)

Frontend URL: $FRONTEND_URL
API Endpoint: $API_ENDPOINT
CloudFront URL: https://$CLOUDFRONT_URL
Frontend Bucket: $FRONTEND_BUCKET
CloudFront Distribution ID: $CLOUDFRONT_DIST_ID

AWS Account: $ACCOUNT_ID
Region: $AWS_REGION
Environment: $ENVIRONMENT
EOF

echo -e "${GREEN}✅ Deployment info saved to deployment-info.txt${NC}"
echo ""

# Ask about frontend deployment
if [ -d "../frontend" ]; then
    read -p "Deploy frontend files? (y/n): " DEPLOY_FRONTEND

    if [ "$DEPLOY_FRONTEND" = "y" ]; then
        echo ""
        echo "📤 Deploying frontend..."

        cd ../frontend

        if [ -f "package.json" ]; then
            echo "Building React app..."
            npm run build

            echo "Uploading to S3..."
            aws s3 sync build/ "s3://$FRONTEND_BUCKET" --delete
        else
            echo "Uploading HTML files..."
            aws s3 sync . "s3://$FRONTEND_BUCKET" --exclude "node_modules/*"
        fi

        echo "Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id "$CLOUDFRONT_DIST_ID" \
            --paths "/*"

        echo -e "${GREEN}✅ Frontend deployed!${NC}"
        cd ../infrastructure
    fi
fi

echo ""
echo "=============================================="
echo "🎉 All Done!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Visit your frontend: $FRONTEND_URL"
echo "2. Test the API: curl $API_ENDPOINT/health"
echo "3. View CloudWatch dashboard for monitoring"
echo "4. Set up automated discovery schedules"
echo ""
echo "For detailed documentation, see DEPLOYMENT_GUIDE.md"
echo ""
echo -e "${GREEN}Happy visualizing! 🚀${NC}"
