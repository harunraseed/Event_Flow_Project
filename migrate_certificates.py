#!/usr/bin/env python3
"""
Certificates Migration Script
Migrate certificates from SQLite to Supabase after participants are migrated
"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

SQLITE_DB = 'instance/event_ticketing.db'
POSTGRES_URL = os.getenv('DATABASE_URL')

def migrate_certificates():
    """Migrate certificates table"""
    print("🏆 CERTIFICATES MIGRATION")
    print("=" * 50)
    
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cursor = pg_conn.cursor()
        
        print("✅ Connected to both databases")
        
        # Check participants exist in Supabase
        pg_cursor.execute("SELECT COUNT(*) FROM participants")
        participants_count = pg_cursor.fetchone()[0]
        print(f"📊 Participants in Supabase: {participants_count}")
        
        # Get certificates from SQLite
        sqlite_cursor.execute("SELECT COUNT(*) FROM certificates")
        total_certificates = sqlite_cursor.fetchone()[0]
        print(f"📊 Certificates in SQLite: {total_certificates}")
        
        if total_certificates == 0:
            print("⏭️  No certificates to migrate")
            return {'migrated': 0, 'skipped': 0, 'final_count': 0}
        
        # Get SQLite column names for certificates
        sqlite_cursor.execute("PRAGMA table_info(certificates)")
        sqlite_columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Get Supabase column names for certificates
        pg_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'certificates' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        supabase_columns = [row[0] for row in pg_cursor.fetchall()]
        
        # Find matching columns
        common_columns = [col for col in sqlite_columns if col in supabase_columns]
        print(f"📋 Migrating columns: {common_columns}")
        
        # Get all certificates data
        sqlite_cursor.execute("SELECT * FROM certificates ORDER BY id")
        certificates = sqlite_cursor.fetchall()
        
        migrated = 0
        skipped = 0
        errors = []
        
        print(f"\n📦 Processing {len(certificates)} certificates...")
        
        for idx, certificate_row in enumerate(certificates):
            try:
                # Create certificate dict
                certificate_dict = dict(zip(sqlite_columns, certificate_row))
                
                # Extract values for common columns and apply conversions
                values = []
                for col in common_columns:
                    value = certificate_dict.get(col)
                    
                    # Convert boolean fields
                    if col == 'email_sent':
                        value = bool(value) if value is not None else False
                    
                    # Handle empty timestamp strings
                    elif col in ['issued_date', 'email_sent_date'] and value == '':
                        value = None
                    
                    values.append(value)
                
                # Create INSERT query with upsert
                placeholders = ', '.join(['%s'] * len(common_columns))
                columns_str = ', '.join(common_columns)
                
                upsert_query = f"""
                    INSERT INTO certificates ({columns_str}) 
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO UPDATE SET
                        participant_id = EXCLUDED.participant_id,
                        certificate_number = EXCLUDED.certificate_number,
                        issued_date = EXCLUDED.issued_date,
                        status = EXCLUDED.status,
                        email_sent = EXCLUDED.email_sent,
                        email_sent_date = EXCLUDED.email_sent_date
                """
                
                # Execute
                pg_cursor.execute(upsert_query, values)
                
                if pg_cursor.rowcount > 0:
                    migrated += 1
                    if migrated % 10 == 0:
                        print(f"   📈 Progress: {migrated}/{len(certificates)}")
                else:
                    skipped += 1
                    
            except Exception as e:
                error_str = str(e)
                if "foreign key constraint" in error_str:
                    participant_id = certificate_dict.get('participant_id')
                    print(f"   ⚠️  Certificate {certificate_dict.get('id')}: participant {participant_id} not found")
                elif error_str not in errors:
                    errors.append(error_str)
                    print(f"   ⚠️  Error: {error_str[:80]}...")
                
                skipped += 1
                pg_conn.rollback()
                continue
        
        # Commit all changes
        pg_conn.commit()
        
        # Final verification
        pg_cursor.execute("SELECT COUNT(*) FROM certificates")
        final_count = pg_cursor.fetchone()[0]
        
        print(f"\n✅ CERTIFICATES MIGRATION COMPLETED!")
        print(f"   ➕ Migrated: {migrated}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   📊 Total certificates in Supabase: {final_count}")
        
        if errors:
            print(f"   📊 Encountered {len(errors)} unique error types")
        
        # Sample verification
        print(f"\n🔍 SAMPLE VERIFICATION:")
        pg_cursor.execute("""
            SELECT c.id, c.certificate_number, p.name, p.email 
            FROM certificates c 
            JOIN participants p ON c.participant_id = p.id 
            ORDER BY c.id LIMIT 5
        """)
        sample_certificates = pg_cursor.fetchall()
        
        for cert_id, cert_number, participant_name, participant_email in sample_certificates:
            print(f"   {cert_id}: {cert_number} → {participant_name} ({participant_email})")
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        return {
            'migrated': migrated,
            'skipped': skipped,
            'final_count': final_count,
            'errors': len(errors)
        }
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return None

def main():
    print("🎯 CERTIFICATES MIGRATION")
    print("=" * 60)
    
    # Prerequisites check
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database not found: {SQLITE_DB}")
        return
    
    if not POSTGRES_URL:
        print("❌ DATABASE_URL not set")
        return
    
    # Run migration
    results = migrate_certificates()
    
    if results:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Certificates migration completed")
        print(f"📊 Final status: {results['final_count']} certificates in Supabase")
        
        if results['migrated'] > 0:
            print(f"✅ Successfully migrated {results['migrated']} certificates")
        
        if results['skipped'] > 0:
            print(f"⚠️  Skipped {results['skipped']} certificates (duplicates or missing participants)")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Verify certificate data in Supabase dashboard")
        print(f"   2. Test Flask app end-to-end functionality")
        print(f"   3. Check certificate generation and email features")
        
    else:
        print("❌ Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    main()