# ========== SWING TRADING PROGRAME ==========
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objects as go
from swing_logic import analyze_swing
from streamlit_autorefresh import st_autorefresh
import requests
import json
import os

# ========== CONFIG ========== #
st.set_page_config(page_title="Swing Trade Screener", layout="wide")
st_autorefresh(interval=15 * 60 * 1000, key="datarefresh")
st.title("📈 Top Stocks Swing Trade Setups")

# ========== TELEGRAM CONFIG ========== #
TELEGRAM_TOKEN = "7735892458:AAELFRclang2MgJwO2Rd9RRwNmoll1LzlFg"
TELEGRAM_CHAT_ID = "5073531512"

# Telegram Alert Function
def send_telegram_alert(stock, signal, trend, confidence, entry=None, target=None, stoploss=None):
    message = f"""
🚀 *Swing Trade Alert*

📌 *Stock:* {stock}
📈 *Signal:* {signal}
📉 *Trend:* {trend}
🔎 *Confidence:* {confidence}/5

💰 *Entry:* ₹{entry}
🎯 *Target:* ₹{target}
🛡️ *Stoploss:* ₹{stoploss}

_Review the chart and confirm before trading._
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            st.error(f"❌ Telegram failed for {stock}: {response.text}")
    except Exception as e:
        st.error(f"❌ Telegram exception for {stock}: {e}")

# ========== ALERT TRACKING ========== #
STATUS_FILE = "alert_status.json"

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

def already_alerted(stock):
    status = load_status()
    return status.get(stock, False)

def mark_alert_sent(stock):
    status = load_status()
    status[stock] = True
    save_status(status)

# ========== STOCK LIST ========== #
stocks = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS",
    "LT.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BHARTIARTL.NS","SIEMENS.NS",
    "DIXON.NS", "OFSS.NS", "BOSCHLTD.NS", "HAL.NS", "BSE.NS", "COFORGE.NS",
    "TITAN.NS", "KAYNES.NS", "ULTRACEMCO.NS", "MARUTI.NS", "TRENT.NS", "CAMS.NS"
]

results = []

# ========== ANALYSIS LOOP ========== #
for stock in stocks:
    try:
        df = yf.download(stock, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 50:
            continue
        analysis = analyze_swing(df)

        stock_name = stock.replace(".NS", "")

        if analysis["Signal"] == "BUY" and analysis.get("Trend") == "Uptrend":
            latest_close = df['Close'].iloc[-1]
            swing_low = df['Low'].rolling(window=10).min().iloc[-1]
            recent_high = df['High'].rolling(window=10).max().iloc[-1]

            analysis["Entry"] = round(latest_close, 2)
            analysis["Stoploss"] = round(swing_low, 2)
            analysis["Target"] = round(recent_high, 2)

            # === Telegram alert if not already sent === #
            if not already_alerted(stock_name):
                send_telegram_alert(
                    stock=stock_name,
                    signal=analysis["Signal"],
                    trend=analysis["Trend"],
                    confidence=analysis["Confidence"],
                    entry=analysis["Entry"],
                    target=analysis["Target"],
                    stoploss=analysis["Stoploss"]
                )
                mark_alert_sent(stock_name)

        results.append({"Stock": stock_name, **analysis})
    except Exception:
        continue

# ========== DISPLAY RESULTS ========== #
if results:
    df_screen = pd.DataFrame(results)

    st.subheader("📋 All Analysis Results")
    st.dataframe(df_screen)

    st.write("🔢 Signal Summary:")
    st.write(df_screen["Signal"].value_counts())

    top5 = df_screen[df_screen["Trend"] == "Uptrend"].sort_values(by="Confidence", ascending=False).head(5)

    st.subheader("📌 Top 5 Stocks (by Confidence)")
    st.dataframe(
        top5.style.applymap(lambda v: 'background-color: lightgreen' if v == 'BUY' else
                            'background-color: salmon' if v == 'SELL' else '',
                            subset=["Signal"])
    )

    for index, row in top5.iterrows():
        st.markdown("---")
        st.markdown(f"### {row['Stock']}")

        col1, col2, col3 = st.columns(3)
        col1.metric("📍 Signal", row.get("Signal", "N/A"))
        col2.metric("📈 Trend", row.get("Trend", "Unknown"))
        col3.metric("📊 Confidence", f"{row.get('Confidence', 0)}")

        if "Entry" in row:
            st.markdown(f"**💰 Entry:** ₹{row['Entry']}  |  🎯 Target: ₹{row['Target']}  |  🛡️ Stoploss: ₹{row['Stoploss']}")

        df_chart = yf.download(row['Stock'] + ".NS", period="5d", interval="15m", progress=False)
        if not df_chart.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df_chart.index,
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
            )])
            fig.update_layout(height=400, margin=dict(t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Chart data not available.")
else:
    st.info("❌ No analysis results found.")

# ========== RESET BUTTON ========== #
if st.button("🔁 Reset All Telegram Alerts"):
    save_status({})
    st.success("✅ All alerts reset.")
# ========== FIIS AND DIIS screener ========== #
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import requests
import os
import json

# --- CONFIG ---
REFRESH_INTERVAL_MIN = 5
ENABLE_TELEGRAM = True
TELEGRAM_TOKEN = "7735892458:AAELFRclang2MgJwO2Rd9RRwNmoll1LzlFg"
TELEGRAM_CHAT_ID = "5073531512"
ALERT_LOG_FILE = "alert_log.json"

st.set_page_config(layout="wide", page_title="FII/DII Footprint Screener")
st.title("\U0001F4CA FII/DII Footprint Screener Dashboard")
st.caption(f"\U0001F501 Auto-refresh every {REFRESH_INTERVAL_MIN} minutes.")

symbols = [    "RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK",
    "LT", "SBIN", "KOTAKBANK", "AXISBANK", "BSE","SIEMENS",
    "BHARTIARTL", "TITAN", "ASIANPAINT", "OFSS", "MARUTI",
    "BOSCHLTD", "TRENT", "NESTLEIND", "ULTRACEMCO", "MCX",
    "CAMS", "COFORGE","HAL","KEI"
]

# Load alert log to prevent duplicate alerts
if os.path.exists(ALERT_LOG_FILE):
    with open(ALERT_LOG_FILE, "r") as f:
        alert_log = json.load(f)
else:
    alert_log = {}

def save_alert_log(log):
    with open(ALERT_LOG_FILE, "w") as f:
        json.dump(log, f)

@st.cache_data(ttl=REFRESH_INTERVAL_MIN * 60)
def fetch_data(symbol):
    try:
        df = yf.download(symbol + ".NS", period="15d", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 10:
            return None

        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
        df["Signal"] = df["MACD"].ewm(span=9).mean()
        df["RSI"] = compute_rsi(df["Close"])

        prev_close = df["Close"].iloc[-2].item()
        today_close = df["Close"].iloc[-1].item()
        today_volume = df["Volume"].iloc[-1].item()
        avg_volume = df["Volume"].iloc[-6:-1].mean().item()
        recent_high = df["Close"].iloc[-6:-1].max().item()

        delivery_perc = round((today_volume / avg_volume) * 100, 2)
        breakout = today_close > recent_high
        volume_surge = today_volume > 1.5 * avg_volume
        price_strength = today_close > prev_close * 1.01

        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]
        macd_signal = df["Signal"].iloc[-1]

        rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        macd_signal_type = "Bullish" if macd > macd_signal else "Bearish"

        long_buildup = today_close > prev_close and today_volume > avg_volume
        short_buildup = today_close < prev_close and today_volume > avg_volume

        signal = "BUY" if all([breakout, volume_surge, price_strength, macd > macd_signal]) else \
                 "SELL" if price_strength and macd < macd_signal else "AVOID"
        action = "\U0001F4C8 Buy" if signal == "BUY" else "\U0001F4C9 Sell" if signal == "SELL" else "\u23F8\uFE0F Wait"

        alert_key = f"{symbol}_{signal}"
        if ENABLE_TELEGRAM and signal in ["BUY", "SELL"] and alert_key not in alert_log:
            msg = f"""\U0001F9E0 *FII/DII Footprint Alert*
*{symbol}* \u25B6\uFE0F {signal}
CMP: ₹{today_close:.2f}
Volume: {int(today_volume):,} (Avg: {int(avg_volume):,})
Delivery%: {delivery_perc}%
Breakout: {"\u2705" if breakout else "\u274C"}
MACD: {macd_signal_type}
RSI: {rsi_signal}
Long Buildup: {"\u2705" if long_buildup else "-"}
Short Buildup: {"\u2705" if short_buildup else "-"}
Action: {action}"""
            send_telegram_alert(msg)
            alert_log[alert_key] = str(datetime.datetime.now())

        return {
            "Symbol": symbol,
            "CMP": round(today_close, 2),
            "Prev Close": round(prev_close, 2),
            "Avg Volume": int(avg_volume),
            "Today Vol": int(today_volume),
            "Delivery %": delivery_perc,
            "Breakout": breakout,
            "Vol Surge": volume_surge,
            "Price Strength": price_strength,
            "MACD": macd_signal_type,
            "RSI": rsi_signal,
            "Long Buildup": "\u2705" if long_buildup else "",
            "Short Buildup": "\u2705" if short_buildup else "",
            "Signal": signal,
            "Action": action
        }

    except Exception:
        st.warning(f"\u26A0\uFE0F Failed to fetch data for {symbol}")
        return None

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload)
    except Exception:
        st.warning("\u26A0\uFE0F Telegram alert failed.")

# --- MAIN VIEW ---
st.markdown("### \U0001F50D Screener Results")
results = []

for symbol in symbols:
    row = fetch_data(symbol)
    if row:
        results.append(row)

save_alert_log(alert_log)

if results:
    df = pd.DataFrame(results)

    def highlight_missing(val):
        return "background-color: yellow" if pd.isna(val) else ""

    styled_df = df.style.map(highlight_missing)
    st.dataframe(styled_df, use_container_width=True)

    st.download_button("\U0001F4C5 Download CSV", data=df.to_csv(index=False), file_name="fii_dii_signals.csv")
else:
    st.warning("\u26A0\uFE0F No data returned or API limit reached.")

# --- Auto-refresh JS ---
st.caption(f"\U0001F552 Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown(f"""
    <script>
        setTimeout(function() {{
            window.location.reload();
        }}, {REFRESH_INTERVAL_MIN * 60 * 1000});
    </script>
""", unsafe_allow_html=True)
# --- DOUBLE BREAKOUT SCREENER ---
import os
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== CONFIGURATION ==========
st.set_page_config(page_title="Market Dashboard", layout="wide")
st_autorefresh(interval=900000, key="refresh_15min")  # Auto-refresh every 15 mins
st.title("📈 Intraday Breakout Screener with MACD (Live)")

# ========== STOCK LIST ==========
index_list = ["^NSEI", "^NSEBANK"]
stock_list = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "ICICIBANK.NS",
    "LT.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BSE.NS","SIEMENS.NS",
    "BHARTIARTL.NS", "TITAN.NS", "ASIANPAINT.NS", "OFSS.NS", "MARUTI.NS",
    "BOSCHLTD.NS", "TRENT.NS", "NESTLEIND.NS", "ULTRACEMCO.NS", "MCX.NS",
    "CAMS.NS", "COFORGE.NS","HAL.NS","KEI.NS"
] + index_list

# ========== FUNCTIONS ==========
def fetch_data(symbol):
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today = now.date()
    start_date = today - timedelta(days=7)

    df_15m = yf.download(symbol, interval="15m", start=start_date, end=now)
    df_15m = df_15m.tz_localize(None)
    df_15m.index = df_15m.index.tz_localize('UTC').tz_convert('Asia/Kolkata')

    df_day = yf.download(symbol, interval="1d", start=start_date, end=now)

    return df_15m, df_day

def analyze(symbol):
    try:
        df_15m, df_day = fetch_data(symbol)
    except Exception as e:
        print(f"Data fetch failed for {symbol}: {e}")
        return None

    result = {
        "Stock": symbol.replace(".NS", "").replace("^", ""),
        "CMP": 0,
        "Today Breakout": "",
        "2-Day Breakout": "",
        "Breakout Type": "",
        "Trend": "",
        "MACD": "",
        "Signal": "",
        "MACD Trend": ""
    }

    if df_15m.empty or df_day.empty:
        return None

    today_date = df_15m.index[-1].date()
    df_today = df_15m[df_15m.index.date == today_date]
    first_15m = df_today.between_time("09:15", "09:30")

    if first_15m.empty or df_today.empty:
        return None

    high_15m = float(first_15m['High'].max())
    low_15m = float(first_15m['Low'].min())
    current_price = float(df_today["Close"].iloc[-1])
    result["CMP"] = round(current_price, 2)

    df_2d = df_day[df_day.index.date < today_date].tail(2)
    if df_2d.empty:
        return None

    high_2d = float(df_2d["High"].max())
    low_2d = float(df_2d["Low"].min())

    if current_price > high_15m:
        result["Today Breakout"] = "🔼 Above 15m High"
    elif current_price < low_15m:
        result["Today Breakout"] = "🔽 Below 15m Low"
    if current_price > high_2d:
        result["2-Day Breakout"] = "📈 Above 2-Day High"
    elif current_price < low_2d:
        result["2-Day Breakout"] = "📉 Below 2-Day Low"

    if result["Today Breakout"] and result["2-Day Breakout"]:
        result["Breakout Type"] = "✅ Double Breakout"
    elif result["Today Breakout"]:
        result["Breakout Type"] = result["Today Breakout"]
    elif result["2-Day Breakout"]:
        result["Breakout Type"] = result["2-Day Breakout"]

    df_today["EMA12"] = df_today["Close"].ewm(span=12, adjust=False).mean()
    df_today["EMA26"] = df_today["Close"].ewm(span=26, adjust=False).mean()
    df_today["MACD"] = df_today["EMA12"] - df_today["EMA26"]
    df_today["Signal"] = df_today["MACD"].ewm(span=9, adjust=False).mean()

    macd = df_today["MACD"].iloc[-1]
    signal = df_today["Signal"].iloc[-1]
    result["MACD"] = round(macd, 2)
    result["Signal"] = round(signal, 2)

    if macd > signal:
        result["MACD Trend"] = "🟢 Bullish"
    elif macd < signal:
        result["MACD Trend"] = "🔴 Bearish"
    else:
        result["MACD Trend"] = "⚪️ Sideways"

    if current_price > high_15m and current_price > high_2d:
        result["Trend"] = "🚀 Very Bullish"
    elif current_price > high_15m or current_price > high_2d:
        result["Trend"] = "📈 Bullish"
    elif current_price < low_15m and current_price < low_2d:
        result["Trend"] = "🔻 Very Bearish"
    elif current_price < low_15m or current_price < low_2d:
        result["Trend"] = "📉 Bearish"
    else:
        result["Trend"] = "⏸️ Sideways"

    return result

def send_email_alert(stock):
    sender_email = "rajasinha2000@gmail.com"
    receiver_email = "mdrinfotech79@gmail.com"
    password = "hefy otrq yfji ictv"

    subject = f"🚨 DOUBLE BREAKOUT in {stock}"
    body = f"The stock {stock} has triggered a ✅ DOUBLE BREAKOUT."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"✅ Email sent for {stock}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ========== TELEGRAM ALERT FUNCTION ==========
def send_telegram_alert(message):
    token = "7735892458:AAELFRclang2MgJwO2Rd9RRwNmoll1LzlFg"
    chat_id = "5073531512"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

# ========== MAIN ==========
results = []
for stock in stock_list:
    print(f"Checking {stock}...")
    res = analyze(stock)
    if res:
        results.append(res)

df_result = pd.DataFrame(results)

if not df_result.empty and "Breakout Type" in df_result.columns:
    df_result = df_result[df_result["Breakout Type"] != ""]

    priority = {"🚀 Very Bullish": 1, "🔻 Very Bearish": 2, "📈 Bullish": 3, "📉 Bearish": 4, "⏸️ Sideways": 5}
    df_result["SortKey"] = df_result["Trend"].map(priority)
    df_result = df_result.sort_values("SortKey").drop(columns="SortKey")

    st.dataframe(df_result, use_container_width=True)

    csv = df_result.to_csv(index=False).encode("utf-8")
    st.download_button("📂 Download Breakout CSV", data=csv, file_name="breakout_screener.csv", mime="text/csv")

    EMAIL_LOG_FILE = "emailed_stocks.txt"
    def load_emailed_stocks():
        if os.path.exists(EMAIL_LOG_FILE):
            with open(EMAIL_LOG_FILE, "r") as f:
                return set(f.read().splitlines())
        return set()

    def save_emailed_stock(stock):
        with open(EMAIL_LOG_FILE, "a") as f:
            f.write(f"{stock}\n")

    emailed_stocks = load_emailed_stocks()
    double_breakouts = df_result[df_result["Breakout Type"] == "✅ Double Breakout"]

    if not double_breakouts.empty:
        st.markdown("""
            <div style='padding:20px; background-color:#ffcccc; border:3px solid red; border-radius:10px; animation: flash 1s infinite; text-align:center; font-size:24px; font-weight:bold;'>
                🚨 DOUBLE BREAKOUT ALERT! 🚨
            </div>
            <style>
            @keyframes flash {
                0% {opacity: 1;}
                50% {opacity: 0.5;}
                100% {opacity: 1;}
            }
            </style>
        """, unsafe_allow_html=True)
        st.dataframe(double_breakouts)

        for row in double_breakouts.itertuples():
            if row.Stock not in emailed_stocks:
   #==          send_email_alert(row.Stock)
                send_telegram_alert(f"🟢 DOUBLE BREAKOUT in {row.Stock} ✅ CMP: {row.CMP}")
                save_emailed_stock(row.Stock)
                emailed_stocks.add(row.Stock)

    if st.button("🔄 Reset Email Log"):
        if os.path.exists(EMAIL_LOG_FILE):
            os.remove(EMAIL_LOG_FILE)
            st.success("✅ Email log file cleared.")
        else:
            st.info("ℹ️ No email log file found.")
else:
    st.warning("⚠️ No valid breakout data found.")
