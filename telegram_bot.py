import logging
import os
import re
import asyncio  # For simulating delay
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from app import detect_intent, generate_invoice_pdf, save_invoice, deduct_inventory, get_inventory, get_pending_invoices_by_customer

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Predefined keyboard prompt
KEYBOARD = [
    ["📝 Naya Bill (Create Order)", "💰 Check Payment (Udhaar)"],
    ["📦 Check Stock (Samaan)", "❌ Cancel Action"]
]

# State constants
WAITING_CONFIRMATION = 'WAITING_CONFIRMATION'
WAITING_BILL_DETAILS = 'WAITING_BILL_DETAILS'
WAITING_PAYMENT_NAME = 'WAITING_PAYMENT_NAME'
WAITING_SEND_CONFIRMATION = 'WAITING_SEND_CONFIRMATION'
WAITING_CUSTOMER_PHONE = 'WAITING_CUSTOMER_PHONE'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and the predefined keyboard."""
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Welcome to Vyapar Setu Bot!\n\n"
        "Main aapka personal business assistant hoon via Telegram.\n"
        "Niche diye gaye buttons se shuru karein ya seedha likh kar batayein.",
        reply_markup=reply_markup
    )
    context.user_data['state'] = None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # ---------------- STATE: WAITING CONFIRMATION ----------------
    if state == WAITING_CONFIRMATION:
        action = context.user_data.get('pending_action')
        if text.lower() in ['yes', 'haan', 'confirm', 'kardo', 'han', 'y', 'ok']:
            # Execute action
            pdf_path = generate_invoice_pdf(action['customer'], action['amount'])
            save_invoice(action['customer'], action['amount'], pdf_path)
            deduct_inventory(action['amount'])
            
            await update.message.reply_text(
                f"✅ Order confirm ho gaya!\nCustomer: {action['customer']}\nAmount: ₹{action['amount']}\nStock update ho gaya.",
                reply_markup=ReplyKeyboardRemove()
            )
            # Send PDF
            try:
                with open(pdf_path, 'rb') as f:
                    await update.message.reply_document(f, caption="Ye raha invoice PDF 📄")
            except Exception as e:
                logging.error(f"Failed to send PDF: {e}")
                
            # Ask to send to customer
            context.user_data['state'] = WAITING_SEND_CONFIRMATION
            context.user_data['last_pdf_path'] = pdf_path 
            await update.message.reply_text(
                "Kya aap ye invoice customer ke phone number par bhejna chahte hain? (Yes/No)",
                reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True)
            )
            return

        elif text.lower() in ['no', 'nahi', 'cancel', 'n', 'mat karo']:
            context.user_data['state'] = None
            context.user_data['pending_action'] = None
            await update.message.reply_text("❌ Theek hai, order cancel kar diya.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
            return
        
        else:
            await update.message.reply_text("Confirm karna hai? (Yes/No)")
            return

    # ---------------- STATE: WAITING SEND CONFIRMATION ----------------
    if state == WAITING_SEND_CONFIRMATION:
        if text.lower() in ['yes', 'haan', 'y', 'ok']:
            context.user_data['state'] = WAITING_CUSTOMER_PHONE
            await update.message.reply_text(
                "Customer ka mobile number enter karein:",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        else:
            # Assume NO
            context.user_data['state'] = None
            await update.message.reply_text("Okay 👍", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
            return

    # ---------------- STATE: WAITING CUSTOMER PHONE ----------------
    if state == WAITING_CUSTOMER_PHONE:
        phone_number = text.strip()
        # Verify if it looks like a number (basic check)
        if re.match(r'^\+?\d{10,15}$', phone_number):
            await update.message.reply_text(f"Sending invoice to {phone_number} via Telegram...")
            # Simulate sending delay
            await asyncio.sleep(2)
            
            # Since bots cannot initiate messages to phone numbers without prior contact/API, we clarify this.
            msg = (
                f"✅ Virtual Sent: Invoice marked as sent to {phone_number}!\n\n"
                "ℹ️ Note: Due to Telegram privacy rules, bots cannot directly message a phone number unless the user has started the bot.\n"
                "👉 Please forward the PDF above to the customer manually."
            )
            await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
            context.user_data['state'] = None
            return
        else:
            if 'cancel' in text.lower():
                context.user_data['state'] = None
                await update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
                return
            await update.message.reply_text("Invalid phone number. Kripya sahi number daalein (e.g. 9876543210) ya 'cancel' likhein.")
            return

    # ---------------- STATE: WAITING BILL DETAILS ----------------
    if state == WAITING_BILL_DETAILS:
        # Check CANCEL first
        if "cancel" in text.lower():
             context.user_data['state'] = None
             await update.message.reply_text("❌ Action cancel kar diya.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
             return

        # Expecting "Name Amount"
        amount_match = re.search(r"\b\d+\b", text)
        amount = int(amount_match.group()) if amount_match else 0
        
        if amount > 0:
            name_part = text.replace(str(amount), "").strip()
            # If name is empty, maybe prompt again or use 'Unknown'
            # But let's assume they might type "500" then we need name? For now, simplistic.
            customer = name_part if name_part else "Customer"
            
            # Move to confirmation
            context.user_data['pending_action'] = {
                "customer": customer,
                "amount": amount
            }
            context.user_data['state'] = WAITING_CONFIRMATION
            
            await update.message.reply_text(
                f"🛒 {customer} ka order ready hai (₹{amount}).\nConfirm karna hai? (Yes/No)",
                reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True)
            )
            return
        else:
            await update.message.reply_text("Amount nahi mila. Kripya 'Name Amount' likhein (e.g. 'Raju 500').")
            return

    # ---------------- STATE: WAITING PAYMENT NAME ----------------
    if state == WAITING_PAYMENT_NAME:
        if "cancel" in text.lower():
             context.user_data['state'] = None
             await update.message.reply_text("❌ Action cancel kar diya.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
             return

        name = text.strip().split()[0].capitalize() # Take first word as name usually
        
        # Check if text matches a button logic to abort current flow?
        if any(keyword in text.lower() for keyword in ["check stock", "naya bill", "cancel action", "check payment"]):
            # Fall through to normal intent detection by resetting state
            context.user_data['state'] = None
            # Do NOT return, let it flow down
        else:
            # Process as name
            pending = get_pending_invoices_by_customer(name)
            if pending == 0:
                await update.message.reply_text(f"🎉 {name} ka koi payment baaki nahi hai.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
            else:
                await update.message.reply_text(f"⚠️ {name} ka ₹{pending} payment pending hai.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))
            
            context.user_data['state'] = None
            return

    # ---------------- NORMAL INTENT DETECTION ----------------
    intent = detect_intent(text.lower())
    
    # Overrides for specific button texts
    if "naya bill" in text.lower():
        intent = "CREATE_ORDER_PROMPT"
    elif "check payment" in text.lower():
        intent = "PAYMENT_CHECK_PROMPT"
    elif "check stock" in text.lower():
        intent = "CHECK_STOCK"
    elif "cancel" in text.lower():
        intent = "CANCEL"

    # Handle Intents
    if intent == "CHECK_STOCK":
        inventory = get_inventory()
        # Sum quantity at index 3
        total_qty = sum(item[3] for item in inventory)
        await update.message.reply_text(f"📦 Abhi total stock me {total_qty} items hai across {len(inventory)} products. Dashboard dekhein details ke liye.")

    elif intent == "PAYMENT_CHECK_PROMPT":
         context.user_data['state'] = WAITING_PAYMENT_NAME
         await update.message.reply_text("Kiska payment check karna hai? Naam likhiye (e.g. 'Raju').", reply_markup=ReplyKeyboardRemove())

    elif intent == "PAYMENT_CHECK":
        # Usually from "Raju payment check"
        words = text.split()
        if len(words) > 1:
            name = words[0].capitalize() # simplistic
            if name.lower() in ["payment", "check", "udhaar"]:
                 context.user_data['state'] = WAITING_PAYMENT_NAME
                 await update.message.reply_text("Kiska payment check karna hai? Naam likhiye.")
            else:
                pending = get_pending_invoices_by_customer(name)
                if pending == 0:
                    await update.message.reply_text(f"🎉 {name} ka koi payment baaki nahi hai.")
                else:
                    await update.message.reply_text(f"⚠️ {name} ka ₹{pending} payment pending hai.")
        else:
             context.user_data['state'] = WAITING_PAYMENT_NAME
             await update.message.reply_text("Kiska payment check karna hai? Naam likhiye.")

    elif intent == "CREATE_ORDER_PROMPT":
        context.user_data['state'] = WAITING_BILL_DETAILS
        await update.message.reply_text("Kiska bill banana hai aur kitne ka? (e.g. 'Raju 500')", reply_markup=ReplyKeyboardRemove())

    elif intent == "CREATE_ORDER":
        amount_match = re.search(r"\b\d+\b", text)
        amount = int(amount_match.group()) if amount_match else 0
        
        if amount == 0:
             context.user_data['state'] = WAITING_BILL_DETAILS
             await update.message.reply_text("Amount samajh nahi aaya. Kripya 'Name Amount' likhein (e.g. 'Raju 500').", reply_markup=ReplyKeyboardRemove())
             return

        customer = text.split()[0].capitalize()
        context.user_data['state'] = WAITING_CONFIRMATION
        context.user_data['pending_action'] = {
            "customer": customer,
            "amount": amount
        }
        
        await update.message.reply_text(
            f"🛒 {customer} ka order ready hai (₹{amount}).\nConfirm karna hai? (Yes/No)",
            reply_markup=ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True, resize_keyboard=True)
        )

    elif intent == "CANCEL":
        context.user_data['state'] = None
        context.user_data['pending_action'] = None
        await update.message.reply_text("❌ Action cancel kar diya.", reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True))

    else:
        await update.message.reply_text("🤔 Samajh nahi aaya via text. Kripya buttons use karein ya saaf likhein (e.g. 'Raju 500' for bill).")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        print("Please set it and run again.")
        print("Example: set TELEGRAM_BOT_TOKEN=123456:ABC-DEF... && python telegram_bot.py")
        exit(1)
        
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is polling...")
    application.run_polling()
