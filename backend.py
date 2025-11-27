import mysql.connector
from flask import Flask, request, jsonify
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string


app = Flask(__name__)

# --- CONFIGURATION ---
db_config = {
    'user': 'root',       
    'password': '121104', 
    'host': 'localhost',
    'database': 'bookstore_db'
}

# SECRET CODE required to create a manager account
MANAGER_CREATION_SECRET = "ManagerCode2025" 

verification_storage = {}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to DB: {err}")
        return None

# --- EMAIL HELPER (Kept from your original code) ---
def send_email_receipt(user_email, order_id, total_amount, items):
    SENDER_EMAIL = "ishitajaggi22@gmail.com"
    APP_PASSWORD = "esnp hwtv vfli ozyk"
    
    subject = f"Receipt for Order #{order_id}"
    body = f"Thank you for your order!\n\nOrder ID: {order_id}\nTotal Amount: ${total_amount:.2f}\n\nItems:\n"
    for item in items:
        body += f"- {item['title']} ({item['type'].upper()}): ${item['price']}\n"
    body += "\nPlease pay if you haven't already."

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_verification_email(to_email, code):
    SENDER = "ishitajaggi22@gmail.com"
    PASSWORD = "esnp hwtv vfli ozyk"
    msg = MIMEMultipart()
    msg['Subject'] = "Verification Code"
    msg['From'] = SENDER
    msg['To'] = to_email
    msg.attach(MIMEText(f"Your code is: {code}", 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.send_message(msg)
        server.quit()
    except:
        pass

# --- AUTH ENDPOINTS ---

@app.route('/send-code', methods=['POST'])
def send_code():
    data = request.json
    email = data.get('email')
    if not email: return jsonify({"error": "Email required"}), 400
    code = ''.join(random.choices(string.digits, k=6))
    verification_storage[email] = code
    # In production, use a thread for this
    send_verification_email(email, code)
    return jsonify({"message": "Code sent"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'customer') # Default to customer
    code = data.get('code')
    manager_secret = data.get('manager_secret') # New field

    # 1. Verify Email Code
    if not code or verification_storage.get(email) != code:
        return jsonify({"error": "Invalid verification code"}), 400

    # 2. Security Check for Manager
    if role == 'manager':
        if manager_secret != MANAGER_CREATION_SECRET:
             return jsonify({"error": "Invalid Manager Access Code"}), 403

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)",
                       (username, hashed, email, role))
        conn.commit()
        del verification_storage[email]
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (data.get('username'),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(data.get('password').encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({
            "message": "Login successful",
            "user_id": user['id'],
            "role": user['role']
        }), 200
    return jsonify({"error": "Invalid credentials"}), 401

# --- BOOK & INVENTORY ENDPOINTS ---

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
    # Manager: Add new book
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO books (title, author, price_buy, price_rent, stock) VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(sql, (data['title'], data['author'], data['price_buy'], data['price_rent'], data['stock']))
        conn.commit()
        return jsonify({"message": "Book added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/books/update', methods=['POST'])
def update_book():
    # Manager: Update existing book (ALL fields)
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Updated SQL to include title and author
    sql = "UPDATE books SET title=%s, author=%s, price_buy=%s, price_rent=%s, stock=%s WHERE id=%s"
    
    try:
        cursor.execute(sql, (
            data['title'], 
            data['author'], 
            data['price_buy'], 
            data['price_rent'], 
            data['stock'], 
            data['id']
        ))
        conn.commit()
        return jsonify({"message": "Book updated"}), 200
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
    items = data.get('items')
    
    if not items: return jsonify({"error": "No items"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check Stock
        for item in items:
            cursor.execute("SELECT stock, title FROM books WHERE id = %s", (item['book_id'],))
            result = cursor.fetchone()
            if not result or result[0] < 1:
                raise Exception(f"Book '{result[1] if result else 'Unknown'}' is out of stock.")

        # 2. Create Order
        total_amount = sum(float(item['price']) for item in items)
        cursor.execute("INSERT INTO orders (user_id, total_amount, payment_status) VALUES (%s, %s, 'Pending')", 
                       (user_id, total_amount))
        order_id = cursor.lastrowid
        
        # 3. Items & Stock Decrement
        for item in items:
            cursor.execute(
                "INSERT INTO order_items (order_id, book_id, type, price, is_returned) VALUES (%s, %s, %s, %s, FALSE)",
                (order_id, item['book_id'], item['type'], item['price'])
            )
            cursor.execute("UPDATE books SET stock = stock - 1 WHERE id = %s", (item['book_id'],))
        
        # 4. Email
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        res = cursor.fetchone()
        if res: send_email_receipt(res[0], order_id, total_amount, items)
            
        conn.commit()
        return jsonify({"message": "Order placed", "order_id": order_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- MANAGER RETURN/RENTAL ENDPOINTS ---

@app.route('/admin/rentals', methods=['GET'])
def get_rentals():
    # Get all items that are RENTED and NOT RETURNED
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT oi.id, b.title, u.username, oi.price, o.order_date
        FROM order_items oi
        JOIN books b ON oi.book_id = b.id
        JOIN orders o ON oi.order_id = o.id
        JOIN users u ON o.user_id = u.id
        WHERE oi.type = 'rent' AND oi.is_returned = FALSE
    """)
    rentals = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rentals)

@app.route('/admin/return', methods=['POST'])
def return_book():
    data = request.json
    order_item_id = data.get('order_item_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get book_id to restore stock
        cursor.execute("SELECT book_id FROM order_items WHERE id = %s", (order_item_id,))
        res = cursor.fetchone()
        if not res: raise Exception("Item not found")
        book_id = res[0]
        
        # Mark as returned
        cursor.execute("UPDATE order_items SET is_returned = TRUE WHERE id = %s", (order_item_id,))
        
        # Increase Stock
        cursor.execute("UPDATE books SET stock = stock + 1 WHERE id = %s", (book_id,))
        
        conn.commit()
        return jsonify({"message": "Book returned and stock updated"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/orders', methods=['GET'])
def get_all_orders():
    # Includes USER EMAIL now
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.id, u.username, u.email, o.total_amount, o.payment_status, o.order_date 
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
    status = data.get('status') # Should be 'Paid' or 'Pending'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET payment_status = %s WHERE id = %s", (status, order_id))
        conn.commit()
        return jsonify({"message": "Payment status updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)