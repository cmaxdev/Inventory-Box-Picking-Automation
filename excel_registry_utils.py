#!/usr/bin/env python3
"""
Excel Registry Utilities

This module provides utilities and decorators to ensure all Excel files
are automatically registered in the registry system when created.

Author: AI Assistant
Version: 1.0
"""

import os
import pandas as pd
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
import logging
from excel_registry import ExcelRegistry

logger = logging.getLogger(__name__)


def auto_register_excel(category: str, subcategory: str = "", description: str = "", tags: List[str] = None):
    """
    Decorator to automatically register Excel files in the registry.
    
    Args:
        category: File category (inventory, client_orders, selection_results, history, templates)
        subcategory: Optional subcategory
        description: Description of the file
        tags: List of tags for categorization
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Try to register the Excel file if one was created
            try:
                registry = ExcelRegistry()
                
                # Look for output_file in kwargs or result
                output_file = None
                if 'output_file' in kwargs and kwargs['output_file']:
                    output_file = kwargs['output_file']
                elif isinstance(result, dict) and 'output_file' in result:
                    output_file = result['output_file']
                elif isinstance(result, str) and result.endswith('.xlsx'):
                    output_file = result
                
                if output_file and os.path.exists(output_file):
                    # Extract additional metadata from function arguments
                    client_name = kwargs.get('client_name', '')
                    order_id = kwargs.get('order_id', '')
                    
                    registry.register_file(
                        file_path=output_file,
                        category=category,
                        subcategory=subcategory,
                        description=description,
                        client_name=client_name,
                        order_id=order_id,
                        tags=tags or []
                    )
                    
                    logger.info(f"Auto-registered Excel file: {output_file}")
                
            except Exception as e:
                logger.warning(f"Could not auto-register Excel file: {e}")
            
            return result
        
        return wrapper
    return decorator


class ExcelFileCreator:
    """Helper class for creating and registering Excel files."""
    
    def __init__(self):
        self.registry = ExcelRegistry()
    
    def create_and_register(
        self,
        file_path: str,
        data: Dict[str, pd.DataFrame],
        category: str,
        subcategory: str = "",
        description: str = "",
        client_name: str = "",
        order_id: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Create an Excel file and automatically register it.
        
        Args:
            file_path: Path where to save the Excel file
            data: Dictionary of sheet names and DataFrames
            category: File category
            subcategory: Optional subcategory
            description: Description of the file
            client_name: Client name (for client orders)
            order_id: Order identifier
            tags: List of tags
            
        Returns:
            str: Path to the created file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create Excel file
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Register the file
            file_id = self.registry.register_file(
                file_path=file_path,
                category=category,
                subcategory=subcategory,
                description=description,
                client_name=client_name,
                order_id=order_id,
                tags=tags or []
            )
            
            logger.info(f"Created and registered Excel file: {file_path} (ID: {file_id})")
            return file_path
            
        except Exception as e:
            logger.error(f"Error creating and registering Excel file {file_path}: {e}")
            raise
    
    def create_client_order_file(
        self,
        client_name: str,
        results: Dict,
        output_dir: str = "data/orders/client_orders"
    ) -> str:
        """
        Create a client order Excel file and register it.
        
        Args:
            client_name: Name of the client
            results: Results dictionary from order processing
            output_dir: Output directory
            
        Returns:
            str: Path to the created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"client_order_{client_name}_{timestamp}.xlsx"
        file_path = os.path.join(output_dir, filename)
        
        # Prepare data for Excel
        data = {}
        if 'selected_boxes' in results:
            data['Selected_Boxes'] = results['selected_boxes']
        if 'section_summary' in results:
            data['Section_Summary'] = results['section_summary']
        if 'description_summary' in results:
            data['Description_Summary'] = results['description_summary']
        if 'model_summary' in results:
            data['Model_Summary'] = results['model_summary']
        
        return self.create_and_register(
            file_path=file_path,
            data=data,
            category='client_orders',
            subcategory='processed',
            description=f"Client order results for {client_name}",
            client_name=client_name,
            order_id=timestamp,
            tags=['client_data', 'order_results']
        )
    
    def create_selection_result_file(
        self,
        result_type: str,
        results: Dict,
        output_dir: str = "data/orders/selection_results"
    ) -> str:
        """
        Create a selection result Excel file and register it.
        
        Args:
            result_type: Type of selection result
            results: Results dictionary
            output_dir: Output directory
            
        Returns:
            str: Path to the created file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{result_type}_{timestamp}.xlsx"
        file_path = os.path.join(output_dir, filename)
        
        # Prepare data for Excel
        data = {}
        if 'selected_boxes' in results:
            data['Selected_Boxes'] = results['selected_boxes']
        if 'section_summary' in results:
            data['Section_Summary'] = results['section_summary']
        if 'description_summary' in results:
            data['Description_Summary'] = results['description_summary']
        if 'model_summary' in results:
            data['Model_Summary'] = results['model_summary']
        
        return self.create_and_register(
            file_path=file_path,
            data=data,
            category='selection_results',
            subcategory='automated',
            description=f"Automated selection results: {result_type}",
            tags=['automated', 'selection_results']
        )


def ensure_excel_registration(func: Callable) -> Callable:
    """
    Decorator to ensure Excel files are registered after function execution.
    This decorator looks for Excel files created by the function and registers them.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get initial list of Excel files
        initial_files = set(Path('.').glob('**/*.xlsx'))
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Get final list of Excel files
        final_files = set(Path('.').glob('**/*.xlsx'))
        
        # Find new Excel files
        new_files = final_files - initial_files
        
        # Register new files
        registry = ExcelRegistry()
        for file_path in new_files:
            try:
                # Determine category based on file path
                if 'client_orders' in str(file_path):
                    category = 'client_orders'
                    subcategory = 'processed'
                    description = 'Client order results'
                elif 'selection_results' in str(file_path):
                    category = 'selection_results'
                    subcategory = 'automated'
                    description = 'Selection results'
                elif 'history' in str(file_path):
                    category = 'history'
                    subcategory = 'tracking'
                    description = 'History file'
                elif 'inventory' in str(file_path):
                    category = 'inventory'
                    subcategory = 'main'
                    description = 'Inventory file'
                else:
                    category = 'templates'
                    subcategory = 'misc'
                    description = 'Miscellaneous file'
                
                registry.register_file(
                    file_path=str(file_path),
                    category=category,
                    subcategory=subcategory,
                    description=description,
                    tags=['auto_registered']
                )
                
                logger.info(f"Auto-registered new Excel file: {file_path}")
                
            except Exception as e:
                logger.warning(f"Could not auto-register file {file_path}: {e}")
        
        return result
    
    return wrapper


def register_existing_excel_files(directory: str = "."):
    """
    Register all existing Excel files in a directory.
    
    Args:
        directory: Directory to scan for Excel files
    """
    registry = ExcelRegistry()
    directory_path = Path(directory)
    
    excel_files = list(directory_path.glob('**/*.xlsx'))
    registered_count = 0
    
    for file_path in excel_files:
        try:
            # Skip the registry file itself
            if 'excel_registry.xlsx' in str(file_path):
                continue
            
            # Determine category based on path
            if 'inventory' in str(file_path):
                category = 'inventory'
                subcategory = 'main'
                description = 'Inventory data file'
            elif 'client_orders' in str(file_path):
                category = 'client_orders'
                subcategory = 'processed'
                description = 'Client order results'
            elif 'selection_results' in str(file_path):
                category = 'selection_results'
                subcategory = 'automated'
                description = 'Selection results'
            elif 'history' in str(file_path):
                category = 'history'
                subcategory = 'tracking'
                description = 'History file'
            else:
                category = 'templates'
                subcategory = 'misc'
                description = 'Miscellaneous file'
            
            # Extract client name if possible
            client_name = ""
            if 'client_order_' in str(file_path):
                parts = file_path.name.replace('client_order_', '').split('_')
                if len(parts) >= 2:
                    client_name = parts[0]
            
            registry.register_file(
                file_path=str(file_path),
                category=category,
                subcategory=subcategory,
                description=description,
                client_name=client_name,
                tags=['existing_file']
            )
            
            registered_count += 1
            
        except Exception as e:
            logger.warning(f"Could not register existing file {file_path}: {e}")
    
    logger.info(f"Registered {registered_count} existing Excel files")
    return registered_count


def main():
    """Main function to register all existing Excel files."""
    print("Excel Registry Utilities")
    print("=" * 30)
    
    # Register all existing Excel files
    registered_count = register_existing_excel_files()
    
    print(f"Registered {registered_count} existing Excel files")
    
    # Print registry summary
    registry = ExcelRegistry()
    registry.print_registry_summary()


if __name__ == "__main__":
    main()
