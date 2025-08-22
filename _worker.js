// Cloudflare Worker for FastAPI Driver Scheduling API

export default {
  async fetch(request, env, ctx) {
    // Environment variables from Cloudflare dashboard
    const config = {
      DATABASE_URL: env.DATABASE_URL,
      SUPABASE_PASSWORD: env.SUPABASE_PASSWORD, 
      SUPABASE_URL: env.SUPABASE_URL,
      SUPABASE_KEY: env.SUPABASE_KEY,
      GCF_URL: env.GCF_URL,
      DEBUG: env.DEBUG || 'false',
      LOG_LEVEL: env.LOG_LEVEL || 'INFO'
    };

    // Set environment variables for the Python app
    for (const [key, value] of Object.entries(config)) {
      if (value) {
        globalThis.process = globalThis.process || {};
        globalThis.process.env = globalThis.process.env || {};
        globalThis.process.env[key] = value;
      }
    }

    // CORS headers for your domain
    const corsHeaders = {
      'Access-Control-Allow-Origin': request.headers.get('Origin') || '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Credentials': 'true'
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders
      });
    }

    try {
      // Import and run the FastAPI app
      const { default: app } = await import('./main.py');
      
      // Convert Cloudflare Request to Python request format
      const url = new URL(request.url);
      const method = request.method;
      const headers = Object.fromEntries(request.headers);
      const body = ['GET', 'HEAD'].includes(method) ? null : await request.text();

      // Call FastAPI app
      const response = await app({
        method,
        url: url.pathname + url.search,
        headers,
        body
      });

      // Add CORS headers to response
      const responseHeaders = new Headers(response.headers);
      Object.entries(corsHeaders).forEach(([key, value]) => {
        responseHeaders.set(key, value);
      });

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });

    } catch (error) {
      console.error('Worker error:', error);
      
      return new Response(JSON.stringify({
        error: 'Internal server error',
        message: error.message
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  }
};