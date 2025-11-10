#!/usr/bin/env python3
"""
Migration script to add logo_filename and time fields to Event model.
Run this once to update your existing database.
"""

from app import app, db
from models import Event

def migrate_database():
    """Add new columns to existing database."""
    with app.app_context():
        # Check if we need to create the database
        db.create_all()
        
        # Try to add the new columns if they don't exist
        try:
            with db.engine.begin() as conn:
                # Check if logo_filename column exists
                result = conn.execute("PRAGMA table_info(events)")
                columns = [row[1] for row in result.fetchall()]
                
                if 'logo_filename' not in columns:
                    conn.execute("ALTER TABLE events ADD COLUMN logo_filename VARCHAR(255)")
                    print("✅ Added logo_filename column to events table")
                else:
                    print("ℹ️  logo_filename column already exists")
                
                if 'time' not in columns:
                    conn.execute("ALTER TABLE events ADD COLUMN time TIME")
                    print("✅ Added time column to events table")
                else:
                    print("ℹ️  time column already exists")
                    
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            print("💡 If you're using a fresh database, this is normal - just run the app and the tables will be created automatically.")

if __name__ == '__main__':
    migrate_database()
    print("🎉 Migration completed!")