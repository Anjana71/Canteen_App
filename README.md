# Canteen_App
# 🏫 College Canteen Management System

This is a web-based application built using **Streamlit** that allows students to pre-order food, track dues, and make payments, while also offering an owner dashboard for managing orders, menu items, and viewing payments.

---

## 🔧 Features

### 👨‍🎓 Student Portal
- 🔐 **Secure login & registration** with password protection
- 📋 **Menu browsing** and quantity-based food ordering
- ⏰ **Time-based order restriction** to reduce food waste:
  - 10:30 AM Break – Orders must be placed before 9:30 AM
  - 1:00 PM Lunch – Orders must be placed before 12:00 PM
- 💳 Option to **pay immediately or later**
- 💰 View and pay **pending dues**
- 🧾 Check **order history** and delivery status
- 🚪 **Logout** securely

---

### 👨‍🍳 Owner Dashboard
- 📊 View **daily and total orders**, menu items, and dues
- 📦 **Track orders** and mark as completed
- 🛠 **Add, update, or remove** menu items
- 📤 **Export daily orders** to CSV
- 💳 View **payment logs**
- 📈 Summary of:
  - Total orders
  - Delivered vs Pending
  - Slot-wise order counts (10:30 vs 1:00)

---

## 🛠 Technologies Used
- 🐍 **Python 3.10+**
- 📦 **Streamlit** – UI framework
- 🗄️ **SQLite** or **PostgreSQL** – Database
- 🗃️ **Pandas** – Data export
- 🖥️ Localhost Deployment (optionally deploy on Streamlit Cloud or Render)

---

## 🚀 How to Run

### 🖥️ Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/Anjana71/Canteen_App.git
   cd Canteen_App
