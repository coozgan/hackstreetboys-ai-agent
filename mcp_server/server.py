"""
Mock MCP Server for HackstreetBoys AI
Exposes 45+ tools across Shopping, Health, Finance, Career, and Social domains.
"""

import json
import sys
import os

# Ensure parent directory is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp_server import database as db

mcp = FastMCP(
    "HackstreetBoys AI MCP Server",
    instructions="""Multi-domain MCP Server for HackstreetBoys AI.
    Provides tools for Shopping, Health, Finance, Career, and Social domains.
    All data is persisted in a local SQLite database.""",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

# ==========================================
# SHOPPING TOOLS
# ==========================================

@mcp.tool()
def browse_products(category: str = "") -> str:
    """List products in the catalog, optionally filtered by category."""
    products = db.list_products(category=category)
    return json.dumps({"products": products, "count": len(products)})

@mcp.tool()
def search_products(query: str) -> str:
    """Search products by name or description."""
    products = db.search_products(query)
    return json.dumps({"products": products, "count": len(products)})

@mcp.tool()
def get_categories() -> str:
    """Get all available product categories."""
    cats = db.get_categories()
    return json.dumps({"categories": cats})

@mcp.tool()
def view_cart(session_id: str) -> str:
    """View contents and total of the user's cart."""
    return json.dumps(db.get_cart(session_id))

@mcp.tool()
def add_to_cart(session_id: str, product_id: str, quantity: int = 1) -> str:
    """Add a product to the cart."""
    db.add_to_cart(session_id, product_id, quantity)
    return json.dumps({"status": "success", "message": f"Added {quantity} of {product_id} to cart."})

@mcp.tool()
def remove_from_cart(session_id: str, product_id: str) -> str:
    """Remove a product from the cart completely."""
    db.remove_from_cart(session_id, product_id)
    return json.dumps({"status": "success"})

@mcp.tool()
def update_cart_quantity(session_id: str, product_id: str, quantity: int) -> str:
    """Update the quantity of a product in the cart (set to 0 to remove)."""
    db.update_cart_quantity(session_id, product_id, quantity)
    return json.dumps({"status": "success"})

@mcp.tool()
def clear_cart(session_id: str) -> str:
    """Empty the cart."""
    db.clear_cart(session_id)
    return json.dumps({"status": "success"})

@mcp.tool()
def check_stock(product_id: str, quantity: int) -> str:
    """Check if enough stock exists for a product."""
    has_stock = db.check_stock(product_id, quantity)
    return json.dumps({"has_stock": has_stock, "product_id": product_id, "requested": quantity})

@mcp.tool()
def reserve_stock(product_id: str, quantity: int) -> str:
    """Reserve stock for a product."""
    success = db.reserve_stock(product_id, quantity)
    return json.dumps({"success": success})

@mcp.tool()
def create_order(session_id: str) -> str:
    """Create an order from the current cart and empty the cart."""
    cart = db.get_cart(session_id)
    if not cart["items"]:
        return json.dumps({"error": "Cart is empty"})
    
    order_id = db.create_order(session_id, cart["items"], cart["total"])
    db.clear_cart(session_id)
    return json.dumps({"status": "success", "order_id": order_id, "total": cart["total"]})

@mcp.tool()
def get_order(order_id: str) -> str:
    """Get details of a specific order."""
    order = db.get_order(order_id)
    return json.dumps({"order": order} if order else {"error": "Not found"})

@mcp.tool()
def update_order_status(order_id: str, status: str) -> str:
    """Update order status (e.g. pending, completed, cancelled)."""
    db.update_order_status(order_id, status)
    return json.dumps({"status": "success"})

@mcp.tool()
def process_payment(order_id: str, method: str, amount: float) -> str:
    """Process a payment for an order."""
    # In a real app we'd call Stripe/Stripe, here we mock:
    payment_id = db.create_payment(order_id, method, amount, "completed")
    db.update_order_status(order_id, "paid")
    return json.dumps({"status": "success", "payment_id": payment_id})

# ==========================================
# HEALTH TOOLS
# ==========================================

@mcp.tool()
def log_health_entry(log_type: str, value: float, unit: str = "", notes: str = "") -> str:
    """Log a health metric (e.g., sleep, weight, water)."""
    log_id = db.log_health(log_type, value, unit, notes)
    return json.dumps({"status": "success", "id": log_id})

@mcp.tool()
def get_health_logs(log_type: str = "", limit: int = 10) -> str:
    """Retrieve recent health logs."""
    logs = db.get_health_logs(log_type, limit)
    return json.dumps({"logs": logs})

@mcp.tool()
def set_health_goal(goal_type: str, target_value: float, unit: str = "") -> str:
    """Set a target goal for a health metric."""
    goal_id = db.set_health_goal(goal_type, target_value, unit)
    return json.dumps({"status": "success", "id": goal_id})

@mcp.tool()
def get_health_goals() -> str:
    """Get all active health goals."""
    goals = db.get_health_goals()
    return json.dumps({"goals": goals})

@mcp.tool()
def update_health_goal_progress(goal_id: str, current_value: float) -> str:
    """Update the current progress value of a health goal."""
    db.update_health_goal(goal_id, current_value)
    return json.dumps({"status": "success"})

# ==========================================
# FINANCE TOOLS
# ==========================================

@mcp.tool()
def add_transaction(type_: str, category: str, amount: float, description: str = "") -> str:
    """Log an income or expense transaction."""
    if type_ not in ["income", "expense"]:
        return json.dumps({"error": "type_ must be income or expense"})
    txn_id = db.log_transaction(type_, category, amount, description)
    return json.dumps({"status": "success", "id": txn_id})

@mcp.tool()
def list_transactions(limit: int = 50) -> str:
    """List recent financial transactions."""
    txns = db.list_transactions(limit)
    return json.dumps({"transactions": txns})

@mcp.tool()
def set_budget(category: str, limit: float, month: str = "") -> str:
    """Set a monthly budget limit for a category (month format: YYYY-MM)."""
    db.set_budget(category, limit, month)
    return json.dumps({"status": "success"})

@mcp.tool()
def get_budgets(month: str = "") -> str:
    """Get budgets and current spending for a month (defaults to current month)."""
    budgets = db.get_budgets(month)
    return json.dumps({"budgets": budgets})

# ==========================================
# CAREER TOOLS
# ==========================================

@mcp.tool()
def create_career_task(title: str, description: str = "", priority: str = "medium", category: str = "work", due_date: str = "") -> str:
    """Create a new career/work task."""
    task = db.create_career_task(title, description, priority, category, due_date)
    return json.dumps({"status": "success", "task": task})

@mcp.tool()
def list_career_tasks(status: str = "", priority: str = "") -> str:
    """List career tasks optionally filtered by status or priority."""
    tasks = db.list_career_tasks(status, priority)
    return json.dumps({"tasks": tasks})

@mcp.tool()
def update_career_task(task_id: str, status: str = "", priority: str = "") -> str:
    """Update status ('todo', 'in_progress', 'done') or priority of a task."""
    kwargs = {}
    if status: kwargs["status"] = status
    if priority: kwargs["priority"] = priority
    success = db.update_career_task(task_id, **kwargs)
    return json.dumps({"status": "success" if success else "error"})

# ==========================================
# SOCIAL TOOLS
# ==========================================

@mcp.tool()
def add_contact(name: str, relationship: str = "", email: str = "", phone: str = "", notes: str = "") -> str:
    """Add a new contact."""
    contact_id = db.add_contact(name, relationship, email, phone, notes)
    return json.dumps({"status": "success", "id": contact_id})

@mcp.tool()
def list_contacts() -> str:
    """List all contacts."""
    contacts = db.list_contacts()
    return json.dumps({"contacts": contacts})

@mcp.tool()
def log_interaction(contact_id: str) -> str:
    """Log that you recently interacted with a contact to update their last_contact field."""
    db.log_interaction(contact_id)
    return json.dumps({"status": "success"})

@mcp.tool()
def create_social_event(title: str, date: str, event_type: str = "meetup", location: str = "") -> str:
    """Create a social event wrapper."""
    event_id = db.create_social_event(title, date, [], event_type, location)
    return json.dumps({"status": "success", "id": event_id})

@mcp.tool()
def list_social_events(upcoming_only: bool = True) -> str:
    """List upcoming (or all) social events."""
    events = db.list_social_events(upcoming_only)
    return json.dumps({"events": events})

# ==========================================
# CROSS-DOMAIN TOOL
# ==========================================

@mcp.tool()
def get_daily_briefing_data() -> str:
    """Get a cross-domain snapshot: upcoming tasks, events, and over-budget items."""
    tasks = db.list_career_tasks(status="todo")[:3]
    events = db.list_social_events(upcoming_only=True)[:3]
    budgets = [b for b in db.get_budgets() if b["current_spent"] >= b["monthly_limit"]]
    health = db.get_health_logs(limit=3)
    
    return json.dumps({
        "priority_tasks": tasks,
        "upcoming_events": events,
        "over_budget_alerts": budgets,
        "recent_health": health
    })

# ==========================================
# RUNNER
# ==========================================

# Expose the SSE app at module level for uvicorn import:
#   uvicorn mcp_server.server:sse_app --host 0.0.0.0 --port 8080
sse_app = mcp.sse_app()

if __name__ == "__main__":
    transport = "stdio"
    port = 3000

    if len(sys.argv) > 1:
        if sys.argv[1] == "--sse":
            transport = "sse"
        elif sys.argv[1] == "--stdio":
            transport = "stdio"

    if len(sys.argv) > 2 and sys.argv[1] == "--sse":
        port = int(sys.argv[2])

    if transport == "sse":
        import uvicorn
        print(f"Starting HackstreetBoys MCP Server in SSE mode on port {port}...")
        uvicorn.run(sse_app, host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")

