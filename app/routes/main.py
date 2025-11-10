"""
Main application routes
"""

from flask import render_template, request, redirect, url_for, flash
from app.routes import main_bp
from app.models import Event
from app import db

@main_bp.route('/')
def index():
    """Home page showing all events."""
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('index.html', events=events)

@main_bp.route('/health')
def health_check():
    """Health check endpoint for Azure."""
    return {'status': 'healthy', 'service': 'event-ticketing-app'}, 200