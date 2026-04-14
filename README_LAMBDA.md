# AWS Lambda + Amplify Deployment Guide

## Overview
This guide explains how to deploy the Sentinel View backend using AWS Lambda and Amplify for a scalable, serverless architecture.

## Architecture
```
Frontend (Netlify) → API Gateway → Lambda Functions → S3 Storage
                                      ↓
                                 ML Models (S3)
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured:
   ```bash
   pip install awscli
   aws configure
   ```

3. **AWS SAM CLI** for deployment:
   ```bash
   pip install aws-sam-cli
   ```

4. **Amplify CLI**:
   ```bash
   npm install -g @aws-amplify/cli
   ```

## Deployment Steps

### 1. Prepare ML Models
```bash
# Create S3 bucket for models
aws s3 mb s3://sentinel-view-models-unique-name

# Upload YOLO models
aws s3 cp backend/yolov8n.pt s3://sentinel-view-models-unique-name/yolov8n.pt
aws s3 cp backend/yolov8s.pt s3://sentinel-view-models-unique-name/yolov8s.pt
```

### 2. Build Lambda Package
```bash
cd lambda
pip install -r requirements.txt -t .
zip -r ../deployment.zip .
cd ..
```

### 3. Deploy with SAM
```bash
sam deploy --template-file template.yaml \
  --stack-name sentinel-view-backend \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3BucketName=sentinel-view-models-unique-name
```

### 4. Configure Amplify
```bash
amplify init
amplify add api
amplify add storage
amplify push
```

## Lambda Function Configuration

### Memory and Performance
- **Memory**: 2048MB (required for ML processing)
- **Timeout**: 300 seconds (5 minutes)
- **Runtime**: Python 3.9

### Environment Variables
- `S3_BUCKET_NAME`: For file uploads
- Model paths configured in Lambda function

### Layers
- Custom OpenCV layer for computer vision operations
- Pre-compiled dependencies for faster cold starts

## Cost Considerations

### Lambda Pricing
- **Free Tier**: 1 million requests/month
- **Compute**: $0.0000166667 per GB-second
- **Storage**: S3 costs for models and uploads

### Estimated Monthly Costs
- **Light Usage**: ~$10-20/month
- **Heavy Usage**: ~$50-100/month

## Optimization Tips

1. **Cold Start Reduction**:
   - Use provisioned concurrency for consistent performance
   - Keep Lambda functions warm with scheduled events

2. **Model Optimization**:
   - Use smaller YOLO models (yolov8n) for Lambda
   - Consider model quantization for faster inference

3. **Storage Optimization**:
   - Use S3 lifecycle policies for old uploads
   - Enable S3 compression for model files

## Monitoring and Debugging

### CloudWatch Metrics
- Lambda invocation count
- Duration and error rates
- Memory usage

### Common Issues
1. **Memory Limit Exceeded**: Increase memory allocation
2. **Timeout**: Increase timeout or optimize code
3. **Model Loading Time**: Use Lambda layers for faster cold starts

## Security Considerations

1. **IAM Permissions**: Least privilege access
2. **S3 Security**: Private buckets with signed URLs
3. **API Security**: Enable API throttling and authorization
4. **CORS**: Configure properly for frontend access

## Scaling

### Auto-scaling
Lambda automatically scales based on demand
- Concurrent executions: Up to 1000 (default)
- Burst capacity: 3000 concurrent executions

### Performance Scaling
- Use provisioned concurrency for consistent performance
- Implement queue processing for batch operations
- Consider Step Functions for complex workflows

## Frontend Integration

Update your Netlify environment variables:
```
VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.region.amazonaws.com/Prod
```

## Testing

### Local Testing
```bash
# Test Lambda locally
sam local invoke SentinelViewFunction -e events/test-event.json

# Test API locally
sam local start-api
```

### Integration Testing
1. Upload test images/videos
2. Verify Lambda processes correctly
3. Check CloudWatch logs for errors
4. Test frontend-backend integration

## Troubleshooting

### Common Lambda Issues
- **Module Import Errors**: Check requirements.txt and layers
- **Permission Denied**: Verify IAM roles and S3 permissions
- **Timeout**: Increase timeout or optimize processing

### Debugging Steps
1. Check CloudWatch logs
2. Test with smaller files
3. Verify S3 bucket permissions
4. Monitor Lambda metrics in AWS Console
