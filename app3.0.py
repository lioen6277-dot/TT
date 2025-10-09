import re
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="AI趨勢分析📈 (Expert)",
    page_icon="🤖",
    layout="wide"
)

PERIOD_MAP = { 
    "30 分": ("60d", "30m"), 
    "4 小時": ("1y", "60m"), 
    "1 日": ("5y", "1d"), 
    "1 週": ("max", "1wk")
}

FULL_SYMBOLS_MAP = {
    "AAPL": {"name": "蘋果 (Apple)", "keywords": ["蘋果", "Apple", "AAPL"]},
    "NVDA": {"name": "輝達 (Nvidia)", "keywords": ["輝達", "英偉達", "NVDA", "Nvidia"]},
    "TSLA": {"name": "特斯拉 (Tesla)", "keywords": ["特斯拉", "TSLA", "Tesla"]},
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "2330", "TSMC"]},
    "BTC-USD": {"name": "比特幣 (Bitcoin)", "keywords": ["比特幣", "BTC", "BTC-USD"]},
    # ...可自行補齊所有標的...
}

CATEGORY_MAP = {
    "美股 (US) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if not (c.endswith(".TW") or c.endswith("-USD") or c.startswith("^TWII"))],
    "台股 (TW) - 個股/ETF/指數": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith(".TW") or c.startswith("^TWII")],
    "加密貨幣 (Crypto)": [c for c in FULL_SYMBOLS_MAP.keys() if c.endswith("-USD")],
}

CATEGORY_HOT_OPTIONS = {}
for category, codes in CATEGORY_MAP.items():
    options = {}
    sorted_codes = sorted(codes)
    for code in sorted_codes:
        info = FULL_SYMBOLS_MAP.get(code)
        if info:
            options[f"{code} - {info['name']}"] = code
    CATEGORY_HOT_OPTIONS[category] = options

def get_symbol_from_query(query: str) -> str:
    query = query.strip().upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == code: return code
        if any(query == kw.upper() for kw in data["keywords"]): return code
    query_lower = query.strip().lower()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_lower == data["name"].lower(): return code
    if re.fullmatch(r'\d{4,6}', query.strip()) and ".TW" not in query:
        return f"{query.strip()}.TW"
    return query.strip()

@st.cache_data(ttl=300, show_spinner="正在從 Yahoo Finance 獲取最新市場數據...")
def get_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True, back_adjust=True)
        if df.empty: return pd.DataFrame()
        df.columns = [col.capitalize() for col in df.columns]
        df.index.name = 'Date'
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df[~df.index.duplicated(keep='first')]
        if len(df) > 1:
            df = df.iloc[:-1]
        return df.copy()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    info = FULL_SYMBOLS_MAP.get(symbol, {})
    if info:
        if symbol.endswith(".TW") or symbol.startswith("^TWII"): category, currency = "台股 (TW)", "TWD"
        elif symbol.endswith("-USD"): category, currency = "加密貨幣 (Crypto)", "USD"
        else: category, currency = "美股 (US)", "USD"
        return {"name": info['name'], "category": category, "currency": currency}
    try:
        ticker = yf.Ticker(symbol)
        yf_info = ticker.info
        name = yf_info.get('longName') or yf_info.get('shortName') or symbol
        currency = yf_info.get('currency') or "USD"
        return {"name": name, "category": "未分類", "currency": currency}
    except Exception:
        return {"name": symbol, "category": "未分類", "currency": "USD"}

@st.cache_data
def get_currency_symbol(symbol):
    currency_code = get_company_info(symbol).get('currency', 'USD')
    return 'NT$' if currency_code == 'TWD' else '$' if currency_code == 'USD' else currency_code + ' '

def calculate_technical_indicators(df):
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    macd = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    df['RSI_9'] = ta.momentum.rsi(df['Close'], window=9)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    df['ATR_14'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['ADX_14'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['CMF'] = ta.volume.chaikin_money_flow(df['High'], df['Low'], df['Close'], df['Volume'], window=20)
    df['MFI'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'], window=14)
    ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
    df['Ichimoku_A'] = ichimoku.ichimoku_a()
    df['Ichimoku_B'] = ichimoku.ichimoku_b()
    return df

# --- 修正同步: 側邊欄選擇熱門標的時，同步 text_input ---
def sync_text_input_from_selection():
    selected_category = st.session_state.category_selector
    selected_hot_key = st.session_state.hot_target_selector
    # hot_target_selector填的是顯示名, 要查 map
    symbol_code = CATEGORY_HOT_OPTIONS[selected_category][selected_hot_key]
    st.session_state.sidebar_search_input = symbol_code

def main():
    st.sidebar.markdown("<span style='color: #FA8072; font-weight: bold;'>🚀 AI 趨勢分析</span>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    category_keys = list(CATEGORY_HOT_OPTIONS.keys())
    selected_category = st.sidebar.selectbox(
        '資產類別',
        category_keys,
        index=0,
        key='category_selector'
    )
    hot_options_map = CATEGORY_HOT_OPTIONS[selected_category]
    hot_display_names = list(hot_options_map.keys())
    default_symbol = hot_display_names[0]

    st.sidebar.selectbox(
        '熱門標的',
        hot_display_names,
        index=0,
        key='hot_target_selector',
        on_change=sync_text_input_from_selection
    )

    # --- text_input同步 ---
    st.sidebar.text_input(
        "...或手動輸入代碼/名稱:",
        value=st.session_state.get('sidebar_search_input', hot_options_map[default_symbol]),
        key='sidebar_search_input'
    )

    st.sidebar.markdown("---")
    selected_period_key = st.sidebar.selectbox('週期', list(PERIOD_MAP.keys()), index=2)
    st.sidebar.markdown("---")
    if st.sidebar.button('📊 執行AI分析', use_container_width=True):
        st.session_state['run_analysis'] = True
        st.session_state['symbol_to_analyze'] = get_symbol_from_query(st.session_state.sidebar_search_input)
        st.session_state['period_key'] = selected_period_key

    if st.session_state.get('run_analysis', False):
        symbol = st.session_state['symbol_to_analyze']
        period_key = st.session_state['period_key']
        period, interval = PERIOD_MAP[period_key]
        with st.spinner(f"🔍 正在分析 {symbol} ..."):
            df_raw = get_stock_data(symbol, period, interval)
            if df_raw.empty or len(df_raw) < 60:
                st.error(f"❌ 數據不足或代碼無效：{symbol}。至少需要60個數據點。")
            else:
                info = get_company_info(symbol)
                df_tech = calculate_technical_indicators(df_raw.copy())
                price = df_raw['Close'].iloc[-1]
                prev_close = df_raw['Close'].iloc[-2] if len(df_raw) > 1 else price
                change, pct = price - prev_close, (price - prev_close) / prev_close * 100 if prev_close != 0 else 0
                currency_symbol = get_currency_symbol(symbol)
                pf = 4 if price < 100 and currency_symbol != 'NT$' else 2

                st.header(f"📈 {info['name']} ({symbol}) AI趨勢分析報告")
                st.markdown(f"**分析週期:** {period_key}")
                st.markdown("---")
                st.subheader("💡 價格資訊")
                c1, c2, c3 = st.columns(3)
                c1.metric("💰 當前價格", f"{currency_symbol}{price:.{pf}f}", f"{change:+.{pf}f} ({pct:+.2f}%)")
                # ...略，其餘分析流程與原版本一致...

if __name__ == "__main__":
    main()
