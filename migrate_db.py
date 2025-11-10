#!/usr/bin/env python3
"""
Manual migration script to add logo_filename and time fields to Event model.
This script will safely add the new columns to existing databases.
"""

import sqlite3
import os
from app import app

def migrate_database():
    """Add new columns to existing database."""
    
    # Get the database path from the app config
    with app.app_context():
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/app.db')
        
        # Extract the actual file path
        if db_path.startswith('sqlite:///'):
            db_file = db_path[10:]  # Remove 'sqlite:///'
        else:
            print("❌ Unsupported database type. This script only works with SQLite.")
            return
            
        if not os.path.exists(db_file):
            print(f"ℹ️  Database file {db_file} doesn't exist yet. Creating new database...")
            # Import here to create tables
            from models import db
            db.create_all()
            print("✅ New database created with all required columns!")
            return
            
        print(f"🔧 Migrating database: {db_file}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        try:
            # Check existing columns
            cursor.execute("PRAGMA table_info(events)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            print(f"📋 Existing columns: {existing_columns}")
            
            # Add logo_filename column if it doesn't exist
            if 'logo_filename' not in existing_columns:
                cursor.execute("ALTER TABLE events ADD COLUMN logo_filename VARCHAR(255)")
                conn.commit()
                print("✅ Added logo_filename column")
            else:
                print("ℹ️  logo_filename column already exists")
                
            # Add time column if it doesn't exist  
            if 'time' not in existing_columns:
                cursor.execute("ALTER TABLE events ADD COLUMN time TIME")
                conn.commit()
                print("✅ Added time column")
            else:
                print("ℹ️  time column already exists")
                
            # Verify the changes
            cursor.execute("PRAGMA table_info(events)")
            new_columns = [row[1] for row in cursor.fetchall()]
            print(f"📋 Updated columns: {new_columns}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    print("🚀 Starting database migration...")
    migrate_database()
    print("🎉 Migration completed!")
    print("\n💡 You can now run your Flask app with the new logo and time features!")