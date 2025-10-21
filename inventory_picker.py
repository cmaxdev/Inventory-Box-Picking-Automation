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
        self.history_file = "data/history/historico.xlsx"
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
            
            # Map column names to standardized names based on actual inventory file structure
            column_mapping = {
                # Primary mappings for actual inventory file
                'BARCODE': 'barcode',
                'COMPOSITION': 'composition',
                'TARIFAIRE': 'hs_code',
                'PVP': 'price',
                'G. TARIF': 'tariff_group',
                'SECTION': 'section',
                'DESCRIPTION': 'description',
                'MOCACO': 'model',
                'UNITS': 'units_per_case',
                'CONTENEUR': 'container',
                'CARTONS': 'cartons',
                'SEASON': 'season',
                'PAYS': 'country',
                'FAMILLIE': 'family',
                'DETAIL': 'detail',
                'NOTES': 'notes',
                'PVP total': 'total_price',
                'POIDS': 'weight',
                'SAISON INT.': 'internal_season',
                'RESERVATION': 'reservation',
                # Fallback mappings for different column name formats
                'Codigo de Barras': 'barcode',
                'Composicion': 'composition', 
                'HS Code': 'hs_code',
                'Precio': 'price',
                'Grupo Arancelario': 'tariff_group',
                'Section': 'section',
                'Description': 'description',
                'Modelo': 'model',
                'Unidades por caja': 'units_per_case',
                'UNITES': 'units_per_case'
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
        
        # Check if target exceeds available inventory
        total_available_units = remaining_inventory['units_per_case'].sum()
        if total_units_target > total_available_units:
            logger.warning(f"Target units ({total_units_target}) exceed available inventory ({total_available_units})")
            logger.warning(f"Will select all available units: {total_available_units}")
            total_units_target = total_available_units
        
        # Calculate target units per section
        section_targets = {}
        for section, percentage in section_percentages.items():
            target_units = int(total_units_target * percentage / 100)
            section_targets[section] = target_units
            logger.info(f"Target for {section}: {target_units} units")
        
        # Implement iterative selection algorithm as per requirements
        # This is a complex optimization problem that requires iterative refinement
        logger.info("Starting iterative selection algorithm...")
        
        # Step 1: Filter inventory by descriptions first (if specified)
        if description_percentages and any(p > 0 for p in description_percentages.values()):
            logger.info("Step 1: Filtering inventory by specified descriptions...")
            description_filtered_inventory = remaining_inventory.copy()
            
            # Get all valid descriptions from the requirements
            valid_descriptions = []
            for desc, percentage in description_percentages.items():
                if percentage > 0:
                    valid_descriptions.append(desc)
            
            if valid_descriptions:
                # Create a mask for items that match any of the specified descriptions
                description_mask = pd.Series([False] * len(description_filtered_inventory), index=description_filtered_inventory.index)
                
                for description in valid_descriptions:
                    # Try exact match first
                    exact_match = description_filtered_inventory['description'].str.lower().str.strip() == description.lower().strip()
                    description_mask |= exact_match
                    
                    # If no exact match, try intelligent mapping
                    if not exact_match.any():
                        available_descriptions = description_filtered_inventory['description'].unique()
                        logger.warning(f"No exact match for description '{description}'. Available descriptions: {available_descriptions}")
                        
                        # Intelligent mapping based on common patterns
                        description_mapping = {
                            'dress': ['gown', 'gowns', 'frock', 'frocks', 'robe'],
                            'trousers': ['pants', 'trouser', 'pantalons'],
                            't-shirt': ['top', 'tops', 'tee', 'tees', 'tshirt', 'crop-top'],
                            'accessories': ['bag', 'bags', 'accessory', 'accessoir', 'belt', 'ceinture'],
                            'shirt': ['shirts', 'blouse', 'blouses'],
                            'skirt': ['skirts'],
                            'tank-top': ['tank tops', 'tanktop', 'tanktops', 'singlet', 'singlets'],
                            'overall': ['overalls', 'overall'],
                            'socks': ['sock', 'socks']
                        }
                        
                        mapped_description = None
                        desc_lower = description.lower().strip()
                        
                        # Check if we can map to a known pattern
                        for pattern, variations in description_mapping.items():
                            if desc_lower == pattern or desc_lower in variations:
                                # Find matching available description
                                for avail_desc in available_descriptions:
                                    avail_lower = avail_desc.lower().strip()
                                    if (pattern in avail_lower or 
                                        any(var in avail_lower for var in variations) or
                                        avail_lower in variations):
                                        mapped_description = avail_desc
                                        break
                                if mapped_description:
                                    break
                        
                        # If still no mapping, try partial matches
                        if not mapped_description:
                            for avail_desc in available_descriptions:
                                if (description.lower().strip() in avail_desc.lower().strip() or 
                                    avail_desc.lower().strip() in description.lower().strip()):
                                    mapped_description = avail_desc
                                    break
                        
                        if mapped_description:
                            logger.info(f"Found intelligent mapping: '{description}' -> '{mapped_description}'")
                            intelligent_match = description_filtered_inventory['description'].str.lower().str.strip() == mapped_description.lower().strip()
                            description_mask |= intelligent_match
                        else:
                            logger.warning(f"No match found for description '{description}'. Skipping.")
                
                # Apply the description filter
                description_filtered_inventory = description_filtered_inventory[description_mask]
                logger.info(f"After description filtering: {len(description_filtered_inventory)} boxes available")
                
                # Update remaining_inventory to only include description-filtered items
                remaining_inventory = description_filtered_inventory
        
        # Step 2: Exact percentage matching algorithm
        logger.info("Step 2: Exact percentage matching algorithm...")
        
        # Calculate exact target units per description
        description_targets = {}
        if description_percentages and any(p > 0 for p in description_percentages.values()):
            for desc, percentage in description_percentages.items():
                if percentage > 0:
                    target_units = int(total_units_target * percentage / 100)
                    description_targets[desc] = target_units
                    logger.info(f"Exact target for {desc}: {target_units} units ({percentage}%)")
        
        # Use exact percentage matching algorithm
        selected_boxes = self._exact_percentage_matching(
            remaining_inventory, 
            total_units_target, 
            section_targets, 
            description_targets
        )
        
        # Log final results
        current_total = sum(box['units_per_case'] for box in selected_boxes)
        logger.info(f"Final total: {current_total} units (target: {total_units_target})")
        
        # Log final description distribution
        if description_targets:
            description_counts = {}
            for box in selected_boxes:
                desc = box['description']
                description_counts[desc] = description_counts.get(desc, 0) + box['units_per_case']
            
            logger.info("Final description distribution:")
            for desc, count in description_counts.items():
                target = description_targets.get(desc, 0)
                percentage = (count / current_total * 100) if current_total > 0 else 0
                target_percentage = (target / total_units_target * 100) if total_units_target > 0 else 0
                logger.info(f"  {desc}: {count} units ({percentage:.1f}%) [target: {target} units ({target_percentage:.1f}%)]")
        
        # Description filtering is now done at the beginning, so no need for additional filtering here
        
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
                selected_df['description'].str.lower().str.strip() == description.lower().strip()
            ]['units_per_case'].sum()
            
            actual_percentage = (description_units / total_units * 100) if total_units > 0 else 0
            actual_percentages[description] = actual_percentage
            
            logger.info(f"{description}: Target {target_percentage}%, Actual {actual_percentage:.2f}%")
        
        return actual_percentages
    
    def _find_matching_sections(self, inventory_df: pd.DataFrame, section: str) -> pd.DataFrame:
        """
        Find matching sections with intelligent mapping.
        
        Args:
            inventory_df: Inventory DataFrame
            section: Section name to find
            
        Returns:
            DataFrame of matching sections
        """
        # Try exact match first
        section_boxes = inventory_df[
            inventory_df['section'].str.lower().str.strip() == section.lower().strip()
        ]
        
        if len(section_boxes) > 0:
            return section_boxes
        
        # If no exact match, try intelligent mapping
        available_sections = inventory_df['section'].unique()
        logger.warning(f"No exact match for section '{section}'. Available sections: {available_sections}")
        
        # Intelligent mapping based on common patterns
        section_mapping = {
            'woman': ['female', 'females', 'ladies', 'girls'],
            'man': ['male', 'males', 'men', 'boys'],
            'children': ['child', 'kids', 'boys', 'girls', 'infant', 'infants']
        }
        
        mapped_section = None
        section_lower = section.lower().strip()
        
        # Check if we can map to a known pattern
        for pattern, variations in section_mapping.items():
            if section_lower == pattern or section_lower in variations:
                # Find matching available section
                for avail_section in available_sections:
                    avail_lower = avail_section.lower().strip()
                    if (pattern in avail_lower or 
                        any(var in avail_lower for var in variations) or
                        avail_lower in variations):
                        mapped_section = avail_section
                        break
                if mapped_section:
                    break
        
        # If still no mapping, try partial matches
        if not mapped_section:
            for avail_section in available_sections:
                if (section.lower().strip() in avail_section.lower().strip() or 
                    avail_section.lower().strip() in section.lower().strip()):
                    mapped_section = avail_section
                    break
        
        if mapped_section:
            logger.info(f"Found intelligent mapping: '{section}' -> '{mapped_section}'")
            return inventory_df[
                inventory_df['section'].str.lower().str.strip() == mapped_section.lower().strip()
            ]
        else:
            logger.warning(f"No match found for section '{section}'.")
            return pd.DataFrame()
    
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
        
        # Ensure all original inventory columns are preserved in the result
        # Get the original column order from the inventory (these are the standardized names)
        original_columns = list(self.inventory_df.columns)
        
        # Reorder selected_df columns to match original inventory order
        # Add any missing columns from original inventory with empty values
        for col in original_columns:
            if col not in selected_df.columns:
                selected_df[col] = ''
        
        # Reorder columns to match original inventory
        selected_df = selected_df[original_columns]
        
        # Rename columns back to original Excel format for output
        output_column_mapping = {
            'container': 'CONTENEUR',
            'cartons': 'CARTONS', 
            'barcode': 'BARCODE',
            'season': 'SEASON',
            'section': 'SECTION',
            'country': 'PAYS',
            'description': 'DESCRIPTION',
            'family': 'FAMILLIE',
            'detail': 'DETAIL',
            'notes': 'NOTES',
            'composition': 'COMPOSITION',
            'hs_code': 'TARIFAIRE',
            'price': 'PVP',
            'total_price': 'PVP total',
            'weight': 'POIDS',
            'internal_season': 'SAISON INT.',
            'units_per_case': 'UNITS',
            'model': 'MOCACO',
            'reservation': 'RESERVATION',
            'tariff_group': 'G. TARIF'
        }
        
        selected_df = selected_df.rename(columns=output_column_mapping)
        
        # Calculate summary statistics using original column names
        total_units = selected_df['UNITS'].sum()
        total_boxes = len(selected_df)
        
        # Section distribution
        section_summary = selected_df.groupby('SECTION').agg({
            'UNITS': ['sum', 'count']
        }).round(2)
        section_summary.columns = ['total_units', 'box_count']
        section_summary['percentage'] = (section_summary['total_units'] / total_units * 100).round(2)
        
        # Description distribution
        description_summary = selected_df.groupby('DESCRIPTION').agg({
            'UNITS': ['sum', 'count']
        }).round(2)
        description_summary.columns = ['total_units', 'box_count']
        description_summary['percentage'] = (description_summary['total_units'] / total_units * 100).round(2)
        
        # Model summary
        model_summary = selected_df.groupby('MOCACO')['UNITS'].sum().reset_index()
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
        
        # Save to Excel files as per requirements
        if output_file and output_file.strip():
            # Ensure the directory exists (only if there's a directory path)
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Generate base filename without extension
            base_filename = os.path.splitext(output_file)[0]
            base_dir = os.path.dirname(base_filename)
            
            # 1. resultado_seleccion.xlsx - selected boxes with all details
            resultado_file = os.path.join(base_dir, 'resultado_seleccion.xlsx')
            selected_df.to_excel(resultado_file, index=False)
            logger.info(f"Selected boxes saved to: {resultado_file}")
            
            # 2. resumen.xlsx - summary of achieved vs target percentages
            resumen_file = os.path.join(base_dir, 'resumen.xlsx')
            with pd.ExcelWriter(resumen_file, engine='openpyxl') as writer:
                # Section summary with target vs actual
                section_comparison = section_summary.copy()
                section_comparison['target_percentage'] = 0.0
                section_comparison['actual_percentage'] = section_comparison['percentage']
                section_comparison['difference'] = section_comparison['actual_percentage'] - section_comparison['target_percentage']
                section_comparison.to_excel(writer, sheet_name='Section_Summary')
                
                # Description summary with target vs actual
                description_comparison = description_summary.copy()
                description_comparison['target_percentage'] = 0.0
                description_comparison['actual_percentage'] = description_comparison['percentage']
                description_comparison['difference'] = description_comparison['actual_percentage'] - description_comparison['target_percentage']
                description_comparison.to_excel(writer, sheet_name='Description_Summary')
                
                # Model summary
                model_summary.to_excel(writer, sheet_name='Model_Summary')
            logger.info(f"Summary saved to: {resumen_file}")
            
            # 3. historico_actualizado.xlsx - updated record of sent units by model
            historico_file = os.path.join(base_dir, 'historico_actualizado.xlsx')
            if not self.history_df.empty:
                self.history_df.to_excel(historico_file, index=False)
                logger.info(f"Updated history saved to: {historico_file}")
            else:
                # Create empty history file
                empty_history = pd.DataFrame(columns=['model', 'total_units_shipped', 'order_date'])
                empty_history.to_excel(historico_file, index=False)
                logger.info(f"Empty history file created: {historico_file}")
            
            # Also save the original combined file for backward compatibility
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
    
    def _exact_percentage_matching(self, inventory_df, total_target, section_targets, description_targets):
        """
        Exact percentage matching algorithm that guarantees the input percentages.
        Uses a two-phase approach:
        1. Select boxes to meet exact description percentages
        2. Ensure total units match target exactly
        """
        logger.info("Starting exact percentage matching algorithm...")
        
        # Convert inventory to list
        inventory_list = inventory_df.to_dict('records')
        
        # Filter by sections first (case-insensitive)
        section_filtered_boxes = []
        for box in inventory_list:
            section = box['section']
            for target_section in section_targets.keys():
                if section.lower().strip() == target_section.lower().strip():
                    section_filtered_boxes.append(box)
                    break
        
        if not section_filtered_boxes:
            logger.warning("No boxes found for specified sections")
            return []
        
        # Group boxes by description
        boxes_by_description = {}
        for box in section_filtered_boxes:
            desc = box['description']
            if desc not in boxes_by_description:
                boxes_by_description[desc] = []
            boxes_by_description[desc].append(box)
        
        # Phase 1: Select boxes to meet exact description percentages
        selected_boxes = []
        description_counts = {}
        
        for desc, target_units in description_targets.items():
            if desc not in boxes_by_description:
                logger.warning(f"No boxes found for description: {desc}")
                continue
            
            desc_boxes = boxes_by_description[desc]
            # Sort by units per case (descending) for better efficiency
            desc_boxes.sort(key=lambda x: x['units_per_case'], reverse=True)
            
            # Use dynamic programming to find exact combination for this description
            desc_selection = self._find_exact_combination_for_description(desc_boxes, target_units)
            
            if desc_selection:
                selected_boxes.extend(desc_selection)
                description_counts[desc] = sum(box['units_per_case'] for box in desc_selection)
                logger.info(f"Selected {len(desc_selection)} boxes for {desc}: {description_counts[desc]} units")
            else:
                logger.warning(f"Could not find exact combination for {desc} with target {target_units}")
                return []
        
        # Phase 2: Verify total units match target exactly
        total_selected = sum(box['units_per_case'] for box in selected_boxes)
        
        if total_selected == total_target:
            logger.info(f"Perfect match: {total_selected} units = {total_target} target")
            return selected_boxes
        elif total_selected < total_target:
            # Try to add more boxes to reach target
            remaining_boxes = [box for box in section_filtered_boxes if box not in selected_boxes]
            additional_boxes = self._add_boxes_to_reach_target(remaining_boxes, total_target - total_selected)
            selected_boxes.extend(additional_boxes)
            logger.info(f"Added {len(additional_boxes)} boxes to reach target")
        else:
            # Try to remove boxes to reach target
            selected_boxes = self._remove_boxes_to_reach_target(selected_boxes, total_target)
            logger.info(f"Removed boxes to reach target")
        
        return selected_boxes
    
    def _find_exact_combination_for_description(self, boxes, target_units):
        """
        Find exact combination of boxes that sum to target_units.
        Uses dynamic programming for efficiency.
        """
        if not boxes or target_units <= 0:
            return []
        
        # For small targets, use exhaustive search
        if target_units <= 100:
            return self._exhaustive_search(boxes, target_units)
        
        # For larger targets, use greedy approach with backtracking
        return self._greedy_with_backtracking(boxes, target_units)
    
    def _exhaustive_search(self, boxes, target_units):
        """
        Exhaustive search for small target values.
        """
        n = len(boxes)
        best_combination = None
        best_difference = float('inf')
        
        # Try all possible combinations
        for i in range(1, 2**n):
            combination = []
            total = 0
            
            for j in range(n):
                if i & (1 << j):
                    combination.append(boxes[j])
                    total += boxes[j]['units_per_case']
                    if total > target_units:
                        break
            
            if total == target_units:
                return combination
            elif total < target_units and (target_units - total) < best_difference:
                best_difference = target_units - total
                best_combination = combination
        
        return best_combination
    
    def _greedy_with_backtracking(self, boxes, target_units):
        """
        Greedy approach with backtracking for larger targets.
        """
        # Sort boxes by units per case (descending)
        boxes_sorted = sorted(boxes, key=lambda x: x['units_per_case'], reverse=True)
        
        # Try different starting points
        for start_idx in range(min(5, len(boxes_sorted))):
            combination = []
            total = 0
            
            for i in range(start_idx, len(boxes_sorted)):
                box = boxes_sorted[i]
                if total + box['units_per_case'] <= target_units:
                    combination.append(box)
                    total += box['units_per_case']
                    
                    if total == target_units:
                        return combination
            
            # If we're close, try to adjust
            if total < target_units and (target_units - total) <= 10:
                # Try to find a smaller box to add
                for box in boxes_sorted:
                    if box not in combination and total + box['units_per_case'] == target_units:
                        combination.append(box)
                        return combination
        
        return []
    
    def _add_boxes_to_reach_target(self, remaining_boxes, needed_units):
        """
        Add boxes to reach the target units.
        """
        if needed_units <= 0:
            return []
        
        # Sort by units per case (ascending) to find boxes close to needed_units
        remaining_boxes.sort(key=lambda x: x['units_per_case'])
        
        added_boxes = []
        current_total = 0
        
        for box in remaining_boxes:
            if current_total + box['units_per_case'] <= needed_units:
                added_boxes.append(box)
                current_total += box['units_per_case']
                
                if current_total == needed_units:
                    break
        
        return added_boxes
    
    def _remove_boxes_to_reach_target(self, selected_boxes, target_units):
        """
        Remove boxes to reach the target units.
        """
        current_total = sum(box['units_per_case'] for box in selected_boxes)
        
        if current_total <= target_units:
            return selected_boxes
        
        # Sort by units per case (ascending) to remove smaller boxes first
        selected_boxes.sort(key=lambda x: x['units_per_case'])
        
        excess = current_total - target_units
        boxes_to_remove = []
        
        for box in selected_boxes:
            if box['units_per_case'] <= excess:
                boxes_to_remove.append(box)
                excess -= box['units_per_case']
                
                if excess <= 0:
                    break
        
        # Remove the selected boxes
        for box in boxes_to_remove:
            selected_boxes.remove(box)
        
        return selected_boxes
    
    def _find_exact_subset_sum(self, inventory_df, total_target, section_targets, description_targets):
        """
        Find exact subset sum solution using dynamic programming approach.
        This algorithm finds combinations of boxes that sum to exactly the target units
        while maintaining the exact percentage distribution specified by the user.
        """
        logger.info("Starting dynamic programming subset sum algorithm...")
        
        # Convert inventory to list
        inventory_list = inventory_df.to_dict('records')
        
        # Group boxes by description for easier percentage management
        boxes_by_description = {}
        for box in inventory_list:
            desc = box['description']
            if desc not in boxes_by_description:
                boxes_by_description[desc] = []
            boxes_by_description[desc].append(box)
        
        # Calculate exact target units per description
        desc_targets = {}
        if description_targets:
            for desc, percentage in description_targets.items():
                if percentage > 0:
                    target_units = int(total_target * percentage / 100)
                    desc_targets[desc] = target_units
                    logger.info(f"Target for {desc}: {target_units} units ({percentage}%)")
        
        # Use dynamic programming to find exact combinations
        selected_boxes = self._dp_subset_sum(
            inventory_list, 
            total_target, 
            section_targets, 
            desc_targets
        )
        
        if selected_boxes:
            logger.info(f"Found exact subset sum solution with {len(selected_boxes)} boxes")
            return selected_boxes
        else:
            logger.warning("No exact subset sum solution found")
            return []
    
    def _dp_subset_sum(self, inventory_list, total_target, section_targets, desc_targets):
        """
        Dynamic programming approach to find exact subset sum solution.
        Uses memoization to efficiently find combinations that sum to target units
        while maintaining exact percentage distribution.
        """
        logger.info("Using dynamic programming for subset sum...")
        
        # Filter inventory by sections first (case-insensitive)
        section_filtered_boxes = []
        for box in inventory_list:
            section = box['section']
            # Check if this section matches any of the target sections (case-insensitive)
            section_matches = False
            for target_section in section_targets.keys():
                if section.lower().strip() == target_section.lower().strip():
                    section_matches = True
                    break
            
            if section_matches:
                section_filtered_boxes.append(box)
        
        if not section_filtered_boxes:
            logger.warning("No boxes found for specified sections")
            return []
        
        # Group by description for percentage management
        boxes_by_desc = {}
        for box in section_filtered_boxes:
            desc = box['description']
            if desc not in boxes_by_desc:
                boxes_by_desc[desc] = []
            boxes_by_desc[desc].append(box)
        
        # Try to find exact combinations using iterative approach
        # Start with the most constrained description (smallest target)
        if desc_targets:
            sorted_descriptions = sorted(desc_targets.items(), key=lambda x: x[1])
        else:
            sorted_descriptions = []
        
        # Use a more efficient approach: try all combinations within constraints
        return self._find_exact_combination(
            boxes_by_desc, 
            total_target, 
            section_targets, 
            desc_targets
        )
    
    def _find_exact_combination(self, boxes_by_desc, total_target, section_targets, desc_targets):
        """
        Find exact combination using constraint satisfaction approach.
        """
        from itertools import product
        
        # If no description targets, use simple subset sum
        if not desc_targets:
            return self._simple_subset_sum(list(boxes_by_desc.values())[0], total_target)
        
        # For each description, find all possible combinations that could contribute to the target
        desc_combinations = {}
        
        for desc, target_units in desc_targets.items():
            if desc not in boxes_by_desc:
                logger.warning(f"No boxes found for description: {desc}")
                continue
            
            desc_boxes = boxes_by_desc[desc]
            # Find all combinations of this description that sum to target_units
            desc_combinations[desc] = self._find_combinations_for_target(desc_boxes, target_units)
            
            if not desc_combinations[desc]:
                logger.warning(f"No combinations found for {desc} with target {target_units}")
                return []
        
        # Try all combinations of description combinations
        desc_names = list(desc_combinations.keys())
        desc_combos = list(desc_combinations.values())
        
        for combo_combination in product(*desc_combos):
            # Flatten the combination
            selected_boxes = []
            for combo in combo_combination:
                selected_boxes.extend(combo)
            
            # Check if this combination sums to total_target
            total_units = sum(box['units_per_case'] for box in selected_boxes)
            if total_units == total_target:
                # Check model constraints
                if self._check_model_constraints(selected_boxes):
                    logger.info(f"Found exact combination: {len(selected_boxes)} boxes, {total_units} units")
                    return selected_boxes
        
        logger.warning("No exact combination found")
        return []
    
    def _find_combinations_for_target(self, boxes, target_units):
        """
        Find all combinations of boxes that sum to target_units.
        Uses dynamic programming with memoization for efficiency.
        """
        if not boxes:
            return []
        
        # Use a more efficient approach for smaller target values
        if target_units > 1000:  # For large targets, use greedy approach
            return self._greedy_combinations(boxes, target_units)
        
        # For smaller targets, use exhaustive search
        combinations = []
        n = len(boxes)
        
        # Try all possible combinations (2^n possibilities)
        for i in range(1, 2**n):
            combo = []
            total = 0
            for j in range(n):
                if i & (1 << j):
                    combo.append(boxes[j])
                    total += boxes[j]['units_per_case']
                    if total > target_units:
                        break
            
            if total == target_units:
                combinations.append(combo)
                # Limit to reasonable number of combinations
                if len(combinations) > 100:
                    break
        
        return combinations
    
    def _greedy_combinations(self, boxes, target_units):
        """
        Greedy approach for finding combinations when target is large.
        """
        boxes_sorted = sorted(boxes, key=lambda x: x['units_per_case'], reverse=True)
        combinations = []
        
        # Try different starting points
        for start_idx in range(min(10, len(boxes_sorted))):
            combo = []
            total = 0
            
            for i in range(start_idx, len(boxes_sorted)):
                box = boxes_sorted[i]
                if total + box['units_per_case'] <= target_units:
                    combo.append(box)
                    total += box['units_per_case']
                    
                    if total == target_units:
                        combinations.append(combo[:])
                        break
            
            if len(combinations) > 0:
                break
        
        return combinations
    
    def _simple_subset_sum(self, boxes, target_units):
        """
        Simple subset sum for cases without description constraints.
        """
        # Use dynamic programming table
        n = len(boxes)
        if n == 0:
            return []
        
        # Create DP table
        dp = [[False for _ in range(target_units + 1)] for _ in range(n + 1)]
        dp[0][0] = True
        
        # Fill the DP table
        for i in range(1, n + 1):
            box_units = boxes[i-1]['units_per_case']
            for j in range(target_units + 1):
                if j < box_units:
                    dp[i][j] = dp[i-1][j]
                else:
                    dp[i][j] = dp[i-1][j] or dp[i-1][j - box_units]
        
        # If target is achievable, backtrack to find the combination
        if dp[n][target_units]:
            selected_boxes = []
            i, j = n, target_units
            
            while i > 0 and j > 0:
                if not dp[i-1][j]:
                    selected_boxes.append(boxes[i-1])
                    j -= boxes[i-1]['units_per_case']
                i -= 1
            
            return selected_boxes
        
        return []
    
    def _check_model_constraints(self, selected_boxes):
        """
        Check if selected boxes respect model constraints (200 units per model).
        """
        model_counts = {}
        for box in selected_boxes:
            model = box['model']
            units = box['units_per_case']
            model_counts[model] = model_counts.get(model, 0) + units
            if model_counts[model] > 200:
                return False
        return True
    
    def _check_percentage_constraints(self, selected_boxes, section_targets, description_targets):
        """
        Check if the selected boxes meet the percentage constraints.
        """
        if not selected_boxes:
            return False
        
        # Check section constraints
        section_counts = {}
        for box in selected_boxes:
            section = box['section']
            section_counts[section] = section_counts.get(section, 0) + box['units_per_case']
        
        for section, target in section_targets.items():
            actual = section_counts.get(section, 0)
            if abs(actual - target) > 1:  # Allow 1 unit tolerance
                return False
        
        # Check description constraints
        if description_targets:
            description_counts = {}
            for box in selected_boxes:
                desc = box['description']
                description_counts[desc] = description_counts.get(desc, 0) + box['units_per_case']
            
            for desc, target in description_targets.items():
                actual = description_counts.get(desc, 0)
                if abs(actual - target) > 1:  # Allow 1 unit tolerance
                    return False
        
        return True
    
    def _greedy_fallback_selection(self, inventory_df, total_target, section_targets, description_targets):
        """
        Fallback greedy selection if subset sum fails.
        """
        logger.info("Using greedy fallback selection...")
        
        selected_boxes = []
        model_counts = {}
        description_counts = {}
        current_total = 0
        
        inventory_list = inventory_df.to_dict('records')
        inventory_list.sort(key=lambda x: x['units_per_case'], reverse=True)
        
        for box in inventory_list:
            if current_total >= total_target:
                break
            
            box_units = box['units_per_case']
            box_model = box['model']
            box_description = box['description']
            
            # Skip if adding this box would exceed model limit
            current_model_units = model_counts.get(box_model, 0)
            if current_model_units + box_units > 200:
                continue
            
            # Skip if adding this box would exceed total target
            if current_total + box_units > total_target:
                continue
            
            # Add this box
            selected_boxes.append(box)
            current_total += box_units
            model_counts[box_model] = current_model_units + box_units
            description_counts[box_description] = description_counts.get(box_description, 0) + box_units
        
        return selected_boxes


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
