#!/usr/bin/env python3
"""
Migrate all SQLite databases in the instance directory.
"""

import sqlite3
import os
import glob

def migrate_sqlite_file(db_file):
    """Migrate a single SQLite database file."""
    print(f"🔧 Migrating: {db_file}")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            print(f"ℹ️  No events table found in {db_file}, skipping...")
            conn.close()
            return
            
        # Check existing columns
        cursor.execute("PRAGMA table_info(events)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Existing columns in {db_file}: {existing_columns}")
        
        # Add logo_filename column if it doesn't exist
        if 'logo_filename' not in existing_columns:
            cursor.execute("ALTER TABLE events ADD COLUMN logo_filename VARCHAR(255)")
            conn.commit()
            print(f"✅ Added logo_filename column to {db_file}")
        else:
            print(f"ℹ️  logo_filename column already exists in {db_file}")
            
        # Add time column if it doesn't exist  
        if 'time' not in existing_columns:
            cursor.execute("ALTER TABLE events ADD COLUMN time TIME")
            conn.commit()
            print(f"✅ Added time column to {db_file}")
        else:
            print(f"ℹ️  time column already exists in {db_file}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error migrating {db_file}: {e}")

def main():
    print("🚀 Starting migration of all SQLite databases...")
    
    # Find all .db files in instance directory
    db_files = glob.glob("instance/*.db")
    
    if not db_files:
        print("ℹ️  No database files found in instance directory.")
        return
    
    for db_file in db_files:
        migrate_sqlite_file(db_file)
        print()
    
    print("🎉 Migration completed for all databases!")

if __name__ == '__main__':
    main()