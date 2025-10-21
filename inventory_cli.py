#!/usr/bin/env python3
"""
Command Line Interface for Inventory Box Picking System

This script provides a command-line interface that matches the specified requirements:
- Input Excel file: inventory.xlsx
- Optional historical file: historico.xlsx
- --info-completa flag for data completeness filtering
- --section and --description parameters for percentage-based selection
- Generates three output files: resultado_seleccion.xlsx, resumen.xlsx, historico_actualizado.xlsx

Usage:
    python inventory_cli.py inventory.xlsx --section '{"Woman": 50, "Men": 30, "Children": 20}' --description '{"Accessories": 40, "Trousers": 60}'
    python inventory_cli.py inventory.xlsx --info-completa --section '{"Woman": 70, "Men": 30}' --description '{"Dress": 50, "Trousers": 50}'

Author: AI Assistant
Version: 1.0
"""

import argparse
import json
import sys
import os
from pathlib import Path
from inventory_picker import InventoryPicker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_percentages(percentages_str):
    """Parse percentage string into dictionary."""
    try:
        percentages = json.loads(percentages_str)
        if not isinstance(percentages, dict):
            raise ValueError("Percentages must be a dictionary")
        
        # Validate that percentages are numeric
        for key, value in percentages.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Percentage for '{key}' must be numeric")
            if value < 0 or value > 100:
                raise ValueError(f"Percentage for '{key}' must be between 0 and 100")
        
        return percentages
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format for percentages: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing percentages: {e}")


def validate_input_file(file_path):
    """Validate that input file exists and is readable."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        raise ValueError("Input file must be an Excel file (.xlsx or .xls)")
    
    return True


def main():
    """Main function for command line interface."""
    parser = argparse.ArgumentParser(
        description='Inventory Box Picking System - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inventory_cli.py inventory.xlsx --section '{"Woman": 50, "Men": 30, "Children": 20}' --description '{"Accessories": 40, "Trousers": 60}'
  python inventory_cli.py inventory.xlsx --info-completa --section '{"Woman": 70, "Men": 30}' --description '{"Dress": 50, "Trousers": 50}'
  python inventory_cli.py inventory.xlsx --historico historico.xlsx --section '{"Woman": 100}' --description '{"Dress": 100}'
        """
    )
    
    # Required arguments
    parser.add_argument('inventory_file', 
                       help='Path to inventory Excel file (inventory.xlsx)')
    
    # Optional arguments
    parser.add_argument('--historico', 
                       help='Path to historical Excel file (historico.xlsx)',
                       default='data/history/historico.xlsx')
    
    parser.add_argument('--info-completa', 
                       action='store_true',
                       help='Include only rows with complete information (Composicion, HS Code, Precio, Grupo Arancelario)')
    
    parser.add_argument('--section', 
                       required=True,
                       help='Section percentages as JSON string (e.g., \'{"Woman": 50, "Men": 30, "Children": 20}\')')
    
    parser.add_argument('--description', 
                       required=True,
                       help='Description percentages as JSON string (e.g., \'{"Accessories": 40, "Trousers": 60}\')')
    
    parser.add_argument('--total-units', 
                       type=int,
                       default=1000,
                       help='Total units target (default: 1000)')
    
    parser.add_argument('--max-units-per-model', 
                       type=int,
                       default=200,
                       help='Maximum units per model (default: 200)')
    
    parser.add_argument('--output-dir', 
                       default='data/orders',
                       help='Output directory for generated files (default: data/orders)')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate input file
        validate_input_file(args.inventory_file)
        
        # Parse percentages
        section_percentages = parse_percentages(args.section)
        description_percentages = parse_percentages(args.description)
        
        # Validate that percentages add up to 100%
        section_total = sum(section_percentages.values())
        if abs(section_total - 100) > 0.01:  # Allow small floating point errors
            logger.warning(f"Section percentages sum to {section_total}%, not 100%")
        
        description_total = sum(description_percentages.values())
        if abs(description_total - 100) > 0.01:  # Allow small floating point errors
            logger.warning(f"Description percentages sum to {description_total}%, not 100%")
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Initialize inventory picker
        picker = InventoryPicker()
        picker.max_units_per_model = args.max_units_per_model
        
        # Set history file if provided
        if args.historico and os.path.exists(args.historico):
            picker.history_file = args.historico
        
        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(args.output_dir, f'selection_{timestamp}.xlsx')
        
        # Run selection process
        logger.info("Starting inventory selection process...")
        logger.info(f"Inventory file: {args.inventory_file}")
        logger.info(f"Historical file: {args.historico}")
        logger.info(f"Complete info required: {args.info_completa}")
        logger.info(f"Section percentages: {section_percentages}")
        logger.info(f"Description percentages: {description_percentages}")
        logger.info(f"Total units target: {args.total_units}")
        logger.info(f"Max units per model: {args.max_units_per_model}")
        
        results = picker.run_selection_process(
            excel_file_path=args.inventory_file,
            require_complete_info=args.info_completa,
            section_percentages=section_percentages,
            description_percentages=description_percentages,
            total_units_target=args.total_units,
            output_file=output_file
        )
        
        # Print results
        print("\n" + "="*80)
        print("INVENTORY BOX PICKING RESULTS")
        print("="*80)
        print(f"Total Boxes Selected: {results['total_boxes']}")
        print(f"Total Units: {results['total_units']}")
        print(f"Target Units: {args.total_units}")
        print(f"Selection Efficiency: {(results['total_units'] / args.total_units * 100):.1f}%")
        
        print(f"\nOutput Files Generated:")
        print(f"  - resultado_seleccion.xlsx: Selected boxes with all details")
        print(f"  - resumen.xlsx: Summary of achieved vs target percentages")
        print(f"  - historico_actualizado.xlsx: Updated record of sent units by model")
        print(f"  - {os.path.basename(output_file)}: Combined results file")
        
        print(f"\nFiles saved in: {args.output_dir}")
        print("="*80)
        
        logger.info("Selection process completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\nERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
