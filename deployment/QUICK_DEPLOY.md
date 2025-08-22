# 🚀 Quick Cloudflare Deployment

Deploy your Driver Scheduling API to Cloudflare Workers with your custom domain in 5 minutes.

## Prerequisites
- Cloudflare account with your domain
- Supabase project with database
- Google Cloud Function for sheets integration

## 1-Minute Setup

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Navigate to deployment folder
cd deployment/cloudflare

# Set your secrets (you'll be prompted for each)
wrangler secret put DATABASE_URL
wrangler secret put SUPABASE_PASSWORD
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
wrangler secret put GCF_URL

# Deploy to production
wrangler deploy --env production
```

## Configure Custom Domain

1. Go to **Cloudflare Dashboard > Workers & Pages**
2. Select `driver-scheduling-api-prod`
3. **Settings > Triggers > Custom Domains**
4. Add your domain: `api.yourdomain.com`
5. Wait 2-5 minutes for SSL certificate

## Test Your API

Visit: `https://api.yourdomain.com/docs`

## Required Environment Values

| Variable | Get From | Example |
|----------|----------|---------|
| `DATABASE_URL` | Supabase > Settings > Database | `postgresql://postgres:pass@db.ref.supabase.co:5432/postgres` |
| `SUPABASE_PASSWORD` | Your Supabase database password | `your_password` |
| `SUPABASE_URL` | Supabase > Settings > API | `https://ref.supabase.co` |
| `SUPABASE_KEY` | Supabase > Settings > API > service_role | `eyJhbGciOiJIUzI1NiIs...` |
| `GCF_URL` | Your Google Cloud Function URL | `https://us-central1-project.cloudfunctions.net/update_sheet` |

## API Endpoints

- `GET /` - Health check
- `GET /docs` - API documentation
- `POST /api/v1/assistant/optimize-week` - Run optimization
- `POST /api/v1/assistant/reset` - Reset system
- `GET /api/v1/assistant/fixed-assignments` - View assignments

## Success Indicators

✅ Deployment success: Worker shows "Deployed" status  
✅ Custom domain: SSL certificate active  
✅ Database: Health check returns "connected"  
✅ API docs: `/docs` loads correctly  
✅ Optimization: Returns assignment results  

**Your Driver Scheduling API is now live on Cloudflare Workers!**