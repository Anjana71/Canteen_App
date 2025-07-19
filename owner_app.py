import streamlit as st
import sqlite3
from db import get_connection, init_db
from datetime import datetime
import pandas as pd

OWNER_PASSWORD = "admin123"

# Initialize DB
init_db()
conn = get_connection()
c = conn.cursor()

# Create payment log table
c.execute('''CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                amount REAL,
                payment_mode TEXT,
                paid_on TEXT
            )''')

conn.commit()

# Add slot column to orders if not exists
try:
    c.execute("ALTER TABLE orders ADD COLUMN slot TEXT")
except sqlite3.OperationalError:
    pass
conn.commit()

st.set_page_config(page_title="Owner | College Canteen", layout="wide")
st.title("👨‍🍳 College Canteen – Owner Panel")
st.markdown("---")

# Login Sidebar
with st.sidebar:
    st.header("🔐 Owner Login")
    owner = st.text_input("Enter your Name")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if pwd == OWNER_PASSWORD:
            st.session_state["owner"] = owner
            st.success(f"Welcome {owner}!")
            st.rerun()
        else:
            st.error("❌ Incorrect Password")

if "owner" in st.session_state:
    name = st.session_state["owner"]
    st.sidebar.success(f"Logged in as {name}")

    # Tabs for Navigation
    tab = st.sidebar.radio("📁 Navigation", ["📊 Dashboard", "📦 Orders", "📋 Menu", "💰 Dues", "📤 Export", "🧾 Payments"])

    if tab == "📊 Dashboard":
        st.subheader("📊 Overview Dashboard")
        today = datetime.now().strftime("%Y-%m-%d")
        total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        today_orders = c.execute("SELECT COUNT(*) FROM orders WHERE DATE(order_time)=?", (today,)).fetchone()[0]
        total_items = c.execute("SELECT COUNT(*) FROM menu").fetchone()[0]
        total_dues = c.execute("SELECT SUM(total_due) FROM students").fetchone()[0] or 0

        slot_1030 = c.execute("SELECT COUNT(*) FROM orders WHERE slot='10:30 AM Break' AND DATE(order_time)=?", (today,)).fetchone()[0]
        slot_1pm = c.execute("SELECT COUNT(*) FROM orders WHERE slot='1:00 PM Lunch' AND DATE(order_time)=?", (today,)).fetchone()[0]
        delivered = c.execute("SELECT COUNT(*) FROM orders WHERE status='completed' AND DATE(order_time)=?", (today,)).fetchone()[0]
        pending = c.execute("SELECT COUNT(*) FROM orders WHERE status='pending' AND DATE(order_time)=?", (today,)).fetchone()[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Today's Orders", today_orders)
        col2.metric("🧾 Total Orders", total_orders)
        col3.metric("🍱 Items in Menu", total_items)
        col4.metric("💸 Total Dues", f"₹{total_dues:.2f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("🕤 10:30 Slot Orders", slot_1030)
        col6.metric("🕐 1:00 PM Slot Orders", slot_1pm)
        col7.metric("✅ Delivered Today", delivered)
        col8.metric("⏳ Pending Today", pending)

    elif tab == "📦 Orders":
        st.subheader("📦 All Orders")
        orders = c.execute('''
            SELECT o.order_id, o.student_name, m.item_name, o.quantity, o.status, o.order_time, o.delivery_time, o.slot
            FROM orders o JOIN menu m ON o.item_id = m.id
        ''').fetchall()

        for o in orders:
            oid, student, item, qty, status, o_time, d_time, slot = o
            eta = "-"
            try:
                eta = datetime.fromisoformat(d_time).strftime('%H:%M')
            except:
                pass
            slot_info = f" | Slot: {slot}" if slot else ""
            st.write(f"#{oid} - {student} ordered {qty} x {item} | Status: **{status.upper()}** | ETA: {eta}{slot_info}")
            if status == "pending":
                if st.button(f"✅ Mark Completed #{oid}", key=f"done_{oid}"):
                    c.execute("UPDATE orders SET status='completed' WHERE order_id=?", (oid,))
                    conn.commit()
                    st.success(f"Order #{oid} marked as completed.")

    elif tab == "📋 Menu":
        st.subheader("📋 Menu Management")

        with st.expander("➕ Add New Item"):
            name = st.text_input("Item Name")
            price = st.number_input("Price (₹)", min_value=0.0, format="%.2f")
            if st.button("Add Item"):
                c.execute("INSERT INTO menu (item_name, price) VALUES (?, ?)", (name, price))
                conn.commit()
                st.success(f"Item '{name}' added.")

        menu = c.execute("SELECT * FROM menu").fetchall()
        for item in menu:
            item_id, name, price, available = item
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.write(f"**{name}** (₹{price:.2f}) {'🟢' if available else '🔴'}")
            with col2:
                new_price = st.number_input("Update Price", value=price, key=f"price_{item_id}")
                if st.button("Update", key=f"update_{item_id}"):
                    c.execute("UPDATE menu SET price=? WHERE id=?", (new_price, item_id))
                    conn.commit()
                    st.success("Price updated.")
            with col3:
                if available:
                    if st.button("🚫 Mark Unavailable", key=f"disable_{item_id}"):
                        c.execute("UPDATE menu SET available=0 WHERE id=?", (item_id,))
                        conn.commit()
                else:
                    if st.button("✅ Make Available", key=f"enable_{item_id}"):
                        c.execute("UPDATE menu SET available=1 WHERE id=?", (item_id,))
                        conn.commit()
            with col4:
                if st.button("🗑️ Remove", key=f"delete_{item_id}"):
                    c.execute("DELETE FROM menu WHERE id=?", (item_id,))
                    conn.commit()

    elif tab == "💰 Dues":
        st.subheader("💰 Student Dues")
        dues = c.execute("SELECT name, total_due FROM students WHERE total_due > 0").fetchall()
        for d in dues:
            st.write(f"🔸 {d[0]} - ₹{d[1]}")

    elif tab == "📤 Export":
        st.subheader("📤 Export Today's Orders")
        if st.button("Download CSV"):
            today = datetime.now().strftime("%Y-%m-%d")
            export = c.execute('''
                SELECT o.order_id, o.student_name, m.item_name, o.quantity, o.status, o.order_time, o.delivery_time, o.slot
                FROM orders o JOIN menu m ON o.item_id = m.id
                WHERE DATE(order_time)=?
            ''', (today,)).fetchall()
            df = pd.DataFrame(export, columns=["Order ID", "Student", "Item", "Qty", "Status", "Order Time", "Delivery Time", "Slot"])
            st.download_button("Download CSV", data=df.to_csv(index=False).encode(), file_name=f"{today}_orders.csv", mime="text/csv")

    elif tab == "🧾 Payments":
        st.subheader("🧾 Payment Logs")
        payments = c.execute("SELECT * FROM payments ORDER BY paid_on DESC").fetchall()
        df = pd.DataFrame(payments, columns=["ID", "Student", "Amount", "Mode", "Paid On"])
        st.dataframe(df, use_container_width=True)
