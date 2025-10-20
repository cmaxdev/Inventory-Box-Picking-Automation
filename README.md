# 📦 Inventory Box Picking System

A Python-based system for automatically selecting full boxes from inventory based on client requirements and percentage distributions.

## 🚀 Quick Start

### Option 1: Direct Desktop GUI (Recommended)
```bash
python simple_desktop_ui.py
```

### Option 2: Easy Startup Menu
```bash
python run.py
```

### Option 3: Windows Batch File
```bash
start_desktop.bat
```

### Option 4: Command Line Interface
```bash
python simple_ui.py
```

### Option 5: Quick Order
```bash
python quick_order.py "Client Name" 5000 "60% women, 40% men, 30% accessories, 70% tops"
```

## 🎯 How It Works

1. **Input**: Client provides requirements in natural language
   - Example: "60% women, 25% men, 15% children, 20% accessories, 40% tops, 40% trousers"

2. **Processing**: System automatically:
   - Selects full boxes (never partial cases)
   - Optimizes for percentage requirements
   - Tracks historical model usage (max 200 units per model)
   - Filters by information completeness

3. **Output**: Generates detailed Excel reports with:
   - Selected boxes summary
   - Section and description distribution
   - Model usage tracking
   - Compliance analysis

## 📁 Project Structure

```
Inventory Box Picking Automation/
├── Core System Files
│   ├── inventory_picker.py          # Main inventory selection engine
│   ├── client_order_processor.py    # Client order processing
│   ├── file_manager.py              # File management utilities
│   ├── excel_registry.py            # Excel file registry system
│   └── excel_registry_utils.py      # Auto-registration utilities
│
├── User Interfaces
│   ├── simple_desktop_ui.py         # Simple desktop GUI (tkinter)
│   ├── desktop_ui.py                # Advanced desktop GUI (tkinter)
│   ├── simple_ui.py                 # Command-line interface
│   ├── quick_order.py               # Quick command-line tool
│   ├── run.py                       # Startup script
│   └── start_desktop.bat            # Windows batch file
│
├── Data (Auto-Created)
│   └── data/
│       ├── inventory/               # Inventory files
│       ├── orders/
│       │   ├── client_orders/       # Client order results
│       │   └── selection_results/   # Selection results
│       ├── history/                 # Historical tracking
│       └── excel_registry.xlsx      # Central registry
│
└── Configuration
    ├── requirements.txt             # Python dependencies
    └── README.md                    # This file
```

## 📋 Requirements

- Python 3.7+
- tkinter (comes with Python by default)
- pandas
- numpy
- openpyxl
- xlsxwriter

## 🔧 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the system:
```bash
python run.py
```

## 📊 Features

### ✅ Automated Box Selection
- Intelligent selection based on percentage requirements
- Full box selection (never partial cases)
- Historical constraint tracking (200 units max per model)
- Information completeness filtering

### ✅ Client-Friendly Interface
- Natural language requirements parsing
- Desktop GUI with forms and buttons
- Command-line interface for automation
- Real-time order processing

### ✅ File Management & Organization
- Automatic file organization into directories
- Central registry for all Excel files
- Auto-registration of new files
- Search and retrieval capabilities

### ✅ Order Tracking & History
- Complete client order history
- Model usage tracking
- Compliance reporting
- Audit trail for all orders

## 💡 Usage Examples

### Desktop GUI
1. Run `python run.py`
2. Choose option 1 (Desktop GUI)
3. Fill in client name, total units, and requirements
4. Click "Process Order"
5. View results and order history

### Command Line
```bash
# Interactive mode
python quick_order.py --interactive

# Direct order
python quick_order.py "ABC Fashion Co." 40000 "10% men, 90% women, 10% accessories, 30% pants"
```

### Requirements Format
- **Sections**: Women, Men, Children
- **Descriptions**: Accessories, Trousers, Tops
- **Format**: "50% women, 50% men, 25% accessories, 75% tops"

## 📈 System Status

**🟢 FULLY OPERATIONAL**

- ✅ All core functionality working
- ✅ Desktop GUI available
- ✅ Command-line interfaces working
- ✅ File management system active
- ✅ Auto-registration system operational
- ✅ Order history tracking functional
- ✅ Excel file organization complete

## 🎉 Ready for Production Use

Your inventory box picking system is now ready for real-world use! The system handles exactly the workflow you described: clients tell you their requirements in natural language, and you get automated, intelligent box selection with full reporting.