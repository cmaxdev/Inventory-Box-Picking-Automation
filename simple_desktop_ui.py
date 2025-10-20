#!/usr/bin/env python3
"""
Simple Desktop UI for Inventory Box Picking System

A clean, user-friendly desktop application for processing inventory orders.

Author: AI Assistant
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from datetime import datetime
from client_order_processor import ClientOrderProcessor


class SimpleInventoryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Inventory Box Picking System")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Center the window
        self.center_window()
        
        # Initialize the order processor
        self.order_processor = ClientOrderProcessor()
        self.order_processor.load_client_orders_history()
        
        # Create the GUI
        self.create_widgets()
        
        # Add some sample data for quick testing
        self.set_sample_data()
    
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
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="📦 Inventory Box Picking System", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Automated box selection based on client requirements", 
                                  font=('Arial', 10), foreground='gray')
        subtitle_label.pack(pady=(0, 20))
        
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
        help_text = "Example: 100% Woman, 50% DRESS, 50% TROUSERS (Available: Woman | DRESS, OVERALL, TROUSERS, LEGGINGS, SKIRT, BIB OVERALL)"
        help_label = ttk.Label(input_frame, text=help_text, font=('Arial', 9), foreground='gray')
        help_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Inventory File Selection
        ttk.Label(input_frame, text="Inventory File:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        self.inventory_file_var = tk.StringVar(value="sample.xlsx")
        inventory_file_entry = ttk.Entry(file_frame, textvariable=self.inventory_file_var, 
                                        font=('Arial', 11))
        inventory_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_inventory_file)
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        create_sample_button = ttk.Button(file_frame, text="Create Sample", command=self.create_sample_inventory)
        create_sample_button.pack(side=tk.RIGHT)
        
        # Options
        self.require_complete_info_var = tk.BooleanVar(value=True)
        complete_info_check = ttk.Checkbutton(input_frame, text="Require complete product information", 
                                            variable=self.require_complete_info_var)
        complete_info_check.pack(anchor=tk.W, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.process_button = ttk.Button(button_frame, text="🚀 Process Order", 
                                       command=self.process_order)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.history_button = ttk.Button(button_frame, text="📊 View History", 
                                       command=self.view_history)
        self.history_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear Form", 
                                     command=self.clear_form)
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to process orders")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var, 
                                  font=('Arial', 10, 'bold'))
        progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="📋 Order Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80,
                                                     font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.results_text.tag_configure('success', foreground='green', font=('Consolas', 9, 'bold'))
        self.results_text.tag_configure('error', foreground='red', font=('Consolas', 9, 'bold'))
        self.results_text.tag_configure('header', foreground='blue', font=('Consolas', 10, 'bold'))
        self.results_text.tag_configure('info', foreground='black', font=('Consolas', 9))
        
        # Focus on first entry
        client_name_entry.focus()
    
    def browse_inventory_file(self):
        """Browse for inventory file."""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="Select Inventory File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ],
            initialdir="data/inventory"
        )
        
        if filename:
            self.inventory_file_var.set(filename)
    
    def create_sample_inventory(self):
        """Create a sample inventory file."""
        try:
            import pandas as pd
            import os
            
            # Create data/inventory directory if it doesn't exist
            os.makedirs("data/inventory", exist_ok=True)
            
            # Create sample inventory data with correct structure
            sample_data = []
            sections = ['Women', 'Men', 'Children']
            descriptions = ['Accessories', 'Trousers', 'Tops']
            families = ['Fashion', 'Casual', 'Formal']
            countries = ['France', 'Italy', 'Spain']
            seasons = ['Spring', 'Summer', 'Fall', 'Winter']
            
            for i in range(1, 101):  # Create 100 sample items
                section = sections[i % len(sections)]
                description = descriptions[i % len(descriptions)]
                family = families[i % len(families)]
                country = countries[i % len(countries)]
                season = seasons[i % len(seasons)]
                model = f"MOC{i:04d}"
                units = 5 + (i % 25)  # Random units between 5 and 29
                price = 10.0 + (i % 50)  # Random price between 10 and 60
                
                sample_data.append({
                    'CONTENEUR': f'CONT{i:03d}',
                    'CARTONS': f'CART{i:03d}',
                    'BARCODE': f'1234567890{i:03d}',
                    'SEASON': season,
                    'SECTION': section,
                    'PAYS': country,
                    'DESCRIPTION': description,
                    'FAMILLIE': family,
                    'DETAIL': f'Detail {i}',
                    'NOTES': f'Notes for item {i}',
                    'COMPOSITION': 'Cotton 100%',
                    'TARIFAIRE': f'HS{i:06d}',
                    'PVP': price,
                    'PVP total': price * units,
                    'POIDS': 0.5 + (i % 10) * 0.1,
                    'SAISON INT.': season,
                    'UNITES': units,
                    'MOCACO': model,
                    'RESERVATION': '',
                    'G. TARIF': f'TARIF{i % 10}'
                })
            
            # Create DataFrame and save to Excel
            df = pd.DataFrame(sample_data)
            sample_file = "data/inventory/sample_inventory.xlsx"
            df.to_excel(sample_file, index=False)
            
            # Update the file path in the UI
            self.inventory_file_var.set(sample_file)
            
            messagebox.showinfo("Success", f"Sample inventory file created successfully!\n\nFile saved to: {sample_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creating sample inventory file:\n{str(e)}")
    
    def set_sample_data(self):
        """Set sample data for quick testing."""
        self.client_name_var.set("Test Client")
        self.total_units_var.set("1000")
        self.requirements_var.set("100% Woman, 50% DRESS, 50% TROUSERS")
    
    def validate_input(self):
        """Validate user input."""
        client_name = self.client_name_var.get().strip()
        total_units_str = self.total_units_var.get().strip()
        requirements = self.requirements_var.get().strip()
        
        if not client_name:
            messagebox.showerror("Error", "Please enter a client name.")
            return False
        
        if not total_units_str:
            messagebox.showerror("Error", "Please enter total units.")
            return False
        
        try:
            units = int(total_units_str.replace(',', ''))
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
        """Process the client order."""
        if not self.validate_input():
            return
        
        # Disable buttons and start progress
        self.process_button.config(state='disabled')
        self.history_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Processing order...")
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "🔄 Processing order...\n", 'info')
        self.root.update()
        
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
            require_complete_info = self.require_complete_info_var.get()
            
            # Get inventory file path
            inventory_file = self.inventory_file_var.get().strip()
            if not inventory_file:
                inventory_file = "sample.xlsx"
            
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
        
        # Clear processing message
        self.results_text.delete(1.0, tk.END)
        
        if result['success']:
            self.progress_var.set("Order completed successfully!")
            
            # Display results
            self.results_text.insert(tk.END, "✅ ORDER COMPLETED SUCCESSFULLY!\n\n", 'success')
            
            results = result['results']
            order_summary = result['order_summary']
            
            # Basic info
            self.results_text.insert(tk.END, "📋 ORDER SUMMARY\n", 'header')
            self.results_text.insert(tk.END, f"Client: {order_summary['client_name']}\n", 'info')
            self.results_text.insert(tk.END, f"Requested Units: {order_summary['total_units']:,}\n", 'info')
            self.results_text.insert(tk.END, f"Selected Boxes: {results['total_boxes']}\n", 'info')
            self.results_text.insert(tk.END, f"Actual Units: {results['total_units']:,}\n", 'info')
            # Calculate efficiency if target units is available
            if 'target_units' in results and results['target_units'] > 0:
                efficiency = (results['total_units'] / results['target_units']) * 100
                self.results_text.insert(tk.END, f"Efficiency: {efficiency:.1f}%\n\n", 'info')
            else:
                self.results_text.insert(tk.END, f"Efficiency: N/A\n\n", 'info')
            
            # Section distribution
            self.results_text.insert(tk.END, "📊 SECTION DISTRIBUTION\n", 'header')
            section_summary = results['section_summary']
            for section in section_summary.index:
                actual_pct = section_summary.loc[section, 'percentage']
                boxes = section_summary.loc[section, 'box_count']
                self.results_text.insert(tk.END, f"{section}: {actual_pct:.1f}% ({boxes} boxes)\n", 'info')
            
            self.results_text.insert(tk.END, "\n", 'info')
            
            # Description distribution
            self.results_text.insert(tk.END, "🏷️ DESCRIPTION DISTRIBUTION\n", 'header')
            description_summary = results['description_summary']
            for desc in description_summary.index:
                actual_pct = description_summary.loc[desc, 'percentage']
                boxes = description_summary.loc[desc, 'box_count']
                self.results_text.insert(tk.END, f"{desc}: {actual_pct:.1f}% ({boxes} boxes)\n", 'info')
            
            # Output file info
            if order_summary['output_file'] and order_summary['output_file'] != 'N/A':
                import os
                full_path = os.path.abspath(order_summary['output_file'])
                self.results_text.insert(tk.END, f"\n📁 Results saved to: {full_path}\n", 'info')
                self.results_text.insert(tk.END, f"📋 Copy this path: {full_path}\n", 'info')
                
                # Show success message with copyable path
                messagebox.showinfo("Success", f"Order completed successfully!\n\nResults saved to:\n{full_path}\n\nPath copied to clipboard!")
                
                # Copy path to clipboard
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(full_path)
                except:
                    pass
            
        else:
            self.progress_var.set("Order processing failed")
            
            # Display error
            self.results_text.insert(tk.END, "❌ ORDER FAILED\n\n", 'error')
            self.results_text.insert(tk.END, f"Error: {result['error']}\n", 'error')
            
            messagebox.showerror("Error", f"Order processing failed:\n{result['error']}")
        
        # Scroll to top
        self.results_text.see(1.0)
    
    def view_history(self):
        """View order history."""
        try:
            # Create a new window for history
            history_window = tk.Toplevel(self.root)
            history_window.title("📊 Order History")
            history_window.geometry("800x600")
            
            # Center the window
            history_window.update_idletasks()
            x = (history_window.winfo_screenwidth() // 2) - (400)
            y = (history_window.winfo_screenheight() // 2) - (300)
            history_window.geometry(f'800x600+{x}+{y}')
            
            # Create history display
            history_frame = ttk.Frame(history_window, padding="20")
            history_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(history_frame, text="📊 Order History", 
                     font=('Arial', 14, 'bold')).pack(pady=(0, 10))
            
            # Load and display history
            if os.path.exists(self.order_processor.client_orders_file):
                history_df = self.order_processor.load_client_orders_history()
                if not history_df.empty:
                    # Create a simple text display of history
                    history_text = scrolledtext.ScrolledText(history_frame, height=25, width=80,
                                                           font=('Consolas', 9))
                    history_text.pack(fill=tk.BOTH, expand=True)
                    
                    # Display history
                    history_text.insert(tk.END, "Order History:\n\n", 'header')
                    for _, row in history_df.iterrows():
                        history_text.insert(tk.END, f"Date: {row['order_date']}\n", 'info')
                        history_text.insert(tk.END, f"Client: {row['client_name']}\n", 'info')
                        history_text.insert(tk.END, f"Units: {row['total_units']:,}\n", 'info')
                        history_text.insert(tk.END, f"Requirements: {row['requirements']}\n", 'info')
                        history_text.insert(tk.END, f"Output: {row['output_file']}\n", 'info')
                        history_text.insert(tk.END, "-" * 50 + "\n\n", 'info')
                else:
                    ttk.Label(history_frame, text="No order history found.", 
                             font=('Arial', 12)).pack(pady=50)
            else:
                ttk.Label(history_frame, text="No order history found.", 
                         font=('Arial', 12)).pack(pady=50)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading history:\n{str(e)}")
    
    def clear_form(self):
        """Clear the form."""
        self.client_name_var.set("")
        self.total_units_var.set("")
        self.requirements_var.set("")
        self.inventory_file_var.set("sample.xlsx")
        self.require_complete_info_var.set(True)
        self.results_text.delete(1.0, tk.END)
        self.progress_var.set("Ready to process orders")


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = SimpleInventoryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
