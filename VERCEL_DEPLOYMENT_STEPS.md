# Vercel Deployment Guide - Your Event Ticketing App

## Completed Setup Steps:
- [x] Vercel configuration files created
- [x] Cloud storage service implemented  
- [x] SQLite files cleaned up and backed up
- [x] Local uploads backed up (99 files)
- [x] Serverless compatibility updates
- [x] Runtime and ignore files created

## Next Steps for Deployment:

### 1. Setup Cloud Storage (Choose One):

#### Option A: Cloudinary (Recommended for Images)
1. Sign up: https://cloudinary.com (Free: 25 credits/month)
2. Get credentials from Dashboard > Settings > Access Keys
3. Add to Vercel environment variables:
   ```
   STORAGE_PROVIDER=cloudinary
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

#### Option B: Vercel Blob Storage
1. In Vercel Dashboard: Storage > Create Database > Blob
2. Copy the token
3. Add to environment variables:
   ```
   STORAGE_PROVIDER=vercel-blob
   BLOB_READ_WRITE_TOKEN=your-token
   ```

### 2. Deploy to Vercel:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Visit https://vercel.com
   - Import your GitHub repository
   - Vercel will auto-detect Flask app

3. **Configure Environment Variables:**
   In Vercel Dashboard > Settings > Environment Variables, add:
   ```
   DATABASE_URL=your-supabase-url
   SECRET_KEY=your-secret-key-32-chars-min
   STORAGE_PROVIDER=cloudinary
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

4. **Deploy:**
   - Vercel deploys automatically on git push
   - Your app will be available at: https://your-app.vercel.app

### 3. Migrate Existing Files:

#### Upload Files to Cloud Storage:
1. Download backed up files from: `backup/local_uploads_backup/`
2. Upload manually through your app's upload interface
3. Files will automatically save to Cloudinary/Vercel Blob

#### Test Everything:
- [ ] Event creation with logo upload
- [ ] Participant registration  
- [ ] Certificate generation
- [ ] Email sending
- [ ] Database operations (Supabase)

## File Backup Locations:
- SQLite databases: `backup/sqlite_removed/`
- Upload files: `backup/local_uploads_backup/`
- Original app.py: `app.py.backup`

## Production Benefits:
- Automatic HTTPS and CDN
- Global edge deployment
- Zero-config scaling  
- Instant rollbacks
- Preview deployments
- Custom domains (free)

## Expected Costs:
- Vercel Hobby (Free): Up to 100GB bandwidth/month
- Cloudinary (Free): 25 credits/month (~500 images)  
- Supabase (Free): 500MB database, 2GB bandwidth
- **Total: $0/month for small-medium usage**

## Need Help?
- Vercel docs: https://vercel.com/docs
- Cloudinary docs: https://cloudinary.com/documentation
- Your app is ready - just follow the steps above!
