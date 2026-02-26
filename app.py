"""
Weekly Stock Takes - Flask Web Application
A web-based coffee shop inventory management system
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
import sqlite3
import os
from dateutil import parser
import csv
from io import StringIO
import json

app = Flask(__name__)
DATABASE = 'stocktakes.db'

# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Milk usage table
    c.execute('''CREATE TABLE IF NOT EXISTS milkUsage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        twoLiter INTEGER DEFAULT 0,
        oneLiter INTEGER DEFAULT 0,
        fiveMil INTEGER DEFAULT 0,
        coffeeSold REAL DEFAULT 0,
        usage REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Coffee bean table
    c.execute('''CREATE TABLE IF NOT EXISTS coffeeBean (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        americano INTEGER DEFAULT 0,
        cafeCreme INTEGER DEFAULT 0,
        cafeLatte INTEGER DEFAULT 0,
        cappuccino INTEGER DEFAULT 0,
        flatWhite INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0,
        coffeeSold REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Lavazza table
    c.execute('''CREATE TABLE IF NOT EXISTS lavazza (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        deliveries INTEGER DEFAULT 0,
        actualCount INTEGER DEFAULT 0,
        coffeeSold REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Coffee sugar table
    c.execute('''CREATE TABLE IF NOT EXISTS coffeeSugar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        sugarBuy INTEGER DEFAULT 0,
        sugarHand REAL DEFAULT 0,
        sweetnerBuy INTEGER DEFAULT 0,
        sweetnerHand REAL DEFAULT 0,
        coffeeSold REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # CSV Settings table - stores product descriptions mapping
    c.execute('''CREATE TABLE IF NOT EXISTS csvSettings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL UNIQUE,
        descriptions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Imported CSV data table
    c.execute('''CREATE TABLE IF NOT EXISTS importedData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        description TEXT NOT NULL,
        date TEXT,
        quantity REAL DEFAULT 0,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Bakery dough table
    c.execute('''CREATE TABLE IF NOT EXISTS bakeryDough (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        cakeFlour REAL DEFAULT 0,
        breadFlour REAL DEFAULT 0,
        yeast REAL DEFAULT 0,
        oil REAL DEFAULT 0,
        sugar REAL DEFAULT 0,
        cakeFlourBought REAL DEFAULT 0,
        breadFlourBought REAL DEFAULT 0,
        yeastBought REAL DEFAULT 0,
        oilBought REAL DEFAULT 0,
        sugarBought REAL DEFAULT 0,
        pizzaSales REAL DEFAULT 0,
        normalSales REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# ==================== DATABASE FUNCTIONS ====================

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def format_date(date_str):
    """Format date string to DD/MM/YYYY"""
    try:
        # Check if it's already in DD/MM/YYYY format
        if '/' in date_str and date_str.count('/') == 2:
            parts = date_str.split('/')
            if len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
                return date_str  # Already in DD/MM/YYYY format
        
        # HTML date input is YYYY-MM-DD (ISO format), parse without dayfirst
        if '-' in date_str and date_str.count('-') == 2:
            parsed_date = parser.parse(date_str, dayfirst=False)
        else:
            # CSV dates might be in different formats, use dayfirst
            parsed_date = parser.parse(date_str, dayfirst=True)
        
        return parsed_date.strftime('%d/%m/%Y')
    except Exception as e:
        return date_str

def get_table_data(table_name):
    """Get all records from a table"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name} ORDER BY date DESC")
    records = c.fetchall()
    conn.close()
    return records

def delete_record(table_name, record_id):
    """Delete a record from a table"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def get_settings(category):
    """Get CSV settings for a category"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT descriptions FROM csvSettings WHERE category = ?", (category,))
    result = c.fetchone()
    conn.close()
    
    if result:
        desc_str = result['descriptions']
        if desc_str:
            # Split by pipe delimiter if it's a string
            descriptions = desc_str.split('|')
            return descriptions
    return []

def save_settings(category, descriptions):
    """Save CSV settings for a category"""
    conn = get_db_connection()
    c = conn.cursor()
    desc_str = '|'.join(descriptions)
    c.execute("""INSERT OR REPLACE INTO csvSettings (category, descriptions, updated_at)
                 VALUES (?, ?, CURRENT_TIMESTAMP)""",
              (category, desc_str))
    conn.commit()
    conn.close()

def parse_sales_csv(file_content):
    """Parse sales CSV: columns 1 (description), 3 (date), 6 (quantity)"""
    rows = []
    try:
        csv_reader = csv.reader(StringIO(file_content))
        for row in csv_reader:
            if len(row) > 6:  # Ensure row has enough columns
                try:
                    description = row[1].strip()
                    date_str = row[3].strip()
                    quantity = float(row[6].strip())
                    if description and date_str and quantity:
                        rows.append({
                            'description': description,
                            'date': format_date(date_str),
                            'quantity': quantity
                        })
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f"Error parsing sales CSV: {e}")
    return rows

def parse_purchases_csv(file_content):
    """Parse purchases CSV: columns 0 (description), 6 (quantity)"""
    rows = []
    try:
        csv_reader = csv.reader(StringIO(file_content))
        for row in csv_reader:
            if len(row) > 6:  # Ensure row has enough columns
                try:
                    description = row[0].strip()
                    quantity = float(row[6].strip())
                    if description and quantity:
                        rows.append({
                            'description': description,
                            'quantity': quantity
                        })
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        print(f"Error parsing purchases CSV: {e}")
    return rows

def get_matching_quantity(imported_rows, description, date_from, date_to):
    """Get matching quantity from imported data between two dates"""
    total = 0
    for row in imported_rows:
        if description.lower() in row['description'].lower():
            if 'date' in row:  # Sales data has dates
                try:
                    row_date = parser.parse(row['date'], dayfirst=True).date()
                    from_date = parser.parse(date_from, dayfirst=True).date()
                    to_date = parser.parse(date_to, dayfirst=True).date()
                    if from_date <= row_date <= to_date:
                        total += row['quantity']
                except:
                    continue
            else:  # Purchases data (sum all)
                total += row['quantity']
    return total

def decode_file_content(file_bytes):
    """Try to decode file content with multiple encodings"""
    encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
    
    for encoding in encodings:
        try:
            return file_bytes.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue
    
    # If all encodings fail, use utf-8 with error handling
    return file_bytes.decode('utf-8', errors='replace')

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main dashboard"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get latest records from each table
    c.execute("SELECT COUNT(*) as count FROM milkUsage")
    milk_count = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM coffeeBean")
    bean_count = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM lavazza")
    lavazza_count = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM coffeeSugar")
    sugar_count = c.fetchone()['count']
    
    conn.close()
    
    return render_template('index.html', 
                         milk_count=milk_count, 
                         bean_count=bean_count,
                         lavazza_count=lavazza_count,
                         sugar_count=sugar_count)

# ==================== MILK USAGE ROUTES ====================

@app.route('/milk')
def milk_page():
    """Milk usage page"""
    records = get_table_data('milkUsage')
    
    # Get the latest milk usage entry to find the date range for coffee calculations
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT date FROM milkUsage ORDER BY date DESC LIMIT 1")
    latest_record = c.fetchone()
    
    # Calculate coffees sold from imported sales data
    coffees_from_csv = 0
    if records:  # Only calculate if we have existing records
        if latest_record:
            last_date = latest_record['date']
            c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
            imported_rows = [dict(row) for row in c.fetchall()]
            
            if imported_rows:
                # Get milk coffee settings
                milk_settings = get_settings('milk')
                
                try:
                    # Find the next date after the last stock take
                    from datetime import datetime, timedelta
                    last_date_obj = parser.parse(last_date, dayfirst=True).date()
                    today = datetime.now().date()
                    
                    # Sum all coffee sales between last date and today
                    for row in imported_rows:
                        for coffee_desc in milk_settings:
                            if coffee_desc.lower() in row['description'].lower():
                                try:
                                    row_date = parser.parse(row['date'], dayfirst=True).date()
                                    if row_date > last_date_obj:
                                        coffees_from_csv += row['quantity']
                                except:
                                    continue
                except Exception as e:
                    print(f"Error calculating coffees from CSV: {e}")
    
    conn.close()
    
    return render_template('milk.html', records=records, coffees_from_csv=coffees_from_csv)

@app.route('/api/milk', methods=['POST'])
def add_milk_entry():
    """Add new milk usage entry"""
    try:
        data = request.json
        date_input = data.get('date', '')
        date = format_date(date_input)
        two_liter = data.get('twoLiter', 0)
        one_liter = data.get('oneLiter', 0)
        five_mil = data.get('fiveMil', 0)
        coffee_sold = data.get('coffeeSold', 0)
        
        if not date:
            return jsonify({'success': False, 'error': 'Date is required'}), 400
        
        # Calculate usage (ml per cup)
        total_ml = (int(two_liter) * 2000) + (int(one_liter) * 1000) + (int(five_mil) * 500)
        usage = total_ml / float(coffee_sold) if float(coffee_sold) > 0 else 0
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO milkUsage (date, twoLiter, oneLiter, fiveMil, coffeeSold, usage)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (date, two_liter, one_liter, five_mil, coffee_sold, usage))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Milk usage entry saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/milk/coffee-sold/<date>')
def get_coffee_sold_for_date(date):
    """Get coffee sold from CSV for a specific date"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the latest milk entry before this date
        c.execute("SELECT date FROM milkUsage WHERE date < ? ORDER BY date DESC LIMIT 1", (date,))
        previous_record = c.fetchone()
        
        coffees_from_csv = 0
        
        # Determine the start date for the range
        if previous_record:
            last_date = previous_record['date']
        else:
            # If no previous record, use a very old date so we get all sales up to current date
            last_date = "1900-01-01"
        
        # Get imported sales data
        c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        if imported_rows:
            # Get milk coffee settings
            milk_settings = get_settings('milk')
            
            try:
                # last_date is in DD/MM/YYYY format from database, parse explicitly
                last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                # HTML date input is always YYYY-MM-DD format
                current_date_obj = parser.parse(date, dayfirst=False).date()
                
                # Sum all coffee sales between last date and current date
                for row in imported_rows:
                    if not row['date']:
                        continue
                    try:
                        row_date = parser.parse(row['date'], dayfirst=True).date()
                        
                        for coffee_desc in milk_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                if last_date_obj < row_date <= current_date_obj:
                                    coffees_from_csv += row['quantity']
                                break
                    except Exception as e:
                        continue
            except Exception as e:
                pass
        
        conn.close()
        
        return jsonify({'success': True, 'coffeesSold': coffees_from_csv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/milk/<int:record_id>', methods=['DELETE'])
def delete_milk_entry(record_id):
    """Delete milk entry"""
    try:
        delete_record('milkUsage', record_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== BEAN COFFEE ROUTES ====================

@app.route('/bean')
def bean_page():
    """Bean coffee page"""
    records = get_table_data('coffeeBean')
    
    # Get the latest bean coffee entry to find the date range for sales calculations
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT date FROM coffeeBean ORDER BY date DESC LIMIT 1")
    latest_record = c.fetchone()
    
    # Calculate coffee sold from imported sales data
    coffees_from_csv = 0
    if records:  # Only calculate if we have existing records
        if latest_record:
            last_date = latest_record['date']
            c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
            imported_rows = [dict(row) for row in c.fetchall()]
            
            if imported_rows:
                # Get bean coffee settings
                bean_settings = get_settings('bean')
                
                try:
                    # Parse the last date (DD/MM/YYYY format from DB)
                    from datetime import datetime
                    last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                    today = datetime.now().date()
                    
                    # Sum all coffee sales between last date and today
                    for row in imported_rows:
                        for coffee_desc in bean_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                try:
                                    row_date = parser.parse(row['date'], dayfirst=True).date()
                                    if row_date > last_date_obj:
                                        coffees_from_csv += row['quantity']
                                except:
                                    continue
                except Exception as e:
                    print(f"Error calculating coffees from CSV: {e}")
    
    conn.close()
    
    return render_template('bean.html', records=records, coffees_from_csv=coffees_from_csv)

@app.route('/api/bean', methods=['POST'])
def add_bean_entry():
    """Add new bean coffee entry"""
    try:
        data = request.json
        date_str = format_date(data.get('date', ''))
        
        americano = int(data.get('americano', 0))
        creme = int(data.get('cafeCreme', 0))
        latte = int(data.get('cafeLatte', 0))
        cappuccino = int(data.get('cappuccino', 0))
        flat = int(data.get('flatWhite', 0))
        
        total = americano + creme + latte + cappuccino + flat
        coffee_sold = float(data.get('coffeeSold', 0))
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO coffeeBean
                    (date, americano, cafeCreme, cafeLatte, cappuccino, flatWhite, total, coffeeSold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                 (date_str, americano, creme, latte, cappuccino, flat, total, coffee_sold))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Bean coffee entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bean/coffee-sold/<date>')
def get_bean_coffee_sold_for_date(date):
    """Get coffee sold from CSV for a specific date"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the latest bean coffee entry before this date
        c.execute("SELECT date FROM coffeeBean WHERE date < ? ORDER BY date DESC LIMIT 1", (date,))
        previous_record = c.fetchone()
        
        coffees_from_csv = 0
        
        # Determine the start date for the range
        if previous_record:
            last_date = previous_record['date']
        else:
            # If no previous record, use a very old date so we get all sales up to current date
            last_date = "1900-01-01"
        
        # Get imported sales data
        c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        if imported_rows:
            # Get bean coffee settings
            bean_settings = get_settings('bean')
            
            try:
                # last_date is in DD/MM/YYYY format from database, parse explicitly
                last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                # HTML date input is always YYYY-MM-DD format
                current_date_obj = parser.parse(date, dayfirst=False).date()
                
                # Sum all coffee sales between last date and current date
                for row in imported_rows:
                    if not row['date']:
                        continue
                    try:
                        row_date = parser.parse(row['date'], dayfirst=True).date()
                        
                        for coffee_desc in bean_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                if last_date_obj < row_date <= current_date_obj:
                                    coffees_from_csv += row['quantity']
                                break
                    except Exception as e:
                        continue
            except Exception as e:
                pass
        
        conn.close()
        
        return jsonify({'success': True, 'coffeesSold': coffees_from_csv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bean/<int:record_id>', methods=['DELETE'])
def delete_bean_entry(record_id):
    """Delete bean coffee entry"""
    try:
        delete_record('coffeeBean', record_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== LAVAZZA ROUTES ====================

@app.route('/lavazza')
def lavazza_page():
    """Lavazza coffee page"""
    records = get_table_data('lavazza')
    
    # Calculate deliveries from imported purchases data
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT description, quantity FROM importedData WHERE data_type = 'purchases'")
    imported_purchases_rows = [dict(row) for row in c.fetchall()]
    
    delivers_from_csv = 0
    if imported_purchases_rows:
        # Get lavazza purchases settings
        lavazza_purchases_settings = get_settings('lavazza_purchases')
        
        # Sum all purchases matching lavazza descriptions
        for row in imported_purchases_rows:
            for coffee_desc in lavazza_purchases_settings:
                if coffee_desc and coffee_desc.lower() in row['description'].lower():
                    delivers_from_csv += row['quantity']
                    break
    
    # Calculate coffee sold from imported sales data
    coffees_from_csv = 0
    if records:  # Only calculate if we have existing records
        c.execute("SELECT date FROM lavazza ORDER BY date DESC LIMIT 1")
        latest_record = c.fetchone()
        
        if latest_record:
            last_date = latest_record['date']
            c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
            imported_rows = [dict(row) for row in c.fetchall()]
            
            if imported_rows:
                # Get lavazza coffee settings
                lavazza_settings = get_settings('lavazza')
                
                try:
                    # Parse the last date (DD/MM/YYYY format from DB)
                    from datetime import datetime
                    last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                    today = datetime.now().date()
                    
                    # Sum all coffee sales between last date and today
                    for row in imported_rows:
                        for coffee_desc in lavazza_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                try:
                                    row_date = parser.parse(row['date'], dayfirst=True).date()
                                    if row_date > last_date_obj:
                                        coffees_from_csv += row['quantity']
                                except:
                                    continue
                except Exception as e:
                    print(f"Error calculating coffees from CSV: {e}")
    
    conn.close()
    
    return render_template('lavazza.html', records=records, coffees_from_csv=coffees_from_csv, delivers_from_csv=delivers_from_csv)

@app.route('/api/lavazza', methods=['POST'])
def add_lavazza_entry():
    """Add new lavazza entry"""
    try:
        data = request.json
        date_str = format_date(data.get('date', ''))
        
        deliveries = int(data.get('deliveries', 0))
        count = int(data.get('actualCount', 0))
        coffee_sold = float(data.get('coffeeSold', 0))
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO lavazza
                    (date, deliveries, actualCount, coffeeSold)
                    VALUES (?, ?, ?, ?)""",
                 (date_str, deliveries, count, coffee_sold))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Lavazza entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/lavazza/coffee-sold/<date>')
def get_lavazza_coffee_sold_for_date(date):
    """Get coffee sold from CSV for a specific date"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the latest lavazza entry before this date
        c.execute("SELECT date FROM lavazza WHERE date < ? ORDER BY date DESC LIMIT 1", (date,))
        previous_record = c.fetchone()
        
        coffees_from_csv = 0
        
        # Determine the start date for the range
        if previous_record:
            last_date = previous_record['date']
        else:
            # If no previous record, use a very old date so we get all sales up to current date
            last_date = "1900-01-01"
        
        # Get imported sales data
        c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        if imported_rows:
            # Get lavazza coffee settings
            lavazza_settings = get_settings('lavazza')
            
            try:
                # last_date is in DD/MM/YYYY format from database, parse explicitly
                last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                # HTML date input is always YYYY-MM-DD format
                current_date_obj = parser.parse(date, dayfirst=False).date()
                
                # Sum all coffee sales between last date and current date
                for row in imported_rows:
                    if not row['date']:
                        continue
                    try:
                        row_date = parser.parse(row['date'], dayfirst=True).date()
                        
                        for coffee_desc in lavazza_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                if last_date_obj < row_date <= current_date_obj:
                                    coffees_from_csv += row['quantity']
                                break
                    except Exception as e:
                        continue
            except Exception as e:
                pass
        
        conn.close()
        
        return jsonify({'success': True, 'coffeesSold': coffees_from_csv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/lavazza/deliveries')
def get_lavazza_deliveries():
    """Get deliveries from CSV purchases data"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get imported purchases data
        c.execute("SELECT description, quantity FROM importedData WHERE data_type = 'purchases'")
        imported_purchases_rows = [dict(row) for row in c.fetchall()]
        
        delivers_from_csv = 0
        if imported_purchases_rows:
            # Get lavazza purchases settings
            lavazza_purchases_settings = get_settings('lavazza_purchases')
            
            # Sum all purchases matching lavazza descriptions
            for row in imported_purchases_rows:
                for coffee_desc in lavazza_purchases_settings:
                    if coffee_desc and coffee_desc.lower() in row['description'].lower():
                        delivers_from_csv += row['quantity']
                        break
        
        conn.close()
        
        return jsonify({'success': True, 'deliveries': delivers_from_csv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/lavazza/<int:record_id>', methods=['DELETE'])
def delete_lavazza_entry(record_id):
    """Delete lavazza entry"""
    try:
        delete_record('lavazza', record_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== SUGAR ROUTES ====================

@app.route('/sugar')
def sugar_page():
    """Sugar and sweetener page"""
    records = get_table_data('coffeeSugar')
    
    # Get weight settings
    sugar_weight_settings = get_settings('sugar_weight')
    sweetener_weight_settings = get_settings('sweetener_weight')
    
    sugar_weight = float(sugar_weight_settings[0]) if sugar_weight_settings else 1000
    sweetener_weight = float(sweetener_weight_settings[0]) if sweetener_weight_settings else 500
    
    # Calculate coffees sold from imported sales data
    coffees_from_csv = 0
    if records:  # Only calculate if we have existing records
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT date FROM coffeeSugar ORDER BY date DESC LIMIT 1")
        latest_record = c.fetchone()
        
        if latest_record:
            last_date = latest_record['date']
            c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
            imported_rows = [dict(row) for row in c.fetchall()]
            
            if imported_rows:
                # Get sugar coffee settings (from sales CSV settings)
                sugar_settings = get_settings('sugar')
                
                try:
                    # Parse the last date (DD/MM/YYYY format from DB)
                    from datetime import datetime
                    last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                    today = datetime.now().date()
                    
                    # Sum all coffee sales between last date and today
                    for row in imported_rows:
                        for coffee_desc in sugar_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                try:
                                    row_date = parser.parse(row['date'], dayfirst=True).date()
                                    if row_date > last_date_obj:
                                        coffees_from_csv += row['quantity']
                                except:
                                    continue
                except Exception as e:
                    print(f"Error calculating coffees from CSV: {e}")
        
        conn.close()
    
    return render_template('sugar.html', records=records, sugar_weight=sugar_weight, sweetener_weight=sweetener_weight, coffees_from_csv=coffees_from_csv)

@app.route('/api/sugar', methods=['POST'])
def add_sugar_entry():
    """Add new sugar entry"""
    try:
        data = request.json
        date_str = format_date(data.get('date', ''))
        
        sugar_buy = int(data.get('sugarBuy', 0))
        sweetner_buy = int(data.get('sweetnerBuy', 0))
        coffee_sold = float(data.get('coffeeSold', 0))
        
        # Get weight settings from database
        sugar_weight_settings = get_settings('sugar_weight')
        sweetener_weight_settings = get_settings('sweetener_weight')
        
        sugar_weight = float(sugar_weight_settings[0]) if sugar_weight_settings else 1000
        sweetener_weight = float(sweetener_weight_settings[0]) if sweetener_weight_settings else 500
        
        # Store the actual user input (in grams), not the calculated units
        sugar_hand = float(data.get('sugarHand', 0))
        sweetner_hand = float(data.get('sweetnerHand', 0))
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO coffeeSugar
                    (date, sugarBuy, sugarHand, sweetnerBuy, sweetnerHand, coffeeSold)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                 (date_str, sugar_buy, sugar_hand, sweetner_buy, sweetner_hand, coffee_sold))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Sugar entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sugar/<int:record_id>', methods=['DELETE'])
def delete_sugar_entry(record_id):
    """Delete sugar entry"""
    try:
        delete_record('coffeeSugar', record_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sugar/coffee-sold/<date>')
def get_sugar_coffee_sold_for_date(date):
    """Get coffee sold from CSV for a specific date"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the latest sugar entry before this date
        c.execute("SELECT date FROM coffeeSugar WHERE date < ? ORDER BY date DESC LIMIT 1", (date,))
        previous_record = c.fetchone()
        
        coffees_from_csv = 0
        
        # Determine the start date for the range
        if previous_record:
            last_date = previous_record['date']
        else:
            # If no previous record, use a very old date so we get all sales up to current date
            last_date = "1900-01-01"
        
        # Get imported sales data
        c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = 'sales'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        if imported_rows:
            # Get sugar coffee settings
            sugar_settings = get_settings('sugar')
            
            try:
                # last_date is in DD/MM/YYYY format from database, parse explicitly
                last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                # HTML date input is always YYYY-MM-DD format
                current_date_obj = parser.parse(date, dayfirst=False).date()
                
                # Sum all coffee sales between last date and current date
                for row in imported_rows:
                    if not row['date']:
                        continue
                    try:
                        row_date = parser.parse(row['date'], dayfirst=True).date()
                        
                        for coffee_desc in sugar_settings:
                            if coffee_desc and coffee_desc.lower() in row['description'].lower():
                                if last_date_obj < row_date <= current_date_obj:
                                    coffees_from_csv += row['quantity']
                                break
                    except Exception as e:
                        continue
            except Exception as e:
                pass
        
        conn.close()
        
        return jsonify({'success': True, 'coffeesSold': coffees_from_csv})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sugar/purchases')
def get_sugar_purchases():
    """Get sugar and sweetener purchases from CSV"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get imported purchases data
        c.execute("SELECT description, quantity FROM importedData WHERE data_type = 'purchases'")
        imported_purchases_rows = [dict(row) for row in c.fetchall()]
        
        sugar_bought = 0
        sweetener_bought = 0
        
        if imported_purchases_rows:
            # Get sugar purchases settings
            sugar_purchases_settings = get_settings('sugar_purchases')
            sweetener_purchases_settings = get_settings('sweetener_purchases')
            
            # Sum all purchases matching sugar and sweetener descriptions
            for row in imported_purchases_rows:
                for sugar_desc in sugar_purchases_settings:
                    if sugar_desc and sugar_desc.lower() in row['description'].lower():
                        sugar_bought += row['quantity']
                        break
                else:
                    # Only check sweetener if not matched as sugar
                    for sweetener_desc in sweetener_purchases_settings:
                        if sweetener_desc and sweetener_desc.lower() in row['description'].lower():
                            sweetener_bought += row['quantity']
                            break
        
        conn.close()
        
        return jsonify({'success': True, 'sugarBought': sugar_bought, 'sweetenerBought': sweetener_bought})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== REPORTS ROUTES ====================

@app.route('/api/milk/data')
def get_milk_data():
    """Get all milk data as JSON"""
    records = get_table_data('milkUsage')
    data = [dict(r) for r in records]
    return jsonify(data)

@app.route('/api/bean/data')
def get_bean_data():
    """Get all bean coffee data as JSON"""
    records = get_table_data('coffeeBean')
    data = [dict(r) for r in records]
    return jsonify(data)

@app.route('/api/lavazza/data')
def get_lavazza_data():
    """Get all lavazza data as JSON"""
    records = get_table_data('lavazza')
    data = [dict(r) for r in records]
    return jsonify(data)

@app.route('/api/sugar/data')
def get_sugar_data():
    """Get all sugar data as JSON"""
    records = get_table_data('coffeeSugar')
    data = [dict(r) for r in records]
    return jsonify(data)

# ==================== SETTINGS & IMPORT ROUTES ====================

# Bakery Routes
@app.route('/bakery/dough')
def bakery_dough():
    """Bakery dough tracking page"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bakeryDough ORDER BY date DESC")
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template('bakery/dough.html', records=records)

@app.route('/bakery/egg-wash')
def bakery_egg_wash():
    """Bakery egg wash tracking page"""
    return render_template('bakery/egg-wash.html')

@app.route('/bakery/mayo')
def bakery_mayo():
    """Bakery mayo usage tracking page"""
    return render_template('bakery/mayo.html')

@app.route('/bakery/sweet-chilli')
def bakery_sweet_chilli():
    """Bakery sweet chilli usage tracking page"""
    return render_template('bakery/sweet-chilli.html')

# Bakery API Endpoints
@app.route('/api/bakery/dough', methods=['POST'])
def add_bakery_dough():
    """Add dough entry"""
    try:
        data = request.json
        print(f"[v0] Received data: {data}")
        
        date_str = format_date(data.get('date', ''))
        cake_flour = float(data.get('cakeFlour', 0))
        bread_flour = float(data.get('breadFlour', 0))
        yeast = float(data.get('yeast', 0))
        oil = float(data.get('oil', 0))
        sugar = float(data.get('sugar', 0))
        cake_flour_bought = float(data.get('cakeFlourBought', 0))
        bread_flour_bought = float(data.get('breadFlourBought', 0))
        yeast_bought = float(data.get('yeastBought', 0))
        oil_bought = float(data.get('oilBought', 0))
        sugar_bought = float(data.get('sugarBought', 0))
        pizza_sales = float(data.get('pizzaSales', 0))
        normal_sales = float(data.get('normalSales', 0))
        
        print(f"[v0] Parsed values - date: {date_str}, pizza_sales: {pizza_sales}, normal_sales: {normal_sales}")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO bakeryDough
                    (date, cakeFlour, breadFlour, yeast, oil, sugar, cakeFlourBought, breadFlourBought, yeastBought, oilBought, sugarBought, pizzaSales, normalSales)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (date_str, cake_flour, bread_flour, yeast, oil, sugar, cake_flour_bought, bread_flour_bought, yeast_bought, oil_bought, sugar_bought, pizza_sales, normal_sales))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Dough entry added successfully'})
    except Exception as e:
        print(f"[v0] Error in add_bakery_dough: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/dough/<int:record_id>', methods=['DELETE'])
def delete_bakery_dough(record_id):
    """Delete bakery dough entry"""
    try:
        delete_record('bakeryDough', record_id)
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/dough-purchases/<date>')
def get_dough_purchases_for_date(date):
    """Get dough ingredient purchases from CSV - sum all matching products"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        purchases = {
            'cakeFlourBought': 0,
            'breadFlourBought': 0,
            'yeastBought': 0,
            'oilBought': 0,
            'sugarBought': 0
        }
        
        # Get imported purchase data
        c.execute("SELECT description, quantity FROM importedData WHERE data_type = 'purchases'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        print(f"[v0] Found {len(imported_rows)} imported rows")
        
        if imported_rows:
            # Get dough purchase settings
            cake_flour_settings = get_settings('cake_flour_bought')
            bread_flour_settings = get_settings('bread_flour_bought')
            yeast_settings = get_settings('yeast_bought')
            oil_settings = get_settings('oil_bought')
            sugar_settings = get_settings('sugar_bought')
            
            print(f"[v0] Settings - Cake flour: {cake_flour_settings}, Bread flour: {bread_flour_settings}, Yeast: {yeast_settings}, Oil: {oil_settings}, Sugar: {sugar_settings}")
            
            # Sum all purchases that match product descriptions
            for row in imported_rows:
                if not row['description']:
                    continue
                
                description_lower = row['description'].lower()
                quantity = row['quantity']
                
                # Check cake flour
                for desc in cake_flour_settings:
                    if desc and desc.lower() in description_lower:
                        purchases['cakeFlourBought'] += quantity
                        print(f"[v0] Matched cake flour: '{desc}' in '{row['description']}' (+{quantity})")
                        break
                
                # Check bread flour
                for desc in bread_flour_settings:
                    if desc and desc.lower() in description_lower:
                        purchases['breadFlourBought'] += quantity
                        print(f"[v0] Matched bread flour: '{desc}' in '{row['description']}' (+{quantity})")
                        break
                
                # Check yeast
                for desc in yeast_settings:
                    if desc and desc.lower() in description_lower:
                        purchases['yeastBought'] += quantity
                        print(f"[v0] Matched yeast: '{desc}' in '{row['description']}' (+{quantity})")
                        break
                
                # Check oil
                for desc in oil_settings:
                    if desc and desc.lower() in description_lower:
                        purchases['oilBought'] += quantity
                        print(f"[v0] Matched oil: '{desc}' in '{row['description']}' (+{quantity})")
                        break
                
                # Check sugar
                for desc in sugar_settings:
                    if desc and desc.lower() in description_lower:
                        purchases['sugarBought'] += quantity
                        print(f"[v0] Matched sugar: '{desc}' in '{row['description']}' (+{quantity})")
                        break
        
        conn.close()
        
        print(f"[v0] Final purchases result: {purchases}")
        return jsonify({'success': True, 'purchases': purchases})
    except Exception as e:
        print(f"[v0] Exception in get_dough_purchases_for_date: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/dough-sales/<date>')
def get_dough_sales_for_date(date):
    """Get dough sales from CSV between last entry and current date - split by pizza and normal"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get the latest dough entry before this date
        c.execute("SELECT date FROM bakeryDough WHERE date < ? ORDER BY date DESC LIMIT 1", (date,))
        previous_record = c.fetchone()
        
        # Determine the start date for the range
        if previous_record:
            last_date = previous_record['date']
        else:
            last_date = "1900-01-01"
        
        print(f"[v0] Sales range: {last_date} < date <= {date}")
        
        pizza_sales = 0
        normal_sales = 0
        
        # Get imported sales data with dates
        c.execute("SELECT description, quantity, date FROM importedData WHERE data_type = 'sales'")
        imported_rows = [dict(row) for row in c.fetchall()]
        
        if imported_rows:
            # Get pizza and normal dough sales settings
            pizza_dough_settings = get_settings('pizza_dough_sales')
            normal_dough_settings = get_settings('normal_dough_sales')
            
            try:
                last_date_obj = datetime.strptime(last_date, '%d/%m/%Y').date()
                current_date_obj = parser.parse(date, dayfirst=False).date()
                
                # Sum all sales that match product descriptions between dates
                for row in imported_rows:
                    if not row['description'] or not row['date']:
                        continue
                    
                    try:
                        row_date = parser.parse(row['date'], dayfirst=True).date()
                        
                        # Check if date is in range
                        if last_date_obj < row_date <= current_date_obj:
                            description_lower = row['description'].lower()
                            quantity = row['quantity']
                            
                            # Check pizza dough products
                            for desc in pizza_dough_settings:
                                if desc and desc.lower() in description_lower:
                                    pizza_sales += quantity
                                    print(f"[v0] Matched pizza dough sale: '{desc}' in '{row['description']}' (+{quantity})")
                                    break
                            else:
                                # Check normal dough products
                                for desc in normal_dough_settings:
                                    if desc and desc.lower() in description_lower:
                                        normal_sales += quantity
                                        print(f"[v0] Matched normal dough sale: '{desc}' in '{row['description']}' (+{quantity})")
                                        break
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"[v0] Error parsing dates: {e}")
        
        conn.close()
        
        print(f"[v0] Sales calculated - Pizza: {pizza_sales}, Normal: {normal_sales}")
        return jsonify({'success': True, 'pizza_sales': pizza_sales, 'normal_sales': normal_sales})
    except Exception as e:
        print(f"[v0] Exception in get_dough_sales_for_date: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/dough-count')
def get_dough_entry_count():
    """Get count of existing dough entries"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) as count FROM bakeryDough")
        result = c.fetchone()
        count = result['count'] if result else 0
        
        conn.close()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"[v0] Exception in get_dough_entry_count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/egg-wash', methods=['POST'])
def add_bakery_egg_wash():
    """Add egg wash entry"""
    try:
        data = request.json
        return jsonify({'success': True, 'message': 'Egg wash entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/mayo', methods=['POST'])
def add_bakery_mayo():
    """Add mayo usage entry"""
    try:
        data = request.json
        return jsonify({'success': True, 'message': 'Mayo entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/bakery/sweet-chilli', methods=['POST'])
def add_bakery_sweet_chilli():
    """Add sweet chilli usage entry"""
    try:
        data = request.json
        return jsonify({'success': True, 'message': 'Sweet chilli entry added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/settings')
def settings_page():
    """Settings page for CSV configuration - Coffee and Milk"""
    milk_settings = get_settings('milk')
    bean_settings = get_settings('bean')
    lavazza_settings = get_settings('lavazza')
    lavazza_purchases_settings = get_settings('lavazza_purchases')
    sugar_settings = get_settings('sugar')
    sugar_purchases_settings = get_settings('sugar_purchases')
    sweetener_purchases_settings = get_settings('sweetener_purchases')
    
    # Get weight settings
    sugar_weight_settings = get_settings('sugar_weight')
    sweetener_weight_settings = get_settings('sweetener_weight')
    
    sugar_weight = float(sugar_weight_settings[0]) if sugar_weight_settings else 1000
    sweetener_weight = float(sweetener_weight_settings[0]) if sweetener_weight_settings else 500
    
    return render_template('settings.html',
                          milk_settings=milk_settings,
                          bean_settings=bean_settings,
                          lavazza_settings=lavazza_settings,
                          lavazza_purchases_settings=lavazza_purchases_settings,
                          sugar_settings=sugar_settings,
                          sugar_purchases_settings=sugar_purchases_settings,
                          sweetener_purchases_settings=sweetener_purchases_settings,
                          sugar_weight=sugar_weight,
                          sweetener_weight=sweetener_weight)

@app.route('/bakery/settings')
def bakery_settings_page():
    """Settings page for Bakery configuration"""
    cake_flour_bought_settings = get_settings('cake_flour_bought')
    bread_flour_bought_settings = get_settings('bread_flour_bought')
    yeast_bought_settings = get_settings('yeast_bought')
    oil_bought_settings = get_settings('oil_bought')
    sugar_bought_settings = get_settings('sugar_bought')
    pizza_dough_sales_settings = get_settings('pizza_dough_sales')
    normal_dough_sales_settings = get_settings('normal_dough_sales')
    
    return render_template('bakery/settings.html',
                          cake_flour_bought_settings=cake_flour_bought_settings,
                          bread_flour_bought_settings=bread_flour_bought_settings,
                          yeast_bought_settings=yeast_bought_settings,
                          oil_bought_settings=oil_bought_settings,
                          sugar_bought_settings=sugar_bought_settings,
                          pizza_dough_sales_settings=pizza_dough_sales_settings,
                          normal_dough_sales_settings=normal_dough_sales_settings)

@app.route('/api/settings/<category>', methods=['POST'])
def save_category_settings(category):
    """Save settings for a category"""
    try:
        data = request.json
        descriptions = data.get('descriptions', [])
        
        # Filter out empty descriptions
        descriptions = [d.strip() for d in descriptions if d.strip()]
        
        if descriptions:
            save_settings(category, descriptions)
            return jsonify({'success': True, 'message': f'{category.title()} settings saved'})
        else:
            return jsonify({'success': False, 'error': 'At least one description required'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/settings/sugar-weights', methods=['POST'])
def save_sugar_weights():
    """Save sugar and sweetener weight settings"""
    try:
        data = request.json
        sugar_weight = float(data.get('sugarWeight', 0))
        sweetener_weight = float(data.get('sweetenerWeight', 0))
        
        if sugar_weight <= 0 or sweetener_weight <= 0:
            return jsonify({'success': False, 'error': 'Weight must be greater than 0'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Delete existing weights
        c.execute("DELETE FROM csvSettings WHERE category IN ('sugar_weight', 'sweetener_weight')")
        
        # Insert new weights (storing weight as the description field)
        c.execute("INSERT INTO csvSettings (category, descriptions) VALUES (?, ?)", 
                  ('sugar_weight', str(sugar_weight)))
        c.execute("INSERT INTO csvSettings (category, descriptions) VALUES (?, ?)", 
                  ('sweetener_weight', str(sweetener_weight)))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Weight settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/settings/dough-purchases', methods=['POST'])
def save_dough_purchases_settings():
    """Save dough purchases CSV product descriptions"""
    try:
        data = request.json
        
        categories = {
            'cake_flour_bought': data.get('cake_flour_bought', []),
            'bread_flour_bought': data.get('bread_flour_bought', []),
            'yeast_bought': data.get('yeast_bought', []),
            'oil_bought': data.get('oil_bought', []),
            'sugar_bought': data.get('sugar_bought', [])
        }
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Save each category's descriptions
        for category, descriptions in categories.items():
            if descriptions:
                desc_str = '|'.join(descriptions)
                c.execute("""INSERT OR REPLACE INTO csvSettings (category, descriptions, updated_at)
                             VALUES (?, ?, CURRENT_TIMESTAMP)""",
                         (category, desc_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Dough purchases settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/settings/dough-sales', methods=['POST'])
def save_dough_sales_settings():
    """Save dough sales CSV product descriptions"""
    try:
        data = request.json
        
        categories = {
            'pizza_dough_sales': data.get('pizza_dough_sales', []),
            'normal_dough_sales': data.get('normal_dough_sales', [])
        }
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Save each category's descriptions
        for category, descriptions in categories.items():
            if descriptions:
                desc_str = '|'.join(descriptions)
                c.execute("""INSERT OR REPLACE INTO csvSettings (category, descriptions, updated_at)
                             VALUES (?, ?, CURRENT_TIMESTAMP)""",
                         (category, desc_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Dough sales settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/import')
def import_page():
    """CSV import page"""
    return render_template('import.html')

@app.route('/api/import/sales', methods=['POST'])
def import_sales_csv():
    """Import sales CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
        
        # Read and parse CSV with encoding fallback
        file_bytes = file.read()
        content = decode_file_content(file_bytes)
        sales_data = parse_sales_csv(content)
        
        # Clear old import data and save new data
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM importedData WHERE data_type = 'sales'")
        
        for row in sales_data:
            c.execute("""INSERT INTO importedData (data_type, description, date, quantity)
                        VALUES (?, ?, ?, ?)""",
                     ('sales', row['description'], row['date'], row['quantity']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Imported {len(sales_data)} sales records',
                       'count': len(sales_data)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/import/purchases', methods=['POST'])
def import_purchases_csv():
    """Import purchases CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
        
        # Read and parse CSV with encoding fallback
        file_bytes = file.read()
        content = decode_file_content(file_bytes)
        purchases_data = parse_purchases_csv(content)
        
        # Clear old import data and save new data
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM importedData WHERE data_type = 'purchases'")
        
        for row in purchases_data:
            c.execute("""INSERT INTO importedData (data_type, description, quantity)
                        VALUES (?, ?, ?)""",
                     ('purchases', row['description'], row['quantity']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Imported {len(purchases_data)} purchase records',
                       'count': len(purchases_data)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/import/get-data/<data_type>/<category>/<date_from>/<date_to>')
def get_import_data(data_type, category, date_from, date_to):
    """Get imported data for a category and date range"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get settings for this category
        descriptions = get_settings(category)
        
        # Get imported data
        c.execute("SELECT description, date, quantity FROM importedData WHERE data_type = ?",
                 (data_type,))
        imported_rows = [dict(row) for row in c.fetchall()]
        conn.close()
        
        # Match and sum quantities
        result = {}
        for desc in descriptions:
            quantity = get_matching_quantity(imported_rows, desc, date_from, date_to)
            result[desc] = quantity
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
