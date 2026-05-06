"""
Flask API for Trading Bot
"""
import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot modules
from exchange import BinanceFuturesClient
from strategy import calculate_signals, calculate_sl_tp
import config as config_module

app = Flask(__name__)

# In-memory config
bot_config = {
    "whitelist": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"],
    "volume_percent": 3,
    "max_positions": 3,
}

# Bot state
class TradingBot:
    def __init__(self):
        self.running = False
        self.thread = None
        self.client = None
        self.positions = []
        self.balance = 0
        self.logs = []

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.insert(0, f"[{timestamp}] {msg}")
        if len(self.logs) > 50:
            self.logs = self.logs[:50]

    def get_quantity(self, price):
        risk_amount = self.balance * (bot_config["volume_percent"] / 100)
        return round(risk_amount / price, 4)

    def check_position_sl_tp(self, client, position):
        """Manual SL/TP check."""
        symbol = position["symbol"]
        side = position["side"]
        entry = position["entry_price"]

        client.symbol = symbol
        price = client.get_current_price()

        sl_price, tp_price = calculate_sl_tp(entry, side)

        should_close = False
        if side == "LONG":
            if price <= sl_price:
                self.log(f"SL HIT {symbol}")
                should_close = True
            elif price >= tp_price:
                self.log(f"TP HIT {symbol}")
                should_close = True
        else:
            if price >= sl_price:
                self.log(f"SL HIT {symbol}")
                should_close = True
            elif price <= tp_price:
                self.log(f"TP HIT {symbol}")
                should_close = True

        if should_close:
            client.close_position()
            return True
        return False

    def run(self):
        """Main bot loop."""
        self.client = BinanceFuturesClient()
        self.log("Bot started")

        while self.running:
            try:
                # Get balance
                balance_info = self.client.get_account_balance()
                if balance_info:
                    self.balance = balance_info["balance"]

                # Get all positions
                self.positions = self.client.get_all_positions()

                # Check SL/TP for open positions
                for pos in self.positions:
                    self.client.symbol = pos["symbol"]
                    if self.check_position_sl_tp(self.client, pos):
                        time.sleep(1)

                # Re-fetch positions
                self.positions = self.client.get_all_positions()
                open_count = len(self.positions)

                # Scan whitelist
                for symbol in bot_config["whitelist"]:
                    if not self.running:
                        break

                    self.client.symbol = symbol

                    try:
                        # Check if already has position
                        pos = self.client.get_position()
                        if pos:
                            continue

                        if open_count >= bot_config["max_positions"]:
                            continue

                        # Get signals
                        klines = self.client.get_klines()
                        signal, indicators = calculate_signals(klines)
                        price = self.client.get_current_price()

                        if signal:
                            qty = self.get_quantity(price)
                            self.log(f"SIGNAL: {signal} {symbol} @ {price}")

                            if signal == "LONG":
                                self.client.open_long(qty)
                            else:
                                self.client.open_short(qty)

                            open_count += 1
                            time.sleep(1)

                    except Exception as e:
                        self.log(f"Error {symbol}: {str(e)[:30]}")

                time.sleep(30)

            except Exception as e:
                self.log(f"Error: {str(e)[:50]}")
                time.sleep(30)

        self.log("Bot stopped")

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        self.running = False

    def get_status(self):
        return {
            "running": self.running,
            "balance": self.balance,
            "positions": self.positions,
            "config": bot_config,
            "logs": self.logs[:20],
        }


# Global bot instance
bot = TradingBot()


@app.route("/api/status", methods=["GET"])
def get_status():
    """Get bot status."""
    return jsonify(bot.get_status())


@app.route("/api/start", methods=["POST"])
def start_bot():
    """Start bot."""
    bot.start()
    return jsonify({"success": True})


@app.route("/api/stop", methods=["POST"])
def stop_bot():
    """Stop bot."""
    bot.stop()
    return jsonify({"success": True})


@app.route("/api/config", methods=["POST", "GET"])
def config():
    """Get or update config."""
    if request.method == "POST":
        data = request.json
        if "whitelist" in data:
            bot_config["whitelist"] = data["whitelist"]
        if "volume_percent" in data:
            bot_config["volume_percent"] = data["volume_percent"]
        if "max_positions" in data:
            bot_config["max_positions"] = data["max_positions"]
        return jsonify({"success": True})
    return jsonify(bot_config)


if __name__ == "__main__":
    print("Starting Flask API on http://localhost:5000")
    print("Endpoints:")
    print("  GET  /api/status")
    print("  POST /api/start")
    print("  POST /api/stop")
    print("  GET  /api/config")
    print("  POST /api/config")
    app.run(host="0.0.0.0", port=5000, debug=True)