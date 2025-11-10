# Deployment Guide

## Azure Web App Deployment

### Prerequisites
- Azure subscription
- GitHub account
- Azure CLI (optional)

### Step 1: Prepare Repository

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production-ready application structure"
   git push origin main
   ```

2. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Update all values with production settings
   - **Important**: Never commit `.env` to GitHub

### Step 2: Create Azure Web App

#### Option A: Azure Portal

1. **Create Resource**
   - Go to Azure Portal
   - Create new "Web App" resource
   - Choose subscription and resource group
   - Set name (e.g., `your-event-app`)
   - Runtime: Python 3.11
   - Region: Choose nearest location

2. **Configure Deployment**
   - Go to "Deployment Center"
   - Choose "GitHub" as source
   - Authorize and select repository
   - Branch: `main`
   - Build provider: "App Service Build Service"

#### Option B: Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name event-app-rg --location "East US"

# Create App Service plan
az appservice plan create \
  --name event-app-plan \
  --resource-group event-app-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group event-app-rg \
  --plan event-app-plan \
  --name your-event-app \
  --runtime "PYTHON:3.11" \
  --deployment-source-url https://github.com/yourusername/event-ticketing-app
```

### Step 3: Configure Application Settings

**🔒 CRITICAL**: Environment variables are set in Azure Portal, NOT in .env file!

In Azure Portal → Your Web App → Configuration → Application Settings, add:

| Name | Value | Notes |
|------|-------|-------|
| `SECRET_KEY` | `your-production-secret-key` | Generate strong random key |
| `FLASK_ENV` | `production` | Sets production mode |
| `DATABASE_URL` | `your-production-database-url` | PostgreSQL connection string |
| `MAIL_SERVER` | `smtp.gmail.com` | Email server |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `True` | Enable TLS |
| `MAIL_USERNAME` | `your-production-email@gmail.com` | Production email |
| `MAIL_PASSWORD` | `your-production-app-password` | **App-specific password** |
| `MAIL_DEFAULT_SENDER` | `your-production-email@gmail.com` | Default sender |
| `WEBSITES_PORT` | `8000` | Azure Web App port |

**⚠️ Security Notes:**
- These variables are **NOT** in your .env file
- .env file is **never committed to Git**
- Production uses Azure Portal configuration
- Local development uses .env file (Git ignored)

### Step 4: Database Setup

#### Option A: Azure Database for PostgreSQL

1. **Create PostgreSQL Server**
   ```bash
   az postgres server create \
     --resource-group event-app-rg \
     --name event-app-db \
     --location "East US" \
     --admin-user dbadmin \
     --admin-password YourPassword123! \
     --sku-name GP_Gen5_2
   ```

2. **Configure Firewall**
   ```bash
   # Allow Azure services
   az postgres server firewall-rule create \
     --resource-group event-app-rg \
     --server event-app-db \
     --name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

3. **Update DATABASE_URL**
   ```
   DATABASE_URL=postgresql://dbadmin:YourPassword123!@event-app-db.postgres.database.azure.com:5432/postgres?sslmode=require
   ```

#### Option B: SQLite (for testing only)
- Keep default SQLite for initial testing
- Upgrade to PostgreSQL for production

### Step 5: First Deployment

1. **Trigger Deployment**
   - Push changes to GitHub main branch
   - Azure will automatically deploy

2. **Monitor Deployment**
   - Check "Deployment Center" for build logs
   - View "Log stream" for runtime logs

3. **Initialize Database**
   - SSH into App Service or use Azure Cloud Shell
   ```bash
   # Navigate to app directory
   cd /home/site/wwwroot
   
   # Initialize migrations (if not done)
   python migrate_manager.py init
   
   # Create initial migration
   python migrate_manager.py create "Initial production migration"
   
   # Apply migrations
   python migrate_manager.py upgrade
   ```

### Step 6: Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to "Custom domains" in Azure Portal
   - Add your domain
   - Configure DNS records

2. **SSL Certificate**
   - Use "App Service Managed Certificate" (free)
   - Or upload your own certificate

### Step 7: Monitoring and Scaling

1. **Application Insights**
   - Enable Application Insights
   - Monitor performance and errors

2. **Auto-scaling**
   - Configure scale rules based on CPU/memory
   - Set minimum and maximum instances

3. **Backup**
   - Enable automatic backups
   - Configure backup retention

## Continuous Deployment

### GitHub Actions (Automatic)

Azure creates a GitHub Action workflow automatically. It's located at:
`.github/workflows/main_your-app-name.yml`

### Manual Deployment Commands

```bash
# Build and deploy manually
git add .
git commit -m "Update application"
git push origin main

# Check deployment status
az webapp deployment list --resource-group event-app-rg --name your-event-app
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies in `requirements.txt`
   - Check Python version compatibility

2. **Database Connection**
   - Verify DATABASE_URL format
   - Check firewall rules for PostgreSQL

3. **Static Files**
   - Ensure correct static file configuration
   - Check file permissions

4. **Email Issues**
   - Verify SMTP settings
   - Use app-specific passwords for Gmail

### Logs and Debugging

1. **View Logs**
   ```bash
   # Stream logs in real-time
   az webapp log tail --resource-group event-app-rg --name your-event-app
   
   # Download log files
   az webapp log download --resource-group event-app-rg --name your-event-app
   ```

2. **SSH Access**
   ```bash
   # SSH into the container
   az webapp ssh --resource-group event-app-rg --name your-event-app
   ```

3. **Debug Mode**
   - Set `DEBUG=True` temporarily for detailed errors
   - **Remember to disable in production**

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to Git
   - Use Azure Key Vault for sensitive data

2. **HTTPS**
   - Always use HTTPS in production
   - Configure HTTP to HTTPS redirect

3. **Database Security**
   - Use SSL connections
   - Regular security updates
   - Backup encryption

4. **Access Control**
   - Implement proper authentication
   - Use role-based access control
   - Regular security audits

## Performance Optimization

1. **Caching**
   - Implement Redis caching
   - Use CDN for static files

2. **Database Optimization**
   - Index frequently queried fields
   - Connection pooling
   - Query optimization

3. **Monitoring**
   - Set up alerts for errors
   - Monitor response times
   - Track user metrics

## Backup and Recovery

1. **Automated Backups**
   - Database backups
   - File system snapshots
   - Configuration exports

2. **Disaster Recovery**
   - Multi-region deployment
   - Backup restoration procedures
   - Business continuity planning