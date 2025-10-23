#!/usr/bin/env python3
"""
Client Order Processor - Simple Interface for Inventory Box Picking

This script provides a simple, client-friendly interface for processing orders.
Clients can specify their requirements and get automated box selection results.

Usage Examples:
- "40,000 units with 10% men, 90% women, 10% accessories, 30% pants"
- "5,000 units with 60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers"

Author: AI Assistant
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from inventory_picker import InventoryPicker
from file_manager import FileManager
from excel_registry_utils import auto_register_excel, ExcelFileCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client_orders.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ClientOrderProcessor:
    """Client-friendly order processing system."""
    
    def __init__(self):
        self.picker = InventoryPicker()
        self.file_manager = FileManager()
        self.excel_creator = ExcelFileCreator()
        self.client_orders_file = "data/orders/client_orders_history.xlsx"
        self.client_orders_df = None
        
    def load_client_orders_history(self):
        """Load client orders history."""
        try:
            if os.path.exists(self.client_orders_file):
                self.client_orders_df = pd.read_excel(self.client_orders_file)
                logger.info(f"Loaded {len(self.client_orders_df)} client orders from history")
            else:
                self.client_orders_df = pd.DataFrame(columns=[
                    'order_date', 'client_name', 'total_units', 'section_percentages', 
                    'description_percentages', 'selected_boxes', 'actual_units',
                    'compliance_summary', 'output_file'
                ])
                logger.info("Created new client orders history")
        except Exception as e:
            logger.error(f"Error loading client orders history: {str(e)}")
            self.client_orders_df = pd.DataFrame(columns=[
                'order_date', 'client_name', 'total_units', 'section_percentages', 
                'description_percentages', 'selected_boxes', 'actual_units',
                'compliance_summary', 'output_file'
            ])
    
    def save_client_order(self, order_data: Dict):
        """Save client order to history."""
        try:
            new_order = pd.DataFrame([order_data])
            self.client_orders_df = pd.concat([self.client_orders_df, new_order], ignore_index=True)
            self.client_orders_df.to_excel(self.client_orders_file, index=False)
            
            # Register the client orders history file in the registry
            try:
                self.file_manager.registry.register_file(
                    file_path=self.client_orders_file,
                    category='client_orders',
                    subcategory='history',
                    description='Client orders history tracking file',
                    tags=['historical', 'client_tracking']
                )
                logger.info(f"Client orders history file registered in Excel registry: {self.client_orders_file}")
            except Exception as e:
                logger.warning(f"Could not register client orders history file in registry: {e}")
            
            logger.info("Client order saved to history")
        except Exception as e:
            logger.error(f"Error saving client order: {str(e)}")
    
    def parse_client_requirements(self, total_units: int, requirements: str) -> Dict:
        """
        Parse client requirements from natural language.
        
        Args:
            total_units: Total units requested
            requirements: String like "10% men, 90% women, 10% accessories, 30% pants"
            
        Returns:
            Dict with parsed percentages
        """
        logger.info(f"Parsing requirements: {requirements}")
        
        # Default values (will be populated dynamically based on requirements)
        section_percentages = {}
        description_percentages = {}
        
        # Parse section percentages dynamically
        # Look for any section names mentioned in the requirements
        import re
        
        # Common section patterns with flexible mapping
        section_patterns = [
            (r'(\d+(?:\.\d+)?)\s*%\s*(women|woman|female|females)', 'Woman'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(men|man|male|males)', 'Man'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(children|child|kids|kid|boys|boy|girls|girl)', 'Children')
        ]
        
        for pattern, section_name in section_patterns:
            match = re.search(pattern, requirements.lower())
            if match:
                percentage = float(match.group(1))
                section_percentages[section_name] = percentage
        
        # If no sections specified, try to infer from context
        if sum(section_percentages.values()) == 0:
            # Look for any percentage without explicit section
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', requirements.lower())
            if percentage_matches:
                # If only one percentage found, assume it's for the main section
                if len(percentage_matches) == 1:
                    section_percentages["Woman"] = float(percentage_matches[0])
                else:
                    # Multiple percentages without sections - distribute equally
                    total_pct = sum(float(p) for p in percentage_matches)
                    if total_pct <= 100:
                        section_percentages["Woman"] = total_pct
                    else:
                        section_percentages["Woman"] = 100.0
            else:
                # No percentages found, default to Woman 100%
                section_percentages["Woman"] = 100.0
        
        # Parse description percentages dynamically with flexible mapping
        # Support both formats: "50% dress" and "dress 50%"
        # Include both English and French terms
        description_patterns = [
            # Format: "50% dress" or "dress 50%" - English terms for DESCRIPTION column
            (r'(\d+(?:\.\d+)?)\s*%\s*(dress|dresses|gown|gowns)|(dress|dresses|gown|gowns)\s*(\d+(?:\.\d+)?)\s*%', 'DRESS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(trousers|pants)|(trousers|pants)\s*(\d+(?:\.\d+)?)\s*%', 'TROUSERS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(t-shirt|tshirt|t shirt|top|tops)|(t-shirt|tshirt|t shirt|top|tops)\s*(\d+(?:\.\d+)?)\s*%', 'T-SHIRT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(accessories|accessory|bag|bags)|(accessories|accessory|bag|bags)\s*(\d+(?:\.\d+)?)\s*%', 'ACCESSORIES'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(shirt|shirts)|(shirt|shirts)\s*(\d+(?:\.\d+)?)\s*%', 'SHIRT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(skirt|skirts)|(skirt|skirts)\s*(\d+(?:\.\d+)?)\s*%', 'SKIRT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(o\.garment|o garment|other garment)|(o\.garment|o garment|other garment)\s*(\d+(?:\.\d+)?)\s*%', 'O.GARMENT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(overall|overalls)|(overall|overalls)\s*(\d+(?:\.\d+)?)\s*%', 'OVERALL'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(leggings|legging)|(leggings|legging)\s*(\d+(?:\.\d+)?)\s*%', 'LEGGINGS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(bib overall|bib overalls)|(bib overall|bib overalls)\s*(\d+(?:\.\d+)?)\s*%', 'BIB OVERALL'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(jacket|jackets)|(jacket|jackets)\s*(\d+(?:\.\d+)?)\s*%', 'JACKET'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(coat|coats)|(coat|coats)\s*(\d+(?:\.\d+)?)\s*%', 'COAT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(sweater|sweaters)|(sweater|sweaters)\s*(\d+(?:\.\d+)?)\s*%', 'SWEATER'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(blouse|blouses)|(blouse|blouses)\s*(\d+(?:\.\d+)?)\s*%', 'BLOUSE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(polo|polos)|(polo|polos)\s*(\d+(?:\.\d+)?)\s*%', 'POLO'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(hoodie|hoodies)|(hoodie|hoodies)\s*(\d+(?:\.\d+)?)\s*%', 'HOODIE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(jeans|jean)|(jeans|jean)\s*(\d+(?:\.\d+)?)\s*%', 'JEANS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(shorts|short)|(shorts|short)\s*(\d+(?:\.\d+)?)\s*%', 'SHORTS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(underwear|underwears)|(underwear|underwears)\s*(\d+(?:\.\d+)?)\s*%', 'UNDERWEAR'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(socks|sock)|(socks|sock)\s*(\d+(?:\.\d+)?)\s*%', 'SOCKS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(tank-top|tank tops|tanktop|tanktops)|(tank-top|tank tops|tanktop|tanktops)\s*(\d+(?:\.\d+)?)\s*%', 'TANK-TOP'),
            
            # French terms for FAMILLIE column - these should be treated as family categories
            (r'(\d+(?:\.\d+)?)\s*%\s*(robe|robes)|(robe|robes)\s*(\d+(?:\.\d+)?)\s*%', 'ROBE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(pantalons|pantalon)|(pantalons|pantalon)\s*(\d+(?:\.\d+)?)\s*%', 'PANTALONS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(chemise|chemises)|(chemise|chemises)\s*(\d+(?:\.\d+)?)\s*%', 'CHEMISE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(accessoir|accessoires)|(accessoir|accessoires)\s*(\d+(?:\.\d+)?)\s*%', 'ACCESSOIR'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(combinaison|combinaisons)|(combinaison|combinaisons)\s*(\d+(?:\.\d+)?)\s*%', 'COMBINAISON'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(exterieur|extérieur)|(exterieur|extérieur)\s*(\d+(?:\.\d+)?)\s*%', 'EXTERIEUR'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(t-shirt|tshirt|t shirt)|(t-shirt|tshirt|t shirt)\s*(\d+(?:\.\d+)?)\s*%', 'T-SHIRT'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(jupe|jupes)|(jupe|jupes)\s*(\d+(?:\.\d+)?)\s*%', 'JUPE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(chaussure|chaussures)|(chaussure|chaussures)\s*(\d+(?:\.\d+)?)\s*%', 'CHAUSSURE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(sacs|sac)|(sacs|sac)\s*(\d+(?:\.\d+)?)\s*%', 'SACS'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(maille|mailles)|(maille|mailles)\s*(\d+(?:\.\d+)?)\s*%', 'MAILLE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(ensemble|ensembles)|(ensemble|ensembles)\s*(\d+(?:\.\d+)?)\s*%', 'ENSEMBLE'),
            (r'(\d+(?:\.\d+)?)\s*%\s*(bas|bases)|(bas|bases)\s*(\d+(?:\.\d+)?)\s*%', 'BAS')
        ]
        
        for pattern, description_name in description_patterns:
            match = re.search(pattern, requirements.lower())
            if match:
                # Handle both formats: "50% dress" (group 1) or "dress 50%" (group 4)
                if match.group(1):  # Format: "50% dress"
                    percentage = float(match.group(1))
                else:  # Format: "dress 50%"
                    percentage = float(match.group(4))
                description_percentages[description_name] = percentage
        
        # If no descriptions specified, default to equal distribution of available descriptions
        if sum(description_percentages.values()) == 0:
            description_percentages = {"DRESS": 33.33, "TROUSERS": 33.33, "LEGGINGS": 33.34}
        
        # Use the client's requirements as-is, don't distribute remaining percentages
        # The client knows what they want, so we respect their exact specifications
        total_desc_pct = sum(description_percentages.values())
        if total_desc_pct > 100:
            # If percentages exceed 100%, normalize them
            for key in description_percentages:
                description_percentages[key] = (description_percentages[key] / total_desc_pct) * 100
        
        logger.info(f"Parsed section percentages: {section_percentages}")
        logger.info(f"Parsed description percentages: {description_percentages}")
        
        return {
            "section_percentages": section_percentages,
            "description_percentages": description_percentages
        }
    
    def _extract_percentage(self, text: str, keywords: List[str]) -> float:
        """Extract percentage value for given keywords."""
        import re
        
        # Look for patterns like "10% men", "men 10%", "10 percent men"
        patterns = [
            rf'(\d+(?:\.\d+)?)\s*%\s*{"|".join(keywords)}',
            rf'{"|".join(keywords)}\s*(\d+(?:\.\d+)?)\s*%',
            rf'(\d+(?:\.\d+)?)\s*percent\s*{"|".join(keywords)}',
            rf'{"|".join(keywords)}\s*(\d+(?:\.\d+)?)\s*percent'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing percentage for {keywords}: {e}")
                    continue
        
        return 0.0
    
    @auto_register_excel(
        category='client_orders',
        subcategory='processed',
        description='Client order processing results',
        tags=['client_data', 'order_results']
    )
    def process_client_order(
        self, 
        client_name: str,
        total_units: int, 
        requirements: str,
        inventory_file: str = "data/inventory/sample_inventory.xlsx",
        require_complete_info: bool = True
    ) -> Dict:
        """
        Process a client order with natural language requirements.
        
        Args:
            client_name: Name of the client
            total_units: Total units requested
            requirements: Natural language requirements
            inventory_file: Path to inventory file
            require_complete_info: Whether to require complete product information
            
        Returns:
            Dict with order results
        """
        logger.info(f"Processing order for {client_name}: {total_units} units")
        logger.info(f"Requirements: {requirements}")
        
        try:
            # Parse requirements
            parsed_reqs = self.parse_client_requirements(total_units, requirements)
            if not parsed_reqs:
                raise Exception("Failed to parse client requirements")
            
            # Load inventory
            if not self.picker.load_inventory(inventory_file):
                raise Exception(f"Failed to load inventory from {inventory_file}")
            
            if not self.picker.load_history():
                raise Exception("Failed to load order history")
            
            # Generate output file path (save in data/orders/ directory)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"data/orders/client_order_{client_name}_{timestamp}.xlsx"
            
            # Process the order
            results = self.picker.run_selection_process(
                excel_file_path=inventory_file,
                require_complete_info=require_complete_info,
                section_percentages=parsed_reqs["section_percentages"],
                family_percentages=parsed_reqs["description_percentages"],
                total_units_target=total_units,
                output_file=output_file
            )
            
            # Prepare order summary
            order_summary = {
                'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'client_name': client_name,
                'total_units': total_units,
                'section_percentages': str(parsed_reqs["section_percentages"]),
                'description_percentages': str(parsed_reqs["description_percentages"]),
                'selected_boxes': results['total_boxes'],
                'actual_units': results['total_units'],
                'compliance_summary': self._generate_compliance_summary(results),
                'output_file': results.get('output_file', output_file)
            }
            
            # Save to client orders history
            self.save_client_order(order_summary)
            
            # Print client-friendly summary
            self._print_client_summary(client_name, results, parsed_reqs)
            
            return {
                'success': True,
                'results': results,
                'order_summary': order_summary
            }
            
        except Exception as e:
            logger.error(f"Error processing client order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_compliance_summary(self, results: Dict) -> str:
        """Generate a compliance summary for the client."""
        try:
            section_summary = results['section_summary']
            description_summary = results['description_summary']
            
            compliance_parts = []
            
            # Section compliance
            for section in section_summary.index:
                actual_pct = section_summary.loc[section, 'percentage']
                compliance_parts.append(f"{section}: {actual_pct:.1f}%")
            
            # Description compliance
            for desc in description_summary.index:
                actual_pct = description_summary.loc[desc, 'percentage']
                compliance_parts.append(f"{desc}: {actual_pct:.1f}%")
            
            return "; ".join(compliance_parts)
            
        except Exception as e:
            return f"Error generating compliance summary: {str(e)}"
    
    def _print_client_summary(self, client_name: str, results: Dict, parsed_reqs: Dict):
        """Print a client-friendly summary of the order."""
        print("\n" + "="*80)
        print(f"ORDER COMPLETED FOR: {client_name.upper()}")
        print("="*80)
        print(f"Total Boxes Selected: {results['total_boxes']}")
        print(f"Total Units: {results['total_units']:,}")
        print()
        
        print("SECTION DISTRIBUTION:")
        section_summary = results['section_summary']
        for section in section_summary.index:
            target_pct = parsed_reqs['section_percentages'].get(section, 0)
            actual_pct = section_summary.loc[section, 'percentage']
            boxes = section_summary.loc[section, 'box_count']
            print(f"   {section}: {actual_pct:.1f}% ({boxes} boxes) [Target: {target_pct:.1f}%]")
        
        print()
        print("DESCRIPTION DISTRIBUTION:")
        description_summary = results['description_summary']
        for desc in description_summary.index:
            target_pct = parsed_reqs['description_percentages'].get(desc, 0)
            actual_pct = description_summary.loc[desc, 'percentage']
            boxes = description_summary.loc[desc, 'box_count']
            print(f"   {desc}: {actual_pct:.1f}% ({boxes} boxes) [Target: {target_pct:.1f}%]")
        
        print()
        print("SUCCESS: Order processed successfully!")
        output_file = results.get('output_file', 'N/A')
        if output_file != 'N/A' and output_file:
            full_path = os.path.abspath(output_file)
            print(f"Results saved to: {full_path}")
            print(f"Copy this path: {full_path}")
        else:
            print(f"Results saved to: {output_file}")
        print("="*80)


def interactive_order_processor():
    """Interactive interface for processing client orders."""
    processor = ClientOrderProcessor()
    processor.load_client_orders_history()
    
    print("INVENTORY BOX PICKING - CLIENT ORDER PROCESSOR")
    print("="*60)
    print("Welcome! I'll help you process client orders automatically.")
    print()
    
    while True:
        try:
            print("\nNEW CLIENT ORDER")
            print("-" * 30)
            
            # Get client information
            client_name = input("Client Name: ").strip()
            if not client_name:
                print("ERROR: Client name is required!")
                continue
            
            # Get total units
            total_units_input = input("Total Units Requested: ").strip()
            try:
                total_units = int(total_units_input.replace(',', ''))
            except ValueError:
                print("ERROR: Please enter a valid number for total units!")
                continue
            
            # Get requirements
            print("\nREQUIREMENTS (Examples below)")
            print("Examples:")
            print("  - 10% men, 90% women, 10% accessories, 30% pants")
            print("  - 60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers")
            print("  - 50% women, 50% men, 25% accessories, 75% tops")
            
            requirements = input("\nEnter Requirements: ").strip()
            if not requirements:
                print("ERROR: Requirements are required!")
                continue
            
            # Get inventory file
            inventory_file = input("Inventory File (press Enter for 'sample_inventory.xlsx'): ").strip()
            if not inventory_file:
                inventory_file = "sample_inventory.xlsx"
            
            # Get information completeness requirement
            info_req = input("Require complete product information? (y/n, default=y): ").strip().lower()
            require_complete_info = info_req != 'n'
            
            # Process the order
            print(f"\nProcessing order for {client_name}...")
            result = processor.process_client_order(
                client_name=client_name,
                total_units=total_units,
                requirements=requirements,
                inventory_file=inventory_file,
                require_complete_info=require_complete_info
            )
            
            if result['success']:
                print("SUCCESS: Order completed successfully!")
            else:
                print(f"ERROR: Order failed: {result['error']}")
            
            # Ask if user wants to process another order
            continue_choice = input("\nProcess another order? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}")
    
    print("\nCLIENT ORDERS SUMMARY")
    print("-" * 30)
    if not processor.client_orders_df.empty:
        print(f"Total orders processed: {len(processor.client_orders_df)}")
        print("Recent orders:")
        recent_orders = processor.client_orders_df.tail(5)
        for _, order in recent_orders.iterrows():
            print(f"  - {order['client_name']}: {order['total_units']} units ({order['order_date']})")
    else:
        print("No orders processed yet.")
    
    print("\nThank you for using the Inventory Box Picking system!")


def main():
    """Main function with example usage."""
    processor = ClientOrderProcessor()
    processor.load_client_orders_history()
    
    print("INVENTORY BOX PICKING - CLIENT ORDER PROCESSOR")
    print("="*60)
    
    # Example 1: Client wants 40,000 units with 10% men, 90% women, 10% accessories, 30% pants
    print("\nEXAMPLE 1: Large Order")
    print("-" * 40)
    
    result1 = processor.process_client_order(
        client_name="ABC Fashion Co.",
        total_units=40000,
        requirements="10% men, 90% women, 10% accessories, 30% pants",
        inventory_file="sample_inventory.xlsx",
        require_complete_info=False  # Allow incomplete info for larger selection
    )
    
    # Example 2: Client wants 5,000 units with specific distribution
    print("\nEXAMPLE 2: Medium Order")
    print("-" * 40)
    
    result2 = processor.process_client_order(
        client_name="Fashion Retail Inc.",
        total_units=5000,
        requirements="60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers",
        inventory_file="sample_inventory.xlsx",
        require_complete_info=True
    )
    
    # Example 3: Client wants simple order
    print("\nEXAMPLE 3: Simple Order")
    print("-" * 40)
    
    result3 = processor.process_client_order(
        client_name="Local Store",
        total_units=1000,
        requirements="50% women, 50% men, 25% accessories, 75% tops",
        inventory_file="sample_inventory.xlsx",
        require_complete_info=True
    )
    
    print("\nAll example orders completed!")
    print("Check the generated Excel files for detailed results.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_order_processor()
    else:
        main()
