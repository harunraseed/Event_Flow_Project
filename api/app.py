"""
Simplified Event Ticketing App for Vercel Serverless Deployment
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy()

# Simple database models for Vercel
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=db.func.now())

class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    checked_in = db.Column(db.Boolean, default=False)
    checkin_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Initialize database with app
db.init_app(app)

@app.route('/')
def home():
    """Home page showing event management dashboard"""
    try:
        # Test database connection
        events = Event.query.all()
        return jsonify({
            "message": "🎉 Event Ticketing App - Fully Operational!",
            "status": "success",
            "platform": "vercel",
            "database": "connected",
            "events_count": len(events),
            "environment": {
                "DATABASE_URL": "✅ Connected" if os.getenv('DATABASE_URL') else "❌ Missing",
                "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                "FLASK_ENV": os.getenv('FLASK_ENV', 'development')
            },
            "available_endpoints": [
                "GET / - This status page",
                "GET /events - List all events", 
                "GET /events/<id> - Get event details",
                "GET /health - Health check"
            ]
        })
    except Exception as e:
        return jsonify({
            "message": "🔧 Event Ticketing App - Database Connection Issue",
            "status": "database_error",
            "platform": "vercel", 
            "error": str(e),
            "environment": {
                "DATABASE_URL": "✅ Set" if os.getenv('DATABASE_URL') else "❌ Missing",
                "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                "FLASK_ENV": os.getenv('FLASK_ENV', 'development')
            }
        }), 500

@app.route('/events')
def list_events():
    """List all events"""
    try:
        events = Event.query.all()
        return jsonify({
            "events": [{
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "date": event.date.isoformat() if event.date else None,
                "location": event.location,
                "status": event.status
            } for event in events]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/<int:event_id>')
def event_details(event_id):
    """Get event details and participants"""
    try:
        event = Event.query.get_or_404(event_id)
        participants = Participant.query.filter_by(event_id=event_id).all()
        
        return jsonify({
            "event": {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "date": event.date.isoformat() if event.date else None,
                "location": event.location,
                "status": event.status
            },
            "participants_count": len(participants),
            "participants": [{
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "ticket_number": p.ticket_number,
                "checked_in": p.checked_in,
                "checkin_time": p.checkin_time.isoformat() if p.checkin_time else None
            } for p in participants]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "platform": "vercel",
        "app": "event-ticketing-simplified"
    })

# For local development
if __name__ == '__main__':
    app.run(debug=True)