-- Stock Sense — MySQL Setup
-- Run this manually OR just run app.py (auto-creates tables)

CREATE DATABASE IF NOT EXISTS stock_sense;
USE stock_sense;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT '',
    quantity INT DEFAULT 0,
    purchase_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) DEFAULT 'Walk-in Customer',
    total_amount DECIMAL(10,2) NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    profit DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

-- Sample products
INSERT INTO products (name,category,quantity,purchase_price,selling_price,expiry_date) VALUES
('Amul Butter 500g','Dairy',50,220,270,DATE_ADD(CURDATE(),INTERVAL 20 DAY)),
('Parle-G Biscuits 800g','Snacks',100,55,75,DATE_ADD(CURDATE(),INTERVAL 180 DAY)),
('Tata Tea Premium 500g','Beverages',30,130,165,DATE_ADD(CURDATE(),INTERVAL 365 DAY)),
('Basmati Rice 5kg','Grains',20,340,420,DATE_ADD(CURDATE(),INTERVAL 730 DAY)),
('Lays Classic 50g','Snacks',80,18,25,DATE_ADD(CURDATE(),INTERVAL 5 DAY)),
('Colgate Toothpaste 200g','Personal Care',40,80,105,DATE_ADD(CURDATE(),INTERVAL 500 DAY)),
('Surf Excel 1kg','Personal Care',25,185,240,DATE_ADD(CURDATE(),INTERVAL 900 DAY)),
('Fresh Milk 1L','Dairy',15,52,65,DATE_ADD(CURDATE(),INTERVAL 3 DAY)),
('Maggi Noodles 70g','Snacks',120,12,16,DATE_ADD(CURDATE(),INTERVAL 270 DAY)),
('Sunflower Oil 1L','Groceries',35,110,135,DATE_ADD(CURDATE(),INTERVAL 400 DAY));
