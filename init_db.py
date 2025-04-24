import sqlite3
import hashlib

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Connect to SQLite database (this creates the file)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table with phone number column
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        phone TEXT
    )
''')

# Optional: Insert a test user with phone number
username = "testuser"
password = "testpass"
phone = "+911234567890"  # Example phone number
hashed = hash_password(password)

try:
    c.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)", (username, hashed, phone))
    print(f"User '{username}' created.")
except sqlite3.IntegrityError:
    print(f"User '{username}' already exists.")

# Commit and close
conn.commit()
conn.close()
