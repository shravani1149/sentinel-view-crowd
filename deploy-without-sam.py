#!/usr/bin/env python3
"""
Deploy Lambda function without SAM CLI using AWS CLI
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

def create_lambda_role(iam_client, role_name):
    """Create IAM role for Lambda function"""
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            })
        )
        
        # Attach policies
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
        )
        
        return response['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            # Get existing role ARN
            response = iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        raise

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

def create_lambda_function(lambda_client, function_name, role_arn, s3_bucket):
    """Create Lambda function"""
    try:
        # Upload deployment package to S3
        s3_client = boto3.client('s3')
        s3_client.upload_file('deployment.zip', s3_bucket, 'deployment.zip')
        
        # Create Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
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
            raise

def create_api_gateway(apigateway_client, lambda_arn):
    """Create API Gateway"""
    try:
        # Create REST API
        api = apigateway_client.create_rest_api(
            name='SentinelViewAPI',
            description='API for Sentinel View computer vision application'
        )
        api_id = api['id']
        
        # Get root resource
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_resource_id = None
        for resource in resources['items']:
            if resource['path'] == '/':
                root_resource_id = resource['id']
                break
        
        # Create proxy resource
        proxy_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='{proxy+}'
        )
        
        # Add ANY method
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=proxy_resource['id'],
            httpMethod='ANY',
            authorizationType='NONE'
        )
        
        # Add OPTIONS method for CORS
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=proxy_resource['id'],
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Set up Lambda integration
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource['id'],
            httpMethod='ANY',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{boto3.session.Session().region_name}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        
        # Deploy API
        deployment = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='Prod'
        )
        
        api_url = f"https://{api_id}.execute-api.{boto3.session.Session().region_name}.amazonaws.com/Prod"
        print(f"✅ API Gateway created: {api_url}")
        
        return api_url
        
    except Exception as e:
        print(f"❌ Error creating API Gateway: {e}")
        return None

def main():
    """Main deployment function"""
    stack_name = "sentinel-view-backend"
    function_name = "SentinelViewFunction"
    role_name = "SentinelViewLambdaRole"
    
    print("🚀 Starting deployment without SAM CLI...")
    
    # Initialize AWS clients
    iam_client = boto3.client('iam')
    lambda_client = boto3.client('lambda')
    s3_client = boto3.client('s3')
    apigateway_client = boto3.client('apigateway')
    
    try:
        # Create deployment package
        create_deployment_package()
        
        # Create IAM role
        print("🔐 Creating IAM role...")
        role_arn = create_lambda_role(iam_client, role_name)
        print(f"✅ Role ARN: {role_arn}")
        
        # Create S3 buckets
        print("📁 Creating S3 buckets...")
        upload_bucket, models_bucket = create_s3_buckets(s3_client, stack_name)
        
        # Create Lambda function
        print("⚡ Creating Lambda function...")
        lambda_arn = create_lambda_function(lambda_client, function_name, role_arn, upload_bucket)
        
        # Create API Gateway
        print("🌐 Creating API Gateway...")
        api_url = create_api_gateway(apigateway_client, lambda_arn)
        
        if api_url:
            print("\n🎉 Deployment completed successfully!")
            print(f"📍 API URL: {api_url}")
            print(f"📁 Upload Bucket: {upload_bucket}")
            print(f"🤖 Models Bucket: {models_bucket}")
            print(f"\n📋 Next steps:")
            print(f"1. Upload models to: {models_bucket}")
            print(f"2. Update frontend with: {api_url}")
            print(f"3. Test endpoints at: {api_url}/health")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
