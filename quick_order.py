#!/usr/bin/env python3
"""
Quick Order Interface - Simple command-line tool for processing client orders

Usage Examples:
python quick_order.py "ABC Company" 40000 "10% men, 90% women, 10% accessories, 30% pants"
python quick_order.py "Fashion Store" 5000 "60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers"

Author: AI Assistant
Version: 1.0
"""

import sys
import argparse
from client_order_processor import ClientOrderProcessor


def main():
    """Main function for quick order processing."""
    parser = argparse.ArgumentParser(
        description="Quick Order Processing for Inventory Box Picking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quick_order.py "ABC Company" 40000 "10% men, 90% women, 10% accessories, 30% pants"
  python quick_order.py "Fashion Store" 5000 "60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers"
  python quick_order.py "Local Shop" 1000 "50% women, 50% men, 25% accessories, 75% tops"

Section Options: Women, Men, Children
Description Options: Accessories, Trousers (or Pants), Tops
        """
    )
    
    parser.add_argument("client_name", nargs="?", help="Name of the client placing the order")
    parser.add_argument("total_units", nargs="?", type=int, help="Total units requested (e.g., 40000)")
    parser.add_argument("requirements", nargs="?", help="Requirements in natural language (e.g., '10% men, 90% women, 10% accessories, 30% pants')")
    parser.add_argument("--inventory", default="sample.xlsx", help="Inventory file path (default: sample.xlsx)")
    parser.add_argument("--no-complete-info", action="store_true", help="Allow incomplete product information (default: require complete info)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = ClientOrderProcessor()
    processor.load_client_orders_history()
    
    if args.interactive or not args.client_name:
        # Run interactive mode
        from client_order_processor import interactive_order_processor
        interactive_order_processor()
        return
    
    # Process the order
    print(f"Processing order for {args.client_name}")
    print(f"Total Units: {args.total_units:,}")
    print(f"Requirements: {args.requirements}")
    print("-" * 60)
    
    result = processor.process_client_order(
        client_name=args.client_name,
        total_units=args.total_units,
        requirements=args.requirements,
        inventory_file=args.inventory,
        require_complete_info=not args.no_complete_info
    )
    
    if result['success']:
        print("\nSUCCESS: Order completed successfully!")
          
        output_file = result['order_summary']['output_file']
        if output_file and output_file != 'N/A':
            import os
            full_path = os.path.abspath(output_file)
            print(f"Results saved to: {full_path}")
            print(f"Copy this path: {full_path}")
        else:
            print(f"Results saved to: {output_file}")
    else:
        print(f"\nERROR: Order failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
