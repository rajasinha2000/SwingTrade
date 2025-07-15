from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator

def analyze_swing(df):
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    volume = df['Volume'].squeeze()

    # Indicators
    rsi = RSIIndicator(close=close).rsi()
    macd_ind = MACD(close=close)
    macd_line = macd_ind.macd()
    macd_signal = macd_ind.macd_signal()
    adx = ADXIndicator(high=high, low=low, close=close).adx()
    vol_avg = volume.rolling(5).mean()

    # Signal logic
    latest = close.iloc[-1]
    breakout = latest > max(high[-3:-1])
    rsi_ok = rsi.iloc[-1] > 60
    macd_ok = macd_line.iloc[-1] > macd_signal.iloc[-1]
    adx_ok = adx.iloc[-1] > 20
    vol_ok = volume.iloc[-1] > 1.5 * vol_avg.iloc[-1]

    # Confidence score
    confidence = sum([breakout, rsi_ok, macd_ok, adx_ok, vol_ok])
    signal = "BUY" if confidence >= 3 else "WAIT"

    # Trend logic
    ma_short = close.rolling(5).mean().iloc[-1]
    ma_long = close.rolling(20).mean().iloc[-1]
    if abs(ma_short - ma_long) < 0.01 * ma_long:
        trend = "Sideways"
    elif ma_short > ma_long:
        trend = "Uptrend"
    else:
        trend = "Downtrend"

    return {
        "CMP": round(latest, 2),
        "Breakout": "✔️" if breakout else "❌",
        "RSI": f"{int(rsi.iloc[-1])} {'✔️' if rsi_ok else '❌'}",
        "MACD": "✔️" if macd_ok else "❌",
        "ADX": f"{int(adx.iloc[-1])} {'✔️' if adx_ok else '❌'}",
        "Volume": "✔️" if vol_ok else "❌",
        "Confidence": confidence,
        "Signal": signal,
        "Trend": trend
    }
