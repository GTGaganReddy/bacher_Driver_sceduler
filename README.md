# FastAPI Driver Scheduling System - Contabo Deployment Guide

This guide will help you deploy your FastAPI driver scheduling system to your Contabo server using SSH and key authentication.

## Prerequisites

- Contabo VPS with Ubuntu 20.04+ or Debian 11+
- SSH key pair configured
- Domain name pointing to your server IP (optional but recommended)
- Root or sudo access

## 1. Server Preparation

### Connect to Your Server
```bash
ssh -i /path/to/your/private-key.pem user@your-contabo-ip
```

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
sudo apt install -y python3 python3-pip python3-venv nginx git curl ufw
```

### Install Python 3.11 (if not available)
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

## 2. Firewall Configuration

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

## 3. Application Deployment

### Create Application User
```bash
sudo adduser --system --group --home /home/driverscheduler driverscheduler
sudo usermod -aG sudo driverscheduler
```

### Switch to Application User
```bash
sudo su - driverscheduler
```

### Clone Your Repository
```bash
cd /home/driverscheduler
git clone https://github.com/yourusername/your-repo-name.git driver-scheduler
cd driver-scheduler
```

### Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install fastapi uvicorn asyncpg pydantic pydantic-settings httpx python-dotenv ortools
```

### Create Environment File
```bash
nano .env
```

Add your environment variables:
```env
# Database Configuration
SUPABASE_PASSWORD=your_supabase_password
SUPABASE_URL=https://nqwyglxhvhlrviknykmt.supabase.co
SUPABASE_KEY=your_supabase_key
DATABASE_URL=postgresql://postgres.nqwyglxhvhlrviknykmt:your_password@aws-0-eu-north-1.pooler.supabase.com:5432/postgres

# Google Cloud Function
GCF_URL=https://us-central1-driver-schedule-updater.cloudfunctions.net/update_sheet

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
PORT=8000
```

### Test the Application
```bash
python main.py
```

Press Ctrl+C to stop the test run.

## 4. Systemd Service Setup

### Create Service File
```bash
sudo nano /etc/systemd/system/driver-scheduler.service
```

Add the following content:
```ini
[Unit]
Description=FastAPI Driver Scheduling System
After=network.target

[Service]
Type=simple
User=driverscheduler
Group=driverscheduler
WorkingDirectory=/home/driverscheduler/driver-scheduler
Environment=PATH=/home/driverscheduler/driver-scheduler/venv/bin
ExecStart=/home/driverscheduler/driver-scheduler/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable driver-scheduler
sudo systemctl start driver-scheduler
sudo systemctl status driver-scheduler
```

## 5. Nginx Configuration

### Create Nginx Site Configuration
```bash
sudo nano /etc/nginx/sites-available/driver-scheduler
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/driver-scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 6. SSL Certificate (Optional but Recommended)

### Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Get SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 7. Application Management Commands

### View Logs
```bash
# Application logs
sudo journalctl -u driver-scheduler -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart application
sudo systemctl restart driver-scheduler

# Restart Nginx
sudo systemctl restart nginx
```

### Update Application
```bash
sudo su - driverscheduler
cd /home/driverscheduler/driver-scheduler
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt  # if you have requirements.txt
sudo systemctl restart driver-scheduler
```

## 8. Testing Your Deployment

### Test Endpoints
```bash
# Test root endpoint
curl http://your-server-ip/

# Test health check
curl http://your-server-ip/health

# Test API endpoints
curl http://your-server-ip/api/v1/assistant/status
```

### Expected Response
```json
{
  "service": "Driver Scheduling Backend",
  "version": "1.0.0",
  "status": "healthy",
  "docs": "/docs",
  "health": "/health",
  "healthz": "/healthz"
}
```

## 9. Monitoring and Maintenance

### Check Service Status
```bash
sudo systemctl status driver-scheduler
sudo systemctl status nginx
```

### Monitor Resources
```bash
# Check memory and CPU usage
htop
# or
top

# Check disk usage
df -h
```

### Backup Configuration
```bash
# Backup environment file
sudo cp /home/driverscheduler/driver-scheduler/.env /home/driverscheduler/backup-env-$(date +%Y%m%d)

# Backup nginx configuration
sudo cp /etc/nginx/sites-available/driver-scheduler /home/driverscheduler/backup-nginx-$(date +%Y%m%d)
```

## 10. Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u driver-scheduler --no-pager
   ```

2. **Database connection issues:**
   - Check environment variables in `.env`
   - Verify Supabase credentials
   - Test network connectivity

3. **Nginx 502 errors:**
   - Check if application is running on port 8000
   - Verify proxy_pass configuration

4. **Permission issues:**
   ```bash
   sudo chown -R driverscheduler:driverscheduler /home/driverscheduler/driver-scheduler
   ```

### Performance Tuning

For production use, consider:
- Using Gunicorn with multiple workers
- Setting up Redis for caching
- Implementing rate limiting
- Adding monitoring with Prometheus/Grafana

## 11. API Documentation

Once deployed, access your API documentation at:
- Swagger UI: `http://your-domain.com/docs`
- ReDoc: `http://your-domain.com/redoc`

## Security Notes

1. Change default SSH port
2. Use fail2ban for intrusion prevention
3. Regularly update system packages
4. Monitor access logs
5. Use strong passwords for all accounts
6. Keep SSL certificates updated

## Support

Your FastAPI driver scheduling system includes:
- ✅ Driver management and availability tracking
- ✅ Route optimization with OR-Tools
- ✅ Fixed assignments management
- ✅ Google Sheets integration
- ✅ Real-time scheduling optimization
- ✅ Complete REST API with 10+ endpoints

For issues, check the application logs first, then verify database connectivity and environment configuration.
