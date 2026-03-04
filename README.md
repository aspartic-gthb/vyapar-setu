# Vyapar Setu (Bharat Biz Agent)

**The AI-Powered Business Assistant for India's 60M+ SMBs**

Vyapar Setu is a comprehensive solution designed to empower local shopkeepers (Kirana stores) by bringing enterprise-level tools to their fingertips via a simple **Telegram Bot** and a powerful **Web Dashboard**.

It bridges the gap between traditional business operations and modern digital management by using an AI agent that understands natural language (Hinglish).

---

## 📌 Problem Statement

Small and medium businesses (SMBs) in India face daily challenges in managing orders, invoices, and inventory while interacting with customers through familiar platforms like WhatsApp or Telegram. Most existing tools are either too technical or disconnected from how shop owners actually communicate and operate.

**Vyapar Setu** builds a bridge ("Setu") by allowing shop owners to simply type or speak instructions in Hindi or Hinglish, while the agent takes care of execution and backend updates.

---

## 🌟 Key Features

1.  **Hinglish AI Bot**: Understands natural language commands like *"Raju ka 500 ka bill bana do"* or *"Stock check karo"*.
2.  **Instant Invoicing**: Generates PDF invoices on-the-fly and allows sending them virtually to customers.
3.  **Smart Inventory**: Automatically deducts stock upon order confirmation and alerts for low stock.
4.  **Udhaar (Credit) Tracking**: Keeps track of pending payments for customers.
5.  **Interactive Dashboard**: A modern, responsive web interface to visualize sales, inventory, and order history.

---

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI
-   **Database**: SQLite (Embedded, Zero-config)
-   **Interface**: Telegram Bot API (using `python-telegram-bot`)
-   **Frontend**: HTML5, TailwindCSS (CDN), Vanilla JS (Single Page Application architecture)
-   **PDF Engine**: ReportLab
-   **Deployment**: Docker

---

This project is containerized for easy deployment.

1.  **Configure Environment**
    Create a `.env` file with your bot token:
    ```env
    TELEGRAM_BOT_TOKEN=your_token_here
    ```

2.  **Run with Docker Compose** (Recommended)
    ```bash
    docker compose up --build
    ```

3.  **Access App**
    -   Dashboard: `http://localhost:8000/dashboard`
    -   Bot: Active immediately.

---

## 🚀 Local Installation (Manual)

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/aspartic-gthb/vyapar-setu.git
    cd vyapar-setu
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    -   Create a `.env` file in the root directory.
    -   Add your Telegram Bot Token: `TELEGRAM_BOT_TOKEN=your_token_here`

4.  **Run the Application**
    
    You can use the provided helper script:
    ```bash
    ./start.sh
    ```
    
    Or run manually in two terminals:
    ```bash
    # Terminal 1: Dashboard
    python app.py

    # Terminal 2: Bot
    python telegram_bot.py
    ```

---

## 📱 How to Use (Demo Flow)

1.  **Start the Bot**: Open your bot in Telegram and send `/start`.
2.  **Create an Order**:
    -   Type: *`Raju 500`* (or click "Naya Bill")
    -   Bot will ask for confirmation. Click **Yes**.
    -   Bot generates a PDF and asks if you want to send it to the customer.
    -   Click **Yes** and enter a phone number.
3.  **Check Stock**:
    -   Type: *`Stock check karo`* (or click "Check Stock").
    -   Bot responds with total items count.
4.  **View Dashboard**:
    -   Go to `http://localhost:8000/dashboard` in your browser.
    -   See the "Recent Orders" update instantly.
    -   Check the "Inventory" tab for stock details.

---

## 📂 Project Structure

-   `app.py`: Main FastAPI server, handles database logic, PDF generation, and Dashboard rendering.
-   `telegram_bot.py`: Handles Telegram interaction, conversational state management, and user intents.
-   `database.py`: SQLite connection and schema management.
-   `invoices/`: Generated PDF invoices are stored here.
-   `bharat_biz.db`: Local SQLite database file.
-   `docs/`: Additional documentation and walkthroughs.

---

## 💡 Future Roadmap

-   WhatsApp Integration (using Meta API).
-   OCR for reading handwritten bills.
-   Regional Language Support (Tamil, Telugu, Bengali, etc.).
-   GST Calculation & Filing Support.

---

*Built with ❤️ for Bharat's Business.*
