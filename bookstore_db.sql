CREATE DATABASE IF NOT EXISTS bookstore_db;
USE bookstore_db;

-- Users Table (Customers and Managers)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role ENUM('customer', 'manager') DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books Table
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    price_buy DECIMAL(10, 2) NOT NULL,
    price_rent DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 1,
    is_available BOOLEAN DEFAULT TRUE
);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10, 2),
    payment_status ENUM('Pending', 'Paid') DEFAULT 'Pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Order Items (Linking orders to books)
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    book_id INT,
    type ENUM('buy', 'rent') NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Sample book insert
INSERT INTO books (title, author, price_buy, price_rent, stock) VALUES 
('The Great Gatsby', 'F. Scott Fitzgerald', 15.00, 5.00, 10),
('1984', 'George Orwell', 12.50, 4.00, 15);