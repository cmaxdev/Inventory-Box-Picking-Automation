#!/usr/bin/env python3
"""
Desktop GUI for Inventory Box Picking System

A simple desktop application using tkinter for processing client orders.

Author: AI Assistant
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os
from datetime import datetime
from client_order_processor import ClientOrderProcessor


class InventoryBoxPickingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Box Picking System")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Initialize the order processor
        self.order_processor = ClientOrderProcessor()
        self.order_processor.load_client_orders_history()
        
        # Create the GUI
        self.create_widgets()
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and arrange the GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="📦 Inventory Box Picking System", 
                               font=('Arial', 18, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Automated box selection based on client requirements", 
                                  font=('Arial', 10), foreground='gray')
        subtitle_label.pack()
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Order Information", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Client Name
        ttk.Label(input_frame, text="Client Name:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.client_name_var = tk.StringVar()
        client_name_entry = ttk.Entry(input_frame, textvariable=self.client_name_var, 
                                     font=('Arial', 11), width=50)
        client_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Total Units
        ttk.Label(input_frame, text="Total Units:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.total_units_var = tk.StringVar()
        total_units_entry = ttk.Entry(input_frame, textvariable=self.total_units_var, 
                                     font=('Arial', 11), width=50)
        total_units_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Requirements
        ttk.Label(input_frame, text="Requirements:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.requirements_var = tk.StringVar()
        requirements_entry = ttk.Entry(input_frame, textvariable=self.requirements_var, 
                                      font=('Arial', 11), width=50)
        requirements_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Requirements help text
        help_text = "Example: 60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers"
        help_label = ttk.Label(input_frame, text=help_text, font=('Arial', 9), foreground='gray')
        help_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Options section
        options_frame = ttk.Frame(input_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        self.require_complete_info_var = tk.BooleanVar(value=True)
        complete_info_check = ttk.Checkbutton(options_frame, text="Require complete product information", 
                                            variable=self.require_complete_info_var)
        complete_info_check.pack(side=tk.LEFT)
        
        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Main action buttons
        self.process_button = ttk.Button(button_frame, text="🚀 Process Order", 
                                       command=self.process_order, style='Accent.TButton')
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.history_button = ttk.Button(button_frame, text="📊 View History", 
                                       command=self.view_history)
        self.history_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear Form", 
                                     command=self.clear_form)
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to process orders")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, 
                                  font=('Arial', 10, 'bold'))
        progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="📋 Order Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=80,
                                                     font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for better formatting
        self.results_text.tag_configure('success', foreground='green', font=('Consolas', 9, 'bold'))
        self.results_text.tag_configure('error', foreground='red', font=('Consolas', 9, 'bold'))
        self.results_text.tag_configure('header', foreground='blue', font=('Consolas', 10, 'bold'))
        self.results_text.tag_configure('info', foreground='black', font=('Consolas', 9))
        self.results_text.tag_configure('highlight', background='lightyellow')
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, 
                              anchor=tk.W, font=('Arial', 9))
        status_bar.pack(fill=tk.X)
        
        # Focus on first entry
        client_name_entry.focus()
    
    def browse_inventory_file(self):
        """Browse for inventory file."""
        filename = filedialog.askopenfilename(
            title="Select Inventory File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.inventory_file_var.set(filename)
    
    def clear_form(self):
        """Clear all form fields."""
        self.client_name_var.set("")
        self.total_units_var.set("")
        self.requirements_var.set("")
        self.inventory_file_var.set("data/inventory/sample_inventory.xlsx")
        self.require_complete_info_var.set(True)
        self.results_text.delete(1.0, tk.END)
        self.progress_var.set("Ready")
        self.status_var.set("Form cleared")
    
    def validate_input(self):
        """Validate user input."""
        client_name = self.client_name_var.get().strip()
        total_units = self.total_units_var.get().strip()
        requirements = self.requirements_var.get().strip()
        
        if not client_name:
            messagebox.showerror("Error", "Please enter a client name.")
            return False
        
        if not total_units:
            messagebox.showerror("Error", "Please enter total units.")
            return False
        
        try:
            units = int(total_units.replace(',', ''))
            if units <= 0:
                messagebox.showerror("Error", "Total units must be greater than 0.")
                return False
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for total units.")
            return False
        
        if not requirements:
            messagebox.showerror("Error", "Please enter requirements.")
            return False
        
        return True
    
    def process_order(self):
        """Process the client order in a separate thread."""
        if not self.validate_input():
            return
        
        # Disable buttons and start progress
        self.process_button.config(state='disabled')
        self.history_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Processing order...")
        self.status_var.set("Processing order for " + self.client_name_var.get())
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self._process_order_thread)
        thread.daemon = True
        thread.start()
    
    def _process_order_thread(self):
        """Process order in a separate thread."""
        try:
            # Get form data
            client_name = self.client_name_var.get().strip()
            total_units = int(self.total_units_var.get().replace(',', ''))
            requirements = self.requirements_var.get().strip()
            inventory_file = self.inventory_file_var.get()
            require_complete_info = self.require_complete_info_var.get()
            
            # Process the order
            result = self.order_processor.process_client_order(
                client_name=client_name,
                total_units=total_units,
                requirements=requirements,
                inventory_file=inventory_file,
                require_complete_info=require_complete_info
            )
            
            # Update UI in main thread
            self.root.after(0, self._update_results, result)
            
        except Exception as e:
            # Update UI with error in main thread
            self.root.after(0, self._update_results, {'success': False, 'error': str(e)})
    
    def _update_results(self, result):
        """Update the results display."""
        # Stop progress bar and re-enable buttons
        self.progress_bar.stop()
        self.process_button.config(state='normal')
        self.history_button.config(state='normal')
        
        if result['success']:
            self.progress_var.set("Order completed successfully!")
            self.status_var.set("Order completed for " + self.client_name_var.get())
            
            # Display results
            self.results_text.insert(tk.END, "SUCCESS: ORDER COMPLETED!\n", 'success')
            self.results_text.insert(tk.END, "=" * 50 + "\n", 'header')
            
            results = result['results']
            order_summary = result['order_summary']
            
            # Basic info
            self.results_text.insert(tk.END, f"Client: {order_summary['client_name']}\n", 'info')
            self.results_text.insert(tk.END, f"Date: {order_summary['order_date']}\n", 'info')
            self.results_text.insert(tk.END, f"Requested Units: {order_summary['total_units']:,}\n", 'info')
            self.results_text.insert(tk.END, f"Selected Boxes: {results['total_boxes']}\n", 'info')
            self.results_text.insert(tk.END, f"Actual Units: {results['total_units']:,}\n", 'info')
            self.results_text.insert(tk.END, "\n", 'info')
            
            # Section distribution
            self.results_text.insert(tk.END, "SECTION DISTRIBUTION:\n", 'header')
            section_summary = results['section_summary']
            for section in section_summary.index:
                actual_pct = section_summary.loc[section, 'percentage']
                boxes = section_summary.loc[section, 'box_count']
                self.results_text.insert(tk.END, f"  {section}: {actual_pct:.1f}% ({boxes} boxes)\n", 'info')
            
            self.results_text.insert(tk.END, "\n", 'info')
            
            # Description distribution
            self.results_text.insert(tk.END, "DESCRIPTION DISTRIBUTION:\n", 'header')
            description_summary = results['description_summary']
            for desc in description_summary.index:
                actual_pct = description_summary.loc[desc, 'percentage']
                boxes = description_summary.loc[desc, 'box_count']
                self.results_text.insert(tk.END, f"  {desc}: {actual_pct:.1f}% ({boxes} boxes)\n", 'info')
            
            self.results_text.insert(tk.END, "\n", 'info')
            
            # Compliance summary
            self.results_text.insert(tk.END, "COMPLIANCE SUMMARY:\n", 'header')
            self.results_text.insert(tk.END, order_summary['compliance_summary'] + "\n", 'info')
            
            # Output file info
            if order_summary['output_file'] and order_summary['output_file'] != 'N/A':
                self.results_text.insert(tk.END, f"\nResults saved to: {order_summary['output_file']}\n", 'info')
            
            messagebox.showinfo("Success", f"Order completed successfully for {order_summary['client_name']}!")
            
        else:
            self.progress_var.set("Order failed!")
            self.status_var.set("Order failed")
            
            self.results_text.insert(tk.END, "ERROR: ORDER FAILED!\n", 'error')
            self.results_text.insert(tk.END, "=" * 50 + "\n", 'header')
            self.results_text.insert(tk.END, f"Error: {result['error']}\n", 'error')
            
            messagebox.showerror("Error", f"Order failed: {result['error']}")
    
    def view_history(self):
        """View order history in a new window."""
        try:
            orders = self.order_processor.file_manager.get_client_orders()
            
            # Create new window
            history_window = tk.Toplevel(self.root)
            history_window.title("Order History")
            history_window.geometry("900x500")
            history_window.resizable(True, True)
            
            # Create treeview for orders
            frame = ttk.Frame(history_window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Order History", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            
            # Create treeview
            columns = ('Date', 'Client', 'Units', 'Boxes', 'Actual Units', 'Section %', 'Description %')
            tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
            
            # Define headings
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack treeview and scrollbar
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add orders to treeview
            if not orders.empty:
                recent_orders = orders.tail(20)  # Show last 20 orders
                for _, order in recent_orders.iterrows():
                    tree.insert('', tk.END, values=(
                        order['order_date'],
                        order['client_name'],
                        f"{order['total_units']:,}",
                        order['selected_boxes'],
                        f"{order['actual_units']:,}",
                        order['section_percentages'][:30] + "..." if len(str(order['section_percentages'])) > 30 else order['section_percentages'],
                        order['description_percentages'][:30] + "..." if len(str(order['description_percentages'])) > 30 else order['description_percentages']
                    ))
            else:
                tree.insert('', tk.END, values=("No orders found", "", "", "", "", "", ""))
            
            # Close button
            ttk.Button(frame, text="Close", command=history_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {str(e)}")


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme
    
    # Create the application
    app = InventoryBoxPickingGUI(root)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
