import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

print("=== RUNNING STOCK ALERTS SCRIPT ===")

# --- ENV VARS ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")
SHEET_UPDATE_URL = os.getenv("SHEET_UPDATE_URL")

print("Loaded environment variables")
print(f"BOT TOKEN exists? {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
print(f"CHAT ID exists? {'Yes' if TELEGRAM_CHAT_ID else 'No'}")

# Send telegram
def send_telegram(message: str):
    print("Sending Telegram message...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    print("Telegram response code:", r.status_code)
    r.raise_for_status()

# Fetch price
def get_current_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except Exception as e:
        print("Price fetch error:", str(e))
        return None

# Mark alerted
def mark_alerted(symbol: str):
    print("Marking alerted for:", symbol)
    payload = {"symbol": symbol}
    r = requests.post(SHEET_UPDATE_URL, json=payload)
    print("Update response:", r.status_code)

# Main logic
def main():
    print("Reading sheet from:", SHEET_CSV_URL)
    df = pd.read_csv(SHEET_CSV_URL)
    print("Sheet rows:", len(df))

    for _, row in df.iterrows():
        symbol = row["Symbol"]
        try:
            buy_price = float(row["BuyPrice"])
            alerted = str(row["Alerted"]).strip().upper()
        except Exception as e:
            print(f"Skipping row due to format error: {row}", str(e))
            continue

        print(f"Checking {symbol} | Target buy: {buy_price} | Alerted: {alerted}")

        if alerted == "YES":
            print("Already alerted — skipping")
            continue

        price = get_current_price(symbol)
        if price is None:
            print("Could not fetch price for", symbol)
            continue

        print(f"Current price for {symbol}: {price}")

        if price <= buy_price:
            alert_msg = (
                f"📉 BUY ALERT — {symbol}\n"
                f"Current Price: {price}\n"
                f"Target Price: {buy_price}"
            )
            send_telegram(alert_msg)
            mark_alerted(symbol)
        else:
            print("Target not reached")

if __name__ == "__main__":
    main()
