from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import re
import uuid
import os
import uvicorn

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import (
    create_tables,
    save_invoice,
    get_pending_invoices_by_customer,
    get_all_invoices,
    create_inventory_table,
    deduct_inventory,
    get_inventory
)

# ---------------- APP INIT ----------------
app = FastAPI()

create_tables()
create_inventory_table()

# In-memory store for confirmation flow
pending_actions = {}

# ---------------- REQUEST MODEL ----------------
class WebhookRequest(BaseModel):
    text: str
    user_id: str = "owner"

# ---------------- OWNER NATIVE INTENTS ----------------
INTENT_KEYWORDS = {
    "CREATE_ORDER": ["order", "bill", "bana do", "bhej do", "pack", "note"],
    "PAYMENT_CHECK": ["payment", "udhaar", "baaki", "paisa", "pending", "reminder"],
    "CHECK_STOCK": ["stock", "maal", "samaan"],
    "CANCEL": ["cancel", "galti"]
}

def detect_intent(message: str):
    for intent, keywords in INTENT_KEYWORDS.items():
        for word in keywords:
            if word in message:
                return intent
    return "UNKNOWN"

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health():
    return {"status": "OK"}

# ---------------- PDF GENERATION ----------------
def generate_invoice_pdf(customer_name, amount):
    if not os.path.exists("invoices"):
        os.makedirs("invoices")

    invoice_id = str(uuid.uuid4())[:8]
    path = f"invoices/invoice_{invoice_id}.pdf"

    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(50, 800, "INVOICE")
    c.drawString(50, 760, f"Customer: {customer_name}")
    c.drawString(50, 730, f"Amount: ₹{amount}")
    c.showPage()
    c.save()

    return path

# ---------------- MAIN WEBHOOK ----------------
@app.post("/webhook")
async def webhook(payload: WebhookRequest):
    message = payload.text.lower().strip()
    user_id = payload.user_id

    # -------- YES / NO CONFIRMATION --------
    if message in ["yes", "no"] and user_id in pending_actions:
        action = pending_actions.pop(user_id)

        if message == "yes":
            pdf = generate_invoice_pdf(action["customer"], action["amount"])
            save_invoice(action["customer"], action["amount"], pdf)
            deduct_inventory(action["amount"])

            return {
                "message": "Order confirm ho gaya 👍 Stock update ho gaya."
            }

        return {
            "message": "Theek hai 👍 Order cancel kar diya."
        }

    # -------- INTENT DETECTION --------
    intent = detect_intent(message)

    # -------- CHECK STOCK --------
    if intent == "CHECK_STOCK":
        inventory = get_inventory()
        # inventory row: (name, cat, price, qty, updated) -> index 3 is qty
        total_qty = sum(item[3] for item in inventory)
        return {
            "message": f"Abhi total stock me {total_qty} items hai across {len(inventory)} products. Dashboard dekhein details ke liye."
        }

    # -------- PAYMENT / UDHAAR --------
    if intent == "PAYMENT_CHECK":
        name = message.split()[0].capitalize()
        pending = get_pending_invoices_by_customer(name)

        if pending == 0:
            return {"message": f"{name} ka koi payment baaki nahi hai."}

        return {
            "message": f"{name} ka ₹{pending} payment pending hai. Reminder bhej diya ja sakta hai."
        }

    # -------- CANCEL --------
    if intent == "CANCEL":
        pending_actions.pop(user_id, None)
        return {"message": "Theek hai 👍 Koi action nahi liya."}

    # -------- CREATE ORDER --------
    if intent == "CREATE_ORDER":
        amount_match = re.search(r"\b\d+\b", message)
        amount = int(amount_match.group()) if amount_match else 1

        customer = message.split()[0].capitalize()

        pending_actions[user_id] = {
            "customer": customer,
            "amount": amount
        }

        return {
            "message": f"{customer} ka order ready hai (₹{amount}). Confirm karna hai? YES / NO"
        }

    # -------- FALLBACK --------
    return {
        "message": "Samajh nahi aaya 😅 Thoda simple bolo."
    }

# ---------------- DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    invoices = get_all_invoices()
    inventory = get_inventory()
    
    # Calculate stats
    total_sales = sum(inv[1] for inv in invoices)
    low_stock_count = sum(1 for item in inventory if item[3] < 20)
    total_products = len(inventory)
    
    # Generate Inventory Rows
    inv_rows = ""
    for name, cat, price, qty, updated in inventory:
        status_color = "green" if qty >= 20 else "red"
        status_text = "In Stock" if qty >= 20 else "Low Stock"
        inv_rows += f"""
        <tr class="hover:bg-gray-50 transition">
            <td class="p-4 border-b border-gray-100 font-medium text-gray-800">{name}</td>
            <td class="p-4 border-b border-gray-100 text-gray-600">{cat}</td>
            <td class="p-4 border-b border-gray-100 text-gray-600">₹{price}</td>
            <td class="p-4 border-b border-gray-100">
                <span class="px-2 py-1 bg-{status_color}-100 text-{status_color}-700 rounded-full text-xs font-bold">{qty}</span>
            </td>
            <td class="p-4 border-b border-gray-100 text-gray-500 text-sm">{status_text}</td>
        </tr>
        """

    # Generate Invoice Rows (Limit to last 10)
    order_rows = ""
    for cust, amt, _, date in invoices[:10]:
        order_rows += f"""
        <tr class="hover:bg-gray-50 transition">
            <td class="p-4 border-b border-gray-100 font-medium text-gray-800">{cust}</td>
            <td class="p-4 border-b border-gray-100 text-gray-600">₹{amt}</td>
            <td class="p-4 border-b border-gray-100 text-gray-500 text-sm">{date if date else 'Just now'}</td>
            <td class="p-4 border-b border-gray-100 text-green-600 text-sm font-semibold">Completed</td>
        </tr>
        """

    # Generate Full Invoice Rows (For Orders Tab)
    full_order_rows = ""
    for cust, amt, _, date in invoices:
        full_order_rows += f"""
        <tr class="hover:bg-gray-50 transition">
            <td class="p-4 border-b border-gray-100 font-medium text-gray-800">{cust}</td>
            <td class="p-4 border-b border-gray-100 text-gray-600">₹{amt}</td>
            <td class="p-4 border-b border-gray-100 text-gray-500 text-sm">{date if date else 'Just now'}</td>
            <td class="p-4 border-b border-gray-100 text-green-600 text-sm font-semibold">Completed</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vyapar Setu Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f3f4f6; }}
            .glass {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); }}
            .hidden-section {{ display: none; }}
        </style>
        <script>
            function showSection(sectionId) {{
                // Hide all sections
                document.querySelectorAll('.app-section').forEach(el => el.classList.add('hidden-section'));
                // Show target section
                document.getElementById(sectionId).classList.remove('hidden-section');
                
                // Update Sidebar Active State
                document.querySelectorAll('.nav-link').forEach(el => {{
                    el.classList.remove('bg-blue-600', 'text-white', 'shadow-md');
                    el.classList.add('text-slate-300', 'hover:bg-slate-800');
                }});
                
                const activeLink = document.getElementById('link-' + sectionId);
                if(activeLink) {{
                    activeLink.classList.remove('text-slate-300', 'hover:bg-slate-800');
                    activeLink.classList.add('bg-blue-600', 'text-white', 'shadow-md');
                }}
                
                // Update Header Title
                const titles = {{
                    'dashboard': 'Overview',
                    'inventory': 'Inventory Management',
                    'orders': 'Order History',
                    'settings': 'Settings'
                }};
                document.getElementById('page-title').innerText = titles[sectionId];
            }}
        </script>
    </head>
    <body class="text-gray-800">
        <div class="flex h-screen overflow-hidden">
            <!-- Sidebar -->
            <aside class="w-64 bg-slate-900 text-white flex flex-col hidden md:flex shadow-2xl">
                <div class="p-6">
                    <h1 class="text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-400">Vyapar Setu</h1>
                    <p class="text-xs text-slate-400 mt-1">Empowering Local Business</p>
                </div>
                <nav class="flex-1 px-4 space-y-2 mt-4">
                    <button id="link-dashboard" onclick="showSection('dashboard')" class="nav-link w-full flex items-center gap-3 px-4 py-3 bg-blue-600 rounded-lg text-white shadow-md transition transform hover:scale-105 text-left">
                        <span>📊</span> Dashboard
                    </button>
                    <button id="link-inventory" onclick="showSection('inventory')" class="nav-link w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition text-left">
                        <span>📦</span> Inventory
                    </button>
                    <button id="link-orders" onclick="showSection('orders')" class="nav-link w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition text-left">
                        <span>🧾</span> Orders
                    </button>
                    <button id="link-settings" onclick="showSection('settings')" class="nav-link w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition text-left">
                        <span>⚙️</span> Settings
                    </button>
                </nav>
                <div class="p-4 border-t border-slate-800">
                    <div class="flex items-center gap-3 cursor-pointer" onclick="alert('Owner Profile: Amit Kumar\\nStore: Apna Kirana')">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-400 to-orange-500"></div>
                        <div>
                            <p class="text-sm font-medium">Owner</p>
                            <p class="text-xs text-slate-500">View Policy</p>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Main Content -->
            <main class="flex-1 overflow-y-auto bg-gray-50 p-4 md:p-8">
                <!-- Header -->
                <header class="flex justify-between items-center mb-8">
                    <div>
                        <h2 id="page-title" class="text-3xl font-bold text-gray-800">Overview</h2>
                        <p class="text-gray-500 mt-1">Manage your store efficiently.</p>
                    </div>
                    <button class="bg-white p-2 rounded-full shadow-sm text-gray-600 hover:bg-gray-100">
                        🔔 <span class="absolute top-8 right-8 w-2 h-2 bg-red-500 rounded-full"></span>
                    </button>
                </header>

                <!-- 1. DASHBOARD SECTION -->
                <div id="dashboard" class="app-section">
                    <!-- Stats Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                            <div>
                                <p class="text-sm text-gray-500 font-medium mb-1">Total Sales</p>
                                <h3 class="text-3xl font-bold text-gray-800">₹{total_sales}</h3>
                            </div>
                            <div class="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xl">💰</div>
                        </div>
                        <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                            <div>
                                <p class="text-sm text-gray-500 font-medium mb-1">Total Products</p>
                                <h3 class="text-3xl font-bold text-gray-800">{total_products}</h3>
                            </div>
                            <div class="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xl">📦</div>
                        </div>
                        <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                            <div>
                                <p class="text-sm text-gray-500 font-medium mb-1">Low Stock Alerts</p>
                                <h3 class="text-3xl font-bold text-{ "red" if low_stock_count > 0 else "gray" }-600">{low_stock_count}</h3>
                            </div>
                            <div class="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xl">⚠️</div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <!-- Inventory Preview -->
                        <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div class="p-6 border-b border-gray-100 flex justify-between items-center">
                                <h3 class="text-lg font-bold text-gray-800">📦 Live Inventory Status</h3>
                                <button onclick="showSection('inventory')" class="text-sm text-blue-600 font-medium hover:underline">View All</button>
                            </div>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse">
                                    <thead>
                                        <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                                            <th class="p-4 font-semibold">Product Name</th>
                                            <th class="p-4 font-semibold">Category</th>
                                            <th class="p-4 font-semibold">Price</th>
                                            <th class="p-4 font-semibold">Stock</th>
                                        </tr>
                                    </thead>
                                    <tbody class="text-sm">
                                        {inv_rows}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Recent Orders Preview -->
                        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div class="p-6 border-b border-gray-100">
                                <h3 class="text-lg font-bold text-gray-800">🧾 Recent Orders</h3>
                            </div>
                            <div class="p-0">
                                <table class="w-full text-left">
                                    <tbody class="text-sm">
                                        {order_rows}
                                    </tbody>
                                </table>
                                { "<div class='p-6 text-center text-gray-400'>No orders yet</div>" if not invoices else "" }
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 2. INVENTORY SECTION -->
                <div id="inventory" class="app-section hidden-section">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                        <div class="p-6 border-b border-gray-100">
                            <h3 class="text-lg font-bold text-gray-800">Stock Management</h3>
                        </div>
                         <div class="overflow-x-auto p-0">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                                        <th class="p-4 font-semibold">Product Name</th>
                                        <th class="p-4 font-semibold">Category</th>
                                        <th class="p-4 font-semibold">Price</th>
                                        <th class="p-4 font-semibold">Current Stock</th>
                                        <th class="p-4 font-semibold">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="text-sm">
                                    {inv_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- 3. ORDERS SECTION -->
                <div id="orders" class="app-section hidden-section">
                     <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                        <div class="p-6 border-b border-gray-100">
                            <h3 class="text-lg font-bold text-gray-800">All Orders</h3>
                        </div>
                         <div class="overflow-x-auto p-0">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                                        <th class="p-4 font-semibold">Customer</th>
                                        <th class="p-4 font-semibold">Amount</th>
                                        <th class="p-4 font-semibold">Date</th>
                                        <th class="p-4 font-semibold">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="text-sm">
                                    {full_order_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- 4. SETTINGS SECTION -->
                <div id="settings" class="app-section hidden-section">
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 max-w-2xl">
                        <h3 class="text-lg font-bold text-gray-800 mb-6">Store Settings</h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Store Name</label>
                                <input type="text" value="Apna Kirana Store" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border">
                            </div>
                             <div>
                                <label class="block text-sm font-medium text-gray-700">Currency</label>
                                <select class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border">
                                    <option>INR (₹)</option>
                                    <option>USD ($)</option>
                                </select>
                            </div>
                            <div class="pt-4">
                                <button class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Save Changes</button>
                            </div>
                        </div>
                    </div>
                </div>

            </main>
        </div>
    </body>
    </html>
    """

    return html

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
