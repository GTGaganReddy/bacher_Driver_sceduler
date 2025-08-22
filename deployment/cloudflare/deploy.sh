#!/bin/bash

# Cloudflare Workers Deployment Script
# Deploy your Driver Scheduling API to Cloudflare with custom domain

echo "🚀 Deploying Driver Scheduling API to Cloudflare Workers..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Login to Cloudflare (if not already logged in)
echo "🔐 Checking Cloudflare authentication..."
wrangler whoami || wrangler login

# Set required secrets
echo "🔑 Setting up environment secrets..."
echo "You'll need to set these secrets for your deployment:"

# Set secrets interactively
echo "Setting DATABASE_URL..."
wrangler secret put DATABASE_URL

echo "Setting SUPABASE_PASSWORD..."
wrangler secret put SUPABASE_PASSWORD

echo "Setting SUPABASE_URL..."
wrangler secret put SUPABASE_URL

echo "Setting SUPABASE_KEY..."
wrangler secret put SUPABASE_KEY

echo "Setting GCF_URL..."
wrangler secret put GCF_URL

# Deploy to staging first
echo "🚀 Deploying to staging environment..."
wrangler deploy --env staging

# Ask for production deployment
read -p "Deploy to production? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to production..."
    wrangler deploy --env production
    
    echo "✅ Production deployment complete!"
    echo "📝 Next steps:"
    echo "1. Go to Cloudflare Dashboard > Workers & Pages"
    echo "2. Select your worker: driver-scheduling-api-prod"
    echo "3. Go to Settings > Triggers > Custom Domains"
    echo "4. Add your custom domain (e.g., api.yourdomain.com)"
    echo "5. Configure DNS records as instructed"
else
    echo "✅ Staging deployment complete!"
    echo "Test your staging environment first, then run:"
    echo "wrangler deploy --env production"
fi

echo ""
echo "🌐 Your API endpoints will be available at:"
echo "📍 Staging: https://driver-scheduling-api-staging.YOUR-SUBDOMAIN.workers.dev"
echo "📍 Production: https://api.yourdomain.com (after custom domain setup)"
echo ""
echo "🔧 Manage your deployment:"
echo "• View logs: wrangler tail"
echo "• Update secrets: wrangler secret put SECRET_NAME"
echo "• Check status: wrangler dev"