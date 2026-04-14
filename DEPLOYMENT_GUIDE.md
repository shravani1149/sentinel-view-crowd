# Deployment Guide for Sentinel View

## Overview
This project consists of a React frontend and Flask backend with computer vision capabilities. Since Netlify only hosts static sites, we need to deploy them separately.

## Deployment Options

### Option 1: Separate Hosting (Recommended)
- **Frontend**: Netlify
- **Backend**: Railway, Render, or Vercel Serverless

### Option 2: Netlify Functions (Limited)
Convert Flask to Netlify serverless functions (not recommended for ML workloads)

---

## Frontend Deployment (Netlify)

### 1. Build the Frontend
```bash
npm run build
```

### 2. Deploy to Netlify
1. Push your code to GitHub
2. Connect your repository to Netlify
3. Set build settings:
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`

### 3. Environment Variables
Set this in Netlify dashboard:
```
VITE_API_BASE_URL=https://your-backend-url.com
```

---

## Backend Deployment Options

### Option A: AWS Lambda + Amplify (Recommended for Production)
Perfect for serverless deployment with auto-scaling and pay-per-use pricing.

#### Prerequisites:
- AWS Account
- AWS CLI installed and configured
- AWS SAM CLI installed
- Amplify CLI installed

#### Deployment Steps:

1. **Install Dependencies**:
```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Install Amplify CLI
npm install -g @aws-amplify/cli
```

2. **Deploy Lambda Functions**:
```bash
# Make deployment script executable
chmod +x scripts/deploy-lambda.sh

# Run deployment
./scripts/deploy-lambda.sh
```

3. **Manual AWS Console Steps**:
   - Create S3 bucket for ML models
   - Upload `yolov8n.pt` and `yolov8s.pt` to the models bucket
   - Deploy CloudFormation stack using `template.yaml`
   - Note the API Gateway URL from outputs

4. **Configure Amplify**:
```bash
amplify init
amplify add api
amplify add storage
amplify push
```

#### Lambda Function Details:
- **Memory**: 2048MB (for ML processing)
- **Timeout**: 300 seconds (5 minutes)
- **Runtime**: Python 3.9
- **Storage**: S3 for file uploads and models
- **Layer**: Custom OpenCV layer for computer vision

### Option B: Railway (Alternative)
1. Create `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python backend/app.py",
    "healthcheckPath": "/health"
  }
}
```

2. Deploy:
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Option C: Render (Alternative)
1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: sentinel-view-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python backend/app.py
    healthCheckPath: "/health"
```

---

## Required Backend Files for Deployment

### 1. requirements.txt (already exists)
```
flask
flask-cors
ultralytics
opencv-python
numpy
deep-sort-realtime
```

### 2. Procfile (for Railway/Render)
```
web: python backend/app.py
```

### 3. runtime.txt (optional)
```
python-3.9.0
```

---

## CORS Configuration
Your Flask backend already has CORS configured. Make sure it allows your Netlify domain:

```python
CORS(app, origins=["https://your-netlify-site.netlify.app"])
```

---

## Post-Deployment Steps

1. **Update Environment Variables**:
   - Set `VITE_API_BASE_URL` in Netlify to your backend URL
   - Update CORS origins in Flask if needed

2. **Test the Integration**:
   - Upload a test image/video
   - Verify API calls work correctly

3. **Monitor Performance**:
   - Check backend logs for processing errors
   - Monitor frontend console for API errors

---

## Troubleshooting

### Common Issues:
1. **CORS Errors**: Update Flask CORS configuration
2. **API Timeouts**: Increase timeout limits for large video processing
3. **Memory Issues**: Consider using smaller YOLO models for serverless deployment

### Environment Variables:
- Frontend: `VITE_API_BASE_URL`
- Backend: May need additional env vars for production

---

## Cost Considerations

- **Netlify**: Free tier available
- **Railway**: $5-20/month depending on usage
- **Render**: Free tier available, then $7/month
- **ML Processing**: Consider GPU costs for heavy workloads
