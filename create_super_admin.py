#!/usr/bin/env python3
"""
Create Super Admin User Script

This script creates a super admin user for the hire-match-ai system.
Run this script to bootstrap the initial super admin account.

Usage:
    python create_super_admin.py
"""

import sys
import getpass
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import User
from app.services.auth_service import AuthService

def create_super_admin():
    """Create a super admin user interactively"""
    print("🚀 Hire Match AI - Super Admin Setup")
    print("=" * 40)
    
    # Get super admin details
    print("\nEnter details for the super admin account:")
    
    while True:
        email = input("Email: ").strip()
        if email and "@" in email:
            break
        print("Please enter a valid email address.")
    
    while True:
        username = input("Username: ").strip()
        if username and len(username) >= 3:
            break
        print("Username must be at least 3 characters long.")
    
    while True:
        password = getpass.getpass("Password: ")
        if len(password) >= 8:
            confirm_password = getpass.getpass("Confirm password: ")
            if password == confirm_password:
                break
            else:
                print("Passwords don't match. Please try again.")
        else:
            print("Password must be at least 8 characters long.")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if super admin already exists
        existing_super_admin = db.query(User).filter(User.is_super_admin == True).first()
        if existing_super_admin:
            print(f"\n⚠️  Super admin already exists: {existing_super_admin.email}")
            response = input("Do you want to create another super admin? (y/N): ").strip().lower()
            if response != 'y':
                print("Setup cancelled.")
                return
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists.")
            return
        
        # Check if username already exists
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            print(f"❌ Username {username} is already taken.")
            return
        
        # Create super admin user
        hashed_password = AuthService.get_password_hash(password)
        
        super_admin = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_admin=True,
            is_super_admin=True,
            is_active=True
        )
        
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        print(f"\n✅ Super admin created successfully!")
        print(f"   ID: {super_admin.id}")
        print(f"   Email: {super_admin.email}")
        print(f"   Username: {super_admin.username}")
        print(f"   Created: {super_admin.created_at}")
        
        print(f"\n🔑 You can now login with:")
        print(f"   Email/Username: {username}")
        print(f"   Password: [hidden]")
        
        print(f"\n📖 Next steps:")
        print("   1. Start the application: python run.py")
        print("   2. Login with your super admin credentials")
        print("   3. Create OAuth2 clients for API access")
        print("   4. Onboard regular admin users as needed")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating super admin: {e}")
        return
    
    finally:
        db.close()

def main():
    """Main function"""
    try:
        create_super_admin()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
