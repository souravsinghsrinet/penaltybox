# 🚀 Deployment Guide - Render.com

## Overview
This guide will help you deploy the PenaltyBox application to Render.com with zero cost.

## What You'll Deploy
1. **Backend API** (FastAPI + PostgreSQL) - Docker container
2. **Frontend** (React SPA) - Static site via Docker + Nginx
3. **Database** (PostgreSQL) - Managed database

---

## Prerequisites

✅ GitHub account  
✅ Render.com account (free - no credit card required)  
✅ Code pushed to GitHub repository  

---

## Step 1: Prepare Your Code

### 1.1 Update Frontend Environment Variable

Edit `/penaltybox_ui/.env.production`:
```bash
VITE_API_BASE_URL=https://penaltybox-backend.onrender.com
```
*Note: Replace `penaltybox-backend` with your actual backend service name*

### 1.2 Commit and Push to GitHub

```bash
# From penaltybox directory
cd /path/to/penaltybox
git add .
git commit -m "Prepare for Render deployment"
git push origin main

# From penaltybox_ui directory
cd /path/to/penaltybox_ui
git add .
git commit -m "Add Docker configuration for deployment"
git push origin main
```

---

## Step 2: Deploy Backend to Render

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started" and sign up with GitHub
3. Authorize Render to access your repositories

### 2.2 Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `penaltybox-db`
   - **Database**: `penaltybox`
   - **User**: `postgres`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Free
3. Click "Create Database"
4. **Save the connection details** (Internal Database URL)

### 2.3 Deploy Backend Service
1. Click "New +" → "Web Service"
2. Connect your `penaltybox` repository
3. Configure:
   - **Name**: `penaltybox-backend`
   - **Environment**: Docker
   - **Region**: Oregon (same as database)
   - **Branch**: main
   - **Plan**: Free

4. Add Environment Variables:
   ```
   DATABASE_URL = [Paste Internal Database URL from step 2.2]
   SECRET_KEY = [Generate random string: e.g., your-super-secret-key-12345]
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ALLOWED_ORIGINS = https://penaltybox-frontend.onrender.com
   ```
   *Note: Replace `penaltybox-frontend` with your actual frontend service name*

5. Click "Create Web Service"
6. Wait for deployment to complete (~5-10 minutes)
7. **Save your backend URL**: `https://penaltybox-backend.onrender.com`

### 2.4 Run Database Migrations
Once backend is deployed:
1. Go to your backend service dashboard
2. Click "Shell" tab
3. Run migration:
   ```bash
   alembic upgrade head
   ```

### 2.5 Create Admin User
In the Shell, create your first admin user:
```bash
curl -X POST "https://penaltybox-backend.onrender.com/auth/register-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Name",
    "email": "admin@example.com",
    "password": "your-secure-password"
  }'
```

---

## Step 3: Deploy Frontend to Render

### 3.1 Update Environment Variable
Before deploying, update `.env.production` with your actual backend URL:
```bash
VITE_API_BASE_URL=https://penaltybox-backend.onrender.com
```

Commit and push:
```bash
cd /path/to/penaltybox_ui
git add .env.production
git commit -m "Update backend URL for production"
git push origin main
```

### 3.2 Deploy Frontend Service
1. Click "New +" → "Web Service"
2. Connect your `penaltybox_ui` repository
3. Configure:
   - **Name**: `penaltybox-frontend`
   - **Environment**: Docker
   - **Region**: Oregon (same as backend)
   - **Branch**: main
   - **Plan**: Free

4. Add Environment Variables:
   ```
   VITE_API_BASE_URL = https://penaltybox-backend.onrender.com
   ```
   *Replace with your actual backend URL from Step 2.3*

5. Click "Create Web Service"
6. Wait for deployment (~5-10 minutes)
7. **Your app is live!** 🎉

---

## Step 4: Update Backend CORS

Now that you have the frontend URL, update backend CORS:

1. Go to backend service → "Environment"
2. Update `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS = https://penaltybox-frontend.onrender.com,http://localhost:5173
   ```
   *This allows both production and local development*

3. Save and redeploy

---

## Step 5: Test Your Deployment

1. Open your frontend URL: `https://penaltybox-frontend.onrender.com`
2. Test registration (create a regular user)
3. Test login
4. Test dashboard access
5. Verify admin features (if logged in as admin)

---

## 🎯 Your Live URLs

After deployment, you'll have:

- **Frontend**: `https://penaltybox-frontend.onrender.com`
- **Backend API**: `https://penaltybox-backend.onrender.com`
- **API Docs**: `https://penaltybox-backend.onrender.com/docs`
- **Database**: Internal Render PostgreSQL

---

## ⚡ Important Notes

### Free Tier Limitations
- **Cold Starts**: Services spin down after 15 minutes of inactivity
- **First Request**: May take 30-50 seconds to wake up
- **Database**: 90 days data retention on free tier
- **Bandwidth**: 100GB/month

### Keeping Services Awake (Optional)
To reduce cold starts, you can:
1. Use UptimeRobot (free) to ping your backend every 14 minutes
2. Upgrade to paid plan ($7/month per service)

### Custom Domain (Optional)
1. Buy a domain (Namecheap, Google Domains)
2. In Render → Settings → Add custom domain
3. Update DNS records as instructed
4. Free HTTPS certificate automatically provisioned

---

## 🔧 Troubleshooting

### Frontend can't connect to backend
- Check CORS settings in backend
- Verify `VITE_API_BASE_URL` in frontend environment variables
- Check backend logs for errors

### Database connection failed
- Verify `DATABASE_URL` in backend environment variables
- Check if database is running (Render dashboard)
- Run migrations: `alembic upgrade head`

### Build failed
- Check Render build logs
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt / package.json

### 500 Internal Server Error
- Check backend logs in Render dashboard
- Verify environment variables are set correctly
- Check database connection

---

## 📱 Accessing Your App

### From Anywhere
Just visit: `https://penaltybox-frontend.onrender.com`

### Share with Others
Share the URL with friends to test your app!

---

## 🔄 Continuous Deployment

Render automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Add new feature"
git push origin main

# Render automatically detects the push and redeploys! 🚀
```

---

## 💡 Tips

1. **Monitor Usage**: Check Render dashboard for service health
2. **View Logs**: Click on service → "Logs" to debug issues
3. **Environment Variables**: Can be updated without redeploying
4. **Restart Services**: Use "Manual Deploy" → "Clear build cache & deploy"
5. **Database Backup**: Render doesn't auto-backup free tier - export manually

---

## 📊 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Backend | Free | $0/month |
| Frontend | Free | $0/month |
| Database | Free | $0/month |
| **Total** | | **$0/month** |

---

## 🎉 You're Done!

Your PenaltyBox app is now live and accessible from anywhere in the world!

**Next Steps:**
- Share with friends for feedback
- Add more features (Tasks 3-15)
- Monitor performance
- Consider upgrading for production use

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Your Project**: Check GitHub issues or README

---

**Deployment Date**: _____________  
**Frontend URL**: _____________  
**Backend URL**: _____________  
**Admin Email**: _____________
