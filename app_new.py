"""
Event Ticketing Flask Application
Entry point for development and fallback for production
"""
import os
import sys
from app import create_app, db

def main():
    """Main application function"""
    # Create the Flask application
    app = create_app()
    
    # Development mode check
    if __name__ == '__main__' or os.environ.get('FLASK_ENV') == 'development':
        with app.app_context():
            try:
                # Create database tables if they don't exist
                db.create_all()
                print("✅ Database tables created successfully!")
            except Exception as e:
                print(f"⚠️  Database initialization warning: {e}")
        
        # Get configuration
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        print("🎯 Event Ticketing & Quiz Management Application")
        print(f"🚀 Starting on port {port}")
        print(f"🌐 Visit: http://localhost:{port}")
        print(f"🔧 Debug mode: {debug}")
        print("📊 Features: Events, Quizzes, Certificates, QR Codes")
        
        # Run the application
        app.run(host='0.0.0.0', port=port, debug=debug)
    
    return app

# Create app instance for WSGI servers
app = create_app()

if __name__ == '__main__':
    main()