# AWS Setup Instructions

## Step 1: Get AWS Credentials

### Create IAM User:
1. Go to AWS Console → IAM → Users → "Create user"
2. User name: `sentinel-view-deployer`
3. Select "Access key - Programmatic access"
4. Attach policies:
   - AWSLambda_FullAccess
   - AmazonS3FullAccess
   - AWSCloudFormation_FullAccess
   - AmazonAPIGatewayAdministrator
5. Download the CSV file with credentials

## Step 2: Configure AWS CLI

Run this command and enter your credentials:
```bash
aws configure
```

You'll need to enter:
- AWS Access Key ID: [from IAM user]
- AWS Secret Access Key: [from IAM user]
- Default region: us-east-1 (or your preferred region)
- Default output format: json

## Step 3: Verify Configuration

Test the configuration:
```bash
aws sts get-caller-identity
```

## Step 4: Continue Deployment

Once configured, run:
```bash
# Create S3 bucket for models
aws s3 mb s3://sentinel-view-models-$(date +%s)

# Upload models
aws s3 cp backend/yolov8n.pt s3://sentinel-view-models-$(date +%s)/yolov8n.pt
aws s3 cp backend/yolov8s.pt s3://sentinel-view-models-$(date +%s)/yolov8s.pt
```

## Alternative: Use AWS Credentials File

Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Create `~/.aws/config`:
```ini
[default]
region = us-east-1
output = json
```
