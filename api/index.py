import sys
import os
import traceback
from flask import Flask, jsonify

# Set default environment variables for Vercel
if not os.getenv('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'vercel-fallback-key-change-in-production'
if not os.getenv('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

# Add parent directory to path to import the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize app variable
app = None

try:
    # Try to import the main Flask app
    from app import app as main_app
    app = main_app
    print("✅ Successfully imported main Flask app")
except Exception as e:
    print(f"⚠️ Could not import main app: {e}")
    print(f"⚠️ Full traceback: {traceback.format_exc()}")
    
    # Fallback to simple Flask app for debugging
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            "message": "🎉 Event Ticketing App - Vercel Deployment (Debug Mode)",
            "status": "fallback_mode", 
            "platform": "vercel",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "environment_vars": {
                "DATABASE_URL": "✅ Set" if os.getenv('DATABASE_URL') else "❌ Missing",
                "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing", 
                "FLASK_ENV": os.getenv('FLASK_ENV', 'not set'),
                "PYTHONPATH": sys.path[:3]  # Show first 3 paths
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "platform": "vercel", 
            "mode": "debug",
            "app": "event-ticketing-fallback"
        })
    
    @app.route('/test-db')
    def test_db():
        db_url = os.getenv('DATABASE_URL')
        return jsonify({
            "database_configured": bool(db_url),
            "db_type": "postgresql" if db_url and "postgresql" in db_url else "unknown"
        })

# Ensure we always have a valid app
if app is None:
    app = Flask(__name__)
    
    @app.route('/')
    def emergency_fallback():
        return jsonify({
            "message": "Emergency Fallback - Something went very wrong",
            "status": "emergency_mode",
            "platform": "vercel"
        })

# This is the entry point for Vercel
if __name__ == "__main__":
    app.run(debug=False)