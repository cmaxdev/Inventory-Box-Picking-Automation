#!/usr/bin/env python3
"""
Simple Command-Line UI for Inventory Box Picking System

A simple command-line interface for processing client orders.

Author: AI Assistant
Version: 1.0
"""

import os
import sys
from client_order_processor import ClientOrderProcessor


def print_header():
    """Print the application header."""
    print("=" * 60)
    print("INVENTORY BOX PICKING SYSTEM")
    print("=" * 60)
    print("Simple Command-Line Interface")
    print()


def print_menu():
    """Print the main menu."""
    print("\nMAIN MENU")
    print("-" * 30)
    print("1. Process New Order")
    print("2. View Order History")
    print("3. Exit")
    print()


def get_client_input():
    """Get client order input from user."""
    print("\nNEW CLIENT ORDER")
    print("-" * 30)
    
    # Get client name
    while True:
        client_name = input("Client Name: ").strip()
        if client_name:
            break
        print("ERROR: Client name is required!")
    
    # Get total units
    while True:
        try:
            total_units_input = input("Total Units: ").strip()
            total_units = int(total_units_input.replace(',', ''))
            if total_units > 0:
                break
            print("ERROR: Please enter a positive number!")
        except ValueError:
            print("ERROR: Please enter a valid number!")
    
    # Get requirements
    print("\nREQUIREMENTS")
    print("Examples:")
    print("  • 60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers")
    print("  • 50% women, 50% men, 25% accessories, 75% tops")
    print("  • 10% men, 90% women, 10% accessories, 30% pants")
    
    while True:
        requirements = input("\nEnter Requirements: ").strip()
        if requirements:
            break
        print("ERROR: Requirements are required!")
    
    # Get inventory file preference
    inventory_file = input("\nInventory File (press Enter for default): ").strip()
    if not inventory_file:
        inventory_file = "data/inventory/sample_inventory.xlsx"
    
    # Get information completeness requirement
    while True:
        info_req = input("\nRequire complete product information? (y/n, default=y): ").strip().lower()
        if info_req in ['', 'y', 'yes', 'n', 'no']:
            break
        print("ERROR: Please enter 'y' or 'n'")
    
    require_complete_info = info_req in ['', 'y', 'yes']
    
    return {
        'client_name': client_name,
        'total_units': total_units,
        'requirements': requirements,
        'inventory_file': inventory_file,
        'require_complete_info': require_complete_info
    }


def process_order(processor, order_data):
    """Process a client order."""
    print(f"\nProcessing order for {order_data['client_name']}...")
    print(f"Total Units: {order_data['total_units']:,}")
    print(f"Requirements: {order_data['requirements']}")
    print("-" * 60)
    
    try:
        result = processor.process_client_order(
            client_name=order_data['client_name'],
            total_units=order_data['total_units'],
            requirements=order_data['requirements'],
            inventory_file=order_data['inventory_file'],
            require_complete_info=order_data['require_complete_info']
        )
        
        if result['success']:
            print("\n✅ ORDER COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            results = result['results']
            print(f"📦 Total Boxes Selected: {results['total_boxes']}")
            print(f"📊 Total Units: {results['total_units']:,}")
            print()
            
            # Section distribution
            print("📋 SECTION DISTRIBUTION:")
            section_summary = results['section_summary']
            for section in section_summary.index:
                actual_pct = section_summary.loc[section, 'percentage']
                boxes = section_summary.loc[section, 'box_count']
                print(f"   {section}: {actual_pct:.1f}% ({boxes} boxes)")
            
            print()
            print("🏷️  DESCRIPTION DISTRIBUTION:")
            description_summary = results['description_summary']
            for desc in description_summary.index:
                actual_pct = description_summary.loc[desc, 'percentage']
                boxes = description_summary.loc[desc, 'box_count']
                print(f"   {desc}: {actual_pct:.1f}% ({boxes} boxes)")
            
            print()
            print("✅ Order processed successfully!")
            if result['order_summary']['output_file'] and result['order_summary']['output_file'] != 'N/A':
                print(f"📁 Results saved to: {result['order_summary']['output_file']}")
            
        else:
            print(f"\n❌ ORDER FAILED: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def view_history(processor):
    """View order history."""
    print("\nORDER HISTORY")
    print("-" * 30)
    
    try:
        orders = processor.file_manager.get_client_orders()
        
        if orders.empty:
            print("No orders found.")
            return
        
        # Show recent orders
        recent_orders = orders.tail(10)
        
        for _, order in recent_orders.iterrows():
            print(f"📅 {order['order_date']}")
            print(f"   Client: {order['client_name']}")
            print(f"   Units: {order['total_units']:,} (selected: {order['actual_units']:,})")
            print(f"   Boxes: {order['selected_boxes']}")
            print()
        
        print(f"Total orders: {len(orders)}")
        
    except Exception as e:
        print(f"❌ Error loading history: {str(e)}")


def main():
    """Main application loop."""
    print_header()
    
    # Initialize the processor
    processor = ClientOrderProcessor()
    processor.load_client_orders_history()
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                order_data = get_client_input()
                process_order(processor, order_data)
                
                # Ask if user wants to process another order
                while True:
                    continue_choice = input("\nProcess another order? (y/n): ").strip().lower()
                    if continue_choice in ['y', 'yes', 'n', 'no']:
                        break
                    print("ERROR: Please enter 'y' or 'n'")
                
                if continue_choice in ['n', 'no']:
                    break
                    
            elif choice == '2':
                view_history(processor)
                
            elif choice == '3':
                print("\nThank you for using the Inventory Box Picking System!")
                break
                
            else:
                print("ERROR: Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
