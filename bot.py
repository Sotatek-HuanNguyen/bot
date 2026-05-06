"""
Binance Futures Trading Bot - Multi Coin
Strategy: EMA Crossover + RSI Filter
Max 3 positions, 3% risk per trade
Manual SL/TP monitoring (testnet API limitation)
"""
import time
import traceback
from datetime import datetime
from collections import defaultdict

import config
from exchange import BinanceFuturesClient
from strategy import calculate_signals, calculate_sl_tp


def print_banner():
    print("=" * 60)
    print("  BINANCE FUTURES TRADING BOT (MULTI-COIN)")
    print(f"  Whitelist: {len(config.SYMBOLS)} coins")
    print(f"  Max Positions: {config.MAX_POSITIONS}")
    print(f"  Risk per Trade: {config.RISK_PER_TRADE}%")
    print(f"  Strategy: EMA {config.EMA_FAST}/{config.EMA_SLOW} Crossover")
    print(f"  Timeframe: {config.TIMEFRAME}")
    print("=" * 60)


def get_quantity(balance, price):
    """Tính quantity = 3% balance / price."""
    risk_amount = balance * (config.RISK_PER_TRADE / 100)
    return round(risk_amount / price, 4)


def check_position_sl_tp(client, position):
    """Check nếu giá chạm SL/TP thì close (manual)."""
    symbol = position['symbol']
    side = position['side']
    entry = position['entry_price']

    # Get current price
    client.symbol = symbol
    price = client.get_current_price()

    # Tính SL/TP
    sl_price, tp_price = calculate_sl_tp(entry, side)

    should_close = False
    reason = ""

    if side == "LONG":
        if price <= sl_price:
            should_close = True
            reason = f"SL ({price} <= {sl_price})"
        elif price >= tp_price:
            should_close = True
            reason = f"TP ({price} >= {tp_price})"
    else:  # SHORT
        if price >= sl_price:
            should_close = True
            reason = f"SL ({price} >= {sl_price})"
        elif price <= tp_price:
            should_close = True
            reason = f"TP ({price} <= {tp_price})"

    if should_close:
        print(f"  -> CLOSING {symbol}: {reason}")
        client.close_position()
        return True

    return False


# ==== BAD POSITION MANAGER ====
# Ngưỡng P&L để xem là position xấu
BAD_PNL_PCT = -1.0  # -1% P&L = xấu
WAIT_TIME_CYCLES = 5  # Đợi 5 cycles trước khi xử lý

def check_and_manage_bad_positions(client, position, bad_positions_counter):
    """Kiểm tra và quản lý positions xấu."""
    symbol = position['symbol']
    side = position['side']
    entry = position['entry_price']
    pnl_pct = position['unrealized_pnl']

    # Get current indicators
    client.symbol = symbol
    try:
        klines = client.get_klines()
        from strategy import calculate_signals
        signal, ind = calculate_signals(klines)
    except:
        return False

    price = ind['price']
    rsi = ind['rsi']

    # Tính % P&L
    if side == "LONG":
        pnl_pct = ((price - entry) / entry) * 100
    else:
        pnl_pct = ((entry - price) / entry) * 100

    # ==== TRIGGER ====
    should_close = False
    close_reason = ""

    # 1. P&L quá xấu (< -1%)
    if pnl_pct < BAD_PNL_PCT:
        bad_positions_counter[symbol] = bad_positions_counter.get(symbol, 0) + 1

        # Đợi vài cycles rồi mới close
        if bad_positions_counter[symbol] >= WAIT_TIME_CYCLES:
            if pnl_pct < -2:  # Quá xấu (< -2%)
                should_close = True
                close_reason = f"CRITICAL LOSS ({pnl_pct:.1f}%)"
            elif rsi > 65 and side == "LONG":  # RSI overbought + LONG
                should_close = True
                close_reason = f"RSI overbought ({rsi})"
            elif rsi < 35 and side == "SHORT":  # RSI oversold + SHORT
                should_close = True
                close_reason = f"RSI oversold ({rsi})"
            elif signal and signal != side:  # Signal đổi chiều
                should_close = True
                close_reason = f"REVERSE signal ({signal})"

        if should_close:
            print(f"  -> CLOSING BAD {symbol}: {close_reason} | P&L: {pnl_pct:.1f}%")
            client.cancel_all_orders()
            client.close_position()
            bad_positions_counter[symbol] = 0
            return True

    else:
        # Reset counter nếu P&L tốt lên
        bad_positions_counter[symbol] = 0

    return False


def run_bot():
    print_banner()

    # Track position SL/TP levels: {symbol: {'side', 'entry', 'sl', 'tp'}}
    active_positions = {}
    bad_positions_counter = {}  # Track cycles with bad P&L

    client = BinanceFuturesClient()

    # Hiển thị balance
    balance = client.get_account_balance()
    if balance:
        print(f"[*] Balance: {balance['balance']:.2f} USDT")
        print(f"[*] Available: {balance['available']:.2f} USDT")

    print(f"\n[*] Scanning {len(config.SYMBOLS)} coins every 30s...\n")

    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            # Update active positions tracker
            all_positions = client.get_all_positions()

            # Check SL/TP cho positions đang mở
            for pos in all_positions:
                client.symbol = pos['symbol']

                # 1. Check SL/TP hit
                if check_position_sl_tp(client, pos):
                    time.sleep(1)
                # 2. Check bad position (P&L xấu, RSI overbought/oversold, reverse signal)
                elif check_and_manage_bad_positions(client, pos, bad_positions_counter):
                    time.sleep(1)
                else:
                    # Log PnL
                    print(f"  - {pos['symbol']}: {pos['side']} @ {pos['entry_price']} | PnL: {pos['unrealized_pnl']:.2f}")

            # Re-get positions after potential closes
            all_positions = client.get_all_positions()
            open_count = len(all_positions)

            print(f"[{now}] Open positions: {open_count}/{config.MAX_POSITIONS}")

            # Scan từng coin trong whitelist
            for symbol in config.SYMBOLS:
                indicators = None

                client.symbol = symbol
                try:
                    client._setup_leverage(symbol)
                except:
                    pass

                try:
                    # Skip nếu đã có position
                    position = client.get_position()
                    if position:
                        continue  # Skip, đã check SL/TP ở trên

                    if open_count >= config.MAX_POSITIONS:
                        continue  # Skip, đã max positions

                    # Check signal
                    klines = client.get_klines()
                    signal, indicators = calculate_signals(klines)
                    price = client.get_current_price()

                    if signal:
                        # Tính quantity = 3% balance
                        balance_info = client.get_account_balance()
                        bal = balance_info['balance'] if balance_info else 5000
                        qty = get_quantity(bal, price)

                        print(f"\n{'='*40}")
                        print(f"  SIGNAL: {signal} {symbol} @ {price}")
                        print(f"  Qty: {qty} ({config.RISK_PER_TRADE}% risk)")
                        print(f"{'='*40}\n")

                        if signal == "LONG":
                            client.open_long(qty)
                        else:
                            client.open_short(qty)

                        # Lưu SL/TP levels cho position mới
                        sl, tp = calculate_sl_tp(price, signal)
                        print(f"  -> SL: {sl}, TP: {tp}")

                        open_count += 1
                        time.sleep(1)

                except Exception as e:
                    # Skip coin lỗi
                    print(f"  {symbol}: SKIP (error)")
                    continue

                # Log indicators
                if indicators:
                    print(f"  {symbol}: {indicators['price']:.4f} | EMA{config.EMA_FAST}:{indicators['ema_fast']} | EMA{config.EMA_SLOW}:{indicators['ema_slow']} | RSI:{indicators['rsi']}")

        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()

        # Chờ 30 giây
        time.sleep(30)


if __name__ == "__main__":
    run_bot()