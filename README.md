# Inventory Box Picking Automation Tool

A comprehensive Python solution for automated inventory box selection based on business rules, percentage distributions, and historical constraints.

## Features

- **Excel Integration**: Reads inventory data from Excel files with automatic column mapping
- **Information Completeness Filter**: Option to require complete product information or allow partial data
- **Historical Tracking**: Maintains order history to prevent over-allocation of models
- **Percentage Distribution**: Automated selection based on section and description percentages
- **Unit Constraints**: Enforces maximum 200 units per model limit (configurable)
- **Full Box Selection**: Always selects complete boxes, never partial cases
- **Comprehensive Reporting**: Generates detailed selection reports with compliance analysis

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from inventory_picker import InventoryPicker

# Initialize the picker
picker = InventoryPicker()

# Configure your selection parameters
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

# Run the selection process
results = picker.run_selection_process(
    excel_file_path="your_inventory.xlsx",
    require_complete_info=True,
    section_percentages=section_percentages,
    description_percentages=description_percentages,
    total_units_target=1000,
    output_file="selection_results.xlsx"
)
```

### Command Line Usage

```bash
python inventory_picker.py
```

## Excel File Format

Your inventory Excel file should contain the following columns (exact names as specified):

| Column Name | Description | Required |
|-------------|-------------|----------|
| BARCODE | Case/product identifier | Yes |
| COMPOSITION | Product composition | Optional* |
| TARIFAIRE | HS Code | Optional* |
| PVP | Price | Optional* |
| G. TARIF | Tariff Group | Optional* |
| SECTION | Section (Women, Children, Men) | Yes |
| DESCRIPTION | Description (Accessories, Trousers, etc.) | Yes |
| MOCACO | Model identifier | Yes |
| UNITES | Units per case | Yes |

*Optional columns are required only if `require_complete_info=True`

## Configuration Options

### Information Completeness
- `require_complete_info=True`: Only selects boxes with all information fields populated
- `require_complete_info=False`: Selects all available boxes regardless of information completeness

### Historical Constraints
- Maximum units per model: 200 (configurable in code)
- Automatically tracks and updates order history
- History file: `order_history.xlsx`

### Percentage Distribution
- Section percentages: Define target distribution by section (Women, Men, Children)
- Description percentages: Define target distribution by product description
- Algorithm uses greedy selection to maximize compliance with targets

## Output Files

The tool generates:

1. **Selection Results Excel File**: Contains detailed results with multiple sheets:
   - `Selected_Boxes`: Complete list of selected boxes
   - `Section_Summary`: Distribution analysis by section
   - `Description_Summary`: Distribution analysis by description
   - `Model_Summary`: Units selected per model

2. **Log File**: `inventory_picker.log` with detailed processing information

3. **History File**: `order_history.xlsx` with updated order history

## Algorithm Details

### Selection Process Flow

1. **Data Loading**: Load inventory and history data from Excel files
2. **Information Filter**: Apply completeness requirements if specified
3. **Historical Constraints**: Calculate available units per model based on previous orders
4. **Percentage Selection**: Use greedy algorithm to select boxes meeting section/description targets
5. **Final Constraints**: Apply 200-unit-per-model limit to current selection
6. **History Update**: Update order history with selected boxes
7. **Report Generation**: Create comprehensive output reports

### Key Features

- **Full Box Selection**: Always selects complete boxes, never partial cases
- **Greedy Algorithm**: Prioritizes larger boxes to maximize efficiency
- **Constraint Validation**: Ensures all business rules are satisfied
- **Compliance Reporting**: Shows how well the selection meets percentage targets

## Customization

### Modifying Maximum Units Per Model

```python
picker = InventoryPicker()
picker.max_units_per_model = 300  # Change from default 200
```

### Custom Column Mapping

If your Excel file uses different column names, modify the `column_mapping` dictionary in the `load_inventory` method.

### Adding New Constraints

Extend the `InventoryPicker` class to add additional business rules or constraints.

## Error Handling

The tool includes comprehensive error handling and logging:
- Validates Excel file format and required columns
- Handles missing or invalid data gracefully
- Provides detailed error messages and logging
- Continues processing even if some data is invalid

## Performance Considerations

- Optimized for large datasets using Pandas
- Efficient memory usage with streaming operations
- Configurable logging levels for performance tuning
- Batch processing for historical updates

## Support

For issues or questions:
1. Check the log file for detailed error information
2. Verify your Excel file format matches the requirements
3. Ensure all required columns are present and properly formatted

## License

This tool is provided as-is for inventory management automation purposes.
