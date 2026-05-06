"""
Advanced Trading Strategy
- EMA Crossover + MACD + Bollinger Bands
- Volume Filter
- RSI Filter
- Dynamic SL/TP based on ATR
"""
import pandas as pd
import ta
import config


def calculate_signals(klines):
    """
    Advanced signal calculation with multiple indicators.
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
        "volume": float,
    })

    # ==== INDICATORS ====

    # EMA
    df.loc[:, "ema_9"] = ta.trend.ema_indicator(df["close"], window=9)
    df.loc[:, "ema_21"] = ta.trend.ema_indicator(df["close"], window=21)
    df.loc[:, "ema_50"] = ta.trend.ema_indicator(df["close"], window=50)

    # MACD
    df.loc[:, "macd"] = ta.trend.macd(df["close"])
    df.loc[:, "macd_signal"] = ta.trend.macd_signal(df["close"])
    df.loc[:, "macd_hist"] = ta.trend.macd_diff(df["close"])

    # RSI
    df.loc[:, "rsi"] = ta.momentum.rsi(df["close"], window=14)

    # Bollinger Bands
    df.loc[:, "bb_upper"] = ta.volatility.bollinger_hband(df["close"])
    df.loc[:, "bb_lower"] = ta.volatility.bollinger_lband(df["close"])
    df.loc[:, "bb_mid"] = ta.volatility.bollinger_mavg(df["close"])

    # ATR (for dynamic SL/TP)
    df.loc[:, "atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)

    # Volume
    df.loc[:, "volume_sma"] = ta.trend.sma_indicator(df["volume"], window=20)
    df.loc[:, "volume_ratio"] = df["volume"] / df["volume_sma"]

    # Stochastic
    df.loc[:, "stoch_k"] = ta.momentum.stoch(df["high"], df["low"], df["close"])
    df.loc[:, "stoch_d"] = ta.momentum.stoch_signal(df["high"], df["low"], df["close"])

    # ==== SIGNALS ====
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signal = None
    reasons = []

    # Check trend direction (EMA 50)
    uptrend = curr["ema_21"] > curr["ema_50"]
    downtrend = curr["ema_21"] < curr["ema_50"]

    # ==== LONG SIGNAL ====
    long_conditions = []

    # 1. EMA 9 crosses above EMA 21
    if prev["ema_9"] <= prev["ema_21"] and curr["ema_9"] > curr["ema_21"]:
        long_conditions.append("EMA cross")
        reasons.append("EMA9 cross UP")

    # 2. MACD crosses above signal line
    if prev["macd"] <= prev["macd_signal"] and curr["macd"] > curr["macd_signal"]:
        long_conditions.append("MACD cross")

    # 3. Price above Bollinger Lower (oversold bounce)
    if curr["close"] > curr["bb_lower"]:
        long_conditions.append("BB oversold")

    # 4. Stochastic oversold and turning up
    if curr["stoch_k"] < 20 and curr["stoch_k"] > prev["stoch_k"]:
        long_conditions.append("Stochastic bounce")

    # Filter conditions for LONG
    if long_conditions:
        # RSI not overbought
        if curr["rsi"] < 70:
            # Volume confirmation
            if curr["volume_ratio"] > 0.8:  # At least 80% of average
                # Uptrend confirmation
                if uptrend or curr["rsi"] < 50:
                    signal = "LONG"

    # ==== SHORT SIGNAL ====
    short_conditions = []

    # 1. EMA 9 crosses below EMA 21
    if prev["ema_9"] >= prev["ema_21"] and curr["ema_9"] < curr["ema_21"]:
        short_conditions.append("EMA cross")
        reasons.append("EMA9 cross DOWN")

    # 2. MACD crosses below signal line
    if prev["macd"] >= prev["macd_signal"] and curr["macd"] < curr["macd_signal"]:
        short_conditions.append("MACD cross")

    # 3. Price below Bollinger Upper (overbought rejection)
    if curr["close"] < curr["bb_upper"]:
        short_conditions.append("BB overbought")

    # 4. Stochastic overbought and turning down
    if curr["stoch_k"] > 80 and curr["stoch_k"] < prev["stoch_k"]:
        short_conditions.append("Stochastic bounce")

    # Filter conditions for SHORT
    if short_conditions:
        # RSI not oversold
        if curr["rsi"] > 30:
            # Volume confirmation
            if curr["volume_ratio"] > 0.8:
                # Downtrend confirmation
                if downtrend or curr["rsi"] > 50:
                    signal = "SHORT"

    # ==== INDICATORS FOR DISPLAY ====
    return signal, {
        # Price
        "price": round(curr["close"], 2),
        "volume_ratio": round(curr["volume_ratio"], 2),

        # EMA
        "ema_9": round(curr["ema_9"], 2),
        "ema_21": round(curr["ema_21"], 2),
        "ema_50": round(curr["ema_50"], 2),

        # MACD
        "macd": round(curr["macd"], 4),
        "macd_signal": round(curr["macd_signal"], 4),

        # RSI
        "rsi": round(curr["rsi"], 2),

        # Bollinger
        "bb_upper": round(curr["bb_upper"], 2),
        "bb_lower": round(curr["bb_lower"], 2),

        # ATR
        "atr": round(curr["atr"], 2),

        # Stochastic
        "stoch_k": round(curr["stoch_k"], 2),
        "stoch_d": round(curr["stoch_d"], 2),

        # Signal reason
        "reason": ", ".join(reasons) if reasons else "none",
    }


def calculate_sl_tp(entry_price, side, atr=None):
    """Dynamic SL/TP based on ATR and price volatility."""
    if atr is None:
        # Default if no ATR provided
        atr = entry_price * 0.02  # 2% ATR default

    # SL: 1.5x ATR for tight stop
    sl_distance = atr * 1.5

    # TP: 3x ATR for 2:1 reward ratio
    tp_distance = atr * 3

    if side == "LONG":
        sl = entry_price - sl_distance
        tp = entry_price + tp_distance
    else:  # SHORT
        sl = entry_price + sl_distance
        tp = entry_price - tp_distance

    return round(sl, 2), round(tp, 2)


def get_indicators_only(klines):
    """Get indicators without signal (for display only)."""
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df = df.astype({
        "close": float,
        "high": float,
        "low": float,
        "volume": float,
    })

    # All indicators
    df.loc[:, "ema_9"] = ta.trend.ema_indicator(df["close"], window=9)
    df.loc[:, "ema_21"] = ta.trend.ema_indicator(df["close"], window=21)
    df.loc[:, "macd"] = ta.trend.macd(df["close"])
    df.loc[:, "rsi"] = ta.momentum.rsi(df["close"], window=14)
    df.loc[:, "bb_upper"] = ta.volatility.bollinger_hband(df["close"])
    df.loc[:, "bb_lower"] = ta.volatility.bollinger_lband(df["close"])
    df.loc[:, "atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)

    curr = df.iloc[-1]

    return {
        "price": round(curr["close"], 2),
        "ema_9": round(curr["ema_9"], 2),
        "ema_21": round(curr["ema_21"], 2),
        "macd": round(curr["macd"], 4),
        "rsi": round(curr["rsi"], 2),
        "bb_upper": round(curr["bb_upper"], 2),
        "bb_lower": round(curr["bb_lower"], 2),
        "atr": round(curr["atr"], 2),
    }