# Vercel Deployment Guide for Event Ticketing App

## 🚀 **Why Vercel is Great for Your Flask App:**

### **Advantages over Azure Web Apps:**
- ✅ **Simpler deployment** - Git-based auto-deployment
- ✅ **Better performance** - Edge network optimization  
- ✅ **Free tier** - Generous limits for small-medium apps
- ✅ **Zero config** - Automatic HTTPS, CDN, scaling
- ✅ **Instant rollbacks** - Easy version management
- ✅ **Great developer experience** - Preview deployments for PRs

### **Vercel Limitations to Address:**
- ⚠️ **Serverless environment** - No persistent file system
- ⚠️ **Function timeout** - 10s hobby, 15s pro (good for most web apps)
- ⚠️ **Memory limits** - 1024MB max per function

## 📁 **File Storage Solutions for Vercel:**

### **Current Local Dependencies:**
- `/uploads/certificates/` - Certificate assets  
- `/static/uploads/logos/` - Event logos
- `/uploads/logos/` - Logo uploads
- `/instance/` - SQLite files (✅ Already migrated to Supabase)

### **Vercel-Compatible Storage Options:**

#### **Option 1: Vercel Blob Storage (Recommended)**
```bash
# Simple, integrated with Vercel
# Pricing: $0.15/GB stored, $0.30/GB transferred
npm install @vercel/blob  # For frontend uploads
pip install requests      # For Python backend
```

#### **Option 2: Cloudinary (Best for Images)**
```bash
# Specialized for image/video processing
# Free tier: 25 credits/month (good for small apps)
pip install cloudinary
```

#### **Option 3: AWS S3 (Most Flexible)**
```bash
# Industry standard, very reliable
# Pricing: ~$0.023/GB stored
pip install boto3
```

## 🔧 **Vercel Configuration Files:**

### **1. vercel.json (Deployment Config)**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  },
  "functions": {
    "app.py": {
      "maxDuration": 30
    }
  }
}
```

### **2. requirements.txt Updates**
```txt
# Add Vercel-compatible packages
vercel==0.4.0
requests==2.31.0  # For file uploads to external storage
```

## 🗃️ **Database Configuration:**
✅ **Your Supabase PostgreSQL is perfect for Vercel!**
- Serverless-friendly
- Global edge locations
- No connection pooling issues

## 📤 **File Upload Strategy:**

### **Recommended: Vercel Blob + Cloudinary Hybrid**

#### **For Event Logos (Processed Images):**
- Use **Cloudinary** for automatic optimization
- Resize, compress, format conversion
- CDN delivery worldwide

#### **For Certificate Assets (Simple Storage):**  
- Use **Vercel Blob** for direct file storage
- Simple upload/download
- Integrated with Vercel dashboard

## 🔄 **Migration Steps:**

### **Phase 1: Vercel Deployment Setup**
1. Create `vercel.json` configuration
2. Update Flask app for serverless compatibility
3. Configure environment variables
4. Test local deployment

### **Phase 2: File Storage Migration**  
1. Choose storage provider (Cloudinary recommended)
2. Create storage service abstraction
3. Update file upload handlers
4. Migrate existing files

### **Phase 3: Production Deployment**
1. Connect GitHub repository to Vercel
2. Configure production environment variables
3. Deploy and test all features
4. Set up custom domain (optional)

## 💰 **Cost Estimation:**

### **Vercel (Hobby - Free):**
- ✅ 100GB bandwidth/month
- ✅ Unlimited websites  
- ✅ 100 serverless function executions/day
- ✅ 1000 edge requests/hour

### **Storage Costs:**
- **Cloudinary Free:** 25 credits/month (~500 images)
- **Vercel Blob:** $0.15/GB stored + $0.30/GB transfer
- **Total estimated:** $0-10/month for small-medium app

## 🚦 **Next Steps:**

1. **Immediate:** Create Vercel configuration files
2. **Phase 1:** Set up serverless-compatible Flask app  
3. **Phase 2:** Implement cloud file storage
4. **Phase 3:** Deploy to Vercel production

Your app is already 90% ready for Vercel since you have:
- ✅ Cloud database (Supabase)
- ✅ Clean codebase (no temp files)
- ✅ Modern Flask structure