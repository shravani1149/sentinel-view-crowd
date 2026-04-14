import json
import os
import boto3

# Simple state for testing
processing_state = {
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
}

def lambda_handler(event, context):
    """
    Lambda handler for HTTP API Gateway (simpler than REST API)
    """
    try:
        # HTTP API Gateway has different event structure
        route_key = event.get('routeKey', '')
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        
        print(f"Route: {route_key}, Method: {http_method}")
        print(f"Event: {json.dumps(event)}")
        
        # CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
        }
        
        # Route handling for HTTP API Gateway
        if route_key == 'GET /health' or route_key == 'GET /':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "status": "healthy",
                    "processing": processing_state.get("counting", False),
                    "route": route_key
                })
            }
        
        elif route_key == 'GET /stats':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(processing_state)
            }
        
        elif route_key == 'POST /start':
            processing_state['counting'] = True
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Processing started",
                    "counting": True
                })
            }
        
        elif route_key == 'POST /stop':
            processing_state['counting'] = False
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Processing stopped",
                    "counting": False
                })
            }
        
        elif route_key == 'POST /threshold':
            try:
                body = json.loads(event.get('body', '{}'))
                if 'threshold' in body:
                    processing_state['threshold'] = body['threshold']
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        "message": "Threshold updated",
                        "threshold": processing_state['threshold']
                    })
                }
            except Exception as e:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({"error": str(e)})
                }
        
        elif route_key == 'POST /upload':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Upload endpoint ready",
                    "note": "File upload processing to be implemented"
                })
            }
        
        elif route_key == '$default':
            # Default route for testing
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Default route working",
                    "route": route_key,
                    "method": http_method,
                    "available_routes": [
                        "GET /health",
                        "GET /stats",
                        "POST /start",
                        "POST /stop", 
                        "POST /threshold",
                        "POST /upload"
                    ]
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    "error": "Route not found",
                    "route": route_key
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
