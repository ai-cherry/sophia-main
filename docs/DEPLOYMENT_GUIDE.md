# Sophia AI Deployment Guide

## 🚀 Overview

This guide covers deploying Sophia AI's backend infrastructure to Lambda Labs and frontend to Vercel.

## 📋 Prerequisites

### Required Secrets in GitHub (Organization Level)
- ✅ All API keys (already set at org level)
- ❓ `VERCEL_TOKEN` - Need to add for frontend deployment
- ❓ `LAMBDA_LABS_API_KEY` - Verify if set

### Current Status
- **Pull Request**: [#6](https://github.com/ai-cherry/sophia-main/pull/6) created
- **Branch**: `feat/enhanced-infrastructure`
- **GitHub Actions**: Configured and ready

## 🔧 Deployment Steps

### Option 1: Automatic Deployment (Recommended)

1. **Add Vercel Token to GitHub Secrets**
   ```bash
   # Get your Vercel token from: https://vercel.com/account/tokens
   # Add to GitHub org secrets as VERCEL_TOKEN
   ```

2. **Merge the Pull Request**
   - Review PR #6: https://github.com/ai-cherry/sophia-main/pull/6
   - Approve and merge to main
   - GitHub Actions will automatically:
     - Run tests
     - Build Docker images
     - Deploy backend to Lambda Labs
     - Deploy frontend to Vercel

### Option 2: Manual Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   # From project root
   vercel --prod
   
   # Follow prompts:
   # - Set up and deploy: Y
   # - Which scope: Select your account
   # - Link to existing project: N (first time) or Y
   # - Project name: sophia-ai-frontend
   # - In which directory: ./frontend
   # - Override settings: N
   ```

3. **Set Environment Variables in Vercel**
   ```bash
   # Set the API URL for production
   vercel env add VITE_API_URL production
   # Enter: https://api.sophiaai.payready.com (or your backend URL)
   ```

### Option 3: Deploy Backend Manually

1. **Build Docker Image**
   ```bash
   docker build -t sophia-payready:latest .
   ```

2. **Push to Registry**
   ```bash
   docker tag sophia-payready:latest ghcr.io/ai-cherry/sophia-main:latest
   docker push ghcr.io/ai-cherry/sophia-main:latest
   ```

3. **Deploy to Lambda Labs**
   ```bash
   # Use Lambda Labs API or dashboard
   # Image: ghcr.io/ai-cherry/sophia-main:latest
   # Ports: 5001 (backend), 80 (nginx)
   ```

## 🌐 Post-Deployment Configuration

### 1. **Update DNS Records**
- Point `sophiaai.payready.com` to Lambda Labs IP
- Point `app.sophiaai.payready.com` to Vercel deployment

### 2. **Configure SSL**
- Lambda Labs: Use Let's Encrypt via nginx
- Vercel: Automatic SSL

### 3. **Update Frontend API URL**
- In Vercel dashboard, update `VITE_API_URL` to production backend URL

### 4. **Test Deployment**
```bash
# Test backend
curl https://api.sophiaai.payready.com/health

# Test frontend
open https://app.sophiaai.payready.com
```

## 📊 Monitoring

### Backend Monitoring
- Grafana: `https://api.sophiaai.payready.com:3001`
- Prometheus: `https://api.sophiaai.payready.com:9090`

### Frontend Monitoring
- Vercel Analytics (automatic)
- Browser console for errors

## 🔒 Security Checklist

- [ ] All secrets in GitHub organization secrets
- [ ] SSL certificates configured
- [ ] Firewall rules set (Lambda Labs)
- [ ] Environment variables not exposed
- [ ] API authentication enabled

## 🛠️ Troubleshooting

### Frontend Issues
```bash
# Check build logs
vercel logs

# Redeploy
vercel --prod --force
```

### Backend Issues
```bash
# Check Docker logs
docker logs sophia-payready

# Check health endpoint
curl http://localhost:5001/health
```

### Common Issues
1. **CORS errors**: Update backend CORS settings
2. **API connection failed**: Check VITE_API_URL
3. **Build failures**: Check npm/pnpm lockfiles

## 📱 Mobile Access

The frontend is fully responsive and works on:
- iOS Safari
- Android Chrome
- Tablet browsers

## 🎉 Success Indicators

- ✅ Backend health check returns 200
- ✅ Frontend loads without errors
- ✅ API calls successful
- ✅ Metrics visible in dashboard
- ✅ WebSocket connections working

## 📞 Support

For deployment issues:
1. Check GitHub Actions logs
2. Review Vercel deployment logs
3. Verify all environment variables
4. Check network connectivity

---

**Note**: This deployment will make Sophia AI publicly accessible. Ensure all security measures are in place before proceeding. 