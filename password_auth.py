"""
Password Authentication Module
Password protection becomes active from October 25, 2025
"""

import datetime
import hashlib
import base64
from typing import Optional

class PasswordAuth:
    def __init__(self):
        # Password activation date: October 25, 2025
        self.activation_date = datetime.date(2025, 10, 25)
        
        # Default password hash (password: "inventory2025")
        # This is a simple hash for demonstration - in production, use stronger encryption
        self.password_hash = "40f37fabeb8f358405b9387edea6b0257d67e96e6953eb6bca38e2ba087fb28f"
        
    def is_password_required(self) -> bool:
        """Check if password protection is currently required"""
        current_date = datetime.date.today()
        return current_date >= self.activation_date
    
    def verify_password(self, entered_password: str) -> bool:
        """Verify the entered password against the stored hash"""
        if not self.is_password_required():
            return True  # No password required before activation date
        
        # Hash the entered password
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()
        return entered_hash == self.password_hash
    
    def get_activation_info(self) -> dict:
        """Get information about password activation"""
        current_date = datetime.date.today()
        days_until_activation = (self.activation_date - current_date).days
        
        return {
            'activation_date': self.activation_date,
            'current_date': current_date,
            'is_required': self.is_password_required(),
            'days_until_activation': max(0, days_until_activation),
            'message': self._get_activation_message(days_until_activation)
        }
    
    def _get_activation_message(self, days_until: int) -> str:
        """Get appropriate message based on activation status"""
        if days_until <= 0:
            return "Password protection is now ACTIVE"
        elif days_until <= 7:
            return f"Password protection will be activated in {days_until} days"
        elif days_until <= 30:
            return f"Password protection will be activated in {days_until} days"
        else:
            return f"Password protection will be activated on {self.activation_date.strftime('%B %d, %Y')}"
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the password (requires current password)"""
        if not self.verify_password(old_password):
            return False
        
        # Hash and store new password
        self.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        return True

# Global instance
auth = PasswordAuth()
