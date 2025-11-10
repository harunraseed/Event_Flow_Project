"""
Blueprint initialization for route modules
"""

from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
event_bp = Blueprint('event', __name__)
quiz_bp = Blueprint('quiz', __name__)
certificate_bp = Blueprint('certificate', __name__)

# Import route modules to register them with blueprints
from app.routes import main, events, quiz, certificates