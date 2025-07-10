import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

# Create a database connection
def create_connection():
    conn = sqlite3.connect('database.db', timeout=10)  # Timeout of 10 seconds
    conn.row_factory = sqlite3.Row  # Rows behave like dictionaries
    conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode
    return conn

# Function to initialize and create tables
def init_db():
    conn = create_connection()
    cursor = conn.cursor()

    # Drop the old sensors table if it exists
    #cursor.execute('''DROP TABLE IF EXISTS sensors''')

    # Create Users table (with added columns: profile_pic, address, user_type)
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        profile_pic TEXT DEFAULT 'default.png',
        address TEXT DEFAULT '',
        user_type TEXT DEFAULT 'consumer'
    )
    ''')

    # Create Sensors table (fixed schema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensors (
        sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sensor_type TEXT,
        location TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # Create Billing table (with payment_status column)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS billing (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount_due REAL,
        due_date TEXT,
        payment_status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE if not exists area_admin (
    user_id INTEGER PRIMARY KEY,
    service_needed TEXT,
    email TEXT NULL,
    service_status TEXT
);

    ''')

    # Commit and close connection
    conn.commit()
    conn.close()


# Function to get user details (including profile_pic, address, user_type)
def get_user_details(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to update user details (name, address, profile_pic, user_type)
def update_user_details(user_id, name, address, profile_pic, user_type='consumer'):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET name=?, address=?, profile_pic=?, user_type=? WHERE id=?
    ''', (name, address, profile_pic, user_type, user_id))
    conn.commit()
    conn.close()

# Function to update user password
def update_user_password(user_id, password):
    password_hash = generate_password_hash(password)
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET password_hash=? WHERE id=?
    ''', (password_hash, user_id))
    conn.commit()
    conn.close()

# Function to get the total number of sensors for a user
def get_total_sensors(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sensors WHERE user_id=?", (user_id,))
    total_sensors = cursor.fetchone()[0]  # Extract the count value
    conn.close()
    return total_sensors

if __name__ == '__main__':
    init_db()  # This will initialize the database and create the tables
