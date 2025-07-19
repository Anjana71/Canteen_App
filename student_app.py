import streamlit as st
import sqlite3
from db import get_connection, init_db
from datetime import datetime, timedelta

# Initialize DB
init_db()
conn = get_connection()
c = conn.cursor()

# Extend students table to include password if it doesn't exist
try:
    c.execute("ALTER TABLE students ADD COLUMN password TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Column already exists

# Create students table if not exists (with password)
c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        name TEXT PRIMARY KEY,
        password TEXT,
        total_due REAL DEFAULT 0
    )
""")

# Create payments table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                amount REAL,
                payment_mode TEXT,
                paid_on TEXT
            )''')
conn.commit()

MAX_ORDERS_PER_DAY = 200
st.set_page_config(page_title="Student | College Canteen", layout="centered")
st.title("👩‍🎓 College Canteen – Student Portal")

# Login with password
if "student" not in st.session_state:
    tab_login = st.radio("Choose", ["🔐 Login", "📝 Register"])

    if tab_login == "📝 Register":
        new_name = st.text_input("Choose a Name / ID")
        new_pwd = st.text_input("Set a Password", type="password")
        if st.button("Register"):
            exists = c.execute("SELECT * FROM students WHERE name=?", (new_name,)).fetchone()
            if exists:
                st.warning("User already exists. Try logging in.")
            else:
                c.execute("INSERT INTO students (name, password, total_due) VALUES (?, ?, 0)", (new_name, new_pwd))
                conn.commit()
                st.success("Registered! Please login now.")

    elif tab_login == "🔐 Login":
        student_name = st.text_input("Enter your Name / ID")
        password = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            record = c.execute("SELECT * FROM students WHERE name=? AND password=?", (student_name, password)).fetchone()
            if record:
                st.session_state["student"] = student_name
                st.success(f"Logged in as {student_name}")
                st.rerun()

            else:
                st.error("Incorrect credentials.")

if "student" in st.session_state:
    name = st.session_state["student"]

    # Logout button on top right
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout"):
            del st.session_state["student"]
            st.rerun()


    st.subheader(f"Welcome, {name}!")

    tab = st.sidebar.radio("📁 Navigation", ["📋 Menu", "🧾 Orders", "💰 Dues"])

    today = datetime.now().strftime("%Y-%m-%d")
    orders_today = c.execute("SELECT COUNT(*) FROM orders WHERE DATE(order_time)=?", (today,)).fetchone()[0]
    left = MAX_ORDERS_PER_DAY - orders_today

    if tab == "📋 Menu":
        st.subheader("📋 Available Menu")
        st.info(f"📦 Orders Placed Today: {orders_today} / {MAX_ORDERS_PER_DAY} ({left} left)")

        if left <= 0:
            st.warning("🚫 Order limit reached for today.")
        else:
            menu = c.execute("SELECT * FROM menu WHERE available=1").fetchall()
            slot = st.selectbox("Choose Pre-order Slot", ["10:30 AM Break", "1:00 PM Lunch"])

            # Time constraint enforcement
            now = datetime.now()
            current_time = now.time()
            cutoff = {
                "10:30 AM Break": datetime.strptime("09:30", "%H:%M").time(),
                "1:00 PM Lunch": datetime.strptime("23:00", "%H:%M").time()
            }

            if current_time > cutoff[slot]:
                st.error(f"⏰ Ordering for '{slot}' is closed. Deadline was {cutoff[slot].strftime('%H:%M')}")
            else:
                for item in menu:
                    qty = st.number_input(f"{item[1]} (₹{item[2]}) - Qty", min_value=0, step=1, key=f"qty_{item[0]}")
                    if qty > 0:
                        if st.button(f"🛒 Order {item[1]}", key=f"order_{item[0]}"):
                            delivery = now + timedelta(minutes=10)
                            total_price = qty * item[2]

                            c.execute("""
                                INSERT INTO orders (student_name, item_id, quantity, status, order_time, delivery_time, slot)
                                VALUES (?, ?, ?, 'pending', ?, ?, ?)
                            """, (name, item[0], qty, now.isoformat(), delivery.isoformat(), slot))
                            c.execute("UPDATE students SET total_due = total_due + ? WHERE name = ?", (total_price, name))
                            conn.commit()

                            st.session_state["last_order"] = {
                                "item": item[1],
                                "qty": qty,
                                "price": total_price,
                                "slot": slot
                            }

                            st.success(f"✅ Ordered {qty} x {item[1]} for {slot} – ETA: {delivery.strftime('%H:%M')}")

    # Show payment prompt after ordering
    if "last_order" in st.session_state:
        order_info = st.session_state["last_order"]
        with st.expander(f"💳 Pay Now for {order_info['qty']} x {order_info['item']} (₹{order_info['price']})"):
            pay_now = st.radio("Would you like to pay now?", ["No", "Yes"], key="pay_now_choice")
            if pay_now == "Yes":
                pay_mode = st.selectbox("Select Payment Method", ["Cash", "Google Pay", "PhonePe", "Paytm"], key="pay_mode_selection")
                if st.button("✅ Confirm Payment", key="pay_confirm_button"):
                    c.execute("UPDATE students SET total_due = total_due - ? WHERE name=?", (order_info["price"], name))
                    c.execute("INSERT INTO payments (student_name, amount, payment_mode, paid_on) VALUES (?, ?, ?, ?)",
                              (name, order_info["price"], pay_mode, datetime.now().isoformat()))
                    conn.commit()
                    st.success(f"🎉 Payment of ₹{order_info['price']} successful via {pay_mode}")
                    del st.session_state["last_order"]
            else:
                st.info("💡 You can pay later from the Dues section.")

    elif tab == "🧾 Orders":
        st.subheader("🧾 My Orders")
        orders = c.execute('''
            SELECT m.item_name, o.quantity, o.status, o.delivery_time, o.slot
            FROM orders o JOIN menu m ON o.item_id = m.id
            WHERE o.student_name=?
        ''', (name,)).fetchall()
        for item_name, qty, status, d_time, slot in orders:
            eta = "-"
            try:
                eta = datetime.fromisoformat(str(d_time)).strftime('%H:%M')
            except:
                pass
            st.write(f"🛕 {qty} x {item_name} | Status: **{status.upper()}** | ETA: {eta} | Slot: {slot}")

    elif tab == "💰 Dues":
        st.subheader("💸 Pay Dues")
        due = c.execute("SELECT total_due FROM students WHERE name=?", (name,)).fetchone()
        total_due = due[0] if due else 0
        st.write(f"💰 Total Due: ₹{total_due:.2f}")

        if total_due > 0:
            pay_mode = st.selectbox("Select Payment Method", ["Cash", "Google Pay", "PhonePe", "Paytm"])
            amount_to_pay = st.number_input("Enter Amount to Pay", min_value=1.0, max_value=total_due, step=1.0)
            if st.button("✅ Pay Dues"):
                c.execute("UPDATE students SET total_due = total_due - ? WHERE name=?", (amount_to_pay, name))
                c.execute("INSERT INTO payments (student_name, amount, payment_mode, paid_on) VALUES (?, ?, ?, ?)",
                          (name, amount_to_pay, pay_mode, datetime.now().isoformat()))
                conn.commit()
                st.success(f"💸 Payment of ₹{amount_to_pay:.2f} successful via {pay_mode}")
