# Direct Cloudflare Deployment Guide

Deploy your Driver Scheduling API directly to Cloudflare using your domain and API keys.

## Method 1: Cloudflare Dashboard (Recommended)

### Step 1: Upload Your Code
1. Go to **Cloudflare Dashboard > Workers & Pages**
2. Click **Create Application > Pages**
3. **Upload assets** - drag your entire project folder
4. Set **Project name**: `driver-scheduling-api`

### Step 2: Configure Environment Variables
In **Settings > Environment Variables**, add:

```
DATABASE_URL = postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres
SUPABASE_PASSWORD = your_database_password
SUPABASE_URL = https://YOUR_REF.supabase.co
SUPABASE_KEY = your_service_role_key
GCF_URL = https://us-central1-driver-schedule-updater.cloudfunctions.net/update_sheet
DEBUG = false
LOG_LEVEL = INFO
```

### Step 3: Configure Custom Domain
1. Go to **Custom Domains**
2. Add your domain: `api.yourdomain.com`
3. Update DNS records as instructed

## Method 2: Git Integration

### Step 1: Connect Repository
1. **Workers & Pages > Create Application**
2. Connect your Git repository
3. Set build settings:
   - **Build command**: `pip install -r requirements.txt`
   - **Output directory**: `/`

### Step 2: Add Environment Variables
Same as Method 1 - add all required environment variables

## Method 3: Wrangler CLI (Fastest)

```bash
# Install Wrangler
npm install -g wrangler

# Login with your Cloudflare credentials
wrangler login

# Deploy directly
wrangler deploy

# Set environment variables
wrangler secret put DATABASE_URL
wrangler secret put SUPABASE_PASSWORD
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
wrangler secret put GCF_URL
```

## Your Environment Variables

Replace these with your actual values:

| Variable | Your Value |
|----------|------------|
| `DATABASE_URL` | Get from Supabase > Settings > Database |
| `SUPABASE_PASSWORD` | Your database password |
| `SUPABASE_URL` | Get from Supabase > Settings > API |
| `SUPABASE_KEY` | Get from Supabase > Settings > API (service_role) |
| `GCF_URL` | Your Google Cloud Function URL |

## Custom Domain Setup

1. **Add Domain**: In Cloudflare Pages, go to Custom Domains
2. **Enter**: `api.yourdomain.com` (or your preferred subdomain)
3. **DNS**: Cloudflare will show you the DNS records to add
4. **SSL**: Automatically provided by Cloudflare

## Testing Your Deployment

Once deployed, test these endpoints:

- `https://api.yourdomain.com/` - Health check
- `https://api.yourdomain.com/docs` - API documentation
- `https://api.yourdomain.com/health` - Detailed health check

## Troubleshooting

**Build Errors**: Make sure `requirements.txt` includes all dependencies
**Environment Variables**: Double-check all secrets are set correctly
**Domain Issues**: DNS propagation can take up to 24 hours

Your API will be live at your custom domain within minutes!