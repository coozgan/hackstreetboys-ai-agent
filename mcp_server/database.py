"""
Database layer for HackstreetBoys-AI MCP Server.
Provides SQLite-backed CRUD operations for all domains.
"""

import sqlite3
import uuid
import os
import json
from datetime import datetime, timedelta

# Database path: stored in a 'data' directory at the project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "hackstreetboys.db")
DB_PATH = os.environ.get("HACKSTREETBOYS_DB_PATH", DEFAULT_DB_PATH)

def _generate_id() -> str:
    return str(uuid.uuid4())[:8]

def _now() -> str:
    return datetime.now().isoformat()

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        -- SHOPPING SCHEMA
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS cart_items (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            method TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            transaction_ref TEXT,
            created_at TEXT NOT NULL
        );

        -- HEALTH SCHEMA
        CREATE TABLE IF NOT EXISTS health_logs (
            id TEXT PRIMARY KEY,
            log_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            notes TEXT DEFAULT '',
            logged_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS health_goals (
            id TEXT PRIMARY KEY,
            goal_type TEXT NOT NULL,
            target_value REAL NOT NULL,
            current_value REAL DEFAULT 0,
            unit TEXT,
            status TEXT DEFAULT 'active'
        );

        -- FINANCE SCHEMA
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT DEFAULT '',
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            current_spent REAL DEFAULT 0,
            month TEXT NOT NULL
        );

        -- CAREER SCHEMA
        CREATE TABLE IF NOT EXISTS career_tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'in_progress', 'done', 'cancelled')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
            category TEXT DEFAULT 'work',
            due_date TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- SOCIAL SCHEMA
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            relationship TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            last_contact TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS social_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            contact_ids TEXT DEFAULT '[]',
            event_type TEXT DEFAULT 'meetup',
            date TEXT NOT NULL,
            location TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()

def _seed_products():
    """Seed initial products if empty."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            (_generate_id(), "Espresso", "Coffee", 2.50, 100, "Rich and bold single shot espresso"),
            (_generate_id(), "Latte", "Coffee", 4.00, 50, "Espresso with steamed milk"),
            (_generate_id(), "Cappuccino", "Coffee", 4.50, 40, "Espresso with thick milk foam"),
            (_generate_id(), "Mocha", "Coffee", 5.00, 30, "Chocolate flavored latte"),
            (_generate_id(), "Croissant", "Pastry", 3.00, 20, "Buttery, flaky french pastry"),
            (_generate_id(), "Blueberry Muffin", "Pastry", 3.50, 15, "Fresh baked with blueberries"),
            (_generate_id(), "Avocado Toast", "Food", 8.50, 10, "Smashed avocado on sourdough"),
            (_generate_id(), "Eggs Benedict", "Food", 12.00, 5, "Poached eggs on english muffin"),
            (_generate_id(), "Iced Tea", "Drink", 3.00, 100, "Refreshing black tea over ice"),
            (_generate_id(), "Matcha Latte", "Drink", 5.50, 25, "Green tea powder with milk"),
             (_generate_id(), "Club Sandwich", "Food", 10.50, 8, "Classic triple decker sandwich"),
            (_generate_id(), "French Fries", "Food", 4.50, 50, "Crispy potato fries"),
            (_generate_id(), "Lemonade", "Drink", 3.50, 40, "Freshly squeezed lemons"),
            (_generate_id(), "Brownie", "Pastry", 2.75, 12, "Decadent chocolate fudge brownie"),
            (_generate_id(), "Cheeseburger", "Food", 11.00, 10, "Beef patty with cheddar cheese"),
            (_generate_id(), "Vintage Denim Jacket", "Clothing", 75.00, 15, "Classic distressed denim jacket"),
            (_generate_id(), "Cotton Basic Tee", "Clothing", 15.00, 100, "100% organic cotton white t-shirt"),
            (_generate_id(), "High-Waisted Jeans", "Clothing", 60.00, 30, "Slim fit high-waisted blue jeans"),
            (_generate_id(), "Sneakers running shoes", "Clothing", 120.00, 20, "Breathable mesh running shoes"),
            (_generate_id(), "Summer Floral Dress", "Clothing", 45.00, 12, "Lightweight floral patterned dress"),
            (_generate_id(), "Wool Blend Beanie", "Clothing", 18.00, 50, "Cozy winter beanie, charcoal grey")
        ]
        conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", products)
        conn.commit()

        # Seed some contacts
        contacts = [
            (_generate_id(), "Alice Smith", "Colleague", "alice@example.com", "555-0101", "", "Works in marketing"),
            (_generate_id(), "Bob Jones", "Friend", "bob@example.com", "555-0102", _now(), "College buddy"),
            (_generate_id(), "Carol Williams", "Mentor", "carol@example.com", "555-0103", "", "Senior Engineer")
        ]
        conn.executemany("INSERT INTO contacts (id, name, relationship, email, phone, last_contact, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", contacts)
        conn.commit()

        # Seed some budget
        budgets = [
             (_generate_id(), "Food", 500.0, 120.0, datetime.now().strftime("%Y-%m")),
             (_generate_id(), "Coffee", 100.0, 15.0, datetime.now().strftime("%Y-%m")),
        ]
        conn.executemany("INSERT INTO budgets (id, category, monthly_limit, current_spent, month) VALUES (?, ?, ?, ?, ?)", budgets)
        conn.commit()

    conn.close()

init_db()
_seed_products()

# --- SHOPPING CRUD ---

def list_products(category: str = ""):
    conn = get_connection()
    if category:
        rows = conn.execute("SELECT * FROM products WHERE category LIKE ?", (f"%{category}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product(product_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def search_products(query: str):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", (f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT category FROM products").fetchall()
    conn.close()
    return [r["category"] for r in rows]

def add_to_cart(session_id: str, product_id: str, quantity: int = 1):
    conn = get_connection()
    # check if already in cart
    existing = conn.execute("SELECT * FROM cart_items WHERE session_id = ? AND product_id = ?", (session_id, product_id)).fetchone()
    if existing:
        conn.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (quantity, existing["id"]))
    else:
        conn.execute("INSERT INTO cart_items (id, session_id, product_id, quantity) VALUES (?, ?, ?, ?)",
                     (_generate_id(), session_id, product_id, quantity))
    conn.commit()
    conn.close()
    return True

def remove_from_cart(session_id: str, product_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM cart_items WHERE session_id = ? AND product_id = ?", (session_id, product_id))
    conn.commit()
    conn.close()
    return True

def update_cart_quantity(session_id: str, product_id: str, quantity: int):
    conn = get_connection()
    if quantity <= 0:
        conn.execute("DELETE FROM cart_items WHERE session_id = ? AND product_id = ?", (session_id, product_id))
    else:
        conn.execute("UPDATE cart_items SET quantity = ? WHERE session_id = ? AND product_id = ?", (quantity, session_id, product_id))
    conn.commit()
    conn.close()
    return True

def get_cart(session_id: str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.id as cart_item_id, c.product_id, c.quantity, p.name, p.price, p.stock
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.session_id = ?
    """, (session_id,)).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    total = sum(item["price"] * item["quantity"] for item in items)
    return {"items": items, "total": total}

def clear_cart(session_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM cart_items WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return True

def check_stock(product_id: str, quantity: int) -> bool:
    product = get_product(product_id)
    if product and product["stock"] >= quantity:
        return True
    return False

def reserve_stock(product_id: str, quantity: int) -> bool:
    if check_stock(product_id, quantity):
        conn = get_connection()
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        conn.commit()
        conn.close()
        return True
    return False

def release_stock(product_id: str, quantity: int):
    conn = get_connection()
    conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()

def create_order(session_id: str, items: list, total: float, payment_method: str = "pending"):
    order_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO orders (id, session_id, items_json, total, status, payment_method, created_at) VALUES (?, ?, ?, ?, 'pending', ?, ?)",
                 (order_id, session_id, json.dumps(items), total, payment_method, _now()))
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if row:
        order = dict(row)
        order["items"] = json.loads(order["items_json"])
        del order["items_json"]
        return order
    return None

def update_order_status(order_id: str, status: str):
    conn = get_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    return True

def create_payment(order_id: str, method: str, amount: float, status: str = "completed"):
    payment_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO payments (id, order_id, method, amount, status, transaction_ref, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (payment_id, order_id, method, amount, status, f"txn_{_generate_id()}", _now()))
    conn.commit()
    conn.close()
    return payment_id

# --- HEALTH CRUD ---

def log_health(log_type: str, value: float, unit: str = "", notes: str = ""):
    log_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO health_logs (id, log_type, value, unit, notes, logged_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (log_id, log_type, value, unit, notes, _now()))
    conn.commit()
    conn.close()
    return log_id

def get_health_logs(log_type: str = "", limit: int = 50):
    conn = get_connection()
    if log_type:
        rows = conn.execute("SELECT * FROM health_logs WHERE log_type = ? ORDER BY logged_at DESC LIMIT ?", (log_type, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM health_logs ORDER BY logged_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_health_goal(goal_type: str, target_value: float, unit: str = ""):
    goal_id = _generate_id()
    conn = get_connection()
    # Check if active goal exists, update it or create new
    existing = conn.execute("SELECT * FROM health_goals WHERE goal_type = ? AND status = 'active'", (goal_type,)).fetchone()
    if existing:
        conn.execute("UPDATE health_goals SET target_value = ?, unit = ? WHERE id = ?", (target_value, unit, existing["id"]))
        goal_id = existing["id"]
    else:
        conn.execute("INSERT INTO health_goals (id, goal_type, target_value, unit) VALUES (?, ?, ?, ?)",
                     (goal_id, goal_type, target_value, unit))
    conn.commit()
    conn.close()
    return goal_id

def get_health_goals():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM health_goals WHERE status = 'active'").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_health_goal(goal_id: str, current_value: float):
    conn = get_connection()
    conn.execute("UPDATE health_goals SET current_value = ? WHERE id = ?", (current_value, goal_id))
    conn.commit()
    conn.close()
    return True

# --- FINANCE CRUD ---

def log_transaction(type_: str, category: str, amount: float, description: str = ""):
    txn_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO transactions (id, type, category, amount, description, date) VALUES (?, ?, ?, ?, ?, ?)",
                 (txn_id, type_, category, amount, description, _now()[:10]))
    
    # Update budget if expense
    if type_ == "expense":
        month = _now()[:7]
        conn.execute("UPDATE budgets SET current_spent = current_spent + ? WHERE category = ? AND month = ?", (amount, category, month))
        
    conn.commit()
    conn.close()
    return txn_id

def list_transactions(limit: int = 50):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_budget(category: str, limit: float, month: str = ""):
    if not month:
        month = _now()[:7]
    budget_id = _generate_id()
    conn = get_connection()
    existing = conn.execute("SELECT * FROM budgets WHERE category = ? AND month = ?", (category, month)).fetchone()
    if existing:
         conn.execute("UPDATE budgets SET monthly_limit = ? WHERE id = ?", (limit, existing["id"]))
    else:
         conn.execute("INSERT INTO budgets (id, category, monthly_limit, month) VALUES (?, ?, ?, ?)",
                      (budget_id, category, limit, month))
    conn.commit()
    conn.close()
    return True

def get_budgets(month: str = ""):
    if not month:
        month = _now()[:7]
    conn = get_connection()
    rows = conn.execute("SELECT * FROM budgets WHERE month = ?", (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- CAREER CRUD ---
def create_career_task(title: str, description: str = "", priority: str = "medium", category: str = "work", due_date: str = ""):
    task_id = _generate_id()
    now = _now()
    conn = get_connection()
    conn.execute(
        "INSERT INTO career_tasks (id, title, description, status, priority, category, due_date, created_at, updated_at) "
        "VALUES (?, ?, ?, 'todo', ?, ?, ?, ?, ?)",
        (task_id, title, description, priority, category, due_date, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": task_id, "title": title, "status": "todo", "priority": priority}

def list_career_tasks(status: str = "", priority: str = ""):
    conn = get_connection()
    query = "SELECT * FROM career_tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_career_task(task_id: str, **kwargs):
    allowed = {"title", "description", "status", "priority", "category", "due_date"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return False
    updates["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]
    conn = get_connection()
    conn.execute(f"UPDATE career_tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True

# --- SOCIAL CRUD ---
def add_contact(name: str, relationship: str = "", email: str = "", phone: str = "", notes: str = ""):
    contact_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO contacts (id, name, relationship, email, phone, notes) VALUES (?, ?, ?, ?, ?, ?)",
                 (contact_id, name, relationship, email, phone, notes))
    conn.commit()
    conn.close()
    return contact_id

def list_contacts():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM contacts ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_interaction(contact_id: str):
    conn = get_connection()
    conn.execute("UPDATE contacts SET last_contact = ? WHERE id = ?", (_now(), contact_id))
    conn.commit()
    conn.close()
    return True

def create_social_event(title: str, date: str, contact_ids: list = [], event_type: str = "meetup", location: str = "", notes: str = ""):
    event_id = _generate_id()
    conn = get_connection()
    conn.execute("INSERT INTO social_events (id, title, contact_ids, event_type, date, location, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (event_id, title, json.dumps(contact_ids), event_type, date, location, notes))
    conn.commit()
    conn.close()
    return event_id

def list_social_events(upcoming_only: bool = True):
    conn = get_connection()
    if upcoming_only:
        now = _now()
        rows = conn.execute("SELECT * FROM social_events WHERE date >= ? ORDER BY date ASC", (now,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM social_events ORDER BY date ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

