import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objects as go
from swing_logic import analyze_swing
from streamlit_autorefresh import st_autorefresh
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== CONFIG ==========
st.set_page_config(page_title="Swing Trade Screener", layout="wide")
st_autorefresh(interval=15 * 60 * 1000, key="datarefresh")  # Refresh every 15 mins
st.title("📈 Top Stocks Swing Trade Setups")

# ========== EMAIL CONFIG ==========
sender_email = "rajasinha2000@gmail.com"
receiver_email = "mdrinfotech79@gmail.com"
password = "hefy otrq yfji ictv"  # Use Gmail App Password

# Email Alert Function
def send_email_alert(stock, signal, trend, confidence):
    subject = f"Swing Trade Alert: {stock} - {signal}"
    body = f"""
    🚀 Swing Trade Alert 🚀

    Stock: {stock}
    Signal: {signal}
    Trend: {trend}
    Confidence: {confidence}/5

    📈 This may be a good setup to review on the chart.
    """
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
    except Exception as e:
        st.error(f"❌ Email failed for {stock}: {e}")

# ========== STOCK LIST ==========
stocks = [
    "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS",
    "LT.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BHARTIARTL.NS",
    "DIXON.NS", "OFSS.NS", "BOSCHLTD.NS", "HAL.NS", "BSE.NS", "COFORGE.NS",
    "TITAN.NS", "KAYNES.NS", "ULTRACEMCO.NS", "MARUTI.NS", "TRENT.NS", "CAMS.NS"
]

results = []

# ========== ANALYSIS LOOP ==========
for stock in stocks:
    try:
        df = yf.download(stock, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 50:
            continue
        analysis = analyze_swing(df)
        if analysis["Signal"] == "BUY" and analysis.get("Trend") == "Uptrend":
            send_email_alert(stock.replace(".NS", ""), analysis["Signal"], analysis["Trend"], analysis["Confidence"])
            # Add entry/target/stoploss
            latest_close = df['Close'].iloc[-1]
            swing_low = df['Low'].rolling(window=10).min().iloc[-1]
            recent_high = df['High'].rolling(window=10).max().iloc[-1]
            analysis["Entry"] = round(latest_close, 2)
            analysis["Stoploss"] = round(swing_low, 2)
            analysis["Target"] = round(recent_high, 2)
        results.append({"Stock": stock.replace(".NS", ""), **analysis})
    except Exception as e:
        continue

# ========== DISPLAY RESULTS ==========
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
        col3.metric("📊 Confidence", f"{row.get('Confidence', 0)}%")

        # Show entry/target/stoploss
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
