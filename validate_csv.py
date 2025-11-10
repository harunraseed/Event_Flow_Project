#!/usr/bin/env python3
"""
CSV Format Validator for Participant Upload
"""
import csv
import io

def validate_csv_format(file_content):
    """Validate and show CSV format details"""
    try:
        # Parse CSV
        stream = io.StringIO(file_content, newline=None)
        csv_reader = csv.DictReader(stream)
        fieldnames = csv_reader.fieldnames
        
        print("🔍 CSV Analysis:")
        print(f"📋 Detected columns: {fieldnames}")
        
        # Check for expected columns
        name_columns = ['name', 'Name', 'NAME', 'participant_name', 'Participant Name', 'full_name', 'Full Name']
        email_columns = ['email', 'Email', 'EMAIL', 'email_address', 'Email Address', 'e-mail', 'E-mail']
        
        name_found = any(col.strip() in name_columns for col in fieldnames)
        email_found = any(col.strip() in email_columns for col in fieldnames)
        
        print(f"✅ Name column found: {name_found}")
        print(f"✅ Email column found: {email_found}")
        
        if name_found and email_found:
            print("✅ CSV format looks good!")
        else:
            print("❌ CSV format issue detected!")
            print("📝 Expected format:")
            print("   name,email")
            print("   John Doe,john@example.com")
            print("   Jane Smith,jane@example.com")
        
        # Show first few rows
        stream.seek(0)
        csv_reader = csv.DictReader(stream)
        print("\n📄 First few rows:")
        for i, row in enumerate(csv_reader):
            if i >= 3:  # Show only first 3 rows
                break
            print(f"   Row {i+2}: {row}")
            
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

# Test with sample CSV
if __name__ == '__main__':
    sample_csv = """name,email
John Doe,john@example.com
Jane Smith,jane@example.com
Bob Johnson,bob@example.com"""
    
    print("Testing with sample CSV:")
    validate_csv_format(sample_csv)