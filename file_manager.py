#!/usr/bin/env python3
"""
File Manager for Inventory Box Picking System

This module provides utilities for managing files in the organized directory structure.
It integrates with the Excel registry system to provide easy access to files.

Author: AI Assistant
Version: 1.0
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from excel_registry import ExcelRegistry


class FileManager:
    """Manages file operations in the organized directory structure."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.registry = ExcelRegistry(base_path)
        
        # Standard file paths
        self.paths = {
            'inventory': self.base_path / "inventory" / "sample_inventory.xlsx",
            'order_history': self.base_path / "history" / "order_history.xlsx",
            'client_orders_history': self.base_path / "orders" / "client_orders" / "client_orders_history.xlsx",
            'registry': self.base_path / "excel_registry.xlsx"
        }
    
    def get_inventory_file(self) -> str:
        """Get the path to the main inventory file."""
        return str(self.paths['inventory'])
    
    def get_order_history_file(self) -> str:
        """Get the path to the order history file."""
        return str(self.paths['order_history'])
    
    def get_client_orders_history_file(self) -> str:
        """Get the path to the client orders history file."""
        return str(self.paths['client_orders_history'])
    
    def save_client_order_result(self, client_name: str, order_data: Dict) -> str:
        """
        Save client order results to organized directory.
        
        Args:
            client_name: Name of the client
            order_data: Order data dictionary
            
        Returns:
            str: Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"client_order_{client_name}_{timestamp}.xlsx"
        
        # Determine save path
        save_path = self.base_path / "orders" / "client_orders" / filename
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file (assuming order_data contains the Excel data)
        if 'output_file' in order_data and os.path.exists(order_data['output_file']):
            # Move existing file to organized location
            import shutil
            shutil.move(order_data['output_file'], str(save_path))
        else:
            # Create new file
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                if 'selected_boxes' in order_data:
                    order_data['selected_boxes'].to_excel(writer, sheet_name='Selected_Boxes', index=False)
                if 'section_summary' in order_data:
                    order_data['section_summary'].to_excel(writer, sheet_name='Section_Summary')
                if 'description_summary' in order_data:
                    order_data['description_summary'].to_excel(writer, sheet_name='Description_Summary')
                if 'model_summary' in order_data:
                    order_data['model_summary'].to_excel(writer, sheet_name='Model_Summary')
        
        # Register the file
        self.registry.register_file(
            file_path=str(save_path),
            category='client_orders',
            subcategory='processed',
            description=f"Client order results for {client_name}",
            client_name=client_name,
            order_id=timestamp,
            tags=['client_data', 'order_results']
        )
        
        return str(save_path)
    
    def save_selection_result(self, result_type: str, result_data: Dict) -> str:
        """
        Save selection results to organized directory.
        
        Args:
            result_type: Type of selection result
            result_data: Result data dictionary
            
        Returns:
            str: Path to saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{result_type}_{timestamp}.xlsx"
        
        # Determine save path
        save_path = self.base_path / "orders" / "selection_results" / filename
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            if 'selected_boxes' in result_data:
                result_data['selected_boxes'].to_excel(writer, sheet_name='Selected_Boxes', index=False)
            if 'section_summary' in result_data:
                result_data['section_summary'].to_excel(writer, sheet_name='Section_Summary')
            if 'description_summary' in result_data:
                result_data['description_summary'].to_excel(writer, sheet_name='Description_Summary')
            if 'model_summary' in result_data:
                result_data['model_summary'].to_excel(writer, sheet_name='Model_Summary')
        
        # Register the file
        self.registry.register_file(
            file_path=str(save_path),
            category='selection_results',
            subcategory='automated',
            description=f"Automated selection results: {result_type}",
            tags=['automated', 'selection_results']
        )
        
        return str(save_path)
    
    def update_order_history(self, order_data: List[Dict]):
        """
        Update the order history file.
        
        Args:
            order_data: List of order data dictionaries
        """
        history_path = self.paths['order_history']
        
        # Load existing history or create new
        if history_path.exists():
            history_df = pd.read_excel(history_path)
        else:
            history_df = pd.DataFrame(columns=['model', 'total_units_shipped', 'order_date'])
        
        # Add new data
        new_data = pd.DataFrame(order_data)
        history_df = pd.concat([history_df, new_data], ignore_index=True)
        
        # Save updated history
        history_df.to_excel(history_path, index=False)
        
        # Update registry
        self.registry.register_file(
            file_path=str(history_path),
            category='history',
            subcategory='order_history',
            description='Order history tracking file',
            tags=['historical', 'order_tracking']
        )
    
    def update_client_orders_history(self, client_order_data: Dict):
        """
        Update the client orders history file.
        
        Args:
            client_order_data: Client order data dictionary
        """
        history_path = self.paths['client_orders_history']
        
        # Load existing history or create new
        if history_path.exists():
            history_df = pd.read_excel(history_path)
        else:
            history_df = pd.DataFrame(columns=[
                'order_date', 'client_name', 'total_units', 'section_percentages',
                'description_percentages', 'selected_boxes', 'actual_units',
                'compliance_summary', 'output_file'
            ])
        
        # Add new data
        new_data = pd.DataFrame([client_order_data])
        history_df = pd.concat([history_df, new_data], ignore_index=True)
        
        # Save updated history
        history_df.to_excel(history_path, index=False)
        
        # Update registry
        self.registry.register_file(
            file_path=str(history_path),
            category='client_orders',
            subcategory='history',
            description='Client orders history tracking',
            tags=['historical', 'client_tracking']
        )
    
    def get_client_orders(self, client_name: str = None) -> pd.DataFrame:
        """
        Get client orders from history.
        
        Args:
            client_name: Optional client name to filter by
            
        Returns:
            pd.DataFrame: Client orders data
        """
        if self.paths['client_orders_history'].exists():
            df = pd.read_excel(self.paths['client_orders_history'])
            if client_name:
                return df[df['client_name'].str.contains(client_name, case=False, na=False)]
            return df
        return pd.DataFrame()
    
    def get_order_history(self) -> pd.DataFrame:
        """
        Get order history data.
        
        Returns:
            pd.DataFrame: Order history data
        """
        if self.paths['order_history'].exists():
            return pd.read_excel(self.paths['order_history'])
        return pd.DataFrame()
    
    def list_files_by_category(self, category: str) -> List[str]:
        """
        List all files in a specific category.
        
        Args:
            category: File category
            
        Returns:
            List[str]: List of file paths
        """
        category_files = self.registry.get_files_by_category(category)
        return category_files['file_path'].tolist()
    
    def search_files(self, query: str) -> pd.DataFrame:
        """
        Search for files by query.
        
        Args:
            query: Search query
            
        Returns:
            pd.DataFrame: Matching files
        """
        return self.registry.search_files(query)
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict: File information or None if not found
        """
        # Find file in registry
        registry_files = self.registry.registry_df
        matching_files = registry_files[registry_files['file_path'] == file_path]
        
        if not matching_files.empty:
            return matching_files.iloc[0].to_dict()
        return None
    
    def cleanup_old_files(self, days_old: int = 30):
        """
        Clean up old temporary files.
        
        Args:
            days_old: Number of days to consider files as old
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Get old files from registry
        old_files = self.registry.registry_df[
            self.registry.registry_df['date_created'] < cutoff_date
        ]
        
        cleaned_count = 0
        for _, file_info in old_files.iterrows():
            try:
                file_path = Path(file_info['file_path'])
                if file_path.exists() and file_info['category'] in ['selection_results']:
                    # Only delete temporary selection results, not client orders or history
                    file_path.unlink()
                    cleaned_count += 1
                    print(f"Cleaned up old file: {file_path}")
            except Exception as e:
                print(f"Error cleaning up file {file_info['file_path']}: {e}")
        
        print(f"Cleaned up {cleaned_count} old files")
    
    def print_file_summary(self):
        """Print a summary of all files."""
        self.registry.print_registry_summary()


def main():
    """Main function for file management operations."""
    file_manager = FileManager()
    
    print("File Manager for Inventory Box Picking System")
    print("="*50)
    
    # Print current file summary
    file_manager.print_file_summary()
    
    # Example: List client orders
    print("\nRecent Client Orders:")
    client_orders = file_manager.get_client_orders()
    if not client_orders.empty:
        recent_orders = client_orders.tail(5)
        for _, order in recent_orders.iterrows():
            print(f"  - {order['client_name']}: {order['total_units']} units ({order['order_date']})")
    else:
        print("  No client orders found.")
    
    # Example: Search for files
    print("\nSearch Results for 'ABC':")
    search_results = file_manager.search_files('ABC')
    if not search_results.empty:
        for _, file_info in search_results.iterrows():
            print(f"  - {file_info['file_name']} ({file_info['category']})")
    else:
        print("  No files found matching 'ABC'")


if __name__ == "__main__":
    main()
