# Binance Futures Trading Bot (Testnet)

Bot trading futures tự động trên Binance Testnet sử dụng chiến lược EMA Crossover.

## Cài đặt

```bash
# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

## Cấu hình

1. Đăng ký tài khoản testnet tại: https://testnet.binancefuture.com/
2. Tạo API Key trong phần API Management
3. Copy file `.env.example` thành `.env` và điền API keys:

```bash
cp .env.example .env
```

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
SYMBOL=BTCUSDT
LEVERAGE=5
QUANTITY=0.01
```

## Chạy bot

```bash
python bot.py
```

## Chiến lược

- **EMA Crossover**: EMA 9 cắt lên EMA 21 → LONG, cắt xuống → SHORT
- **RSI Filter**: Không LONG khi RSI > 70, không SHORT khi RSI < 30
- **Risk Management**: Stop Loss 1.5%, Take Profit 3%
- **Timeframe**: 15 phút

## Cấu trúc

```
bot/
├── bot.py          # Main loop
├── config.py       # Cấu hình
├── exchange.py     # Binance API client
├── strategy.py     # Logic chiến lược
├── .env.example    # Template env
└── requirements.txt
```

## Lưu ý

- Đây là bot chạy trên **TESTNET**, không dùng tiền thật
- Luôn test kỹ trước khi chuyển sang mainnet
- Điều chỉnh `QUANTITY` và `LEVERAGE` phù hợp với risk management
