from flask import Flask, jsonify
import os

# Create a simple Flask app for debugging
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "🎉 Event Ticketing App - Vercel Deployment Working!",
        "status": "success",
        "platform": "vercel",
        "python_version": "3.9+",
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
        "app": "event-ticketing"
    })

@app.route('/test-db')
def test_db():
    db_url = os.getenv('DATABASE_URL')
    return jsonify({
        "database_configured": bool(db_url),
        "db_type": "postgresql" if db_url and "postgresql" in db_url else "unknown"
    })

# For debugging - show all environment variables (be careful in production)
@app.route('/debug/env')
def debug_env():
    return jsonify({
        "env_vars": {k: "***" if "SECRET" in k or "PASSWORD" in k else v 
                    for k, v in os.environ.items() if not k.startswith('_')}
    })

# This is the entry point for Vercel
if __name__ == "__main__":
    app.run(debug=True)