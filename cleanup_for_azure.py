#!/usr/bin/env python3
"""
Clean up local SQLite files after successful Supabase migration
This script removes the SQLite database files from the instance directory
since we've successfully migrated to Supabase PostgreSQL.
"""

import os
import shutil
from pathlib import Path

def cleanup_sqlite_files():
    """Remove SQLite database files after successful migration to Supabase"""
    
    instance_dir = Path("instance")
    sqlite_files = []
    backup_dir = Path("backup/sqlite_backup")
    
    print("🔍 Checking for SQLite files to clean up...")
    
    if instance_dir.exists():
        # Find all SQLite files
        for file_path in instance_dir.iterdir():
            if file_path.suffix in ['.db', '.sqlite', '.sqlite3']:
                sqlite_files.append(file_path)
        
        if sqlite_files:
            print(f"\n📁 Found {len(sqlite_files)} SQLite files:")
            for file_path in sqlite_files:
                size = file_path.stat().st_size / 1024  # KB
                print(f"  - {file_path.name} ({size:.1f} KB)")
            
            # Ask for confirmation
            response = input("\n⚠️  Do you want to backup and remove these files? (y/N): ")
            
            if response.lower() == 'y':
                # Create backup directory
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"\n📦 Creating backup in {backup_dir}/")
                
                # Backup and remove files
                for file_path in sqlite_files:
                    backup_path = backup_dir / file_path.name
                    shutil.copy2(file_path, backup_path)
                    print(f"  ✅ Backed up: {file_path.name}")
                    
                    file_path.unlink()
                    print(f"  🗑️  Removed: {file_path.name}")
                
                # Remove instance directory if empty
                try:
                    if not any(instance_dir.iterdir()):
                        instance_dir.rmdir()
                        print(f"\n📁 Removed empty instance directory")
                except:
                    pass
                
                print(f"\n✅ Cleanup complete! SQLite files backed up to: {backup_dir}")
                print("   Your app now runs entirely on Supabase PostgreSQL 🎉")
                
            else:
                print("\n❌ Cleanup cancelled. SQLite files remain.")
        else:
            print("✅ No SQLite files found. Instance directory is clean!")
    else:
        print("✅ No instance directory found. Already clean!")

def check_azure_readiness():
    """Check if the app is ready for Azure deployment"""
    
    print("\n🔍 Checking Azure deployment readiness...")
    
    issues = []
    recommendations = []
    
    # Check for Azure Storage service
    if Path("azure_storage.py").exists():
        print("✅ Azure Storage service created")
    else:
        issues.append("❌ Azure Storage service missing")
    
    # Check for Azure dependencies
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        content = requirements_file.read_text()
        if "azure-storage-blob" in content:
            print("✅ Azure Storage SDK in requirements.txt")
        else:
            issues.append("❌ Azure Storage SDK not in requirements.txt")
    
    # Check for environment template
    if Path(".env.azure.template").exists():
        print("✅ Azure environment template created")
    else:
        issues.append("❌ Azure environment template missing")
    
    # Check for local file dependencies
    local_deps = []
    for path in ["uploads/", "static/uploads/", "instance/"]:
        if Path(path).exists():
            local_deps.append(path)
    
    if local_deps:
        recommendations.append(f"🔄 Local directories found: {', '.join(local_deps)}")
        recommendations.append("   Configure Azure Blob Storage before deployment")
    
    # Summary
    if issues:
        print(f"\n⚠️  Issues to resolve ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")
    
    if recommendations:
        print(f"\n💡 Recommendations ({len(recommendations)}):")
        for rec in recommendations:
            print(f"  {rec}")
    
    if not issues and not recommendations:
        print("\n🎉 Your app is ready for Azure deployment!")
        
    return len(issues) == 0

if __name__ == "__main__":
    print("🧹 Event Ticketing App - Post-Migration Cleanup")
    print("=" * 50)
    
    # Clean up SQLite files
    cleanup_sqlite_files()
    
    # Check Azure readiness
    azure_ready = check_azure_readiness()
    
    print("\n" + "=" * 50)
    if azure_ready:
        print("🚀 Ready for Azure Web App deployment!")
        print("\nNext steps:")
        print("1. Create Azure Storage Account")
        print("2. Configure environment variables")
        print("3. Deploy to Azure Web App")
        print("4. Test file uploads in production")
    else:
        print("⚠️  Please resolve the issues above before deployment")