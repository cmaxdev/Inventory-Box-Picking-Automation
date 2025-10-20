#!/usr/bin/env python3
"""
Example usage of the Inventory Box Picking Automation Tool

This script demonstrates how to use the InventoryPicker class with different configurations.
"""

from inventory_picker import InventoryPicker
from datetime import datetime

def example_basic_usage():
    """Example of basic usage with standard parameters."""
    print("=== BASIC USAGE EXAMPLE ===")
    
    picker = InventoryPicker()
    
    # Configuration for a typical order
    excel_file_path = "sample_inventory.xlsx"  # Replace with your actual file
    
    section_percentages = {
        "Women": 60.0,
        "Men": 25.0,
        "Children": 15.0
    }
    
    description_percentages = {
        "Accessories": 20.0,
        "Trousers": 40.0,
        "Tops": 40.0
    }
    
    total_units_target = 800
    
    try:
        results = picker.run_selection_process(
            excel_file_path=excel_file_path,
            require_complete_info=True,
            section_percentages=section_percentages,
            description_percentages=description_percentages,
            total_units_target=total_units_target,
            output_file=f"basic_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        print("Selection completed successfully!")
        return results
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def example_no_info_requirement():
    """Example with no information completeness requirement."""
    print("\n=== NO INFO REQUIREMENT EXAMPLE ===")
    
    picker = InventoryPicker()
    
    excel_file_path = "sample_inventory.xlsx"
    
    section_percentages = {
        "Women": 50.0,
        "Men": 30.0,
        "Children": 20.0
    }
    
    description_percentages = {
        "Accessories": 30.0,
        "Trousers": 35.0,
        "Tops": 35.0
    }
    
    total_units_target = 1200
    
    try:
        results = picker.run_selection_process(
            excel_file_path=excel_file_path,
            require_complete_info=False,  # Allow incomplete information
            section_percentages=section_percentages,
            description_percentages=description_percentages,
            total_units_target=total_units_target,
            output_file=f"no_info_requirement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        print("Selection completed successfully!")
        return results
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def example_custom_constraints():
    """Example with custom maximum units per model."""
    print("\n=== CUSTOM CONSTRAINTS EXAMPLE ===")
    
    picker = InventoryPicker()
    picker.max_units_per_model = 150  # Custom limit instead of default 200
    
    excel_file_path = "sample_inventory.xlsx"
    
    section_percentages = {
        "Women": 70.0,
        "Men": 20.0,
        "Children": 10.0
    }
    
    description_percentages = {
        "Accessories": 25.0,
        "Trousers": 45.0,
        "Tops": 30.0
    }
    
    total_units_target = 600
    
    try:
        results = picker.run_selection_process(
            excel_file_path=excel_file_path,
            require_complete_info=True,
            section_percentages=section_percentages,
            description_percentages=description_percentages,
            total_units_target=total_units_target,
            output_file=f"custom_constraints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        print("Selection completed successfully!")
        return results
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def create_sample_inventory():
    """Create a sample inventory file for testing."""
    import pandas as pd
    import random
    
    print("\n=== CREATING SAMPLE INVENTORY ===")
    
    # Sample data
    sections = ["Women", "Men", "Children"]
    descriptions = ["Accessories", "Trousers", "Tops"]
    models = [f"Model_{i:03d}" for i in range(1, 21)]
    
    sample_data = []
    for i in range(100):  # Create 100 sample boxes
        sample_data.append({
            'BARCODE': f'BOX_{i+1:04d}',
            'COMPOSITION': f'Material_{random.randint(1, 5)}' if random.random() > 0.1 else None,
            'TARIFAIRE': f'HS{random.randint(100000, 999999)}' if random.random() > 0.1 else None,
            'PVP': round(random.uniform(10, 100), 2) if random.random() > 0.1 else None,
            'G. TARIF': f'TG_{random.randint(1, 10)}' if random.random() > 0.1 else None,
            'SECTION': random.choice(sections),
            'DESCRIPTION': random.choice(descriptions),
            'MOCACO': random.choice(models),
            'UNITES': random.randint(1, 50)
        })
    
    df = pd.DataFrame(sample_data)
    df.to_excel('sample_inventory.xlsx', index=False)
    print("Sample inventory created: sample_inventory.xlsx")
    
    # Print summary
    print(f"Total boxes: {len(df)}")
    print(f"Sections: {df['SECTION'].value_counts().to_dict()}")
    print(f"Descriptions: {df['DESCRIPTION'].value_counts().to_dict()}")
    print(f"Models: {df['MOCACO'].nunique()} unique models")

if __name__ == "__main__":
    print("Inventory Box Picking Automation Tool - Examples")
    print("=" * 60)
    
    # Create sample data first
    create_sample_inventory()
    
    # Run examples
    example_basic_usage()
    example_no_info_requirement()
    example_custom_constraints()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("Check the generated Excel files for results.")
