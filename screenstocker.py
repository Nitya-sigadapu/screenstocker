import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Indicator Dashboard", layout="wide")

st.title("📈 Stock Screener with RSI, MACD, Z-Score")

# Upload CSV
uploaded_file = st.file_uploader("Upload stock CSV file", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Show raw data
    st.subheader("📄 Raw Data (first 5 rows)")
    st.write(df.head())

    # Convert numeric columns
    for col in ['OPEN', 'HIGH', 'LOW', 'PREV. CLOSE', 'ltp']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Sort by date
        df = df.sort_values('Date')
        df = df.reset_index(drop=True)

        # Choose price column to calculate indicators
        price_col = 'ltp' if 'ltp' in df.columns else 'PREV. CLOSE'

        # --- RSI Calculation ---
        def compute_rsi(data, window=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        df['RSI'] = compute_rsi(df[price_col])

        # --- Z-Score ---
        df['Z-Score'] = (df[price_col] - df[price_col].rolling(20).mean()) / df[price_col].rolling(20).std()

        # --- MACD ---
        ema12 = df[price_col].ewm(span=12, adjust=False).mean()
        ema26 = df[price_col].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # --- Plot candlestick chart ---
        st.subheader("📊 Candlestick Chart")
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['OPEN'],
            high=df['HIGH'],
            low=df['LOW'],
            close=df[price_col],
            name='Candlestick'
        )])
        fig.update_layout(xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- Plot RSI ---
        st.subheader("📈 RSI Chart")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='orange')))
        fig_rsi.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(), y0=70, y1=70,
                          line=dict(color="red", dash="dash"))
        fig_rsi.add_shape(type="line", x0=df['Date'].min(), x1=df['Date'].max(), y0=30, y1=30,
                          line=dict(color="green", dash="dash"))
        fig_rsi.update_layout(yaxis_title="RSI")
        st.plotly_chart(fig_rsi, use_container_width=True)

        # --- Plot MACD ---
        st.subheader("📉 MACD Chart")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD'))
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal'))
        fig_macd.update_layout(yaxis_title="MACD")
        st.plotly_chart(fig_macd, use_container_width=True)

        # --- Plot Z-Score ---
        st.subheader("🧮 Z-Score Chart")
        fig_z = go.Figure()
        fig_z.add_trace(go.Scatter(x=df['Date'], y=df['Z-Score'], name='Z-Score'))
        fig_z.update_layout(yaxis_title="Z-Score")
        st.plotly_chart(fig_z, use_container_width=True)

        # --- Indicator Table ---
        st.subheader("📋 Latest Indicator Values")
        st.write(df[['Date', price_col, 'RSI', 'MACD', 'Signal', 'Z-Score']].tail())

    else:
        st.error("No 'Date' column found in the CSV.")
