# Git Setup Guide for Different Account

## Method 1: Push to Existing Repository on Different Account

### Step 1: Configure Git for This Project
```bash
# Set your different Git account details (run these commands)
git config user.name "Your-Other-Account-Name"
git config user.email "your-other-account@email.com"

# Verify configuration
git config --list --local
```

### Step 2: Add Your Repository as Remote
```bash
# Add remote repository (replace with your actual repo URL)
git remote add origin https://github.com/your-other-account/your-repo-name.git

# Or if using SSH
git remote add origin git@github.com:your-other-account/your-repo-name.git
```

### Step 3: Stage and Commit Files
```bash
# Add all files
git add .

# Commit with message
git commit -m "Initial commit: Event ticketing app ready for Vercel"
```

### Step 4: Push to Repository
```bash
# Push to main branch
git push -u origin main

# If the repository has a different default branch (like master)
git push -u origin master
```

## Method 2: Create New Repository on Different Account

### Step 1: Create Repository on GitHub/GitLab
1. Log into your different Git account
2. Create new repository named "event-ticketing-app"
3. Don't initialize with README (your project already has files)
4. Copy the repository URL

### Step 2: Connect Local Project
```bash
# Configure git for this project
git config user.name "Your-Other-Account-Name"
git config user.email "your-other-account@email.com"

# Add remote
git remote add origin YOUR_COPIED_REPOSITORY_URL

# Add and commit files
git add .
git commit -m "Initial commit: Event ticketing app ready for Vercel"

# Push to repository
git push -u origin main
```

## Authentication Options

### Option A: Personal Access Token (Recommended)
1. Go to GitHub/GitLab Settings > Developer Settings > Personal Access Tokens
2. Create new token with repo permissions
3. Use token as password when pushing:
   ```bash
   git push -u origin main
   # Username: your-other-account-name
   # Password: your-personal-access-token
   ```

### Option B: SSH Key
1. Generate SSH key: `ssh-keygen -t rsa -b 4096 -C "your-other-account@email.com"`
2. Add to SSH agent: `ssh-add ~/.ssh/id_rsa`
3. Copy public key: `cat ~/.ssh/id_rsa.pub`
4. Add to GitHub/GitLab account Settings > SSH Keys
5. Use SSH URL for remote

### Option C: GitHub CLI (Easiest)
```bash
# Install GitHub CLI, then
gh auth login
# Follow prompts to authenticate with different account
```

## Troubleshooting

### If you get "permission denied":
- Check if you're using correct account credentials
- Verify repository URL
- Ensure you have push access to the repository

### If you get "repository not found":
- Double-check the repository URL
- Ensure the repository exists on the other account
- Verify you're using the correct account name

## Quick Commands Summary

```bash
# Configure for different account
git config user.name "Other-Account-Name"
git config user.email "other-account@email.com"

# Add repository
git remote add origin https://github.com/other-account/repo-name.git

# Push code
git add .
git commit -m "Initial commit: Ready for Vercel deployment"
git push -u origin main
```

## After Successful Push

1. Go to https://vercel.com
2. Import your repository 
3. Configure environment variables:
   - DATABASE_URL (your Supabase URL)
   - SECRET_KEY (32+ character string)
   - STORAGE_PROVIDER=cloudinary
   - Cloudinary credentials
4. Deploy automatically!

Your app will be live at: https://your-repo-name.vercel.app