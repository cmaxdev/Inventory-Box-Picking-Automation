#!/usr/bin/env python3
"""
Excel File Registry System

This module manages the organization and tracking of all Excel files in the system.
It provides a centralized registry for inventory files, client orders, selection results,
and historical data.

Author: AI Assistant
Version: 1.0
"""

import pandas as pd
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelRegistry:
    """Manages Excel file organization and tracking."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.registry_file = self.base_path / "excel_registry.xlsx"
        
        # Directory structure
        self.directories = {
            'inventory': self.base_path / "inventory",
            'orders': self.base_path / "orders",
            'history': self.base_path / "history",
            'templates': self.base_path / "templates"
        }
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Initialize registry
        self.registry_df = self._load_registry()
    
    def _create_directories(self):
        """Create directory structure if it doesn't exist."""
        for dir_path in self.directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {dir_path}")
    
    def _load_registry(self) -> pd.DataFrame:
        """Load or create the Excel file registry."""
        if self.registry_file.exists():
            try:
                df = pd.read_excel(self.registry_file)
                logger.info(f"Loaded registry with {len(df)} files")
                return df
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
        
        # Create new registry
        df = pd.DataFrame(columns=[
            'file_id', 'file_name', 'original_name', 'category', 'subcategory',
            'file_path', 'date_created', 'date_modified', 'file_size',
            'description', 'client_name', 'order_id', 'status', 'tags'
        ])
        
        logger.info("Created new Excel registry")
        return df
    
    def _save_registry(self):
        """Save the registry to Excel file."""
        try:
            self.registry_df.to_excel(self.registry_file, index=False)
            logger.info(f"Registry saved with {len(self.registry_df)} files")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_file(
        self,
        file_path: str,
        category: str,
        subcategory: str = "",
        description: str = "",
        client_name: str = "",
        order_id: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Register a new Excel file in the system.
        
        Args:
            file_path: Path to the Excel file
            category: File category (inventory, orders, history, templates)
            subcategory: Optional subcategory
            description: Description of the file
            client_name: Client name (for client orders)
            order_id: Order identifier
            tags: List of tags for categorization
            
        Returns:
            str: File ID assigned to the file
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate unique file ID
            file_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.stem}"
            
            # Get file information
            stat = file_path.stat()
            file_size = stat.st_size
            date_created = datetime.fromtimestamp(stat.st_ctime)
            date_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Create registry entry
            new_entry = {
                'file_id': file_id,
                'file_name': file_path.name,
                'original_name': file_path.name,
                'category': category,
                'subcategory': subcategory,
                'file_path': str(file_path),
                'date_created': date_created,
                'date_modified': date_modified,
                'file_size': file_size,
                'description': description,
                'client_name': client_name,
                'order_id': order_id,
                'status': 'active',
                'tags': ', '.join(tags) if tags else ''
            }
            
            # Add to registry
            self.registry_df = pd.concat([self.registry_df, pd.DataFrame([new_entry])], ignore_index=True)
            self._save_registry()
            
            logger.info(f"Registered file: {file_path.name} with ID: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error registering file {file_path}: {e}")
            raise
    
    def organize_existing_files(self):
        """Organize existing Excel files into proper directories."""
        logger.info("Starting organization of existing Excel files...")
        
        # Find all Excel files in the project root
        root_path = Path(".")
        excel_files = list(root_path.glob("*.xlsx"))
        
        organized_count = 0
        
        for file_path in excel_files:
            try:
                # Determine category based on filename
                category, subcategory, description = self._categorize_file(file_path.name)
                
                # Determine destination directory
                if category in self.directories:
                    dest_dir = self.directories[category]
                else:
                    dest_dir = self.directories['templates']
                
                # Create new filename if needed
                new_filename = self._generate_organized_filename(file_path.name, category)
                dest_path = dest_dir / new_filename
                
                # Move file
                shutil.move(str(file_path), str(dest_path))
                
                # Register the file
                client_name = self._extract_client_name(file_path.name)
                order_id = self._extract_order_id(file_path.name)
                
                self.register_file(
                    file_path=str(dest_path),
                    category=category,
                    subcategory=subcategory,
                    description=description,
                    client_name=client_name,
                    order_id=order_id,
                    tags=self._generate_tags(file_path.name, category)
                )
                
                organized_count += 1
                logger.info(f"Organized: {file_path.name} -> {dest_path}")
                
            except Exception as e:
                logger.error(f"Error organizing file {file_path.name}: {e}")
        
        logger.info(f"Organized {organized_count} Excel files")
        return organized_count
    
    def _categorize_file(self, filename: str) -> tuple:
        """Categorize a file based on its name."""
        filename_lower = filename.lower()
        
        if 'inventory' in filename_lower or filename == 'sample_inventory.xlsx':
            return 'inventory', 'main', 'Main inventory data file'
        
        elif 'client_order' in filename_lower:
            return 'orders', 'processed', 'Client order selection results'
        
        elif any(x in filename_lower for x in ['selection_results', 'basic_selection', 'no_info_requirement', 'custom_constraints']):
            return 'orders', 'automated', 'Automated selection results'
        
        elif 'history' in filename_lower:
            return 'history', 'order_history', 'Order history tracking'
        
        else:
            return 'templates', 'misc', 'Template or miscellaneous file'
    
    def _generate_organized_filename(self, original_name: str, category: str) -> str:
        """Generate a standardized filename."""
        if category == 'inventory' and 'sample' in original_name.lower():
            return 'sample_inventory.xlsx'
        elif category == 'history' and 'order_history' in original_name.lower():
            return 'order_history.xlsx'
        else:
            # Keep original name but ensure it's properly formatted
            return original_name
    
    def _extract_client_name(self, filename: str) -> str:
        """Extract client name from filename."""
        if 'client_order_' in filename:
            # Extract client name from filename like "client_order_ABC Company_20251020_125435.xlsx"
            parts = filename.replace('client_order_', '').split('_')
            if len(parts) >= 2:
                return parts[0].replace('.xlsx', '')
        return ''
    
    def _extract_order_id(self, filename: str) -> str:
        """Extract order ID from filename."""
        if '_' in filename:
            parts = filename.split('_')
            # Look for date pattern
            for part in parts:
                if len(part) == 15 and part.isdigit():  # YYYYMMDD_HHMMSS format
                    return part
        return ''
    
    def _generate_tags(self, filename: str, category: str) -> List[str]:
        """Generate tags for a file."""
        tags = [category]
        
        if 'sample' in filename.lower():
            tags.append('sample')
        if 'history' in filename.lower():
            tags.append('historical')
        if 'client' in filename.lower():
            tags.append('client_data')
        
        return tags
    
    def get_files_by_category(self, category: str) -> pd.DataFrame:
        """Get all files in a specific category."""
        return self.registry_df[self.registry_df['category'] == category].copy()
    
    def get_files_by_client(self, client_name: str) -> pd.DataFrame:
        """Get all files for a specific client."""
        return self.registry_df[self.registry_df['client_name'].str.contains(client_name, case=False, na=False)].copy()
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get detailed information about a specific file."""
        file_info = self.registry_df[self.registry_df['file_id'] == file_id]
        if not file_info.empty:
            return file_info.iloc[0].to_dict()
        return None
    
    def search_files(self, query: str) -> pd.DataFrame:
        """Search for files by query."""
        query_lower = query.lower()
        
        mask = (
            self.registry_df['file_name'].str.contains(query_lower, case=False, na=False) |
            self.registry_df['description'].str.contains(query_lower, case=False, na=False) |
            self.registry_df['client_name'].str.contains(query_lower, case=False, na=False) |
            self.registry_df['tags'].str.contains(query_lower, case=False, na=False)
        )
        
        return self.registry_df[mask].copy()
    
    def generate_summary_report(self) -> Dict:
        """Generate a summary report of all registered files."""
        summary = {
            'total_files': len(self.registry_df),
            'by_category': self.registry_df['category'].value_counts().to_dict(),
            'by_client': self.registry_df['client_name'].value_counts().to_dict(),
            'total_size': self.registry_df['file_size'].sum(),
            'date_range': {
                'earliest': self.registry_df['date_created'].min(),
                'latest': self.registry_df['date_created'].max()
            }
        }
        
        return summary
    
    def print_registry_summary(self):
        """Print a summary of the registry."""
        summary = self.generate_summary_report()
        
        print("\n" + "="*60)
        print("EXCEL FILE REGISTRY SUMMARY")
        print("="*60)
        print(f"Total Files Registered: {summary['total_files']}")
        print(f"Total Size: {summary['total_size']:,} bytes")
        print(f"Date Range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        print("\nFiles by Category:")
        for category, count in summary['by_category'].items():
            print(f"  {category}: {count} files")
        
        if summary['by_client']:
            print("\nFiles by Client:")
            for client, count in summary['by_client'].items():
                if client:  # Skip empty client names
                    print(f"  {client}: {count} files")
        
        print("\nDirectory Structure:")
        for name, path in self.directories.items():
            file_count = len(list(path.glob("*.xlsx")))
            print(f"  {name}: {path} ({file_count} files)")
        
        print("="*60)


def main():
    """Main function to organize existing Excel files."""
    registry = ExcelRegistry()
    
    print("Excel File Registry System")
    print("="*40)
    
    # Organize existing files
    organized_count = registry.organize_existing_files()
    
    # Print summary
    registry.print_registry_summary()
    
    print(f"\nOrganized {organized_count} Excel files into proper directory structure.")
    print("Registry saved to: data/excel_registry.xlsx")


if __name__ == "__main__":
    main()
