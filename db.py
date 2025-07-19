import sqlite3

def get_connection():
    return sqlite3.connect('canteen.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS menu (
                    id INTEGER PRIMARY KEY,
                    item_name TEXT,
                    price REAL,
                    available INTEGER DEFAULT 1
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    name TEXT PRIMARY KEY,
                    total_due REAL DEFAULT 0
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    student_name TEXT,
                    item_id INTEGER,
                    quantity INTEGER,
                    status TEXT,
                    order_time TEXT,
                    delivery_time TEXT,
                    payment_mode TEXT
                )''')
    try:
        c.execute("ALTER TABLE orders ADD COLUMN slot TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    c.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                amount REAL,
                payment_mode TEXT,
                paid_on TEXT
            )''')


    # Optional: add column if app already in use
    try:
        c.execute("ALTER TABLE orders ADD COLUMN payment_mode TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

