# Weekly Stock Takes - Flask Web Application

A modern web-based coffee shop inventory management system built with Flask and SQLite3. This application replaces the original Tkinter desktop application with an intuitive, responsive web interface.

## Features

- **Milk Usage Tracking**: Monitor consumption of 2L, 1L, and 500ml milk bottles
- **Bean Coffee Management**: Track vending machine coffee sales by type (Americano, Cafe Creme, Latte, Cappuccino, Flat White)
- **Lavazza Coffee Inventory**: Manage fresh-made coffee stock and deliveries
- **Sugar & Sweetener Tracking**: Record sugar/sweetener purchases and on-hand amounts
- **CSV Import**: Upload sales and purchases data from your POS system
- **Product Mapping**: Configure product descriptions for automatic data matching
- **Data Persistence**: All entries stored in SQLite3 database
- **Responsive Design**: Beautiful, mobile-friendly interface with gradient styling
- **Easy Data Management**: Add, view, and delete entries with intuitive forms
- **Dashboard**: Quick overview of all tracked categories

## System Requirements

- Python 3.7 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Download the Project

```bash
cd weekly-stock-takes
```

### 2. Create a Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

## Usage

### Main Dashboard
- View summary statistics for all tracked categories
- Navigate to each tracking section using the menu

### Milk Usage
1. Click "Milk Usage" in the navigation
2. Enter the date and number of milk bottles used
3. Enter the total number of coffees sold
4. Click "Save Milk Usage Entry"
5. View all entries in the table below the form

### Bean Coffee
1. Click "Bean Coffee" in the navigation
2. Enter the date and quantities for each coffee type
3. Enter total coffee sales
4. Click "Save Bean Coffee Entry"

### Lavazza Coffee
1. Click "Lavazza Coffee" in the navigation
2. Enter the date, deliveries received, and actual count
3. Enter total coffee sales
4. Click "Save Lavazza Entry"

### Sugar & Sweetener
1. Click "Sugar & Sweetener" in the navigation
2. Enter purchased units and on-hand amounts
3. Enter total coffee sales
4. Click "Save Sugar Entry"

## CSV Import

### Settings Configuration
1. Click "Settings" in the navigation
2. For each category (Milk, Bean Coffee, Lavazza, Sugar), add product descriptions
3. Enter descriptions that match your CSV data (e.g., "2L Milk", "Cappuccino")
4. Click "Save [Category] Settings" for each category

### Importing CSV Files
1. Click "Import CSV" in the navigation
2. Upload your Sales CSV (columns: 1=Description, 3=Date, 6=Quantity)
3. Upload your Purchases CSV (columns: 0=Description, 6=Quantity)
4. The system automatically matches descriptions and calculates quantities

### Using Imported Data
Once CSV files are imported and settings are configured:
- Sales data is matched by description and date range
- Purchases data is summed for matching descriptions
- The data can be viewed via the API endpoint: `/api/import/get-data/<type>/<category>/<date_from>/<date_to>`

## Database

The application uses SQLite3 with a file-based database (`stocktakes.db`). The database is automatically created on first run with the following tables:

- `milkUsage`: Tracks milk bottle consumption
- `coffeeBean`: Tracks bean coffee machine sales
- `lavazza`: Tracks fresh-made coffee inventory
- `coffeeSugar`: Tracks sugar and sweetener usage
- `csvSettings`: Stores product description mappings for each category
- `importedData`: Stores imported sales and purchase data

## Deleting Entries

Each entry has a "Delete" button in the table. Click it to remove an entry (confirmation required).

## File Structure

```
weekly-stock-takes/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── stocktakes.db          # SQLite database (created on first run)
└── templates/
    ├── base.html          # Base template with styling
    ├── index.html         # Dashboard page
    ├── milk.html          # Milk tracking page
    ├── bean.html          # Bean coffee tracking page
    ├── lavazza.html       # Lavazza tracking page
    ├── sugar.html         # Sugar tracking page
    ├── import.html        # CSV import page
    └── settings.html      # Settings configuration page
```

## Differences from Original Application

| Feature | Original (Tkinter) | Web Version |
|---------|-------------------|------------|
| Interface | Desktop GUI | Web Browser |
| Accessibility | Local machine only | Network accessible |
| Data Export | Excel files | JSON API available |
| Responsiveness | Fixed window size | Mobile-friendly |
| Deployment | Standalone EXE | Any Python environment |
| Data Visualization | Built-in viewers | Foundation for web dashboards |

## API Endpoints

The application provides the following REST API endpoints:

### Milk Usage
- `GET /api/milk/data` - Get all milk entries as JSON
- `POST /api/milk` - Add new milk entry
- `DELETE /api/milk/<id>` - Delete milk entry

### Bean Coffee
- `GET /api/bean/data` - Get all bean entries as JSON
- `POST /api/bean` - Add new bean entry
- `DELETE /api/bean/<id>` - Delete bean entry

### Lavazza
- `GET /api/lavazza/data` - Get all lavazza entries as JSON
- `POST /api/lavazza` - Add new lavazza entry
- `DELETE /api/lavazza/<id>` - Delete lavazza entry

### Sugar
- `GET /api/sugar/data` - Get all sugar entries as JSON
- `POST /api/sugar` - Add new sugar entry
- `DELETE /api/sugar/<id>` - Delete sugar entry

### CSV Import & Settings
- `POST /api/import/sales` - Upload sales CSV file
- `POST /api/import/purchases` - Upload purchases CSV file
- `POST /api/settings/<category>` - Save product descriptions for a category
- `GET /api/import/get-data/<type>/<category>/<date_from>/<date_to>` - Get matching imported data

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, port=8000)  # Use port 8000 instead
```

### Database Errors
Delete `stocktakes.db` to reset the database:
```bash
rm stocktakes.db  # macOS/Linux
del stocktakes.db  # Windows
```

Then restart the application.

### Date Format Issues
Dates are stored in DD/MM/YYYY format. Ensure your input date follows this format.

## Future Enhancements

- User authentication and multi-user support
- Data import/export to CSV and Excel
- Advanced reporting and analytics
- Charts and graphs for data visualization
- Email notifications for low stock
- Backup and restore functionality
- API rate limiting and security

## License

This project is provided as-is for inventory management purposes.
