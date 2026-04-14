# Render Deployment Steps

## 🚀 Deploy Backend to Render

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up or login
3. Click "New" → "Web Service"

### Step 2: Connect GitHub Repository
1. Click "Connect GitHub"
2. Authorize Render to access your GitHub
3. Select repository: `shravani1149/sentinel-view-crowd`
4. Click "Connect"

### Step 3: Configure Web Service
1. **Name**: `sentinel-view-backend`
2. **Root Directory**: `backend/` (IMPORTANT!)
3. **Runtime**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `python app.py`
6. **Instance Type**: Free (starter)
7. **Auto-Deploy**: Yes (on push to main)

### Step 4: Environment Variables (Optional)
Add these if needed:
- `FLASK_ENV`: `production`
- `PORT`: `5000`

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait 2-3 minutes for deployment
3. Your backend will be live at: `https://sentinel-view-backend.onrender.com`

### Step 6: Test Backend
Test these endpoints:
- `https://sentinel-view-backend.onrender.com/health`
- `https://sentinel-view-backend.onrender.com/stats`
- `https://sentinel-view-backend.onrender.com/upload`

### Step 7: Update Frontend
Update `.env.production`:
```
VITE_API_BASE_URL=https://sentinel-view-backend.onrender.com
```

### Step 8: Deploy Frontend to Netlify
1. Push to GitHub
2. Connect Netlify to same repository
3. Build and deploy

## 🎯 Final Architecture
```
Netlify Frontend → Render Backend → File Storage
```

## ✅ Benefits of Render
- No AWS complexity
- Free tier available
- Auto-deploys from GitHub
- Simple HTTPS URLs
- Built-in monitoring
