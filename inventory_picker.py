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
        self.history_file = "order_history.xlsx"
        
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
            
            # Map column names to standardized names
            column_mapping = {
                'BARCODE': 'barcode',
                'COMPOSITION': 'composition',
                'TARIFAIRE': 'hs_code',
                'PVP': 'price',
                'G. TARIF': 'tariff_group',
                'SECTION': 'section',
                'DESCRIPTION': 'description',
                'MOCACO': 'model',
                'UNITES': 'units_per_case'
            }
            
            # Rename columns
            self.inventory_df = self.inventory_df.rename(columns=column_mapping)
            
            # Validate required columns
            required_columns = ['barcode', 'composition', 'hs_code', 'price', 
                              'tariff_group', 'section', 'description', 'model', 'units_per_case']
            
            missing_columns = [col for col in required_columns if col not in self.inventory_df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Clean data
            self.inventory_df = self.inventory_df.dropna(subset=['barcode', 'model', 'units_per_case'])
            self.inventory_df['units_per_case'] = pd.to_numeric(self.inventory_df['units_per_case'], errors='coerce')
            self.inventory_df = self.inventory_df.dropna(subset=['units_per_case'])
            
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
            # Option A: Only boxes with complete information
            info_columns = ['composition', 'hs_code', 'price', 'tariff_group']
            complete_info_mask = self.inventory_df[info_columns].notna().all(axis=1)
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
            section_boxes = remaining_inventory[remaining_inventory['section'] == section]
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
        if description_percentages:
            selected_df = pd.DataFrame(selected_boxes)
            description_compliance = self._check_description_percentages(
                selected_df, description_percentages
            )
            logger.info(f"Description compliance: {description_compliance}")
        
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
            return
        
        selected_df = pd.DataFrame(selected_boxes)
        
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
        if output_file:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                selected_df.to_excel(writer, sheet_name='Selected_Boxes', index=False)
                section_summary.to_excel(writer, sheet_name='Section_Summary')
                description_summary.to_excel(writer, sheet_name='Description_Summary')
                model_summary.to_excel(writer, sheet_name='Model_Summary')
            
            logger.info(f"Output saved to: {output_file}")
        
        return {
            'selected_boxes': selected_df,
            'section_summary': section_summary,
            'description_summary': description_summary,
            'model_summary': model_summary,
            'total_units': total_units,
            'total_boxes': total_boxes
        }
    
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
        results = self.generate_output(final_selected_boxes, output_file)
        
        logger.info("Selection process completed successfully")
        return results


def main():
    """Main function to run the inventory picker."""
    picker = InventoryPicker()
    
    # Example usage - replace with your actual parameters
    excel_file_path = "sample_inventory.xlsx"  # Replace with your inventory file path
    
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
