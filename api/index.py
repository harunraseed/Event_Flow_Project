import sys
import os
from flask import Flask, jsonify

# Add parent directory to path to import the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the main Flask app
try:
    from app import app
    print("✅ Successfully imported main Flask app")
except Exception as e:
    print(f"⚠️ Could not import main app: {e}")
    # Fallback to simple Flask app for debugging
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return jsonify({
            "message": "🎉 Event Ticketing App - Vercel Deployment (Debug Mode)",
            "status": "fallback_mode",
            "platform": "vercel",
            "error": str(e),
            "environment_vars": {
                "DATABASE_URL": "✅ Set" if os.getenv('DATABASE_URL') else "❌ Missing",
                "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                "FLASK_ENV": os.getenv('FLASK_ENV', 'not set')
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

# This is the entry point for Vercel
if __name__ == "__main__":
    app.run(debug=True)