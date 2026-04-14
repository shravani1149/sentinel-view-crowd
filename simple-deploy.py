#!/usr/bin/env python3
"""
Simplified deployment using existing AWS managed roles
"""
import boto3
import zipfile
import os
import json
from botocore.exceptions import ClientError

def create_deployment_package():
    """Create zip package for Lambda deployment"""
    print("📦 Creating deployment package...")
    
    # Create zip file
    with zipfile.ZipFile('deployment.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add Lambda function
        zipf.write('lambda/app.py', 'app.py')
        
        # Add dependencies
        for root, dirs, files in os.walk('lambda'):
            for file in files:
                if file.endswith('.py') or file in ['requirements.txt']:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'lambda')
                    zipf.write(file_path, arcname)
    
    print("✅ Deployment package created: deployment.zip")

def create_s3_buckets(s3_client, stack_name):
    """Create S3 buckets for uploads and models"""
    region = boto3.session.Session().region_name or 'us-east-1'
    
    # Upload bucket
    upload_bucket = f"sentinel-view-uploads-{stack_name}"
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=upload_bucket)
        else:
            s3_client.create_bucket(
                Bucket=upload_bucket,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Created upload bucket: {upload_bucket}")
    except ClientError as e:
        if e.response['Error']['Code'] != 'BucketAlreadyExists':
            print(f"⚠️  Upload bucket may already exist: {upload_bucket}")
    
    # Models bucket
    models_bucket = f"sentinel-view-models-{stack_name}"
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=models_bucket)
        else:
            s3_client.create_bucket(
                Bucket=models_bucket,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Created models bucket: {models_bucket}")
    except ClientError as e:
        if e.response['Error']['Code'] != 'BucketAlreadyExists':
            print(f"⚠️  Models bucket may already exist: {models_bucket}")
    
    return upload_bucket, models_bucket

def create_lambda_function(lambda_client, function_name, s3_bucket):
    """Create Lambda function using existing role"""
    try:
        # Upload deployment package to S3
        s3_client = boto3.client('s3')
        s3_client.upload_file('deployment.zip', s3_bucket, 'deployment.zip')
        
        # Use existing AWS managed role (simpler approach)
        role_arn = 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        
        # Create Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::532048998055:role/lambda-execution-role',  # You may need to create this manually
            Handler='app.handler',
            Code={
                'S3Bucket': s3_bucket,
                'S3Key': 'deployment.zip'
            },
            Timeout=300,
            MemorySize=2048,
            Environment={
                'Variables': {
                    'S3_BUCKET_NAME': f"sentinel-view-uploads-{stack_name}",
                    'MODELS_BUCKET_NAME': f"sentinel-view-models-{stack_name}"
                }
            }
        )
        
        print(f"✅ Lambda function created: {function_name}")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"⚠️  Lambda function already exists: {function_name}")
            # Update existing function
            lambda_client.update_function_code(
                FunctionName=function_name,
                S3Bucket=s3_bucket,
                S3Key='deployment.zip'
            )
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=300,
                MemorySize=2048,
                Environment={
                    'Variables': {
                        'S3_BUCKET_NAME': f"sentinel-view-uploads-{stack_name}",
                        'MODELS_BUCKET_NAME': f"sentinel-view-models-{stack_name}"
                    }
                }
            )
            print(f"✅ Lambda function updated: {function_name}")
        else:
            print(f"❌ Error creating Lambda: {e}")
            return None

def main():
    """Main deployment function"""
    stack_name = "sentinel-view-backend"
    function_name = "SentinelViewFunction"
    
    print("🚀 Starting simplified deployment...")
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda')
    s3_client = boto3.client('s3')
    
    try:
        # Create deployment package
        create_deployment_package()
        
        # Create S3 buckets
        print("📁 Creating S3 buckets...")
        upload_bucket, models_bucket = create_s3_buckets(s3_client, stack_name)
        
        # Create Lambda function
        print("⚡ Creating Lambda function...")
        lambda_arn = create_lambda_function(lambda_client, function_name, upload_bucket)
        
        if lambda_arn:
            print("\n🎉 Lambda deployment completed!")
            print(f"📁 Upload Bucket: {upload_bucket}")
            print(f"🤖 Models Bucket: {models_bucket}")
            print(f"⚡ Lambda Function: {function_name}")
            print(f"\n📋 Next steps:")
            print(f"1. Upload models to: {models_bucket}")
            print(f"2. Create API Gateway manually in AWS Console")
            print(f"3. Test Lambda function in AWS Console")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
