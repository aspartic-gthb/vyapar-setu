# 🏆 Judges' Walkthrough Guide: Vyapar Setu

Welcome, Judges! This guide works as a script to help you explore the **Vyapar Setu** platform effectively. Follow these steps to experience the full customer journey from a shopkeeper's perspective.

---

## 🎯 The Scenario
You are "Amit Kumar", owner of "Apna Kirana Store". You want to manage your busy shop without touching a complex computer software, just by using your phone (Telegram) and occasionally checking your shop's performance (Dashboard).

---

## 🟢 Step 1: The Setup
1.  Ensure `python app.py` is running in one terminal (Backend/Dashboard).
2.  Ensure `python telegram_bot.py` is running in another terminal (Robot).
3.  Open the **Dashboard** in your browser: [http://localhost:8000/dashboard](http://localhost:8000/dashboard).
    -   *Observe*: The "Inventory" tab shows realistic products like Rice, Oil, Soap.
    -   *Observe*: "Recent Orders" might be empty or have few items.

---

## 🟢 Step 2: The "Hinglish" Order (Bot)
*Goal: Test Natural Language Understanding*

1.  Open the Telegram Bot.
2.  Send the message: **`Rahul 250`**
    -   *Context*: You sold items worth ₹250 to customer Rahul.
3.  The Order Bot will confirm: *"🛒 Rahul ka order ready hai (₹250). Confirm karna hai?"*
4.  Click **`Yes`**.
    -   *Action*: The bot generates a professional PDF Invoice and sends it to you.
    -   *Action*: It automatically deducts stock from your inventory.

---

## 🟢 Step 3: Customer Engagement (Bot)
*Goal: Test the "Send to Customer" Feature*

1.  After confirming the order, the bot asks: *"Kya aap ye invoice customer ke phone number par bhejna chahte hain?"*
2.  Click **`Yes`**.
3.  Enter a phone number (e.g., **`9988776655`**).
4.  *Result*: The bot simulates sending the invoices via Telegram/WhatsApp and confirms: *"✅ Virtual Sent: Invoice marked as sent to 9988776655!"*

---

## 🟢 Step 4: Real-Time Updates (Dashboard)
*Goal: Test Synchronization*

1.  Go back to your browser Dashboard ([http://localhost:8000/dashboard](http://localhost:8000/dashboard)).
2.  Click on the **"Orders"** tab.
    -   *Result*: You should see "Rahul - ₹250" listed at the top with status "Completed".
3.  Click on the **"Dashboard"** (Overview) tab.
    -   *Result*: "Total Sales" has increased by ₹250.

---

## 🟢 Step 5: Inventory Check (Bot)
*Goal: Test Stock Query*

1.  Back in Telegram, type: **`Stock kitna hai?`** (or click "📦 Check Stock").
2.  *Result*: The bot replies with the current total stock count (e.g., *"📦 Abhi total stock me 748 items hai..."*).

---

## 🟢 Step 6: Payment/Udhaar Check (Bot)
*Goal: Test Credit Tracking*

1.  Type: **`Rahul payment check`**
2.  *Result*: The bot checks the database and tells you Rahul's total pending/paid amount.

---

## 🌟 What Makes This Stand Out?
-   **Zero Learning Curve**: Shopkeepers just "chat" with their business.
-   **Hybrid Interface**: Chat for quick actions, Dashboard for deep insights.
-   **Localized**: Built for the Indian context (Hinglish support, informal workflows).

---
*Thank you for reviewing Vyapar Setu!*
