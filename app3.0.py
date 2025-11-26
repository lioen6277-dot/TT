# -*- coding: utf-8 -*-
"""
Orbital Command: Tactical Scan (O.C.T.S.) - V4.3 Terran Edition (優化版)
前身：AI 專業操盤策略系統
風格：StarCraft II Terran UI Theme

功能特色：
1. 繼承 V4.2 所有核心功能 (VRVP, Fib, EMA200)
2. 全面泰倫人族介面風格 (Terran Naming Convention)
3. 副官 (Adjutant) 風格的戰術報告
4. 【V4.3 升級】：部署座標 (Entry) 改為斐波那契 0.618 點位，止損邏輯強化。

開發者：SCV 工程協作單位
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# 1. 軌道司令部介面配置 (UI Configuration)
# ==============================================================================

st.set_page_config(
    page_title="Orbital Command (O.C.T.S.)",
    page_icon="🛰️", # 軌道掃描圖示
    layout="wide"
)

st.markdown("""
<style>
    /* 全局背景：深空灰 (Terran UI Base) */
    body, .stApp { background-color: #0E1117; color: #B0C4DE; font-family: 'Segoe UI', 'Noto Sans TC', sans-serif; }
    
    /* 側邊欄：工程灣風格 */
    [data-testid="stSidebar"] { background-color: #161A25; border-right: 1px solid #4A5568; }
    
    /* 戰術卡片容器 */
    .trade-card-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }
    
    /* 通用卡片：金屬質感 */
    .trade-card {
        background: linear-gradient(145deg, #1E222D, #232733);
        border-radius: 4px; /* Terran 喜歡方正硬朗的線條 */
        padding: 20px;
        flex: 1;
        min-width: 140px;
        text-align: center;
        border: 1px solid #3E4C59;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
    }
    
    /* 裝飾線條 (Tech Lines) */
    .trade-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 2px;
        background: rgba(255,255,255,0.1);
    }
    
    .card-title { font-size: 0.85em; color: #8FA3BF; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
    .card-value { font-size: 1.6em; font-weight: 700; color: #E2E8F0; font-family: 'Consolas', 'Roboto Mono', monospace; text-shadow: 0 0 5px rgba(255,255,255,0.1); }
    .card-sub { font-size: 0.75em; margin-top: 8px; opacity: 0.8; font-family: monospace; }

    /* --- 戰術光暈 (Tactical Glows) - 台灣操盤色系適配 --- */
    
    /* Deployment (Entry): 鮭魚粉 / 幽靈特務紅外線 */
    .glow-entry { border-bottom: 3px solid #FA8072; box-shadow: 0 0 15px rgba(250, 128, 114, 0.2); }
    .text-entry { color: #FA8072 !important; }

    /* Objective (TP): 紅色 / 興奮劑 (Stimpack) / 獲利爆發 */
    .glow-tp { border-bottom: 3px solid #DC3545; box-shadow: 0 0 15px rgba(220, 53, 69, 0.3); }
    .text-tp { color: #FF4B4B !important; }

    /* Abort (SL): 綠色 / 生物鋼裝甲 (Bio-Steel) / 防禦虧損 */
    .glow-sl { border-bottom: 3px solid #28A745; box-shadow: 0 0 15px rgba(40, 167, 69, 0.3); }
    .text-sl { color: #28A745 !important; }

    /* Intel (R:R): 藍色 / 副官全息圖 */
    .glow-rr { border-bottom: 3px solid #3498DB; box-shadow: 0 0 15px rgba(52, 152, 219, 0.3); }
    
    /* 狀態標籤 */
    .bullish-tag { background-color: rgba(220, 53, 69, 0.2); color: #FF6B6B; padding: 4px 10px; border: 1px solid #DC3545; font-family: monospace; letter-spacing: 1px; }
    .bearish-tag { background-color: rgba(40, 167, 69, 0.2); color: #5DD55D; padding: 4px 10px; border: 1px solid #28A745; font-family: monospace; letter-spacing: 1px; }
    .neutral-tag { background-color: rgba(128, 128, 128, 0.2); color: #A0A0A0; padding: 4px 10px; border: 1px solid #808080; font-family: monospace; letter-spacing: 1px; }

    /* 副官報告區塊 */
    .adjutant-log {
        background-color: #0d1117;
        border-left: 3px solid #3498DB;
        padding: 15px;
        font-family: 'Consolas', monospace;
        color: #cfd8dc;
        font-size: 0.9em;
    }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. 星區數據庫 (Sector Data Map)
# ==============================================================================

FULL_SYMBOLS_MAP = {
    # A. 美股
    "TSLA": {"name": "Tesla Motors", "keywords": ["TSLA"]}, "NVDA": {"name": "Nvidia Corp", "keywords": ["NVDA"]},
    "AAPL": {"name": "Apple Inc", "keywords": ["AAPL"]}, "AMD": {"name": "AMD Tech", "keywords": ["AMD"]},
    "MSFT": {"name": "Microsoft", "keywords": ["MSFT"]}, "GOOGL": {"name": "Alphabet", "keywords": ["GOOGL"]},
    "AMZN": {"name": "Amazon", "keywords": ["AMZN"]}, "META": {"name": "Meta Plat.", "keywords": ["META"]},
    "SPY": {"name": "S&P 500 ETF", "keywords": ["SPY"]}, "QQQ": {"name": "Nasdaq ETF", "keywords": ["QQQ"]},
    "TQQQ": {"name": "TQQQ (3x Bull)", "keywords": ["TQQQ"]}, "SOXL": {"name": "SOXL (3x Semi)", "keywords": ["SOXL"]},
    "MSTR": {"name": "MicroStrategy", "keywords": ["MSTR"]}, "COIN": {"name": "Coinbase", "keywords": ["COIN"]},
    
    # B. 台股
    "2330.TW": {"name": "TSMC (台積電)", "keywords": ["2330"]}, "2317.TW": {"name": "Foxconn (鴻海)", "keywords": ["2317"]},
    "2454.TW": {"name": "MediaTek (聯發科)", "keywords": ["2454"]}, "2382.TW": {"name": "Quanta (廣達)", "keywords": ["2382"]},
    "3231.TW": {"name": "Wistron (緯創)", "keywords": ["3231"]}, "2603.TW": {"name": "Evergreen (長榮)", "keywords": ["2603"]},
    "0050.TW": {"name": "Yuanta 50", "keywords": ["0050"]}, "^TWII": {"name": "TAIEX Index", "keywords": ["TWII"]},
    
    # C. 加密貨幣
    "BTC-USD": {"name": "Bitcoin Core", "keywords": ["BTC"]}, "ETH-USD": {"name": "Ethereum", "keywords": ["ETH"]},
    "SOL-USD": {"name": "Solana Chain", "keywords": ["SOL"]}, "BNB-USD": {"name": "Binance Coin", "keywords": ["BNB"]},
    "DOGE-USD": {"name": "Dogecoin", "keywords": ["DOGE"]}, "XRP-USD": {"name": "Ripple Protocol", "keywords": ["XRP"]},
}

CATEGORY_MAP = {
    "US Sector (美股)": [k for k in FULL_SYMBOLS_MAP if not k.endswith((".TW", "-USD")) and not k.startswith("^")],
    "TW Sector (台股)": [k for k in FULL_SYMBOLS_MAP if k.endswith(".TW") or k.startswith("^TWII")],
    "Crypto Sector (加密)": [k for k in FULL_SYMBOLS_MAP if k.endswith("-USD")]
}

PERIOD_MAP = {
    "Tactical (15m 短線)": ("1mo", "15m"),
    "Operational (1h 中線)": ("3mo", "60m"),
    "Strategic (4h 長線)": ("1y", "60m"),
    "Global (1d 日線)": ("2y", "1d")
}

# ==============================================================================
# 3. 戰術運算核心 (Strategy Engine)
# ==============================================================================

def get_symbol_name(symbol):
    return FULL_SYMBOLS_MAP.get(symbol, {}).get("name", symbol)

@st.cache_data(ttl=300)
def get_data(symbol, period, interval):
    """從 Yahoo Finance 下載數據"""
    try:
        ticker = yf.Ticker(symbol)
        # 確保數據包含 OHLCV
        df = ticker.history(period=period, interval=interval)
        if df.empty: return None
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = [c.capitalize() for c in df.columns]
        df = df[df['Volume'] > 0]
        return df
    except Exception: return None

def calculate_advanced_indicators(df):
    """計算所有技術指標"""
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    
    # 確保有足夠的數據點來計算 EMA_200
    if len(df) >= 200:
        df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    else:
        df['EMA_200'] = np.nan
    
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    
    # 移除計算指標過程中產生的 NaN 行，以保持數據整潔
    df.dropna(subset=['EMA_50', 'RSI', 'MACD_Hist'], inplace=True)
    return df

def get_volume_profile(df, bins=20):
    """計算成交量分佈 (Volume Profile)"""
    price_min = df['Low'].min()
    price_max = df['High'].max()
    price_range = price_max - price_min
    if price_range == 0: return None
    
    bin_size = price_range / bins
    profile = []
    
    for i in range(bins):
        bin_low = price_min + (i * bin_size)
        bin_high = bin_low + bin_size
        mask = (df['Close'] >= bin_low) & (df['Close'] < bin_high)
        vol_sum = df.loc[mask, 'Volume'].sum()
        profile.append({'price': (bin_low + bin_high)/2, 'volume': vol_sum})
        
    return pd.DataFrame(profile)

def find_fibonacci_levels(df, lookback=60):
    """尋找斐波那契回調/延伸點位"""
    lookback = min(lookback, len(df))
    recent_data = df.tail(lookback)
    high_price = recent_data['High'].max()
    low_price = recent_data['Low'].min()
    idx_high = recent_data['High'].idxmax()
    idx_low = recent_data['Low'].idxmin()
    # 判斷趨勢方向：高點在低點之後為上升趨勢 (UP)
    trend_direction = "UP" if idx_high > idx_low else "DOWN"
    
    levels = {}
    diff = high_price - low_price
    if diff == 0: return None
    
    if trend_direction == "UP":
        # 上升趨勢：回調 (Retracement) 從高點算起
        levels['0.0'] = high_price # Apex (頂點)
        levels['0.382'] = high_price - 0.382 * diff
        levels['0.5'] = high_price - 0.5 * diff
        levels['0.618'] = high_price - 0.618 * diff
        levels['0.786'] = high_price - 0.786 * diff
        levels['1.0'] = low_price  # Nadir (底點)
        levels['Ext_1.618'] = high_price + 0.618 * diff # 延伸目標
    else:
        # 下降趨勢：反彈 (Bounce) 從低點算起
        levels['0.0'] = low_price  # Nadir (底點)
        levels['0.382'] = low_price + 0.382 * diff
        levels['0.5'] = low_price + 0.5 * diff
        levels['0.618'] = low_price + 0.618 * diff
        levels['0.786'] = low_price + 0.786 * diff
        levels['1.0'] = high_price # Apex (頂點)
        levels['Ext_1.618'] = low_price - 0.618 * diff # 延伸目標

    return {
        'trend': trend_direction,
        'high': high_price,
        'low': low_price,
        'levels': levels
    }

def analyze_strategy(df, fib_data):
    """分析進場策略與威脅等級 (Threat Level)"""
    latest = df.iloc[-1]
    reasons = []
    
    # 趨勢評分：MACD, RSI, 價格 vs EMA50
    trend_score = 0
    if latest['MACD_Hist'] > 0: trend_score += 1; reasons.append("MACD 動能 (Kinetic Energy) 偏正")
    else: trend_score -= 1; reasons.append("MACD 動能 (Kinetic Energy) 偏負")
    
    if latest['RSI'] > 50: trend_score += 1; reasons.append("RSI 處於中線之上 (Strength)")
    else: trend_score -= 1; reasons.append("RSI 處於中線之下 (Weakness)")
        
    # 價格與 EMA_50 比較 (中線趨勢)
    if latest['Close'] > latest['EMA_50']: trend_score += 1; reasons.append("價格保持在 50 期趨勢線之上")
    else: trend_score -= 1; reasons.append("價格跌破 50 期趨勢線")

    # 結構 (Structure) 檢查：價格是否在 0.5 - 0.786 區間 (PZR Zone)
    price = latest['Close']
    in_entry_zone = False
    
    # 價格進入潛在進場/反轉區 (Potential Reversal Zone - PZR)
    if fib_data['trend'] == "UP":
        if fib_data['levels']['0.786'] <= price <= fib_data['levels']['0.5']:
            in_entry_zone = True
            reasons.append("價格進入 0.5 - 0.786 戰術支撐區 (PZR)")
    else:
        if fib_data['levels']['0.5'] <= price <= fib_data['levels']['0.786']:
            in_entry_zone = True
            reasons.append("價格進入 0.5 - 0.786 戰術壓力區 (PZR)")
            
    # 成交量驗證
    if latest['Volume'] > latest['Vol_SMA']:
        reasons.append("成交量訊號 (Volume) 增強")
    
    action = "Neutral (觀望)"
    sentiment_color = "neutral"
    
    # 部署建議 (Deployment Recommendation)
    if trend_score >= 1 and in_entry_zone and fib_data['trend'] == "UP":
        action = "Nuclear Launch Detected (部署多頭)"
        sentiment_color = "bullish"
    elif trend_score <= -1 and in_entry_zone and fib_data['trend'] == "DOWN":
        action = "Zerg Rush Detected (部署空頭)"
        sentiment_color = "bearish"
    elif abs(trend_score) >= 2:
        action = "Hold Position (順勢持有)"
        sentiment_color = "bullish" if trend_score > 0 else "bearish"
        
    return {'action': action, 'reasons': reasons, 'trend_score': trend_score, 'sentiment': sentiment_color, 'in_zone': in_entry_zone}

def calculate_trade_setup(df, fib_data, action):
    """計算前瞻交易設定 (Entry, SL, TP)"""
    current_price = df.iloc[-1]['Close']
    atr = df.iloc[-1]['ATR']
    setup = {'entry': current_price, 'sl': 0, 'tp1': 0, 'tp2': 0, 'rr': 0, 'valid': False}
    
    # 決定部署價格 (Theoretical Entry: 0.618 level)
    deployment_price = fib_data['levels']['0.618']

    risk = 0
    reward = 0
    
    if "多頭" in action or ("持有" in action and fib_data['trend'] == "UP"):
        # 1. 部署價格：0.618 支撐
        setup['entry'] = deployment_price
        
        # 2. 撤離閾值 (SL)：低於結構低點 (1.0 Level/Nadir) + 1.5 ATR 緩衝
        setup['sl'] = fib_data['levels']['1.0'] - (atr * 1.5) 
        
        # 3. 戰略目標 (TP)：延伸 1.618
        setup['tp2'] = fib_data['levels']['Ext_1.618']
        
        # 4. R:R 計算
        risk = deployment_price - setup['sl']
        reward = setup['tp2'] - deployment_price
        
    elif "空頭" in action or ("持有" in action and fib_data['trend'] == "DOWN"):
        # 1. 部署價格：0.618 壓力
        setup['entry'] = deployment_price
        
        # 2. 撤離閾值 (SL)：高於結構高點 (1.0 Level/Apex) + 1.5 ATR 緩衝
        setup['sl'] = fib_data['levels']['1.0'] + (atr * 1.5)
        
        # 3. 戰略目標 (TP)：延伸 1.618
        setup['tp2'] = fib_data['levels']['Ext_1.618']
        
        # 4. R:R 計算
        risk = setup['sl'] - deployment_price
        reward = deployment_price - setup['tp2']
        
    else:
        # 觀望時，Entry 仍顯示當前價格作為參考
        setup['entry'] = current_price
        return setup

    if risk > 0:
        setup['rr'] = reward / risk
        setup['valid'] = True
    return setup

# ==============================================================================
# 4. 戰術視圖 (Tactical View)
# ==============================================================================

def plot_pro_chart(df, fib_data, symbol_name, vp_data):
    """繪製專業級戰術分析圖"""
    fig = make_subplots(rows=2, cols=2, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3],
                        column_widths=[0.85, 0.15],
                        horizontal_spacing=0.02,
                        specs=[[{}, {}], [{"colspan": 2}, None]],
                        subplot_titles=(f"{symbol_name} :: Sector Scan", "", "MACD Kinetic Energy"))

    # 1. K線圖
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Unit Price'), row=1, col=1)
    
    # EMA 趨勢線
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='Trend Line (50)'), row=1, col=1)
    if 'EMA_200' in df.columns and not df['EMA_200'].isna().all():
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='purple', width=1, dash='dash'), name='Macro Line (200)'), row=1, col=1)
    
    # 斐波那契戰術標記
    colors = ['gray', 'skyblue', 'yellow', 'salmon', 'red', 'gray', '#00FF00']
    fib_levels = [
        ('Apex/Nadir (1.0)', fib_data['levels']['1.0'], colors[5]), # 結構起點 (Nadir/Apex)
        ('Fib 0.786 (Crit)', fib_data['levels']['0.786'], colors[4]), # 關鍵回調/反彈
        ('Fib 0.618 (Tac)', fib_data['levels']['0.618'], colors[3]), # 戰術部署點
        ('Fib 0.500 (PZR)', fib_data['levels']['0.5'], colors[2]),
        ('Fib 0.382', fib_data['levels']['0.382'], colors[1]),
        ('Apex/Nadir (0.0)', fib_data['levels']['0.0'], colors[0]), # 結構終點 (Apex/Nadir)
        ('Obj Alpha (1.618)', fib_data['levels']['Ext_1.618'], colors[6]) # 延伸目標
    ]
    
    start_date = df.index[0]
    end_date = df.index[-1]
    
    for label, value, color in fib_levels:
        fig.add_shape(type="line", x0=start_date, y0=value, x1=end_date, y1=value,
                      line=dict(color=color, width=1, dash="dot"), row=1, col=1)
        fig.add_annotation(x=end_date, y=value, text=f"{label}",
                           showarrow=False, xanchor="left", font=dict(color=color, size=9), row=1, col=1)

    # 2. Volume Signature (VRVP) 成交量分佈
    if vp_data is not None:
        max_vol = vp_data['volume'].max()
        # 尋找交易量最大點 (POC - Point of Control)
        poc_price = vp_data.loc[vp_data['volume'].idxmax(), 'price']
        
        fig.add_trace(go.Bar(
            y=vp_data['price'], 
            x=vp_data['volume'], 
            orientation='h',
            marker=dict(color=vp_data['volume'], colorscale='Electric', opacity=0.5),
            name='Density',
            showlegend=False
        ), row=1, col=2)
        
        # 標記 POC
        fig.add_shape(type="line", x0=0, x1=max_vol, y0=poc_price, y1=poc_price,
                      line=dict(color="white", width=1), row=1, col=2)

    # 3. MACD 動能
    colors_macd = np.where(df['MACD_Hist'] > 0, '#DC3545', '#28A745')
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_macd, name='Histogram'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='#FAFAFA', width=1), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FFA500', width=1), name='Signal'), row=2, col=1)

    # Terran Dark Theme UI 配置
    fig.update_layout(template="plotly_dark", height=750, margin=dict(l=10, r=10, t=40, b=10),
                      paper_bgcolor='#0E1117', plot_bgcolor='#161A25')
    # 隱藏右側成交量分佈圖的軸標籤
    fig.update_xaxes(showticklabels=False, row=1, col=2)
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    
    return fig

# ==============================================================================
# 5. 指揮中心主程序 (Command Center Main)
# ==============================================================================

def main():
    st.sidebar.header("🛰️ ComSat Station Controls")
    
    cat = st.sidebar.selectbox("1. Sector Selector (星區)", list(CATEGORY_MAP.keys()))
    symbols = CATEGORY_MAP[cat]
    display_symbols = [f"{s} - {FULL_SYMBOLS_MAP[s]['name']}" for s in symbols]
    selected_display = st.sidebar.selectbox("2. Target Designator (目標)", display_symbols)
    symbol = selected_display.split(" - ")[0]
    
    p_label = st.sidebar.selectbox("3. Temporal Frame (時序)", list(PERIOD_MAP.keys()), index=2)
    period, interval = PERIOD_MAP[p_label]
    
    st.sidebar.markdown("---")
    fib_lookback = st.sidebar.slider("📡 Scan Sensitivity (掃描靈敏度)", 
                                     min_value=30, max_value=200, value=100, step=10,
                                     help="調整掃描儀的波段回溯範圍")
    
    run_btn = st.sidebar.button("☢️ Initiate Scanner Sweep", type="primary")

    if run_btn:
        with st.spinner(f"📡 Establishing Uplink to {symbol}... Downloading Telemetry..."):
            df = get_data(symbol, period, interval)
            
            if df is not None and len(df) > fib_lookback:
                df = calculate_advanced_indicators(df)
                fib_data = find_fibonacci_levels(df, lookback=fib_lookback)
                
                if fib_data is None:
                    st.error("Signal Lost: Cannot identify structure. Adjust Sensitivity.")
                    return

                analysis = analyze_strategy(df, fib_data)
                setup = calculate_trade_setup(df, fib_data, analysis['action'])
                vp_data = get_volume_profile(df)
                
                # --- UI ---
                curr_price = df.iloc[-1]['Close']
                price_chg = curr_price - df.iloc[-2]['Close']
                chg_color = "#DC3545" if price_chg > 0 else "#28A745"
                
                st.markdown(f"## {get_symbol_name(symbol)} ({symbol}) :: {p_label}")
                # 顯示當前價格與變化
                st.markdown(f"<h3 style='color:{chg_color}'>${curr_price:,.2f} <small>({price_chg:+.2f})</small></h3>", unsafe_allow_html=True)
                
                # 戰術卡片
                if setup['valid']:
                    st.markdown(f"""
                    <div class="trade-card-container">
                        <div class="trade-card glow-entry">
                            <div class="card-title">Deployment Coords</div>
                            <div class="card-value text-entry">${setup['entry']:,.2f}</div>
                            <div class="card-sub">Tactical 0.618 Entry</div>
                        </div>
                        <div class="trade-card glow-tp">
                            <div class="card-title">Objective Alpha</div>
                            <div class="card-value text-tp">${setup['tp2']:,.2f}</div>
                            <div class="card-sub">Stimpack Limit (1.618)</div>
                        </div>
                        <div class="trade-card glow-sl">
                            <div class="card-title">Abort Threshold</div>
                            <div class="card-value text-sl">${setup['sl']:,.2f}</div>
                            <div class="card-sub">Structure Defense (-1.5 ATR)</div>
                        </div>
                        <div class="trade-card glow-rr">
                            <div class="card-title">Intel Ratio (R:R)</div>
                            <div class="card-value">{setup['rr']:.2f}</div>
                            <div class="card-sub">Efficiency > 2.0</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("⚠️ Protocol Idle: Conditions not met for efficient deployment.")
                    
                col_chart, col_desc = st.columns([2.2, 0.8])
                
                with col_chart:
                    fig = plot_pro_chart(df, fib_data, get_symbol_name(symbol), vp_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_desc:
                    st.markdown("### 🤖 Adjutant Tactical Readout")
                    
                    tag_class = "bullish-tag" if analysis['sentiment'] == "bullish" else "bearish-tag" if analysis['sentiment'] == "bearish" else "neutral-tag"
                    st.markdown(f"**Threat Level:** <span class='{tag_class}'>{analysis['action']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("""<div class="adjutant-log">""", unsafe_allow_html=True)
                    st.markdown(f"> **Trend Vector**: {fib_data['trend']}")
                    st.markdown(f"> **Apex Point**: {fib_data['high']:.2f}")
                    st.markdown(f"> **Nadir Point**: {fib_data['low']:.2f}")
                    st.markdown(f"> **0.618 Tac Entry**: {fib_data['levels']['0.618']:.2f}")
                    
                    st.markdown("---")
                    st.markdown("**> Signal Confirmation:**")
                    for r in analysis['reasons']:
                        st.markdown(f"✅ {r}")
                    
                    if analysis['in_zone']:
                        st.markdown("**>>> ALERT: Target in PZR Zone <<<**")
                    else:
                        st.markdown(">>> STATUS: Awaiting Trajectory <<<")
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.error("Telemetry Error: Insufficient data points. Requires more historical data.")
    else:
        st.info("👋 Awaiting Orders. Click **『☢️ Initiate Scanner Sweep』** to begin.")
        st.markdown("""
        #### System Upgrade (V4.3 - Optimized):
        - 🛰️ **O.C.T.S. Online**: 軌道司令部戰術介面已上線。
        - 🎯 **Tactical Coords**: 部署座標 (Entry) 現已鎖定 0.618 最佳集結點。
        - 🛡️ **Structural SL**: 撤離閾值 (SL) 強化為結構低點 + ATR 緩衝，更加堅固。
        """)

if __name__ == "__main__":
    main()
