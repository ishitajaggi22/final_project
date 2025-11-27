import mysql.connector
from flask import Flask, request, jsonify
import bcrypt
import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
# UPDATE THESE WITH YOUR MYSQL CREDENTIALS
db_config = {
    'user': 'root',       
    'password': '121104', 
    'host': 'localhost',
    'database': 'bookstore_db'
}

# --- DATABASE HELPER ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to DB: {err}")
        return None

# --- AUTHENTICATION ENDPOINTS ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'customer') # Default to customer

    if not username or not password or not email:
        return jsonify({"error": "Missing fields"}), 400

    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)",
            (username, hashed, email, role)
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        # In a real app, generate a JWT token here. 
        # For this v1.0, we return the user ID and role for session management.
        return jsonify({
            "message": "Login successful",
            "user_id": user['id'],
            "role": user['role'],
            "token": "simulated-token-123" 
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

# --- BOOK ENDPOINTS ---

@app.route('/books', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s"
    search_term = f"%{query}%"
    cursor.execute(sql, (search_term, search_term))
    books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    # Manager only endpoint (check role in client or add middleware here)
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "INSERT INTO books (title, author, price_buy, price_rent, stock) VALUES (%s, %s, %s, %s, %s)"
    vals = (data['title'], data['author'], data['price_buy'], data['price_rent'], data['stock'])
    
    try:
        cursor.execute(sql, vals)
        conn.commit()
        return jsonify({"message": "Book added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- ORDER ENDPOINTS ---

@app.route('/order', methods=['POST'])
def place_order():
    data = request.json
    user_id = data.get('user_id')
    items = data.get('items') # List of {book_id, type ('buy'/'rent'), price}
    
    if not items:
        return jsonify({"error": "No items in order"}), 400

    total_amount = sum(float(item['price']) for item in items)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create Order
        cursor.execute("INSERT INTO orders (user_id, total_amount, payment_status) VALUES (%s, %s, 'Pending')", 
                       (user_id, total_amount))
        order_id = cursor.lastrowid
        
        # 2. Create Order Items
        for item in items:
            cursor.execute(
                "INSERT INTO order_items (order_id, book_id, type, price) VALUES (%s, %s, %s, %s)",
                (order_id, item['book_id'], item['type'], item['price'])
            )
            
        conn.commit()
        
        # 3. Simulate Email (Assumption from PRD)
        print(f"--- MOCK EMAIL SERVICE ---")
        print(f"Sending bill to User ID {user_id} for Order #{order_id}")
        print(f"Total Due: ${total_amount}")
        print("--------------------------")
        
        return jsonify({"message": "Order placed successfully", "order_id": order_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/orders', methods=['GET'])
def get_all_orders():
    # Manager endpoint
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.id, u.username, o.total_amount, o.payment_status, o.order_date 
        FROM orders o 
        JOIN users u ON o.user_id = u.id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders)

@app.route('/admin/payment', methods=['POST'])
def update_payment():
    data = request.json
    order_id = data.get('order_id')
    status = data.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET payment_status = %s WHERE id = %s", (status, order_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Payment status updated"}), 200

if __name__ == '__main__':
    print("Starting Flask API on port 5000...")
    app.run(debug=True, port=5000)