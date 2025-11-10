#!/usr/bin/env python3
"""
Database migration: Add instructions field to Event model
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_instructions():
    """Add instructions column to events table"""
    
    # Database paths to check
    db_paths = [
        'instance/event_ticketing.db',
        'event_ticketing.db',
        'instance/database.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"🔍 Found database: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if instructions column already exists
                cursor.execute("PRAGMA table_info(events)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'instructions' not in columns:
                    # Add the instructions column
                    cursor.execute("ALTER TABLE events ADD COLUMN instructions TEXT")
                    print(f"✅ Added 'instructions' column to {db_path}")
                else:
                    print(f"ℹ️  'instructions' column already exists in {db_path}")
                
                conn.commit()
                conn.close()
                print(f"✅ Migration completed for {db_path}")
                
            except Exception as e:
                print(f"❌ Error migrating {db_path}: {e}")
        else:
            print(f"⚠️  Database not found: {db_path}")

if __name__ == '__main__':
    print("🚀 Starting migration: Add instructions field to Event model")
    print(f"📅 Migration date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    migrate_add_instructions()
    
    print("="*60)
    print("✅ Migration script completed!")
    print("💡 You may need to restart your Flask application to see the changes.")