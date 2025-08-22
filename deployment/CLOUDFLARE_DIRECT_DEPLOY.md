# 🚀 Direct Cloudflare Deployment

Deploy your Driver Scheduling API directly to Cloudflare using your domain and keys.

## Quick Deploy (2 minutes)

### Option 1: Cloudflare Dashboard Upload

1. **Go to Cloudflare Dashboard**
   - Navigate to **Workers & Pages**
   - Click **Create Application > Pages > Upload assets**

2. **Upload Your Project**
   - Drag your entire project folder to upload
   - Or zip your project and upload the zip file

3. **Set Environment Variables**
   Go to **Settings > Environment variables** and add:
   ```
   DATABASE_URL = your_supabase_database_url
   SUPABASE_PASSWORD = your_database_password  
   SUPABASE_URL = your_supabase_project_url
   SUPABASE_KEY = your_supabase_service_role_key
   GCF_URL = your_google_cloud_function_url
   ```

4. **Add Your Custom Domain**
   - Go to **Custom Domains**
   - Add: `api.yourdomain.com`
   - Follow DNS instructions

### Option 2: Wrangler CLI (Fastest)

```bash
# Install if needed
npm install -g wrangler

# Login with your Cloudflare account
wrangler login

# Deploy your app
wrangler deploy

# Set your environment secrets
wrangler secret put DATABASE_URL
wrangler secret put SUPABASE_PASSWORD
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
wrangler secret put GCF_URL
```

## Your Environment Values

Get these from your accounts:

| Secret | Where to Find It |
|--------|------------------|
| **DATABASE_URL** | Supabase → Settings → Database → Connection string |
| **SUPABASE_PASSWORD** | Your Supabase database password |
| **SUPABASE_URL** | Supabase → Settings → API → Project URL |
| **SUPABASE_KEY** | Supabase → Settings → API → service_role key |
| **GCF_URL** | Your Google Cloud Function endpoint |

## Custom Domain Setup

1. **In Cloudflare Pages**: Add custom domain `api.yourdomain.com`
2. **DNS Records**: Cloudflare will show you what records to add
3. **SSL Certificate**: Automatically handled by Cloudflare

## Test Your API

Once deployed, visit:
- `https://api.yourdomain.com/` - Health check
- `https://api.yourdomain.com/docs` - Interactive API docs
- `https://api.yourdomain.com/api/v1/assistant/status` - System status

## Ready-to-Use Files

Your project already includes:
- ✅ `wrangler.toml` - Cloudflare configuration
- ✅ `_worker.js` - Cloudflare Worker handler
- ✅ `main.py` - FastAPI application
- ✅ All dependencies configured

**Your Driver Scheduling API will be live at your custom domain in minutes!**