"""
Weekly Stock Takes - Flask Web Application
A web-based coffee shop inventory management system
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
import sqlite3
import os
from dateutil import parser

app = Flask(__name__)
DATABASE = 'stocktakes.db'

# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize the SQLite database with required tables"""
    if os.path.exists(DATABASE):
        return
    
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
        parsed_date = parser.parse(date_str, dayfirst=True)
        return parsed_date.strftime('%d/%m/%Y')
    except:
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
    return render_template('milk.html', records=records)

@app.route('/api/milk', methods=['POST'])
def add_milk_entry():
    """Add new milk usage entry"""
    try:
        data = request.json
        date_str = format_date(data.get('date', ''))
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Calculate coffee sold and usage
        two_liter = int(data.get('twoLiter', 0))
        one_liter = int(data.get('oneLiter', 0))
        five_mil = int(data.get('fiveMil', 0))
        
        total_milk = (two_liter * 2000) + (one_liter * 1000) + (five_mil * 500)
        coffee_sold = float(data.get('coffeeSold', 0))
        
        usage = total_milk / coffee_sold if coffee_sold > 0 else 0
        
        c.execute("""INSERT INTO milkUsage 
                    (date, twoLiter, oneLiter, fiveMil, coffeeSold, usage)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                 (date_str, two_liter, one_liter, five_mil, coffee_sold, usage))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Milk entry added successfully'})
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
    return render_template('bean.html', records=records)

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
    return render_template('lavazza.html', records=records)

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
    return render_template('sugar.html', records=records)

@app.route('/api/sugar', methods=['POST'])
def add_sugar_entry():
    """Add new sugar entry"""
    try:
        data = request.json
        date_str = format_date(data.get('date', ''))
        
        sugar_buy = int(data.get('sugarBuy', 0))
        sugar_hand = float(data.get('sugarHand', 0)) / 4
        sweetner_buy = int(data.get('sweetnerBuy', 0))
        sweetner_hand = float(data.get('sweetnerHand', 0))
        coffee_sold = float(data.get('coffeeSold', 0))
        
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
