from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import hashlib
import os

app = Flask(__name__, template_folder='.')
app.secret_key = os.environ.get("SECRET_KEY", "stocksense-secret-key")  # ← Change this in production!
CORS(app, supports_credentials=True)

# ─── DATABASE CONFIG ──────────────────────────────────────────────────────────
DB_CONFIG = {
    'host': 'mysql.railway.internal',
    'user': 'root',             # ← Change to your MySQL username
    'password': 'aVuKLnRHybdBepNdzPgRjPPLGQSRrEFw', # ← Change to your MySQL password
    'database': 'railway',
    'port': int(3306)
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"DB Error: {e}")
        return None

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def require_login():
    """Returns None if logged in, else a redirect response."""
    if 'user_id' not in session:
        return redirect('/login.html')
    return None

# ─── INIT DATABASE ────────────────────────────────────────────────────────────
def init_db():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS stock_sense")
    cur.execute("USE stock_sense")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            role VARCHAR(20) DEFAULT 'cashier',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) DEFAULT '',
            quantity INT DEFAULT 0,
            purchase_price DECIMAL(10,2) NOT NULL,
            selling_price DECIMAL(10,2) NOT NULL,
            barcode VARCHAR(100) DEFAULT NULL,
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(100) DEFAULT 'Walk-in Customer',
            total_amount DECIMAL(10,2) NOT NULL,
            total_cost DECIMAL(10,2) NOT NULL,
            profit DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_id INT NOT NULL,
            product_id INT NOT NULL,
            product_name VARCHAR(100),
            quantity INT NOT NULL,
            purchase_price DECIMAL(10,2),
            selling_price DECIMAL(10,2),
            subtotal DECIMAL(10,2),
            FOREIGN KEY (bill_id) REFERENCES bills(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.commit(); cur.close(); conn.close()
    print("✅ stock_sense database ready.")

# ─── SERVE HTML PAGES (with auth guard) ──────────────────────────────────────
@app.route('/')
def root():
    if 'user_id' in session:
        return redirect('/home.html')
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index_page(): return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page(): return send_from_directory('.', 'login.html')

@app.route('/signup.html')
def signup_page(): return send_from_directory('.', 'signup.html')

@app.route('/home.html')
def home_page():
    guard = require_login()
    return guard if guard else send_from_directory('.', 'home.html')

@app.route('/billing.html')
def billing_page():

    guard = require_login()

    if guard:
        return guard

    allowed_roles = ['owner', 'manager', 'cashier']

    if session.get('role') not in allowed_roles:
        return "Access Denied"

    return send_from_directory('.', 'billing.html')
@app.route('/inventory.html')
def inventory_page():

    guard = require_login()

    if guard:
        return guard

    allowed_roles = ['owner', 'manager']

    if session.get('role') not in allowed_roles:
        return """
<script>

    alert('⛔ Access Denied');

    window.location.href = '/home.html';

</script>
"""

    return send_from_directory('.', 'inventory.html')
@app.route('/profit.html')
def profit_page():

    guard = require_login()

    if guard:
        return guard

    allowed_roles = ['owner', 'manager']

    if session.get('role') not in allowed_roles:
        return """
<script>

    alert('⛔ Access Denied');

    window.location.href = '/home.html';

</script>
"""

    return send_from_directory('.', 'profit.html')
@app.route('/alerts.html')
def alerts_page():
    guard = require_login()
    return guard if guard else send_from_directory('.', 'alerts.html')

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────
@app.route('/signup', methods=['POST'])
def signup():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        if not username or not password or not role:
            return "All fields are required", 400
        conn = get_db()
        if not conn:
            return "Database connection failed", 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )
        existing_user = cursor.fetchone()
        if existing_user:
            return "Username already exists", 400
        hashed_password = hash_pw(password)
        query = """
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        """
        cursor.execute(
            query,
            (username, hashed_password, role)
        )
        conn.commit()
        return "User registered successfully"

    except Exception as e:

        print(e)

        return str(e), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
@app.route('/login', methods=['POST'])
def login():

    data = request.json

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    conn = get_db()
    if not conn:
        return jsonify({
            'success': False,
            'message': 'Database connection failed'
        }), 500
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE username=%s AND password=%s
        """,
        (username, hash_pw(password))
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        if user['role'] == 'owner':
            return jsonify({
                'success': True,
                'redirect': '/home.html',
                'role': 'owner'
            })
        elif user['role'] == 'manager':
            return jsonify({
                'success': True,
                'redirect': '/home.html',
                'role': 'manager'
            })
        elif user['role'] == 'cashier':
            return jsonify({
                'success': True,
                'redirect': '/billing.html',
                'role': 'cashier'
            })
    return jsonify({
        'success': False,
        'message': 'Invalid username or password'
    }), 401
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login.html')

@app.route('/api/me')
def me():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session.get('username', '')})
    return jsonify({'logged_in': False}), 401

# ─── PRODUCTS API ─────────────────────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM products ORDER BY name")
    products = cur.fetchall()
    for p in products:
        if p['expiry_date']: p['expiry_date'] = str(p['expiry_date'])
        if p['created_at']:  p['created_at']  = str(p['created_at'])
        p['purchase_price'] = float(p['purchase_price'])
        p['selling_price']  = float(p['selling_price'])
    cur.close(); conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    d = request.json; conn = get_db(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (name,category,quantity,purchase_price,selling_price,barcode,expiry_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (d['name'], d.get('category',''), int(d['quantity']),
          float(d['purchase_price']), float(d['selling_price']),
          d.get('barcode') or None, d.get('expiry_date') or None))
    conn.commit(); pid = cur.lastrowid
    cur.close(); conn.close()
    return jsonify({'success': True, 'id': pid}), 201

@app.route('/api/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    d = request.json; conn = get_db(); cur = conn.cursor()
    cur.execute("""
        UPDATE products SET name=%s,category=%s,quantity=%s,
        purchase_price=%s,selling_price=%s,barcode=%s,expiry_date=%s WHERE id=%s
    """, (d['name'], d.get('category',''), int(d['quantity']),
          float(d['purchase_price']), float(d['selling_price']),
          d.get('barcode') or None, d.get('expiry_date') or None, pid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})

# ─── BILLING API ──────────────────────────────────────────────────────────────
@app.route('/api/bills', methods=['POST'])
def create_bill():
    data = request.json
    items    = data.get('items', [])
    customer = data.get('customer_name', 'Walk-in Customer')
    if not items: return jsonify({'error': 'No items'}), 400

    conn = get_db(); cur = conn.cursor(dictionary=True)
    total_amount = total_cost = 0; rows = []

    for item in items:
        cur.execute("SELECT * FROM products WHERE id=%s", (item['product_id'],))
        p = cur.fetchone()
        if not p: return jsonify({'error': 'Product not found'}), 404
        if p['quantity'] < item['quantity']:
            return jsonify({'error': f"Insufficient stock for {p['name']}"}), 400
        sub  = float(p['selling_price']) * item['quantity']
        cost = float(p['purchase_price']) * item['quantity']
        total_amount += sub; total_cost += cost
        rows.append({**p, 'qty': item['quantity'], 'subtotal': sub})

    profit = total_amount - total_cost
    cur2 = conn.cursor()
    cur2.execute("INSERT INTO bills (customer_name,total_amount,total_cost,profit) VALUES (%s,%s,%s,%s)",
                 (customer, total_amount, total_cost, profit))
    bill_id = cur2.lastrowid

    bill_items_out = []
    for r in rows:
        cur2.execute("""INSERT INTO bill_items
            (bill_id,product_id,product_name,quantity,purchase_price,selling_price,subtotal)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (bill_id, r['id'], r['name'], r['qty'],
             float(r['purchase_price']), float(r['selling_price']), r['subtotal']))
        cur2.execute("UPDATE products SET quantity=quantity-%s WHERE id=%s", (r['qty'], r['id']))
        bill_items_out.append({
            'product_name': r['name'], 'quantity': r['qty'],
            'selling_price': float(r['selling_price']), 'subtotal': r['subtotal']
        })

    conn.commit(); cur.close(); cur2.close(); conn.close()
    return jsonify({
        'success': True, 'bill_id': bill_id,
        'total_amount': total_amount, 'total_cost': total_cost,
        'profit': profit, 'items': bill_items_out, 'customer_name': customer
    }), 201

@app.route('/api/bills', methods=['GET'])
def get_bills():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM bills ORDER BY created_at DESC LIMIT 100")
    bills = cur.fetchall()
    for b in bills:
        b['created_at'] = str(b['created_at'])
        b['total_amount'] = float(b['total_amount'])
        b['total_cost']   = float(b['total_cost'])
        b['profit']       = float(b['profit'])
    cur.close(); conn.close()
    return jsonify(bills)

@app.route('/api/bills/<int:bill_id>', methods=['GET'])
def get_bill(bill_id):
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM bills WHERE id=%s", (bill_id,))
    bill = cur.fetchone()
    if not bill: return jsonify({'error':'Not found'}), 404
    bill['created_at']   = str(bill['created_at'])
    bill['total_amount'] = float(bill['total_amount'])
    bill['total_cost']   = float(bill['total_cost'])
    bill['profit']       = float(bill['profit'])
    cur.execute("SELECT * FROM bill_items WHERE bill_id=%s", (bill_id,))
    items = cur.fetchall()
    for i in items:
        i['selling_price']  = float(i['selling_price'])
        i['purchase_price'] = float(i['purchase_price'])
        i['subtotal']       = float(i['subtotal'])
    bill['items'] = items
    cur.close(); conn.close()
    return jsonify(bill)

# ─── PROFIT API ───────────────────────────────────────────────────────────────
@app.route('/api/profit/summary', methods=['GET'])
def profit_summary():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    today       = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    def q(where, val=None):
        sql = f"""SELECT COALESCE(SUM(total_amount),0) revenue,
                         COALESCE(SUM(total_cost),0) cost,
                         COALESCE(SUM(profit),0) profit,
                         COUNT(*) bills
                  FROM bills WHERE {where}"""
        cur.execute(sql, (val,) if val else ())
        return {k: float(v) for k,v in cur.fetchone().items()}

    daily   = q("DATE(created_at)=%s", today)
    monthly = q("DATE(created_at)>=%s", month_start)
    alltime = q("1=1")

    # 30-day daily chart
    cur.execute("""
        SELECT DATE(created_at) day,
               COALESCE(SUM(total_amount),0) revenue,
               COALESCE(SUM(profit),0) profit,
               COUNT(*) bills
        FROM bills WHERE created_at >= DATE_SUB(NOW(),INTERVAL 30 DAY)
        GROUP BY DATE(created_at) ORDER BY day
    """)
    chart = [{'day':str(r['day']),'revenue':float(r['revenue']),
              'profit':float(r['profit']),'bills':int(r['bills'])}
             for r in cur.fetchall()]

    # Top products by profit
    cur.execute("""
        SELECT bi.product_name,
               SUM(bi.quantity) units_sold,
               SUM(bi.subtotal) revenue,
               SUM((bi.selling_price-bi.purchase_price)*bi.quantity) profit
        FROM bill_items bi GROUP BY bi.product_name
        ORDER BY profit DESC LIMIT 8
    """)
    top = [{'product_name':r['product_name'],'units_sold':int(r['units_sold']),
            'revenue':float(r['revenue']),'profit':float(r['profit'])}
           for r in cur.fetchall()]

    # Category breakdown
    cur.execute("""
        SELECT p.category,
               SUM(bi.subtotal) revenue,
               SUM((bi.selling_price-bi.purchase_price)*bi.quantity) profit,
               SUM(bi.quantity) units
        FROM bill_items bi
        JOIN products p ON p.id=bi.product_id
        WHERE p.category != ''
        GROUP BY p.category ORDER BY profit DESC
    """)
    by_cat = [{'category':r['category'],'revenue':float(r['revenue']),
               'profit':float(r['profit']),'units':int(r['units'])}
              for r in cur.fetchall()]

    cur.close(); conn.close()
    return jsonify({'daily':daily,'monthly':monthly,'alltime':alltime,
                    'chart':chart,'top_products':top,'by_category':by_cat})

# ─── ALERTS API ───────────────────────────────────────────────────────────────
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, name, category, quantity, expiry_date,
               DATEDIFF(expiry_date, CURDATE()) days_left
        FROM products
        WHERE expiry_date IS NOT NULL
          AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY expiry_date ASC
    """)
    alerts = []
    for r in cur.fetchall():
        alerts.append({
            'id': r['id'], 'name': r['name'], 'category': r['category'],
            'quantity': r['quantity'], 'expiry_date': str(r['expiry_date']),
            'days_left': int(r['days_left'])
        })
    cur.close(); conn.close()
    return jsonify(alerts)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Stock Sense running on port {port}\n")
    app.run(host='0.0.0.0', port=port)
