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

# Handle database URL for Vercel compatibility
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Fix for Vercel/Supabase connectivity issues
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    # Add SSL and IPv4 preference for Supabase
    if 'sslmode' not in database_url:
        separator = '&' if '?' in database_url else '?'
        database_url += f'{separator}sslmode=require&prefer_server_ciphers=off'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'sslmode': 'require',
        'connect_timeout': 10
    }
}

# Initialize database
db = SQLAlchemy()

# Test database connectivity
def test_db_connection():
    """Test database connection without creating tables"""
    try:
        # Simple connection test using SQLAlchemy 2.0 syntax
        with db.engine.connect() as connection:
            result = connection.execute(db.text('SELECT 1'))
            return True, "Database connection successful"
    except Exception as e:
        return False, str(e)

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
    database_url = os.getenv('DATABASE_URL')
    
    # First test database connectivity
    if database_url:
        try:
            # Test basic connection
            db_connected, db_message = test_db_connection()
            if db_connected:
                # If connected, try to query events
                events = Event.query.all()
                return jsonify({
                    "message": "🎉 Event Ticketing App - Fully Operational!",
                    "status": "success",
                    "platform": "vercel",
                    "database": "connected",
                    "events_count": len(events),
                    "database_info": db_message,
                    "environment": {
                        "DATABASE_URL": "✅ Connected",
                        "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                        "FLASK_ENV": os.getenv('FLASK_ENV', 'development')
                    },
                    "available_endpoints": [
                        "GET / - This status page",
                        "GET /events - List all events", 
                        "GET /events/<id> - Get event details",
                        "GET /health - Health check",
                        "GET /test-db - Database connection test"
                    ]
                })
            else:
                # Connection failed
                return jsonify({
                    "message": "🔧 Event Ticketing App - Database Connection Issue",
                    "status": "database_error",
                    "platform": "vercel", 
                    "error": db_message,
                    "database_url_format": database_url.split('@')[1] if '@' in database_url else "URL format hidden",
                    "troubleshooting": {
                        "step1": "Check Supabase dashboard - is database running?",
                        "step2": "Verify connection string format",
                        "step3": "Check Supabase network settings",
                        "step4": "Try connecting from local machine first"
                    },
                    "environment": {
                        "DATABASE_URL": "✅ Set but can't connect",
                        "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                        "FLASK_ENV": os.getenv('FLASK_ENV', 'development')
                    }
                }), 500
                
        except Exception as e:
            return jsonify({
                "message": "🔧 Event Ticketing App - Database Connection Issue",
                "status": "database_error",
                "platform": "vercel", 
                "error": str(e),
                "error_type": type(e).__name__,
                "environment": {
                    "DATABASE_URL": "✅ Set but connection failed",
                    "SECRET_KEY": "✅ Set" if os.getenv('SECRET_KEY') else "❌ Missing",
                    "FLASK_ENV": os.getenv('FLASK_ENV', 'development')
                }
            }), 500
    else:
        # No database URL set
        return jsonify({
            "message": "⚠️ Event Ticketing App - No Database Configured",
            "status": "no_database",
            "platform": "vercel",
            "environment": {
                "DATABASE_URL": "❌ Missing",
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

@app.route('/test-db')
def test_database():
    """Test database connection endpoint"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return jsonify({"error": "No DATABASE_URL configured"}), 400
    
    try:
        # Test connection
        db_connected, db_message = test_db_connection()
        
        if db_connected:
            return jsonify({
                "status": "success",
                "message": "Database connection successful",
                "database_info": db_message,
                "connection_string": f"Connected to: {database_url.split('@')[1]}" if '@' in database_url else "Connection string hidden"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Database connection failed",
                "error": db_message,
                "troubleshooting": [
                    "Check if Supabase database is running",
                    "Verify network connectivity", 
                    "Check SSL configuration",
                    "Verify credentials"
                ]
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Database test failed",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

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