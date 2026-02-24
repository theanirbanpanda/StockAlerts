print("=== STOCK ALERT SCRIPT STARTED ===")
import os
import requests
import pandas as pd
import yfinance as yf

# --- ENV VARIABLES (FROM GITHUB SECRETS) ---
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
SHEET_CSV_URL = os.environ["SHEET_CSV_URL"]
SHEET_UPDATE_URL = os.environ["SHEET_UPDATE_URL"]

# --- TELEGRAM ---
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    r = requests.post(url, json=payload)
    r.raise_for_status()

# --- PRICE ---
def get_current_price(symbol: str):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])

# --- SHEET UPDATE ---
def mark_alerted(symbol: str):
    payload = {"symbol": symbol}
    r = requests.post(SHEET_UPDATE_URL, json=payload)
    r.raise_for_status()

# --- MAIN ---
def main():
    df = pd.read_csv(SHEET_CSV_URL)

    for _, row in df.iterrows():
        symbol = row["Symbol"]
        buy_price = float(row["BuyPrice"])
        alerted = str(row["Alerted"]).strip().upper()

        if alerted == "YES":
            continue

        price = get_current_price(symbol)
        if price is None:
            continue

        if price <= buy_price:
            message = (
                f"📉 BUY ALERT\n\n"
                f"Stock: {symbol}\n"
                f"Current Price: {price}\n"
                f"Target Buy Price: {buy_price}"
            )
            send_telegram(message)
            mark_alerted(symbol)

if __name__ == "__main__":
    main()
