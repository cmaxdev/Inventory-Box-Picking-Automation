#!/usr/bin/env python3
"""
Password Manager for Inventory Box Picking System
Allows changing the password and viewing status
"""

import sys
from password_auth import auth

def show_status():
    """Show password protection status"""
    info = auth.get_activation_info()
    
    print("Password Protection Status")
    print("=" * 40)
    print(f"Activation Date: {info['activation_date'].strftime('%B %d, %Y')}")
    print(f"Current Date: {info['current_date'].strftime('%B %d, %Y')}")
    print(f"Status: {'ACTIVE' if info['is_required'] else 'INACTIVE'}")
    print(f"Message: {info['message']}")
    
    if info['is_required']:
        print("\nPassword protection is currently ACTIVE")
    else:
        print(f"\nPassword protection will be activated in {info['days_until_activation']} days")

def change_password():
    """Change the password"""
    print("Change Password")
    print("=" * 20)
    
    # Check if password is required
    if auth.is_password_required():
        current_password = input("Enter current password: ")
        if not auth.verify_password(current_password):
            print("Invalid current password!")
            return False
    else:
        print("Password protection is not yet active")
        current_password = "inventory2025"  # Default password
    
    new_password = input("Enter new password: ")
    confirm_password = input("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords do not match!")
        return False
    
    if len(new_password) < 6:
        print("Password must be at least 6 characters long!")
        return False
    
    if auth.change_password(current_password, new_password):
        print("Password changed successfully!")
        return True
    else:
        print("Failed to change password!")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Password Manager for Inventory Box Picking System")
        print("=" * 50)
        print("Usage:")
        print("  python password_manager.py status    - Show password status")
        print("  python password_manager.py change    - Change password")
        print("  python password_manager.py test      - Test password")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "change":
        change_password()
    elif command == "test":
        if auth.is_password_required():
            password = input("Enter password to test: ")
            if auth.verify_password(password):
                print("Password is correct!")
            else:
                print("Password is incorrect!")
        else:
            print("Password protection is not yet active")
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, change, test")

if __name__ == "__main__":
    main()
