# Cloudflare Workers Deployment Guide

Deploy your Driver Scheduling API to Cloudflare Workers with your custom domain.

## 🚀 Quick Deployment

### Prerequisites
- Cloudflare account with your domain configured
- Node.js and npm installed
- Wrangler CLI (`npm install -g wrangler`)

### 1. Setup Wrangler CLI
```bash
# Install Wrangler globally
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

### 2. Configure Your Domain
Update `deployment/cloudflare/wrangler.toml`:
- Replace placeholder domains with your actual domain
- Example: `api.yourdomain.com`

### 3. Set Environment Secrets
```bash
cd deployment/cloudflare

# Set required secrets
wrangler secret put DATABASE_URL
wrangler secret put SUPABASE_PASSWORD
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
wrangler secret put GCF_URL
```

### 4. Deploy
```bash
# Deploy to staging
wrangler deploy --env staging

# Deploy to production
wrangler deploy --env production
```

### 5. Configure Custom Domain
1. Go to **Cloudflare Dashboard > Workers & Pages**
2. Select your worker: `driver-scheduling-api-prod`
3. Go to **Settings > Triggers > Custom Domains**
4. Add your domain: `api.yourdomain.com`
5. Configure DNS records as instructed

## 🔑 Required Environment Variables

Set these secrets in Cloudflare Workers:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DATABASE_URL` | Supabase PostgreSQL connection | `postgresql://postgres:pass@db.ref.supabase.co:5432/postgres` |
| `SUPABASE_PASSWORD` | Your Supabase database password | `your_secure_password` |
| `SUPABASE_URL` | Your Supabase project URL | `https://ref.supabase.co` |
| `SUPABASE_KEY` | Supabase service role key | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` |
| `GCF_URL` | Google Cloud Function endpoint | `https://us-central1-project.cloudfunctions.net/update_sheet` |

## 🌐 Custom Domain Setup

### DNS Configuration
Add these DNS records in your Cloudflare Dashboard:

```
Type: CNAME
Name: api
Content: driver-scheduling-api-prod.your-subdomain.workers.dev
Proxy: Enabled (Orange Cloud)
```

### SSL/TLS Settings
- SSL/TLS encryption mode: **Full (strict)**
- Edge certificates: **Enabled**
- Always Use HTTPS: **Enabled**

## 📊 API Endpoints

Once deployed, your API will be available at:

- **Production**: `https://api.yourdomain.com`
- **Staging**: `https://staging-api.yourdomain.com`

### Core Endpoints
- `GET /` - Health check and API info
- `GET /docs` - Interactive API documentation
- `POST /api/v1/assistant/optimize-week` - Run optimization
- `GET /api/v1/assistant/fixed-assignments` - View fixed assignments
- `POST /api/v1/assistant/reset` - Reset system to defaults

## 🔧 Management Commands

### View Logs
```bash
wrangler tail --env production
```

### Update Secrets
```bash
wrangler secret put SECRET_NAME --env production
```

### Test Locally
```bash
wrangler dev
```

### Deploy Updates
```bash
wrangler deploy --env production
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify DATABASE_URL is correct
   - Check Supabase project is active
   - Ensure password is properly set

2. **Custom Domain Not Working**
   - Check DNS propagation (24-48 hours)
   - Verify CNAME record is correct
   - Ensure SSL certificate is active

3. **API Timeout Errors**
   - Cloudflare Workers have 30-second timeout limit
   - OR-Tools optimization may need chunking for large datasets

4. **CORS Issues**
   - Update allowed origins in `deployment/cloudflare/worker.py`
   - Add your domain to the CORS middleware

### Performance Optimization

- **Cold Starts**: Use Cloudflare Workers' always-on feature
- **Database Pooling**: Configured automatically with asyncpg
- **Caching**: Add Cloudflare Cache API for route data
- **Rate Limiting**: Configure in Cloudflare Dashboard

## 📈 Monitoring

### Analytics
- View traffic in Cloudflare Dashboard > Analytics
- Monitor response times and error rates
- Set up alerts for high error rates

### Health Checks
- Endpoint: `GET /health`
- Automated monitoring via Cloudflare Health Checks
- Uptime monitoring with third-party services

## 🔒 Security

### Production Security
- All secrets are encrypted in Cloudflare Workers
- HTTPS enforced with HSTS headers
- CORS configured for your domain only
- Rate limiting available in Cloudflare Dashboard

### API Security
- Service role authentication for Supabase
- Input validation with Pydantic models
- SQL injection protection with parameterized queries

## 💰 Cost Estimation

### Cloudflare Workers Pricing
- **Free Tier**: 100,000 requests/day
- **Paid Plan**: $5/month for 10M requests
- **Custom Domain**: Free with paid plan

### Expected Usage
- Driver optimization: ~1-5 requests/day
- Status checks: ~100 requests/day
- Well within free tier limits

---

**🎉 Your Driver Scheduling API is now ready for production deployment on Cloudflare Workers with your custom domain!**