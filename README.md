A full-stack desktop application designed to manage a bookstore's operations. This system features a client-server architecture using Python (Tkinter) for the desktop interface, Flask for the REST API backend, and MySQL for persistent data storage.

It supports distinct workflows for Customers (browsing, buying, renting) and Managers (inventory control, order tracking, returns).

Features
Customer Features
User Account Management: Register with email verification (OTP) and secure login.

Book Browsing: Real-time search by title or author.

Shopping Cart: Add books to the cart for either Purchase or Rental.

Checkout System:

Stock is automatically checked and reserved.

Order receipts are sent via email automatically.

Manager Features
Inventory Management: Add new books or update existing book details (price, stock, title).

Order Dashboard: View all customer orders and manually mark "Pending" payments as "Paid."

Rental Management: Track unreturned rentals and process returns (restoring stock automatically).

Technology Stack
Frontend: Python (Tkinter, requests library)

Backend: Python (Flask)

Database: MySQL

Authentication: Bcrypt (Password Hashing), Email OTP

Networking: REST API (JSON)

Prerequisites
Before running the application, ensure you have the following installed:

Python 3.x

MySQL Server

Pip (Python Package Manager)

Installation & Setup
1. Database Configuration
Open your MySQL command line or a tool like MySQL Workbench.

Run the provided SQL script to create the database and tables:

SQL

source bookstore_db.sql
Important: Open backend.py and update the db_config dictionary with your local MySQL credentials:

Python

db_config = {
    'user': 'root',       
    'password': 'YOUR_MYSQL_PASSWORD', 
    'host': 'localhost',
    'database': 'bookstore_db'
}
2. Python Dependencies
Install the required Python libraries:

Bash

pip install flask mysql-connector-python bcrypt requests
(Note: Tkinter is usually included with Python. If you are on Linux and get an error, run sudo apt-get install python3-tk).

3. Email Configuration (Optional but Recommended)
To enable registration codes and receipt emails, you must provide valid Gmail credentials in backend.py.

Locate the functions send_email_receipt and send_verification_email in backend.py.

Replace the SENDER_EMAIL and APP_PASSWORD with your own credentials.

Note: For Gmail, you must generate an "App Password" in your Google Account security settings. Do not use your raw login password.

How to Run
You need to run the backend server first, then the desktop client.

Step 1: Start the Backend API Open a terminal and run:

Bash

python backend.py
You should see the Flask server running on http://127.0.0.1:5000.

Step 2: Start the Desktop Client Open a new terminal window and run:

Bash

python desktop.py

Usage Guide
Registering a Manager
To access the Manager Dashboard, you must register a new account with a specific secret code.

On the Login screen, click Create Account.

Click the Create Manager Account button at the bottom.

Enter the Manager Secret Code defined in backend.py:

Code: ManagerCode2025

Complete the registration form.

Buying vs. Renting
Buy: The user purchases the book permanently.

Rent: The user rents the book at a lower price.

Managers can view active rentals in the "Rentals & Returns" tab and mark them as returned to restore stock.

Project Structure
desktop.py: The GUI client. Handles user input, displays windows (Login, Dashboard, Cart), and communicates with the backend via HTTP requests.

backend.py: The logic layer. Connects to the database, handles password hashing, sends emails, and processes API requests.

bookstore_db.sql: The database schema. Defines tables for users, books, orders, and order_items.

Security Note
This project contains hardcoded credentials in backend.py for demonstration purposes. In a production environment, use Environment Variables (.env) to store database passwords and email credentials securetly.