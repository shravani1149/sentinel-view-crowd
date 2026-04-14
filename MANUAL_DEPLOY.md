# Manual AWS Deployment Guide

## 🔧 Step 1: Create IAM Role Manually

Since your user doesn't have permission to create roles, create it manually:

1. **Go to AWS Console → IAM → Roles**
2. **Click "Create role"**
3. **Trusted entity**: "AWS service"
4. **Use case**: "Lambda"
5. **Click Next**
6. **Add permissions**:
   - ✅ AWSLambdaBasicExecutionRole
   - ✅ AmazonS3FullAccess
   - ✅ AWSLambdaVPCAccessExecutionRole
7. **Role name**: `lambda-execution-role`
8. **Create role**

## 📦 Step 2: Create S3 Buckets

```bash
aws s3 mb s3://sentinel-view-uploads-sentinel-view-backend
aws s3 mb s3://sentinel-view-models-sentinel-view-backend
```

## ⚡ Step 3: Create Lambda Function

1. **Go to AWS Console → Lambda**
2. **Click "Create function"**
3. **Author from scratch**
4. **Function name**: `SentinelViewFunction`
5. **Runtime**: Python 3.9
6. **Architecture**: x86_64
7. **Permissions**: "Use an existing role"
   - Select `lambda-execution-role`
8. **Click Create function**

## 📁 Step 4: Upload Lambda Code

1. **Create deployment package**:
```bash
cd lambda
zip -r ../deployment.zip .
cd ..
```

2. **Upload to Lambda**:
   - In Lambda console, click "Upload from" → ".zip file"
   - Select `deployment.zip`
   - Handler: `app.handler`
   - Memory: 2048 MB
   - Timeout: 300 seconds

3. **Set Environment Variables**:
   - Key: `S3_BUCKET_NAME`, Value: `sentinel-view-uploads-sentinel-view-backend`
   - Key: `MODELS_BUCKET_NAME`, Value: `sentinel-view-models-sentinel-view-backend`

## 🌐 Step 5: Create API Gateway

1. **Go to AWS Console → API Gateway**
2. **Click "Create API" → "REST API"**
3. **API name**: `SentinelViewAPI`
4. **Create API**

5. **Create Resources**:
   - Select root resource `/`
   - Click "Actions" → "Create Resource"
   - Resource name: `{proxy+}`
   - Resource path: `{proxy+}`
   - Check "Configure as proxy resource"
   - Create resource

6. **Add Methods**:
   - Select `{proxy+}` resource
   - Click "Actions" → "Create Method"
   - Method type: `ANY`
   - Integration type: "Lambda Function"
   - Check "Use Lambda Proxy integration"
   - Lambda function: `SentinelViewFunction`
   - Save and grant permissions

7. **Deploy API**:
   - Click "Actions" → "Deploy API"
   - Deployment stage: `Prod`
   - Deployment description: `Initial deployment`

## 🤖 Step 6: Upload Models

```bash
aws s3 cp backend/yolov8n.pt s3://sentinel-view-models-sentinel-view-backend/yolov8n.pt
aws s3 cp backend/yolov8s.pt s3://sentinel-view-models-sentinel-view-backend/yolov8s.pt
```

## 🧪 Step 7: Test Deployment

1. **Test Lambda**:
   - In Lambda console, click "Test"
   - Event template: "hello-world"
   - Click "Test"

2. **Test API Gateway**:
   - Get API URL from API Gateway console
   - Test: `curl https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod/health`

## 🎯 Step 8: Update Frontend

Update `.env.production`:
```
VITE_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod
```

## 📋 What You'll Get

After manual deployment:
- ✅ Lambda function with computer vision
- ✅ S3 buckets for storage
- ✅ API Gateway with all endpoints
- ✅ Ready for Netlify frontend

## 🚨 Important Notes

- **API Gateway URL**: Find it in API Gateway → Stages → Prod
- **Lambda ARN**: Find it in Lambda console
- **S3 Buckets**: Check in S3 console
- **IAM Role**: Verify permissions in IAM console

## 🔍 Troubleshooting

If something fails:
1. Check CloudWatch logs for Lambda errors
2. Verify IAM role permissions
3. Check API Gateway deployment stage
4. Test Lambda function directly first
