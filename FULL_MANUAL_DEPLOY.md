# Complete Manual AWS Deployment Guide

## 🚨 Permission Issues Detected

Your IAM user lacks permissions for:
- `iam:CreateRole`
- `s3:CreateBucket`

## 🔧 Solution: Manual AWS Console Deployment

### Step 1: Create S3 Buckets (Console)
1. **Go to AWS Console → S3**
2. **Click "Create bucket"**
3. **Bucket name**: `sentinel-view-uploads-sentinel-view-backend`
4. **AWS Region**: US East (N. Virginia) us-east-1
5. **Block Public Access settings**: Keep default (Block all public access)
6. **Click "Create bucket"**
7. **Repeat for**: `sentinel-view-models-sentinel-view-backend`

### Step 2: Create IAM Role (Console)
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

### Step 3: Create Lambda Function (Console)
1. **Go to AWS Console → Lambda**
2. **Click "Create function"**
3. **Author from scratch**
4. **Function name**: `SentinelViewFunction`
5. **Runtime**: Python 3.9
6. **Architecture**: x86_64
7. **Permissions**: "Use an existing role"
   - Select `lambda-execution-role`
8. **Click Create function**

### Step 4: Upload Lambda Code
1. **Create deployment package locally**:
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

### Step 5: Upload Models to S3 (Console)
1. **Go to AWS Console → S3**
2. **Open `sentinel-view-models-sentinel-view-backend` bucket**
3. **Click "Upload"**
4. **Select files**:
   - `backend/yolov8n.pt`
   - `backend/yolov8s.pt`
5. **Upload both files**

### Step 6: Create API Gateway (Console)
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

### Step 7: Test Deployment
1. **Test Lambda**:
   - In Lambda console, click "Test"
   - Event template: "hello-world"
   - Click "Test"

2. **Test API Gateway**:
   - Get API URL from API Gateway → Stages → Prod
   - Test: `curl https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod/health`

### Step 8: Update Frontend
Update `.env.production`:
```
VITE_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod
```

## 🎯 What You'll Get
- ✅ Lambda function with computer vision
- ✅ S3 buckets for storage
- ✅ API Gateway with all endpoints
- ✅ Ready for Netlify frontend

## 📋 Important URLs to Save
- **API Gateway URL**: From API Gateway → Stages → Prod
- **Lambda Function**: From Lambda console
- **S3 Buckets**: From S3 console

## 🚨 If You Still Have Permission Issues
Ask your AWS administrator to add these policies to your user:
- `IAMFullAccess` (temporary, for role creation)
- `AmazonS3FullAccess` (for bucket creation)
- `AWSLambdaFullAccess` (for Lambda management)
- `AmazonAPIGatewayAdministrator` (for API Gateway)

## 🎉 After Deployment
1. Deploy frontend to Netlify
2. Update environment variables
3. Test full application
4. Monitor with CloudWatch
