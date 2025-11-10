import sys
import os

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    # Try to import the main Flask app
    from app import app
    print("Successfully imported main Flask app")
except Exception as e:
    print(f"Error importing main app: {e}")
    # Fallback to a simple Flask app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return {
            "message": "Event Ticketing App - Vercel Deployment",
            "status": "running",
            "error": f"Main app import failed: {str(e)}"
        }
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "platform": "vercel"}

# This is required for Vercel
if __name__ == "__main__":
    app.run()