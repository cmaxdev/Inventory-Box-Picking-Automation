"""
Password Dialog for Desktop UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
from password_auth import auth
import datetime

class PasswordDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.dialog = None
        
    def show(self):
        """Show the password dialog"""
        if not auth.is_password_required():
            return True  # No password required yet
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Password Required")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.parent.wait_window(self.dialog)
        
        return self.result
    
    def _create_dialog(self):
        """Create the password dialog content"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🔒 Password Protection Active", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Info message
        info_text = "This application is now password protected.\nPlease enter the password to continue."
        info_label = ttk.Label(main_frame, text=info_text, justify="center")
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Password label and entry
        ttk.Label(main_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(main_frame, show="*", width=30)
        self.password_entry.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        self.password_entry.focus()
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2)
        
        # OK button
        ok_button = ttk.Button(buttons_frame, text="OK", command=self._on_ok)
        ok_button.grid(row=0, column=0, padx=(0, 10))
        
        # Cancel button
        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self._on_cancel)
        cancel_button.grid(row=0, column=1)
        
        # Bind Enter key to OK
        self.password_entry.bind('<Return>', lambda e: self._on_ok())
        
        # Bind Escape key to Cancel
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
    def _on_ok(self):
        """Handle OK button click"""
        password = self.password_entry.get()
        
        if auth.verify_password(password):
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showerror("Invalid Password", "The password you entered is incorrect.\nPlease try again.")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()

class PasswordStatusDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        
    def show(self):
        """Show password status information"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Password Protection Status")
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create the status dialog content"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🔐 Password Protection Status", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Get activation info
        info = auth.get_activation_info()
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Current Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        if info['is_required']:
            status_text = "🟢 ACTIVE - Password protection is currently enabled"
            status_color = "red"
        else:
            status_text = f"🟡 INACTIVE - Will be activated in {info['days_until_activation']} days"
            status_color = "orange"
        
        status_label = ttk.Label(status_frame, text=status_text, foreground=status_color)
        status_label.grid(row=0, column=0)
        
        # Details frame
        details_frame = ttk.LabelFrame(main_frame, text="Details", padding="10")
        details_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        details_text = f"""Activation Date: {info['activation_date'].strftime('%B %d, %Y')}
Current Date: {info['current_date'].strftime('%B %d, %Y')}
Status: {'Password Required' if info['is_required'] else 'Not Yet Required'}
Message: {info['message']}"""
        
        details_label = ttk.Label(details_frame, text=details_text, justify="left")
        details_label.grid(row=0, column=0)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=self.dialog.destroy)
        close_button.grid(row=3, column=0, pady=(10, 0))
