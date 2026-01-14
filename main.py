from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

BINANCE_URL = "https://api.binance.com/api/v3/klines"

@app.get("/analyze")
def analyze(symbol: str = "BTCUSDT"):

    # ---------------- FETCH DATA ----------------
    response = requests.get(
        BINANCE_URL,
        params={
            "symbol": symbol,
            "interval": "15m",
            "limit": 200
        },
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "_","_","_","_","_","_"
    ])

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # ---------------- INDICATORS ----------------
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26

    last = df.iloc[-1]

    # ---------------- STRATEGY ----------------
    signal = "NO TRADE"

    if (
        last["ema20"] > last["ema50"] > last["ema200"]
        and 55 < last["rsi"] < 70
        and last["macd"] > 0
    ):
        signal = "BULLISH"

    elif (
        last["ema20"] < last["ema50"] < last["ema200"]
        and last["rsi"] < 45
        and last["macd"] < 0
    ):
        signal = "BEARISH"

    # ---------------- RISK ----------------
    if signal in ("BULLISH", "BEARISH"):
        risk = {
            "leverage": "3x",
            "stop_loss": "1.5%",
            "take_profit": "3.5%"
        }
    else:
        risk = {"message": "Avoid trading"}

    return {
        "symbol": symbol,
        "signal": signal,
        "risk": risk
    }
