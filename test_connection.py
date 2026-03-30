"""
Quick test to verify database connection
"""
import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get connection string
connection_string = os.getenv("DATABASE_CONNECTION_STRING")
print(f"Connection String: {connection_string}")
print()

try:
    # Attempt connection
    print("Attempting to connect to database...")
    conn = pyodbc.connect(connection_string, timeout=10)
    print("✓ Connection successful!")
    print()
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as customer_count FROM customers")
    result = cursor.fetchone()
    print(f"✓ Query successful! Found {result[0]} customers in database")
    
    # Get table counts
    cursor.execute("""
        SELECT 'categories' AS TableName, COUNT(*) AS RecordCount FROM categories
        UNION ALL
        SELECT 'customers', COUNT(*) FROM customers
        UNION ALL
        SELECT 'products', COUNT(*) FROM products
        UNION ALL
        SELECT 'orders', COUNT(*) FROM orders
        UNION ALL
        SELECT 'order_items', COUNT(*) FROM order_items
        UNION ALL
        SELECT 'reviews', COUNT(*) FROM reviews
        UNION ALL
        SELECT 'inventory', COUNT(*) FROM inventory
        UNION ALL
        SELECT 'shipments', COUNT(*) FROM shipments
    """)
    
    print()
    print("Database Statistics:")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]:20} {row[1]:>10} rows")
    
    cursor.close()
    conn.close()
    print()
    print("✓ All tests passed! Database is ready.")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
