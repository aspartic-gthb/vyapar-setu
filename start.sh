#!/bin/bash

# Start FastAPI/Dashboard in the background
# Output is redirected to stdout so it shows in docker logs
python app.py &

# Start Telegram Bot in the foreground
python telegram_bot.py
