"""
Setup script for Event Ticketing System
Run this script to set up the application for the first time.
"""

import os
import sys
from app import app, db

def setup_application():
    """Set up the application database and initial configuration."""
    print("🎫 Event Ticketing System Setup")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please copy .env.example to .env and configure your settings.")
        print("   Especially important: EMAIL settings for ticket notifications")
        
        choice = input("\n📋 Would you like to create a basic .env file now? (y/n): ")
        if choice.lower() == 'y':
            create_basic_env()
        else:
            print("⚠️  Please create .env file manually before running the app.")
            return
    
    # Create database tables
    with app.app_context():
        print("\n🗄️  Setting up database...")
        db.create_all()
        print("✅ Database tables created successfully!")
    
    print("\n🚀 Setup complete!")
    print("\nNext steps:")
    print("1. Configure your email settings in .env file")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")
    print("\n📖 See README.md for detailed setup instructions.")

def create_basic_env():
    """Create a basic .env file with placeholder values."""
    env_content = """# Flask Configuration
SECRET_KEY=change-this-to-a-random-secret-key
DATABASE_URL=sqlite:///event_ticketing.db

# Email Configuration (Update with your SMTP settings)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Important: Configure email settings before running the app!
# For Gmail: Enable 2FA and create an App Password
# See README.md for detailed email setup instructions
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Basic .env file created!")
    print("⚠️  IMPORTANT: Update email settings in .env before running the app!")

if __name__ == '__main__':
    setup_application()