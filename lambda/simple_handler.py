import json
import os
import boto3

# Simple test handler
def lambda_handler(event, context):
    """
    Simple Lambda handler for testing API Gateway
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        print(f"Method: {http_method}, Path: {path}")
        print(f"Full event: {json.dumps(event)}")
        
        # Handle CORS
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
        }
        
        # Handle OPTIONS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route handling
        if path == '/prod/' or path == '/':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "status": "healthy",
                    "message": "Sentinel View Lambda Backend is running",
                    "method": http_method,
                    "path": path
                })
            }
        
        elif path == '/prod/proxy/health':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "status": "healthy",
                    "processing": False,
                    "path": path
                })
            }
        
        elif path == '/prod/proxy/stats':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "peopleCount": 0,
                    "instantCount": 0,
                    "uniqueCount": 0,
                    "harmfulObjectCount": 0,
                    "harmfulObjectLabels": [],
                    "threshold": 50,
                    "riskLevel": "safe",
                    "counting": False,
                    "mediaType": None,
                    "processingSeconds": 0,
                    "timestamp": "00:00:00"
                })
            }
        
        else:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Endpoint working",
                    "method": http_method,
                    "path": path,
                    "available_endpoints": [
                        "/prod/",
                        "/prod/proxy/health",
                        "/prod/proxy/stats"
                    ]
                })
            }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            },
            'body': json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }
