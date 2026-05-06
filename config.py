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

# ==== STRATEGY PARAMETERS ====
TIMEFRAME = "15m"  # 15 phút

# EMA Parameters
EMA_FAST = 9
EMA_MID = 21
EMA_SLOW = 50

# RSI Parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBROUGHT = 70

# MACD Parameters
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# Volume Filter
VOLUME_MIN_RATIO = 0.8  # Volume must be >= 80% of 20-period SMA

# Stochastic
STOCH_PERIOD = 14
STOCH_OVERSOLD = 20
STOCH_OVERBROUGHT = 80

# ==== RISK MANAGEMENT ====
RISK_PER_TRADE = 3     # 3% risk per trade
MAX_POSITIONS = 3      # Max 3 concurrent positions
MAX_DAILY_TRADES = 10  # Max 10 trades per day

# Dynamic SL/TP based on ATR
USE_ATR_SLTP = True
ATR_MULTIPLIER_SL = 1.5  # SL at 1.5x ATR
ATR_MULTIPLIER_TP = 3.0   # TP at 3x ATR (2:1 reward ratio)

# Fallback if not using ATR
STOP_LOSS_PCT = 1.5
TAKE_PROFIT_PCT = 3.0
