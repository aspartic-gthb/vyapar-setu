import sqlite3
import random
from datetime import datetime

DB_NAME = "bharat_biz.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Drop table to ensure schema update
    cursor.execute("DROP TABLE IF EXISTS invoices")

    cursor.execute("""
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            amount INTEGER,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_invoice(customer_name, amount, pdf_path):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO invoices (customer_name, amount, pdf_path) VALUES (?, ?, ?)",
        (customer_name, amount, pdf_path)
    )

    conn.commit()
    conn.close()

def get_pending_invoices_by_customer(customer_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT amount FROM invoices WHERE customer_name = ?",
        (customer_name,)
    )

    rows = cursor.fetchall()
    conn.close()

    total = sum(row[0] for row in rows)
    return total

def get_all_invoices():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT customer_name, amount, pdf_path, created_at FROM invoices ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows

def create_inventory_table():
    conn = get_connection()
    cursor = conn.cursor()

    # Drop old table for schema update in this demo
    cursor.execute("DROP TABLE IF EXISTS inventory")

    cursor.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            price REAL,
            quantity INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed Data
    products = [
        ("Basmati Rice (Organic)", "Grains", 120.0, 50),
        ("Aashirvaad Atta 5kg", "Flour", 240.0, 30),
        ("Fortune Mustard Oil 1L", "Oil", 165.0, 40),
        ("Tata Salt 1kg", "Spices", 25.0, 100),
        ("Red Label Tea 500g", "Beverages", 280.0, 25),
        ("Maggi Masala Pack", "Snacks", 14.0, 200),
        ("Dettol Handwash", "Hygiene", 99.0, 15),
        ("Dove Soda Soap", "Hygiene", 65.0, 60),
        ("Coca Cola 2.25L", "Beverages", 95.0, 10),
        ("Britannia Marie Gold", "Snacks", 30.0, 80)
    ]

    cursor.executemany(
        "INSERT INTO inventory (name, category, price, quantity) VALUES (?, ?, ?, ?)",
        products
    )

    conn.commit()
    conn.close()

def deduct_inventory(amount):
    # Simplistic logic: Deduct from a random product to simulate activity
    # In a real app, we'd parse the product name.
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get a random product with stock > 0
    cursor.execute("SELECT id FROM inventory WHERE quantity > 0 ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        prod_id = row[0]
        cursor.execute(
            "UPDATE inventory SET quantity = quantity - 1, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
            (prod_id,)
        )

    conn.commit()
    conn.close()

def get_inventory():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, category, price, quantity, last_updated FROM inventory")
    rows = cursor.fetchall()

    conn.close()
    return rows
   


