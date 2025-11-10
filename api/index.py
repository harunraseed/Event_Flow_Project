import sys
import os
from werkzeug.serving import WSGIRequestHandler

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the Flask app
from app import app as application

# For Vercel, we need to export the Flask app directly
app = application