import os
from dotenv import load_dotenv

load_dotenv()

# Binance Futures Testnet
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Testnet endpoints
FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"

# Trading parameters
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
LEVERAGE = int(os.getenv("LEVERAGE", 5))
QUANTITY = float(os.getenv("QUANTITY", 0.01))

# Multi-coin whitelist
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "XRPUSDT", "DOGEUSDT", "ADAUSDT",
    "AVNTUSDT", "PUMPUSDT", "GIGGLEUSDT",
    "AAVEUSDT", "DASHUSDT", "ENAUSDT"
]

# Risk management
EMA_FAST = 9
EMA_SLOW = 21
TIMEFRAME = "15m"

STOP_LOSS_PCT = 1.5    # Stop loss 1.5%
TAKE_PROFIT_PCT = 3.0  # Take profit 3%
RISK_PER_TRADE = 3  # 3% per trade
MAX_POSITIONS = 3       # Tối đa 3 positions cùng lúc
