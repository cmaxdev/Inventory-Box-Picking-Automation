#!/usr/bin/env python3
"""
Inventory Box Picking Automation Tool

This script automates the selection of full boxes from inventory based on:
- Information completeness requirements
- Historical unit limitations per model
- Percentage distribution by section and description
- Unit constraints per model (max 200 units)

Author: AI Assistant
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from file_manager import FileManager
from excel_registry_utils import auto_register_excel, ExcelFileCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_picker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InventoryPicker:
    """Main class for inventory box picking automation."""
    
    def __init__(self):
        self.inventory_df = None
        self.history_df = None
        self.selected_boxes = []
        self.max_units_per_model = 200
        self.history_file = "data/history/order_history.xlsx"
        self.file_manager = FileManager()
        self.excel_creator = ExcelFileCreator()
        
    def load_inventory(self, excel_file_path: str) -> bool:
        """
        Load inventory data from Excel file.
        
        Args:
            excel_file_path: Path to the inventory Excel file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading inventory from: {excel_file_path}")
            
            # Read Excel file
            self.inventory_df = pd.read_excel(excel_file_path)
            
            # Map column names to standardized names based on actual file structure
            column_mapping = {
                'CONTENEUR': 'container',
                'CARTONS': 'cartons',
                'BARCODE': 'barcode',
                'SEASON': 'season',
                'SECTION': 'section',
                'PAYS': 'country',
                'DESCRIPTION': 'description',
                'FAMILLIE': 'family',
                'DETAIL': 'detail',
                'NOTES': 'notes',
                'COMPOSITION': 'composition',
                'TARIFAIRE': 'hs_code',
                'PVP': 'price',
                'PVP total': 'total_price',
                'POIDS': 'weight',
                'SAISON INT.': 'internal_season',
                'UNITES': 'units_per_case',
                'MOCACO': 'model',
                'RESERVATION': 'reservation',
                'G. TARIF': 'tariff_group'
            }
            
            # Rename columns
            self.inventory_df = self.inventory_df.rename(columns=column_mapping)
            
            # Validate required columns based on project requirements
            required_columns = ['barcode', 'composition', 'hs_code', 'price', 'tariff_group', 
                              'section', 'description', 'model', 'units_per_case']
            
            missing_columns = [col for col in required_columns if col not in self.inventory_df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Clean data - only keep rows with essential information
            self.inventory_df = self.inventory_df.dropna(subset=['barcode', 'model', 'units_per_case', 'section', 'description'])
            
            # Ensure all required columns exist (fill missing ones with empty strings)
            for col in required_columns:
                if col not in self.inventory_df.columns:
                    self.inventory_df[col] = ''
            
            # Convert units_per_case to numeric
            self.inventory_df['units_per_case'] = pd.to_numeric(self.inventory_df['units_per_case'], errors='coerce')
            self.inventory_df = self.inventory_df.dropna(subset=['units_per_case'])
            
            # Remove rows with zero or negative units
            self.inventory_df = self.inventory_df[self.inventory_df['units_per_case'] > 0]
            
            # Ensure model column is string type for consistent merging
            self.inventory_df['model'] = self.inventory_df['model'].astype(str)
            
            # Clean text columns
            self.inventory_df['section'] = self.inventory_df['section'].astype(str).str.strip()
            self.inventory_df['description'] = self.inventory_df['description'].astype(str).str.strip()
            
            logger.info(f"Inventory loaded successfully: {len(self.inventory_df)} boxes")
            return True
            
        except Exception as e:
            logger.error(f"Error loading inventory: {str(e)}")
            return False
    
    def load_history(self) -> bool:
        """
        Load order history from Excel file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(self.history_file):
                logger.info(f"Loading order history from: {self.history_file}")
                self.history_df = pd.read_excel(self.history_file)
                
                # Ensure required columns exist
                if 'model' not in self.history_df.columns:
                    self.history_df['model'] = ''
                if 'total_units_shipped' not in self.history_df.columns:
                    self.history_df['total_units_shipped'] = 0
                    
                logger.info(f"History loaded: {len(self.history_df)} records")
            else:
                logger.info("No history file found, creating new one")
                self.history_df = pd.DataFrame(columns=['model', 'total_units_shipped'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            return False
    
    def filter_by_information_completeness(self, require_complete_info: bool) -> pd.DataFrame:
        """
        Filter inventory based on information completeness requirements.
        
        Args:
            require_complete_info: If True, only select boxes with complete information
            
        Returns:
            pd.DataFrame: Filtered inventory
        """
        logger.info(f"Filtering by information completeness: {require_complete_info}")
        
        if require_complete_info:
            # Option A: Only boxes with complete information (composition, HS code, price, tariff group not null/empty)
            complete_info_mask = (
                self.inventory_df['composition'].notna() & 
                (self.inventory_df['composition'].astype(str).str.strip() != '') &
                (self.inventory_df['composition'].astype(str).str.strip() != 'nan') &
                self.inventory_df['hs_code'].notna() & 
                (self.inventory_df['hs_code'].astype(str).str.strip() != '') &
                (self.inventory_df['hs_code'].astype(str).str.strip() != 'nan') &
                self.inventory_df['price'].notna() & 
                (self.inventory_df['price'].astype(str).str.strip() != '') &
                (self.inventory_df['price'].astype(str).str.strip() != 'nan') &
                self.inventory_df['tariff_group'].notna() & 
                (self.inventory_df['tariff_group'].astype(str).str.strip() != '') &
                (self.inventory_df['tariff_group'].astype(str).str.strip() != 'nan')
            )
            filtered_df = self.inventory_df[complete_info_mask].copy()
            logger.info(f"Complete info filter: {len(filtered_df)}/{len(self.inventory_df)} boxes selected")
        else:
            # Option B: All available boxes
            filtered_df = self.inventory_df.copy()
            logger.info(f"No info requirement: All {len(filtered_df)} boxes available")
        
        return filtered_df
    
    def apply_historical_constraints(self, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply historical unit limitations per model.
        
        Args:
            inventory_df: Filtered inventory dataframe
            
        Returns:
            pd.DataFrame: Inventory with available units calculated
        """
        logger.info("Applying historical constraints...")
        
        # Calculate available units per model
        inventory_df = inventory_df.copy()
        inventory_df['available_units'] = inventory_df['units_per_case']
        
        if not self.history_df.empty:
            # Merge with history data
            history_agg = self.history_df.groupby('model')['total_units_shipped'].sum().reset_index()
            history_agg.columns = ['model', 'units_shipped_historically']
            
            # Ensure both 'model' columns are the same data type (string)
            inventory_df['model'] = inventory_df['model'].astype(str)
            history_agg['model'] = history_agg['model'].astype(str)
            
            inventory_df = inventory_df.merge(
                history_agg, 
                on='model', 
                how='left'
            )
            
            # Fill NaN values with 0
            inventory_df['units_shipped_historically'] = inventory_df['units_shipped_historically'].fillna(0)
            
            # Calculate available units
            inventory_df['available_units'] = np.maximum(
                0, 
                self.max_units_per_model - inventory_df['units_shipped_historically']
            )
            
            # Filter out boxes where available units is 0
            inventory_df = inventory_df[inventory_df['available_units'] > 0]
            
            logger.info(f"After historical constraints: {len(inventory_df)} boxes available")
        else:
            inventory_df['units_shipped_historically'] = 0
            logger.info("No historical data, all boxes available")
        
        return inventory_df
    
    def select_by_percentage_distribution(
        self, 
        inventory_df: pd.DataFrame,
        section_percentages: Dict[str, float],
        description_percentages: Dict[str, float],
        total_units_target: int
    ) -> List[Dict]:
        """
        Select boxes based on percentage distribution.
        
        Args:
            inventory_df: Filtered inventory dataframe
            section_percentages: Target percentages by section
            description_percentages: Target percentages by description
            total_units_target: Target total units for the order
            
        Returns:
            List[Dict]: Selected boxes
        """
        logger.info("Starting percentage-based selection...")
        logger.info(f"Section percentages: {section_percentages}")
        logger.info(f"Description percentages: {description_percentages}")
        logger.info(f"Target total units: {total_units_target}")
        
        selected_boxes = []
        remaining_inventory = inventory_df.copy()
        
        # Calculate target units per section
        section_targets = {}
        for section, percentage in section_percentages.items():
            target_units = int(total_units_target * percentage / 100)
            section_targets[section] = target_units
            logger.info(f"Target for {section}: {target_units} units")
        
        # Select boxes by section using greedy algorithm
        for section, target_units in section_targets.items():
            if target_units <= 0:
                continue
                
            # Find matching sections (case-insensitive)
            section_boxes = remaining_inventory[
                remaining_inventory['section'].str.lower().str.strip() == section.lower().strip()
            ]
            
            if len(section_boxes) == 0:
                logger.warning(f"No boxes found for section '{section}'. Available sections: {remaining_inventory['section'].unique()}")
                continue
            
            section_boxes = section_boxes.sort_values('units_per_case', ascending=False)
            
            selected_units = 0
            for _, box in section_boxes.iterrows():
                if selected_units + box['units_per_case'] <= target_units:
                    selected_boxes.append(box.to_dict())
                    selected_units += box['units_per_case']
                    
                    # Remove from remaining inventory
                    remaining_inventory = remaining_inventory[
                        remaining_inventory['barcode'] != box['barcode']
                    ]
        
        # Verify description percentages
        if description_percentages and selected_boxes:
            selected_df = pd.DataFrame(selected_boxes)
            # Ensure units_per_case column exists and is numeric
            if 'units_per_case' in selected_df.columns:
                selected_df['units_per_case'] = pd.to_numeric(selected_df['units_per_case'], errors='coerce')
                description_compliance = self._check_description_percentages(
                    selected_df, description_percentages
                )
                logger.info(f"Description compliance: {description_compliance}")
            else:
                logger.warning("units_per_case column not found in selected boxes")
        
        logger.info(f"Selected {len(selected_boxes)} boxes")
        return selected_boxes
    
    def _check_description_percentages(
        self, 
        selected_df: pd.DataFrame, 
        description_percentages: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Check compliance with description percentages.
        
        Args:
            selected_df: Selected boxes dataframe
            description_percentages: Target percentages by description
            
        Returns:
            Dict[str, float]: Actual percentages achieved
        """
        total_units = selected_df['units_per_case'].sum()
        actual_percentages = {}
        
        for description, target_percentage in description_percentages.items():
            description_units = selected_df[
                selected_df['description'] == description
            ]['units_per_case'].sum()
            
            actual_percentage = (description_units / total_units * 100) if total_units > 0 else 0
            actual_percentages[description] = actual_percentage
            
            logger.info(f"{description}: Target {target_percentage}%, Actual {actual_percentage:.2f}%")
        
        return actual_percentages
    
    def apply_final_model_constraints(self, selected_boxes: List[Dict]) -> List[Dict]:
        """
        Apply final unit constraints per model for current order.
        
        Args:
            selected_boxes: List of selected boxes
            
        Returns:
            List[Dict]: Filtered selected boxes
        """
        logger.info("Applying final model constraints...")
        
        # Group by model and calculate total units
        model_units = {}
        for box in selected_boxes:
            model = box['model']
            units = box['units_per_case']
            if model not in model_units:
                model_units[model] = []
            model_units[model].append((box, units))
        
        # Apply 200 unit limit per model
        final_selected_boxes = []
        for model, boxes_with_units in model_units.items():
            total_model_units = sum(units for _, units in boxes_with_units)
            
            if total_model_units <= self.max_units_per_model:
                # All boxes can be included
                final_selected_boxes.extend([box for box, _ in boxes_with_units])
                logger.info(f"Model {model}: {total_model_units} units (within limit)")
            else:
                # Need to reduce boxes
                # Sort by units per case (descending) to prioritize larger boxes
                boxes_with_units.sort(key=lambda x: x[1], reverse=True)
                
                current_units = 0
                for box, units in boxes_with_units:
                    if current_units + units <= self.max_units_per_model:
                        final_selected_boxes.append(box)
                        current_units += units
                
                logger.info(f"Model {model}: {current_units}/{total_model_units} units selected (limit applied)")
        
        logger.info(f"Final selection: {len(final_selected_boxes)} boxes")
        return final_selected_boxes
    
    def update_history(self, selected_boxes: List[Dict]):
        """
        Update order history with selected boxes.
        
        Args:
            selected_boxes: List of selected boxes
        """
        logger.info("Updating order history...")
        
        if not selected_boxes:
            return
        
        # Calculate units per model for this order
        order_summary = {}
        for box in selected_boxes:
            model = box['model']
            units = box['units_per_case']
            if model not in order_summary:
                order_summary[model] = 0
            order_summary[model] += units
        
        # Create new history records
        new_history_records = []
        for model, units in order_summary.items():
            new_history_records.append({
                'model': model,
                'total_units_shipped': units,
                'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Add to history dataframe
        new_history_df = pd.DataFrame(new_history_records)
        self.history_df = pd.concat([self.history_df, new_history_df], ignore_index=True)
        
        # Save updated history
        self.history_df.to_excel(self.history_file, index=False)
        
        # Register the history file in the registry
        try:
            self.file_manager.registry.register_file(
                file_path=self.history_file,
                category='history',
                subcategory='order_history',
                description='Order history tracking file with model usage statistics',
                tags=['historical', 'order_tracking']
            )
            logger.info(f"History file registered in Excel registry: {self.history_file}")
        except Exception as e:
            logger.warning(f"Could not register history file in registry: {e}")
        
        logger.info(f"History updated with {len(new_history_records)} model records")
    
    def generate_output(self, selected_boxes: List[Dict], output_file: str = None):
        """
        Generate output report with selected boxes and summary.
        
        Args:
            selected_boxes: List of selected boxes
            output_file: Optional output file path
        """
        logger.info("Generating output report...")
        
        if not selected_boxes:
            logger.warning("No boxes selected")
            # Still create an output file even when no boxes are selected
            if output_file and output_file.strip():
                try:
                    # Create empty result file with summary information
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        # Create empty summary sheet
                        empty_summary = pd.DataFrame({
                            'Metric': ['Total Boxes Selected', 'Total Units', 'Selection Status'],
                            'Value': [0, 0, 'No boxes selected - requirements may not match inventory data']
                        })
                        empty_summary.to_excel(writer, sheet_name='Summary', index=False)
                        
                        # Create information sheet about available data
                        info_data = {
                            'Available Sections': ['Woman'],
                            'Available Descriptions': ['DRESS', 'OVERALL', 'TROUSERS', 'LEGGINGS', 'SKIRT', 'BIB OVERALL'],
                            'Note': ['Use these exact names in your requirements']
                        }
                        info_df = pd.DataFrame(info_data)
                        info_df.to_excel(writer, sheet_name='Available_Data', index=False)
                        
                    logger.info(f"Empty result file created: {output_file}")
                except Exception as e:
                    logger.error(f"Error creating empty result file: {e}")
            
            return {
                'total_boxes': 0,
                'total_units': 0,
                'target_units': 0,
                'units_difference': 0,
                'selection_efficiency': 0.0,
                'section_summary': pd.DataFrame(),
                'description_summary': pd.DataFrame(),
                'compliance': {
                    'section_compliance': 0.0,
                    'description_compliance': 0.0,
                    'overall_compliance': 0.0
                },
                'output_file': output_file if output_file and output_file.strip() else None
            }
        
        selected_df = pd.DataFrame(selected_boxes)
        
        # Ensure units_per_case column exists and is numeric
        if 'units_per_case' not in selected_df.columns:
            logger.error("units_per_case column not found in selected boxes")
            return {
                'total_boxes': 0,
                'total_units': 0,
                'target_units': 0,
                'units_difference': 0,
                'selection_efficiency': 0.0,
                'section_summary': pd.DataFrame(),
                'description_summary': pd.DataFrame(),
                'compliance': {
                    'section_compliance': 0.0,
                    'description_compliance': 0.0,
                    'overall_compliance': 0.0
                },
                'output_file': output_file if output_file and output_file.strip() else None
            }
        
        selected_df['units_per_case'] = pd.to_numeric(selected_df['units_per_case'], errors='coerce')
        
        # Calculate summary statistics
        total_units = selected_df['units_per_case'].sum()
        total_boxes = len(selected_df)
        
        # Section distribution
        section_summary = selected_df.groupby('section').agg({
            'units_per_case': ['sum', 'count']
        }).round(2)
        section_summary.columns = ['total_units', 'box_count']
        section_summary['percentage'] = (section_summary['total_units'] / total_units * 100).round(2)
        
        # Description distribution
        description_summary = selected_df.groupby('description').agg({
            'units_per_case': ['sum', 'count']
        }).round(2)
        description_summary.columns = ['total_units', 'box_count']
        description_summary['percentage'] = (description_summary['total_units'] / total_units * 100).round(2)
        
        # Model summary
        model_summary = selected_df.groupby('model')['units_per_case'].sum().reset_index()
        model_summary.columns = ['model', 'total_units']
        
        # Print summary
        print("\n" + "="*60)
        print("INVENTORY BOX PICKING RESULTS")
        print("="*60)
        print(f"Total Boxes Selected: {total_boxes}")
        print(f"Total Units: {total_units}")
        print("\nSECTION DISTRIBUTION:")
        print(section_summary)
        print("\nDESCRIPTION DISTRIBUTION:")
        print(description_summary)
        print("\nMODEL SUMMARY:")
        print(model_summary)
        
        # Save to Excel if output file specified
        if output_file and output_file.strip():
            # Ensure the directory exists (only if there's a directory path)
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                selected_df.to_excel(writer, sheet_name='Selected_Boxes', index=False)
                section_summary.to_excel(writer, sheet_name='Section_Summary')
                description_summary.to_excel(writer, sheet_name='Description_Summary')
                model_summary.to_excel(writer, sheet_name='Model_Summary')
            
            # Automatically register the file in the registry
            try:
                self.file_manager.registry.register_file(
                    file_path=output_file,
                    category='selection_results',
                    subcategory='automated',
                    description='Automated inventory selection results',
                    tags=['automated', 'selection_results']
                )
                logger.info(f"File registered in Excel registry: {output_file}")
            except Exception as e:
                logger.warning(f"Could not register file in registry: {e}")
            
            logger.info(f"Output saved to: {output_file}")
        
        return {
            'selected_boxes': selected_df,
            'section_summary': section_summary,
            'description_summary': description_summary,
            'model_summary': model_summary,
            'total_units': total_units,
            'total_boxes': total_boxes
        }
    
    @auto_register_excel(
        category='selection_results',
        subcategory='automated',
        description='Automated inventory selection results',
        tags=['automated', 'selection_results']
    )
    def run_selection_process(
        self,
        excel_file_path: str,
        require_complete_info: bool,
        section_percentages: Dict[str, float],
        description_percentages: Dict[str, float],
        total_units_target: int,
        output_file: str = None
    ) -> Dict:
        """
        Run the complete selection process.
        
        Args:
            excel_file_path: Path to inventory Excel file
            require_complete_info: Whether to require complete information
            section_percentages: Target percentages by section
            description_percentages: Target percentages by description
            total_units_target: Target total units
            output_file: Optional output file path
            
        Returns:
            Dict: Results summary
        """
        logger.info("Starting inventory selection process...")
        
        # Step 1: Load data
        if not self.load_inventory(excel_file_path):
            raise Exception("Failed to load inventory data")
        
        if not self.load_history():
            raise Exception("Failed to load history data")
        
        # Step 2: Filter by information completeness
        filtered_inventory = self.filter_by_information_completeness(require_complete_info)
        
        # Step 3: Apply historical constraints
        constrained_inventory = self.apply_historical_constraints(filtered_inventory)
        
        # Step 4: Select by percentage distribution
        selected_boxes = self.select_by_percentage_distribution(
            constrained_inventory,
            section_percentages,
            description_percentages,
            total_units_target
        )
        
        # Step 5: Apply final model constraints
        final_selected_boxes = self.apply_final_model_constraints(selected_boxes)
        
        # Step 6: Update history
        self.update_history(final_selected_boxes)
        
        # Step 7: Generate output
        if not output_file:
            # Generate default output file path (save in data/orders/ directory)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/orders/selection_results_{timestamp}.xlsx"
        
        results = self.generate_output(final_selected_boxes, output_file)
        
        logger.info("Selection process completed successfully")
        return results


def main():
    """Main function to run the inventory picker."""
    picker = InventoryPicker()
    
    # Example usage - replace with your actual parameters
    excel_file_path = "data/inventory/sample_inventory.xlsx"  # Replace with your inventory file path
    
    # Configuration parameters
    require_complete_info = True  # Set to False if you don't require complete information
    
    section_percentages = {
        "Women": 50.0,
        "Men": 30.0,
        "Children": 20.0
    }
    
    description_percentages = {
        "Accessories": 25.0,
        "Trousers": 35.0,
        "Tops": 40.0
    }
    
    total_units_target = 1000  # Adjust based on your needs
    
    output_file = f"selection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    try:
        results = picker.run_selection_process(
            excel_file_path=excel_file_path,
            require_complete_info=require_complete_info,
            section_percentages=section_percentages,
            description_percentages=description_percentages,
            total_units_target=total_units_target,
            output_file=output_file
        )
        
        print(f"\nSelection completed successfully!")
        print(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Selection process failed: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
