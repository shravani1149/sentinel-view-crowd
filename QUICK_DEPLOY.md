# Quick AWS Deployment Guide

## 🔐 Step 1: Configure AWS Credentials

You need AWS credentials to deploy. Choose one option:

### Option A: AWS CLI Configure (Recommended)
```bash
aws configure
```
Enter your credentials:
- AWS Access Key ID: [from AWS IAM user]
- AWS Secret Access Key: [from AWS IAM user]  
- Default region: us-east-1
- Default output format: json

### Option B: Create Credentials File
Create `C:\Users\Shravani\.aws\credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Create `C:\Users\Shravani\.aws\config`:
```ini
[default]
region = us-east-1
output = json
```

## 🚀 Step 2: Deploy Backend

Once credentials are configured, run:
```bash
python deploy-without-sam.py
```

## 📋 Step 3: Upload Models

After deployment, upload YOLO models:
```bash
# Get bucket names from deployment output
aws s3 cp backend/yolov8n.pt s3://sentinel-view-models-sentinel-view-backend/yolov8n.pt
aws s3 cp backend/yolov8s.pt s3://sentinel-view-models-sentinel-view-backend/yolov8s.pt
```

## 🌐 Step 4: Update Frontend

Update `.env.production` with your API URL:
```
VITE_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/Prod
```

## 🧪 Step 5: Test

Test your deployment:
```bash
curl https://your-api-url.execute-api.us-east-1.amazonaws.com/Prod/health
```

## 📞 If You Need AWS Credentials

1. Go to AWS Console → IAM → Users → "Create user"
2. User name: `sentinel-view-deployer`
3. Select "Access key - Programmatic access"
4. Attach policies:
   - AWSLambda_FullAccess
   - AmazonS3FullAccess
   - AWSCloudFormation_FullAccess
   - AmazonAPIGatewayAdministrator
5. Download the CSV file with credentials

## ⚡ Alternative: Manual AWS Console Deployment

If scripts don't work, you can deploy manually:

1. **Create S3 Buckets**:
   - `sentinel-view-uploads-sentinel-view-backend`
   - `sentinel-view-models-sentinel-view-backend`

2. **Create Lambda Function**:
   - Name: `SentinelViewFunction`
   - Runtime: Python 3.9
   - Handler: `app.handler`
   - Memory: 2048 MB
   - Timeout: 300 seconds

3. **Upload Code**:
   - Create zip from `lambda/` folder
   - Upload to Lambda

4. **Create API Gateway**:
   - REST API: `SentinelViewAPI`
   - Proxy resource: `{proxy+}`
   - Methods: ANY, OPTIONS
   - Deploy to `Prod` stage

## 🎯 What You'll Get

After successful deployment:
- ✅ Lambda function with computer vision
- ✅ S3 buckets for storage
- ✅ API Gateway with all endpoints
- ✅ Ready for frontend integration

## 📞 Need Help?

If you get stuck, check:
1. AWS credentials are properly configured
2. IAM permissions are sufficient
3. Region is set to us-east-1
4. No existing resources with same names
