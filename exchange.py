"""
Binance Futures Testnet Client
"""
from binance.client import Client
from binance.enums import *
import config


class BinanceFuturesClient:
    def __init__(self, symbol=None):
        self.symbol = symbol or config.SYMBOL
        self.client = Client(
            config.BINANCE_API_KEY,
            config.BINANCE_API_SECRET,
            testnet=True,
        )
        self.client.FUTURES_URL = config.FUTURES_TESTNET_URL + "/fapi"
        self._setup_leverage(self.symbol)

    def _setup_leverage(self, symbol):
        """Set leverage cho symbol."""
        try:
            self.client.futures_change_leverage(
                symbol=symbol, leverage=config.LEVERAGE
            )
            print(f"[+] Leverage set to {config.LEVERAGE}x for {symbol}")
        except Exception as e:
            print(f"[!] Error setting leverage: {e}")

    def get_account_balance(self):
        """Lấy balance USDT."""
        account = self.client.futures_account()
        for asset in account["assets"]:
            if asset["asset"] == "USDT":
                return {
                    "balance": float(asset["walletBalance"]),
                    "unrealized_pnl": float(asset["unrealizedProfit"]),
                    "available": float(asset["availableBalance"]),
                }
        return None

    def get_position(self):
        """Lấy position hiện tại."""
        positions = self.client.futures_position_information(symbol=self.symbol)
        for pos in positions:
            amt = float(pos["positionAmt"])
            if amt != 0:
                return {
                    "symbol": pos["symbol"],
                    "side": "LONG" if amt > 0 else "SHORT",
                    "quantity": abs(amt),
                    "entry_price": float(pos["entryPrice"]),
                    "unrealized_pnl": float(pos["unRealizedProfit"]),
                    "leverage": int(pos["leverage"]),
                }
        return None

    def get_klines(self, interval=None, limit=100):
        """Lấy dữ liệu nến."""
        interval = interval or config.TIMEFRAME
        klines = self.client.futures_klines(
            symbol=self.symbol, interval=interval, limit=limit
        )
        return klines

    def get_current_price(self):
        """Lấy giá hiện tại."""
        ticker = self.client.futures_symbol_ticker(symbol=self.symbol)
        return float(ticker["price"])

    def open_long(self, quantity=None):
        """Mở lệnh LONG."""
        qty = quantity or config.QUANTITY
        order = self.client.futures_create_order(
            symbol=self.symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=qty,
        )
        print(f"[LONG] {self.symbol} | qty={qty}")
        return order

    def open_short(self, quantity=None):
        """Mở lệnh SHORT."""
        qty = quantity or config.QUANTITY
        order = self.client.futures_create_order(
            symbol=self.symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=qty,
        )
        print(f"[SHORT] {self.symbol} | qty={qty}")
        return order

    def close_position(self):
        """Đóng position hiện tại."""
        position = self.get_position()
        if not position:
            return None

        side = SIDE_SELL if position["side"] == "LONG" else SIDE_BUY
        order = self.client.futures_create_order(
            symbol=self.symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=position["quantity"],
        )
        print(f"[CLOSE] {position['side']} | pnl={position['unrealized_pnl']:.2f}")
        return order

    def set_stop_loss(self, stop_price):
        """Đặt stop loss."""
        position = self.get_position()
        if not position:
            return None

        side = SIDE_SELL if position["side"] == "LONG" else SIDE_BUY
        order = self.client.futures_create_order(
            symbol=self.symbol,
            side=side,
            type="STOP_MARKET",
            stopPrice=round(stop_price, 2),
            closePosition=True,
            workingType="MARK_PRICE",
        )
        print(f"[SL] {self.symbol} at {stop_price:.2f}")
        return order

    def set_take_profit(self, tp_price):
        """Đặt take profit."""
        position = self.get_position()
        if not position:
            return None

        side = SIDE_SELL if position["side"] == "LONG" else SIDE_BUY
        order = self.client.futures_create_order(
            symbol=self.symbol,
            side=side,
            type="TAKE_PROFIT_MARKET",
            stopPrice=round(tp_price, 2),
            closePosition=True,
            workingType="MARK_PRICE",
        )
        print(f"[TP] {self.symbol} at {tp_price:.2f}")
        return order

    def cancel_all_orders(self):
        """Hủy tất cả open orders."""
        self.client.futures_cancel_all_open_orders(symbol=self.symbol)

    def get_all_positions(self):
        """Lấy tất cả positions đang mở."""
        positions = self.client.futures_position_information()
        result = []
        for pos in positions:
            amt = float(pos["positionAmt"])
            if amt != 0:
                result.append({
                    "symbol": pos["symbol"],
                    "side": "LONG" if amt > 0 else "SHORT",
                    "quantity": abs(amt),
                    "entry_price": float(pos["entryPrice"]),
                    "unrealized_pnl": float(pos["unRealizedProfit"]),
                    "leverage": int(pos["leverage"]),
                })
        return result
