"""
Trading Strategy: EMA Crossover
- LONG khi EMA fast cắt lên EMA slow
- SHORT khi EMA fast cắt xuống EMA slow
"""
import pandas as pd
import ta

import config


def calculate_signals(klines):
    """
    Phân tích klines và trả về signal trading.
    Returns: "LONG", "SHORT", hoặc None
    """
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df = df.astype({
        "close": float,
        "high": float,
        "low": float,
    })

    df.loc[:, "ema_fast"] = ta.trend.ema_indicator(df["close"], window=config.EMA_FAST)
    df.loc[:, "ema_slow"] = ta.trend.ema_indicator(df["close"], window=config.EMA_SLOW)

    # RSI để filter
    df.loc[:, "rsi"] = ta.momentum.rsi(df["close"], window=14)

    # Lấy 2 nến cuối để detect crossover
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signal = None

    # EMA crossover LONG: fast vượt lên slow
    if prev["ema_fast"] <= prev["ema_slow"] and curr["ema_fast"] > curr["ema_slow"]:
        if curr["rsi"] < 70:  # Không mua khi overbought
            signal = "LONG"

    # EMA crossover SHORT: fast cắt xuống slow
    elif prev["ema_fast"] >= prev["ema_slow"] and curr["ema_fast"] < curr["ema_slow"]:
        if curr["rsi"] > 30:  # Không short khi oversold
            signal = "SHORT"

    return signal, {
        "ema_fast": round(curr["ema_fast"], 2),
        "ema_slow": round(curr["ema_slow"], 2),
        "rsi": round(curr["rsi"], 2),
        "price": round(curr["close"], 2),
    }


def calculate_sl_tp(entry_price, side):
    """Tính stop loss và take profit."""
    if side == "LONG":
        sl = entry_price * (1 - config.STOP_LOSS_PCT / 100)
        tp = entry_price * (1 + config.TAKE_PROFIT_PCT / 100)
    else:
        sl = entry_price * (1 + config.STOP_LOSS_PCT / 100)
        tp = entry_price * (1 - config.TAKE_PROFIT_PCT / 100)

    return round(sl, 2), round(tp, 2)
