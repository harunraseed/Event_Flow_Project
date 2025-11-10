# Vercel Configuration Guide for Event Ticketing App

## 🚀 VERCEL DASHBOARD CONFIGURATION

### 1. ENVIRONMENT VARIABLES (REQUIRED)
Go to: Vercel Dashboard > Your Project > Settings > Environment Variables

Add these variables:

#### Database (REQUIRED - Your Supabase Connection)
```
DATABASE_URL = postgresql://postgres.your-project:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

#### Flask Security (REQUIRED)
```
SECRET_KEY = your-32-character-secret-key-here
FLASK_ENV = production
```

#### File Storage (OPTIONAL - for image uploads)
```
STORAGE_PROVIDER = local
```

OR for Cloudinary (recommended):
```
STORAGE_PROVIDER = cloudinary
CLOUDINARY_CLOUD_NAME = your-cloudinary-cloud-name
CLOUDINARY_API_KEY = your-cloudinary-api-key
CLOUDINARY_API_SECRET = your-cloudinary-api-secret
```

### 2. BUILD SETTINGS
Go to: Vercel Dashboard > Your Project > Settings > General

- Framework Preset: **Other**
- Root Directory: **/** (leave empty or use root)
- Build Command: **Leave Empty** (auto-detected)
- Output Directory: **Leave Empty** (auto-detected)
- Install Command: **pip install -r requirements.txt**

### 3. DOMAIN SETTINGS
Your app will be available at:
- Production: https://event-flow-project.vercel.app
- Preview: https://event-flow-project-git-branch.vercel.app

## 🔧 DEPLOYMENT CHECKLIST

### ✅ Required Files (Already Created)
- [x] `/api/index.py` - Vercel serverless function entry point
- [x] `/vercel.json` - Vercel configuration
- [x] `/requirements.txt` - Python dependencies
- [x] `/app.py` - Main Flask application

### ⚙️ Vercel Project Settings

1. **Import Project:**
   - Go to https://vercel.com/dashboard
   - Click "New Project"
   - Import from GitHub: `harunraseed/Event_Flow_Project`
   - Select branch: `01-harun-initial-change`

2. **Configure Environment Variables:**
   ```
   DATABASE_URL = [Your Supabase URL]
   SECRET_KEY = [32+ character random string]
   FLASK_ENV = production
   ```

3. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Check deployment logs for errors

## 🔍 TROUBLESHOOTING

### If you see 404 errors:
1. Check build logs in Vercel dashboard
2. Verify environment variables are set
3. Ensure `api/index.py` is present
4. Check Python version compatibility

### If you see import errors:
1. Verify all dependencies are in `requirements.txt`
2. Check that file paths are correct
3. Ensure database connection is working

### If database errors:
1. Verify `DATABASE_URL` environment variable
2. Check Supabase connection string format
3. Ensure database is accessible from Vercel

## 📋 STEP-BY-STEP DEPLOYMENT

### Step 1: Configure Vercel Project
1. Go to: https://vercel.com/dashboard
2. Click "New Project"
3. Choose "Import Git Repository"
4. Select: `harunraseed/Event_Flow_Project`
5. Branch: `01-harun-initial-change`
6. Click "Import"

### Step 2: Set Environment Variables
In Vercel Dashboard:
1. Go to Project Settings > Environment Variables
2. Add `DATABASE_URL` (your Supabase connection string)
3. Add `SECRET_KEY` (generate a random 32+ character string)
4. Add `FLASK_ENV = production`
5. Save each variable

### Step 3: Deploy
1. Click "Deploy" button
2. Wait for build to complete (2-3 minutes)
3. Check deployment URL: https://event-flow-project.vercel.app

### Step 4: Test
- Visit your deployment URL
- Should see: "Event Ticketing App - Vercel Deployment"
- If you see this, the basic setup is working

## 🎯 ENVIRONMENT VARIABLE EXAMPLES

### Minimum Required Configuration:
```
DATABASE_URL=postgresql://postgres.abcdefgh:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=my-super-secret-key-that-is-32-characters-long
FLASK_ENV=production
```

### Full Configuration with Cloudinary:
```
DATABASE_URL=postgresql://postgres.abcdefgh:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=my-super-secret-key-that-is-32-characters-long
FLASK_ENV=production
STORAGE_PROVIDER=cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=your-cloudinary-secret
```

## 🚀 AFTER SUCCESSFUL DEPLOYMENT

Once your app is working:
1. Test creating events
2. Test participant registration
3. Test certificate generation
4. Configure custom domain (optional)
5. Set up monitoring and analytics

Your event ticketing app will be live and accessible globally! 🌍