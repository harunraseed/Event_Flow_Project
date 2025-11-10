import sys
import os

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app

# Export the Flask app for Vercel
# Vercel expects the app to be available as a WSGI application
if __name__ == "__main__":
    app.run()