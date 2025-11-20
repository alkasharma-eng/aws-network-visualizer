#!/bin/bash
# Build and push Docker images to ECR
# Usage: ./scripts/build-and-push.sh <environment> <version>

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Building and pushing Docker images for environment: $ENVIRONMENT, version: $VERSION"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push main application image
echo "Building main application image..."
docker build -t network-visualizer-app:$VERSION -f Dockerfile .
docker tag network-visualizer-app:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-app-$ENVIRONMENT:$VERSION
docker tag network-visualizer-app:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-app-$ENVIRONMENT:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-app-$ENVIRONMENT:$VERSION
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-app-$ENVIRONMENT:latest

# Build and push Lambda image
echo "Building Lambda image..."
docker build -t network-visualizer-lambda:$VERSION -f Dockerfile.lambda .
docker tag network-visualizer-lambda:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-lambda-$ENVIRONMENT:$VERSION
docker tag network-visualizer-lambda:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-lambda-$ENVIRONMENT:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-lambda-$ENVIRONMENT:$VERSION
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-lambda-$ENVIRONMENT:latest

# Build and push frontend image
echo "Building frontend image..."
cd frontend
docker build -t network-visualizer-frontend:$VERSION \
  --build-arg VITE_API_BASE_URL=$VITE_API_BASE_URL \
  -f Dockerfile .
docker tag network-visualizer-frontend:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-frontend-$ENVIRONMENT:$VERSION
docker tag network-visualizer-frontend:$VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-frontend-$ENVIRONMENT:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-frontend-$ENVIRONMENT:$VERSION
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-frontend-$ENVIRONMENT:latest
cd ..

echo "✅ All images built and pushed successfully!"
echo "Application image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-app-$ENVIRONMENT:$VERSION"
echo "Lambda image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-lambda-$ENVIRONMENT:$VERSION"
echo "Frontend image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/network-visualizer-frontend-$ENVIRONMENT:$VERSION"
