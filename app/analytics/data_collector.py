import os
from datetime import datetime

DATA_COLLECTION_DIR = "app/system/commander_logs"

def log_commander_victory(ticker, reason):
    if not os.path.exists(DATA_COLLECTION_DIR):
        os.makedirs(DATA_COLLECTION_DIR)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{DATA_COLLECTION_DIR}/{ticker}_{timestamp}.txt"

    with open(filename, 'w') as file:
        file.write(f"Victory Log\n")
        file.write(f"Ticker: {ticker}\n")
        file.write(f"Timestamp: {timestamp}\n")
        file.write(f"Reason: {reason}\n")
        file.write(f"Commander Observations: Manual input or future auto-capture.\n")

    print(f"✅ Victory recorded for {ticker} at {timestamp}")
