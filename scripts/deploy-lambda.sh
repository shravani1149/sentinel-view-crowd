#!/bin/bash

# Deployment script for AWS Lambda + Amplify backend

echo "🚀 Deploying Sentinel View to AWS Lambda + Amplify..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check if AWS SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Please install it first."
    exit 1
fi

# Check if Amplify CLI is installed
if ! command -v amplify &> /dev/null; then
    echo "❌ Amplify CLI not found. Installing..."
    npm install -g @aws-amplify/cli
fi

echo "📦 Building Lambda package..."
cd lambda

# Create deployment package
pip install -r requirements.txt -t .
zip -r ../deployment.zip .

cd ..

echo "📥 Uploading ML models to S3..."
# Upload models to S3 (you need to create the bucket first)
aws s3 cp backend/yolov8n.pt s3://sentinel-view-models-temp/yolov8n.pt
aws s3 cp backend/yolov8s.pt s3://sentinel-view-models-temp/yolov8s.pt

echo "🏗️ Deploying CloudFormation stack..."
sam deploy --template-file template.yaml --stack-name sentinel-view-backend --capabilities CAPABILITY_IAM --guided

echo "⚙️ Configuring Amplify..."
amplify init
amplify add api
amplify add storage
amplify push

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update your frontend .env.production with the API Gateway URL"
echo "2. Test the deployment by uploading an image"
echo "3. Monitor Lambda functions in AWS Console"
