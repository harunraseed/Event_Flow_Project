#!/usr/bin/env python3
"""
Fix Supabase database schema to match app expectations
"""
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

def fix_supabase_schema():
    """Add missing columns to Supabase database"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    parsed = urlparse(database_url)
    
    print("🔧 Fixing Supabase Database Schema")
    print("=" * 50)
    
    try:
        # Connect to Supabase
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        print("✅ Connected to Supabase PostgreSQL")
        
        # Check current participants table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'participants' 
            ORDER BY ordinal_position
        """)
        
        current_columns = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"📊 Current participants columns: {list(current_columns.keys())}")
        
        # Required columns based on app.py expectations
        required_columns = {
            'id': 'integer',
            'event_id': 'integer', 
            'name': 'character varying',
            'email': 'character varying',
            'ticket_number': 'character varying',  # This was ticket_id, needs to be renamed
            'checked_in': 'boolean',
            'checkin_time': 'timestamp without time zone',
            'email_sent': 'boolean',
            'email_sent_at': 'timestamp without time zone',
            'created_at': 'timestamp without time zone'
        }
        
        print(f"🎯 Required columns: {list(required_columns.keys())}")
        
        # Check what needs to be fixed
        fixes_needed = []
        
        # 1. Rename ticket_id to ticket_number if it exists
        if 'ticket_id' in current_columns and 'ticket_number' not in current_columns:
            fixes_needed.append("RENAME ticket_id to ticket_number")
        
        # 2. Add missing columns
        for col_name, col_type in required_columns.items():
            if col_name not in current_columns:
                if col_name == 'checked_in':
                    fixes_needed.append(f"ADD COLUMN {col_name} BOOLEAN DEFAULT FALSE")
                elif col_name == 'email_sent':
                    fixes_needed.append(f"ADD COLUMN {col_name} BOOLEAN DEFAULT FALSE")
                elif col_name in ['checkin_time', 'email_sent_at']:
                    fixes_needed.append(f"ADD COLUMN {col_name} TIMESTAMP")
                elif col_name == 'created_at':
                    fixes_needed.append(f"ADD COLUMN {col_name} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        if not fixes_needed:
            print("✅ Database schema is already correct!")
            return True
            
        print(f"\n🔧 Fixes needed:")
        for fix in fixes_needed:
            print(f"   - {fix}")
        
        # Apply fixes
        for fix in fixes_needed:
            if fix.startswith("RENAME"):
                sql = "ALTER TABLE participants RENAME COLUMN ticket_id TO ticket_number"
            else:
                sql = f"ALTER TABLE participants {fix}"
            
            print(f"\n🔄 Executing: {sql}")
            cursor.execute(sql)
            
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'participants' 
            ORDER BY ordinal_position
        """)
        
        updated_columns = [row[0] for row in cursor.fetchall()]
        print(f"📊 Updated participants columns: {updated_columns}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    success = fix_supabase_schema()
    if success:
        print("\n🎉 Database schema fix completed!")
        print("🚀 Your Flask app should now work properly with Supabase")
    else:
        print("\n❌ Database schema fix failed")