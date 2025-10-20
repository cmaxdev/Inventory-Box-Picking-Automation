#!/usr/bin/env python3
"""
Simple Startup Script for Inventory Box Picking System

Choose between desktop GUI or command-line interface.

Author: AI Assistant
Version: 1.0
"""

import sys
import os


def print_header():
    """Print the startup header."""
    print("=" * 60)
    print("INVENTORY BOX PICKING SYSTEM")
    print("=" * 60)
    print("Choose your interface:")
    print()


def main():
    """Main startup function."""
    print_header()
    
    print("1. Desktop GUI (Recommended)")
    print("   - Modern desktop application")
    print("   - Easy to use with forms and buttons")
    print("   - View order history and results")
    print("   - No additional dependencies")
    print()
    
    print("2. Command-Line Interface")
    print("   - Simple text-based interface")
    print("   - No additional dependencies")
    print("   - Works in any terminal")
    print()
    
    print("3. Quick Order (Command Line)")
    print("   - Direct command-line order processing")
    print("   - For advanced users and automation")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\nStarting Desktop GUI...")
                print("The desktop application will open in a new window")
                print("-" * 60)
                
                try:
                    import simple_desktop_ui
                    simple_desktop_ui.main()
                except ImportError as e:
                    print(f"ERROR: Error starting desktop GUI: {e}")
                    print("Make sure tkinter is installed (comes with Python by default)")
                    
            elif choice == '2':
                print("\nStarting Command-Line Interface...")
                print("-" * 60)
                
                try:
                    import simple_ui
                    # This will start the CLI
                except Exception as e:
                    print(f"ERROR: Error starting CLI: {e}")
                    
            elif choice == '3':
                print("\nQuick Order Mode")
                print("-" * 60)
                print("Usage examples:")
                print('python quick_order.py "Client Name" 5000 "60% women, 40% men, 30% accessories, 70% tops"')
                print()
                print("For interactive mode:")
                print("python quick_order.py --interactive")
                print()
                
                # Ask for parameters
                client_name = input("Client Name: ").strip()
                if client_name:
                    total_units = input("Total Units: ").strip()
                    if total_units:
                        requirements = input("Requirements: ").strip()
                        if requirements:
                            cmd = f'python quick_order.py "{client_name}" {total_units} "{requirements}"'
                            print(f"\nRunning: {cmd}")
                            os.system(cmd)
                        else:
                            print("ERROR: Requirements required")
                    else:
                        print("ERROR: Total units required")
                else:
                    print("ERROR: Client name required")
                    
            else:
                print("ERROR: Invalid choice. Please enter 1, 2, or 3.")
                continue
                
            break
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    main()
