import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas_ta as ta

st.set_page_config(page_title="Swing Trading Master Dashboard", layout="wide")
st.title("🧭 Swing Trading MASTER Dashboard - GICS Sector Rotation")
st.markdown("**Live on your iPhone/iPad • Master Score • Sector Rotation**")

@st.cache_data(ttl=300)
def get_data(ticker, period="2y", interval="1d"):
    df = yf.download(ticker, period=period, interval=interval)
    return df.dropna()

sector_etfs = {
    "Energy": "XLE", "Materials": "XLB", "Industrials": "XLI",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP",
    "Health Care": "XLV", "Financials": "XLF",
    "Information Technology": "XLK", "Communication Services": "XLC",
    "Utilities": "XLU", "Real Estate": "XLRE"
}

spy = get_data("SPY")
vix = get_data("^VIX", period="1y")
macro = {t: get_data(t, period="6mo").iloc[-1]['Close'] for t in ["^TNX", "CL=F", "DX-Y.NYB"]}

def add_indicators(df):
    df['SMA50'] = ta.sma(df['Close'], 50)
    df['SMA200'] = ta.sma(df['Close'], 200)
    df['RSI'] = ta.rsi(df['Close'], 14)
    macd = ta.macd(df['Close'])
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDs_12_26_9']
    df['MACD_Hist'] = macd['MACDh_12_26_9']
    df['OBV'] = ta.obv(df['Close'], df['Volume'])
    df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], 14)
    return df

def master_score(df_daily, spy_daily):
    latest = df_daily.iloc[-1]
    score = 0
    if latest['Close'] > latest['SMA50'] > latest['SMA200']: score += 30
    if 40 < latest['RSI'] < 70: score += 20
    if latest['MACD'] > latest['MACD_Signal']: score += 20
    if latest['OBV'] > df_daily['OBV'].iloc[-10].mean(): score += 15
    if latest['MFI'] > 50: score += 15
    rel_strength = (latest['Close'] / spy_daily.iloc[-1]['Close']) / (df_daily.iloc[-22]['Close'] / spy_daily.iloc[-22]['Close']) if len(df_daily) > 21 else 1
    score += 15 if rel_strength > 1 else 5
    return round(score, 1)

# Build the leaderboard
data = []
for sector, ticker in sector_etfs.items():
    df = get_data(ticker)
    df = add_indicators(df)
    score = master_score(df, spy)
    latest = df.iloc[-1]
    ret_1d = (latest['Close'] / df.iloc[-2]['Close'] - 1) * 100
    data.append({
        "Sector": sector,
        "Master Score": score,
        "1D %": round(ret_1d, 2),
        "Trend": "🟢 STRONG" if score >= 75 else "🟡 Watch" if score >= 55 else "🔴 Weak"
    })

df_summary = pd.DataFrame(data).sort_values("Master Score", ascending=False)
st.dataframe(df_summary.style.background_gradient(cmap='RdYlGn', subset=['Master Score']), use_container_width=True)

st.success("✅ Your dashboard is now live on the cloud! Refresh the page anytime for new market data.")
