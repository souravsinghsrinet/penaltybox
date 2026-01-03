# 🚀 Quick Deployment Checklist

## Before You Start
- [ ] Code is working locally
- [ ] Both repos pushed to GitHub
- [ ] Render.com account created

## Backend Deployment
- [ ] Create PostgreSQL database on Render
- [ ] Copy Internal Database URL
- [ ] Create backend web service (Docker)
- [ ] Add environment variables:
  - [ ] DATABASE_URL
  - [ ] SECRET_KEY  
  - [ ] ALGORITHM=HS256
  - [ ] ACCESS_TOKEN_EXPIRE_MINUTES=30
  - [ ] ALLOWED_ORIGINS
- [ ] Wait for deployment
- [ ] Run migration: `alembic upgrade head`
- [ ] Create admin user via Shell/curl
- [ ] Save backend URL

## Frontend Deployment
- [ ] Update `.env.production` with backend URL
- [ ] Commit and push to GitHub
- [ ] Create frontend web service (Docker)
- [ ] Add environment variable:
  - [ ] VITE_API_BASE_URL=(backend URL)
- [ ] Wait for deployment
- [ ] Save frontend URL

## Post-Deployment
- [ ] Update backend ALLOWED_ORIGINS with frontend URL
- [ ] Test registration
- [ ] Test login
- [ ] Test admin features
- [ ] Share with friends! 🎉

## Your URLs
**Frontend**: ___________________________________  
**Backend**: ___________________________________  
**Admin Email**: ___________________________________  
**Admin Password**: ___________________________________ (Keep secret!)

## Quick Commands

### Create Admin User
```bash
curl -X POST "https://YOUR-BACKEND.onrender.com/auth/register-admin" \
  -H "Content-Type: application/json" \
  -d '{"name":"Admin","email":"admin@example.com","password":"secure123"}'
```

### Run Migration
```bash
# In Render Shell
alembic upgrade head
```

### View Logs
Render Dashboard → Your Service → Logs tab

---

**Estimated Time**: 30-45 minutes  
**Cost**: $0/month  
**Difficulty**: Easy 😊
