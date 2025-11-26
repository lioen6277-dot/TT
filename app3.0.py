# -*- coding: utf-8 -*-
"""
AI 專業操盤策略系統 (Pro Trader Strategy Framework) - V4.0 Fusion
融合 RSI, MACD, 斐波那契與進階驗證架構
特別針對台灣操盤習慣與視覺進行優化 (TP=紅, SL=綠)

開發者：AI 協作 (基於 User 提供的策略框架)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# ==============================================================================
# 1. 頁面配置與 CSS 視覺優化 (UI Glow Effects)
# ==============================================================================

st.set_page_config(
    page_title="AI 專業操盤策略室",
    page_icon="🦅",
    layout="wide"
)

# 定義 CSS 樣式：包含光暈效果與自定義卡片
st.markdown("""
<style>
    /* 全局背景與字體 */
    body, .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Noto Sans TC', sans-serif; }
    
    /* 側邊欄優化 */
    [data-testid="stSidebar"] { background-color: #161A25; border-right: 1px solid #333; }
    
    /* 關鍵指標卡片容器 */
    .trade-card-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    /* 通用卡片樣式 */
    .trade-card {
        background-color: #1E222D;
        border-radius: 10px;
        padding: 20px;
        flex: 1;
        text-align: center;
        border: 1px solid #333;
        transition: transform 0.2s;
    }
    
    .trade-card:hover {
        transform: translateY(-5px);
    }

    .card-title { font-size: 0.9em; color: #A0A0A0; margin-bottom: 5px; }
    .card-value { font-size: 1.6em; font-weight: 700; color: #FFFFFF; }
    .card-sub { font-size: 0.8em; margin-top: 5px; opacity: 0.8; }

    /* --- 光暈特效 (Glow Effects) --- */
    
    /* 1. 進場價 (鮭魚粉) */
    .glow-entry {
        border-bottom: 3px solid #FA8072;
        box-shadow: 0 8px 20px -5px rgba(250, 128, 114, 0.4);
    }
    .text-entry { color: #FA8072 !important; }

    /* 2. 止盈 (紅色 - 台灣多頭/獲利色) */
    .glow-tp {
        border-bottom: 3px solid #DC3545;
        box-shadow: 0 8px 20px -5px rgba(220, 53, 69, 0.4);
    }
    .text-tp { color: #FF4B4B !important; }

    /* 3. 止損 (綠色 - 台灣空頭/虧損色) */
    .glow-sl {
        border-bottom: 3px solid #28A745;
        box-shadow: 0 8px 20px -5px rgba(40, 167, 69, 0.4);
    }
    .text-sl { color: #28A745 !important; }

    /* 4. 風險回報比 (藍色/中性) */
    .glow-rr {
        border-bottom: 3px solid #3498DB;
        box-shadow: 0 8px 20px -5px rgba(52, 152, 219, 0.4);
    }
    
    /* 策略總結區塊 */
    .strategy-box {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #FA8072;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
        line-height: 1.6;
    }
    
    .bullish-tag { background-color: rgba(220, 53, 69, 0.2); color: #FF4B4B; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; border: 1px solid #DC3545; }
    .bearish-tag { background-color: rgba(40, 167, 69, 0.2); color: #28A745; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; border: 1px solid #28A745; }
    .neutral-tag { background-color: rgba(128, 128, 128, 0.2); color: #A0A0A0; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; border: 1px solid #808080; }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. 全域設定與資料映射 (融合 App 2.0 的豐富資產庫)
# ==============================================================================

FULL_SYMBOLS_MAP = {
    # A. 美股
    "TSLA": {"name": "特斯拉", "keywords": ["TSLA"]}, "NVDA": {"name": "輝達", "keywords": ["NVDA"]},
    "AAPL": {"name": "蘋果", "keywords": ["AAPL"]}, "AMD": {"name": "超微", "keywords": ["AMD"]},
    "MSFT": {"name": "微軟", "keywords": ["MSFT"]}, "GOOGL": {"name": "谷歌", "keywords": ["GOOGL"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["AMZN"]}, "META": {"name": "Meta", "keywords": ["META"]},
    "SPY": {"name": "S&P 500 ETF", "keywords": ["SPY"]}, "QQQ": {"name": "納斯達克 ETF", "keywords": ["QQQ"]},
    "TQQQ": {"name": "三倍做多納指", "keywords": ["TQQQ"]}, "SOXL": {"name": "三倍做多半導體", "keywords": ["SOXL"]},
    "COIN": {"name": "Coinbase", "keywords": ["COIN"]}, "MSTR": {"name": "MicroStrategy", "keywords": ["MSTR"]},
    
    # B. 台股
    "2330.TW": {"name": "台積電", "keywords": ["2330"]}, "2317.TW": {"name": "鴻海", "keywords": ["2317"]},
    "2454.TW": {"name": "聯發科", "keywords": ["2454"]}, "2382.TW": {"name": "廣達", "keywords": ["2382"]},
    "3231.TW": {"name": "緯創", "keywords": ["3231"]}, "2603.TW": {"name": "長榮", "keywords": ["2603"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["0050"]}, "^TWII": {"name": "加權指數", "keywords": ["TWII"]},
    
    # C. 加密貨幣
    "BTC-USD": {"name": "比特幣", "keywords": ["BTC"]}, "ETH-USD": {"name": "以太坊", "keywords": ["ETH"]},
    "SOL-USD": {"name": "Solana", "keywords": ["SOL"]}, "BNB-USD": {"name": "幣安幣", "keywords": ["BNB"]},
    "DOGE-USD": {"name": "狗狗幣", "keywords": ["DOGE"]}, "XRP-USD": {"name": "瑞波幣", "keywords": ["XRP"]},
}

CATEGORY_MAP = {
    "美股 (US)": [k for k in FULL_SYMBOLS_MAP if not k.endswith((".TW", "-USD")) and not k.startswith("^")],
    "台股 (TW)": [k for k in FULL_SYMBOLS_MAP if k.endswith(".TW") or k.startswith("^TWII")],
    "加密貨幣 (Crypto)": [k for k in FULL_SYMBOLS_MAP if k.endswith("-USD")]
}

# 週期設定
PERIOD_MAP = {
    "短線 (15分)": ("1mo", "15m"),
    "中線 (1小時)": ("3mo", "60m"),
    "中長線 (4小時)": ("1y", "60m"), # yfinance 不支援直接 4h, 需用 60m 合成或只抓 60m
    "長線 (日線)": ("2y", "1d")
}

# ==============================================================================
# 3. 核心功能與指標計算 (Strategy Engine)
# ==============================================================================

def get_symbol_name(symbol):
    return FULL_SYMBOLS_MAP.get(symbol, {}).get("name", symbol)

@st.cache_data(ttl=300)
def get_data(symbol, period, interval):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        if df.empty: return None
        # 簡單資料清洗
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = [c.capitalize() for c in df.columns]
        return df
    except Exception: return None

def calculate_advanced_indicators(df):
    """計算策略所需的核心指標：EMA, RSI, MACD, ATR"""
    # 1. 趨勢 EMA (10, 50, 200)
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    
    # 2. 動能 RSI (14) - 策略建議中軸判斷
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # 3. MACD (12, 26, 9) - 策略核心
    macd = ta.trend.MACD(df['Close'])
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    # 4. 風控 ATR (14) - 用於計算緩衝
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    # 5. 成交量 SMA (用於判斷量能是否放大)
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    
    df.dropna(inplace=True)
    return df

def find_fibonacci_levels(df, lookback=50):
    """
    自動尋找最近的 Swing High 與 Swing Low 來繪製斐波那契
    """
    # 取最近 lookback 根 K 線
    recent_data = df.tail(lookback)
    
    high_price = recent_data['High'].max()
    low_price = recent_data['Low'].min()
    
    # 判斷最近是 漲勢 (Low -> High) 還是 跌勢 (High -> Low)
    # 簡單邏輯：看最高點和最低點哪個發生得比較晚
    idx_high = recent_data['High'].idxmax()
    idx_low = recent_data['Low'].idxmin()
    
    trend_direction = "UP" if idx_high > idx_low else "DOWN"
    
    levels = {}
    diff = high_price - low_price
    
    if trend_direction == "UP":
        # 上升趨勢的回調 (Retracement 向下找支撐)
        levels['0.0'] = high_price
        levels['0.236'] = high_price - 0.236 * diff
        levels['0.382'] = high_price - 0.382 * diff
        levels['0.5'] = high_price - 0.5 * diff
        levels['0.618'] = high_price - 0.618 * diff # 重點進場區
        levels['0.786'] = high_price - 0.786 * diff # 深層回撤/止損參考
        levels['1.0'] = low_price
        # 擴展 (Extension) 用於止盈
        levels['Ext_1.272'] = high_price + 0.272 * diff
        levels['Ext_1.618'] = high_price + 0.618 * diff
        levels['Ext_2.0'] = high_price + 1.0 * diff
        
        # 關鍵進場區間
        entry_zone_high = levels['0.5']
        entry_zone_low = levels['0.786']
        
    else:
        # 下跌趨勢的反彈 (Retracement 向上找阻力)
        levels['0.0'] = low_price
        levels['0.236'] = low_price + 0.236 * diff
        levels['0.382'] = low_price + 0.382 * diff
        levels['0.5'] = low_price + 0.5 * diff
        levels['0.618'] = low_price + 0.618 * diff
        levels['0.786'] = low_price + 0.786 * diff
        levels['1.0'] = high_price
        # 擴展
        levels['Ext_1.272'] = low_price - 0.272 * diff
        levels['Ext_1.618'] = low_price - 0.618 * diff
        levels['Ext_2.0'] = low_price - 1.0 * diff
        
        entry_zone_high = levels['0.786']
        entry_zone_low = levels['0.5']

    return {
        'trend': trend_direction,
        'high': high_price,
        'low': low_price,
        'levels': levels,
        'entry_zone': (entry_zone_low, entry_zone_high)
    }

def analyze_strategy(df, fib_data):
    """
    執行策略總體理念：趨勢 -> 結構 -> 驗證
    """
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    reasons = []
    
    # 1. 趨勢判斷 (RSI & MACD)
    trend_score = 0
    # MACD 判斷
    if latest['MACD_Hist'] > 0 and latest['MACD_Line'] > latest['MACD_Signal']:
        trend_score += 1
        reasons.append("MACD 柱狀體位於零軸上方且發散 (多頭動能)。")
    elif latest['MACD_Hist'] < 0:
        trend_score -= 1
        reasons.append("MACD 柱狀體位於零軸下方 (空頭動能)。")
        
    # RSI 判斷 (50 中軸)
    if latest['RSI'] > 50:
        trend_score += 1
        reasons.append(f"RSI ({latest['RSI']:.1f}) 位於 50 上方，多頭優勢。")
    else:
        trend_score -= 1
        reasons.append(f"RSI ({latest['RSI']:.1f}) 位於 50 下方，空頭優勢。")
        
    # EMA 判斷
    if latest['Close'] > latest['EMA_50']:
        trend_score += 1
    else:
        trend_score -= 1

    # 2. 結構判斷 (斐波那契位置)
    structure_signal = "中性"
    price = latest['Close']
    fib = fib_data
    
    in_entry_zone = False
    
    if fib['trend'] == "UP":
        # 價格回落到 0.618 附近是買點
        if fib['levels']['0.786'] <= price <= fib['levels']['0.5']:
            structure_signal = "多頭回調結構 (Buy Zone)"
            in_entry_zone = True
            score += 2
            reasons.append("價格進入斐波那契 0.5 - 0.786 潛在反轉區 (PZR)。")
    else:
        # 價格反彈到 0.618 附近是賣點
        if fib['levels']['0.5'] <= price <= fib['levels']['0.786']:
            structure_signal = "空頭反彈結構 (Sell Zone)"
            in_entry_zone = True
            score -= 2
            reasons.append("價格進入斐波那契 0.5 - 0.786 潛在反轉區 (PZR)。")
            
    # 3. 進階驗證 (量能與K線) - 簡化版
    validation = False
    if latest['Volume'] > latest['Vol_SMA']:
        validation = True
        reasons.append("成交量放大，確認市場參與度。")
    
    # 綜合建議
    action = "觀望 (Neutral)"
    sentiment_color = "neutral"
    
    if trend_score > 0 and in_entry_zone and fib['trend'] == "UP":
        action = "做多 (Long)"
        sentiment_color = "bullish"
    elif trend_score < 0 and in_entry_zone and fib['trend'] == "DOWN":
        action = "做空 (Short)"
        sentiment_color = "bearish"
    elif trend_score > 2: # 強力趨勢中，可能不會回調太深
        action = "順勢持有 (Trend Following)"
        sentiment_color = "bullish"
    elif trend_score < -2:
        action = "順勢持有 (Trend Following)"
        sentiment_color = "bearish"
        
    return {
        'action': action,
        'reasons': reasons,
        'trend_score': trend_score,
        'sentiment': sentiment_color,
        'in_zone': in_entry_zone
    }

def calculate_trade_setup(df, fib_data, action, atr_multiplier=2.0):
    """計算 TP/SL 與 R:R"""
    current_price = df.iloc[-1]['Close']
    atr = df.iloc[-1]['ATR']
    
    setup = {
        'entry': current_price,
        'sl': 0,
        'tp1': 0,
        'tp2': 0,
        'rr': 0,
        'valid': False
    }
    
    if "做多" in action or ("持有" in action and fib_data['trend'] == "UP"):
        # 做多邏輯
        # 止損：結構低點 (Swing Low) 減去 ATR 緩衝，或是 Fib 0.786 下方
        sl_structural = fib_data['low'] - (atr * 0.5)
        sl_fib = fib_data['levels']['0.786'] - (atr * 1.0)
        setup['sl'] = min(sl_structural, sl_fib) # 取較保守的
        
        # 止盈：斐波那契擴展
        setup['tp1'] = fib_data['levels']['1.0'] # 前高
        setup['tp2'] = fib_data['levels']['Ext_1.618'] # 強力目標
        
        risk = current_price - setup['sl']
        reward = setup['tp2'] - current_price
        
    elif "做空" in action or ("持有" in action and fib_data['trend'] == "DOWN"):
        # 做空邏輯
        sl_structural = fib_data['high'] + (atr * 0.5)
        sl_fib = fib_data['levels']['0.786'] + (atr * 1.0)
        setup['sl'] = max(sl_structural, sl_fib)
        
        setup['tp1'] = fib_data['levels']['1.0'] # 前低
        setup['tp2'] = fib_data['levels']['Ext_1.618']
        
        risk = setup['sl'] - current_price
        reward = current_price - setup['tp2']
        
    else:
        return setup

    if risk > 0:
        setup['rr'] = reward / risk
        setup['valid'] = True
        
    return setup

# ==============================================================================
# 4. 圖表繪製
# ==============================================================================

def plot_pro_chart(df, fib_data, symbol_name):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3],
                        subplot_titles=(f"{symbol_name} 價格與斐波那契結構", "MACD 動能震盪"))

    # K線圖
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    
    # EMA
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA 50'), row=1, col=1)
    
    # 斐波那契線 (只畫在最近區間向右延伸)
    colors = ['gray', 'gray', 'gray', 'yellow', 'salmon', 'red', 'gray'] # 對應 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1
    fib_levels = [
        ('0.0', fib_data['levels']['0.0'], 'gray'),
        ('0.382', fib_data['levels']['0.382'], 'skyblue'),
        ('0.5', fib_data['levels']['0.5'], 'yellow'),
        ('0.618', fib_data['levels']['0.618'], 'salmon'), # 重點
        ('0.786', fib_data['levels']['0.786'], 'red'),
        ('1.0', fib_data['levels']['1.0'], 'gray'),
        ('TP2 (1.618)', fib_data['levels']['Ext_1.618'], '#00FF00')
    ]
    
    # 取最後 50 根畫線，避免整張圖都是線
    start_date = df.index[-50]
    end_date = df.index[-1]
    
    for label, value, color in fib_levels:
        fig.add_shape(type="line", x0=start_date, y0=value, x1=end_date, y1=value,
                      line=dict(color=color, width=1, dash="dot" if "TP" in label else "solid"), row=1, col=1)
        fig.add_annotation(x=end_date, y=value, text=f"{label}: {value:.2f}",
                           showarrow=False, xanchor="left", font=dict(color=color, size=10), row=1, col=1)

    # MACD
    colors_macd = np.where(df['MACD_Hist'] > 0, '#DC3545', '#28A745') # 紅漲綠跌 (台灣邏輯)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_macd, name='MACD Hist'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='#FAFAFA', width=1), name='MACD Line'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FFA500', width=1), name='Signal'), row=2, col=1)

    fig.update_layout(template="plotly_dark", height=700, margin=dict(l=10, r=10, t=30, b=10))
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])]) # 隱藏週末
    
    return fig

# ==============================================================================
# 5. 主程式
# ==============================================================================

def main():
    # --- Sidebar ---
    st.sidebar.header("🦅 操盤控制台")
    
    # 1. 資產選擇
    cat = st.sidebar.selectbox("1. 市場類別", list(CATEGORY_MAP.keys()))
    symbols = CATEGORY_MAP[cat]
    display_symbols = [f"{s} - {FULL_SYMBOLS_MAP[s]['name']}" for s in symbols]
    selected_display = st.sidebar.selectbox("2. 選擇標的", display_symbols)
    symbol = selected_display.split(" - ")[0]
    
    # 2. 週期選擇
    p_label = st.sidebar.selectbox("3. 時間架構", list(PERIOD_MAP.keys()), index=2)
    period, interval = PERIOD_MAP[p_label]
    
    # 3. 執行按鈕
    run_btn = st.sidebar.button("🚀 執行策略分析", type="primary")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 策略參數說明")
    st.sidebar.info("""
    **核心理念：**
    1. **趨勢 (MACD/EMA)**：確認大方向。
    2. **結構 (Fibonacci)**：回調至 0.618 黃金位進場。
    3. **風控 (ATR)**：動態止損，盈虧比需 > 2。
    
    **色系說明 (台股習慣)：**
    - 🔴 **紅色/粉色**：多頭、獲利、支撐
    - 🟢 **綠色**：空頭、虧損、壓力
    """)

    # --- Main Content ---
    if run_btn:
        with st.spinner(f"正在連線交易所獲取 {symbol} 數據並計算斐波那契結構..."):
            df = get_data(symbol, period, interval)
            
            if df is not None and len(df) > 50:
                # 計算指標
                df = calculate_advanced_indicators(df)
                # 計算結構
                fib_data = find_fibonacci_levels(df)
                # 策略分析
                analysis = analyze_strategy(df, fib_data)
                # 交易設置
                setup = calculate_trade_setup(df, fib_data, analysis['action'])
                
                # --- 顯示區塊 ---
                
                # Header
                curr_price = df.iloc[-1]['Close']
                price_chg = curr_price - df.iloc[-2]['Close']
                chg_color = "#DC3545" if price_chg > 0 else "#28A745" # 紅漲綠跌
                
                st.markdown(f"## {get_symbol_name(symbol)} ({symbol}) - {p_label} 結構分析")
                st.markdown(f"<h3 style='color:{chg_color}'>${curr_price:,.2f} <small>({price_chg:+.2f})</small></h3>", unsafe_allow_html=True)
                
                # 光暈卡片區 (Glow Cards)
                if setup['valid']:
                    st.markdown(f"""
                    <div class="trade-card-container">
                        <div class="trade-card glow-entry">
                            <div class="card-title">建議進場 (Entry)</div>
                            <div class="card-value text-entry">${setup['entry']:,.2f}</div>
                            <div class="card-sub">Fib 結構支撐區</div>
                        </div>
                        <div class="trade-card glow-tp">
                            <div class="card-title">目標止盈 (TP2)</div>
                            <div class="card-value text-tp">${setup['tp2']:,.2f}</div>
                            <div class="card-sub">Fib 1.618 擴展</div>
                        </div>
                        <div class="trade-card glow-sl">
                            <div class="card-title">結構止損 (SL)</div>
                            <div class="card-value text-sl">${setup['sl']:,.2f}</div>
                            <div class="card-sub">前低/高 + ATR</div>
                        </div>
                        <div class="trade-card glow-rr">
                            <div class="card-title">盈虧比 (R:R)</div>
                            <div class="card-value">{setup['rr']:.2f}</div>
                            <div class="card-sub">目標 > 2.0</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 目前市場結構尚未滿足高盈虧比 (R:R > 0) 的進場條件，建議觀望等待結構成型。")

                # 策略詳細分析與圖表
                col_chart, col_desc = st.columns([2, 1])
                
                with col_chart:
                    fig = plot_pro_chart(df, fib_data, get_symbol_name(symbol))
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_desc:
                    st.markdown("### 🦅 專業操盤手觀點")
                    
                    # 趨勢標籤
                    trend_tag = "bullish-tag" if analysis['trend_score'] > 0 else ("bearish-tag" if analysis['trend_score'] < 0 else "neutral-tag")
                    trend_text = "多頭趨勢" if analysis['trend_score'] > 0 else ("空頭趨勢" if analysis['trend_score'] < 0 else "震盪整理")
                    st.markdown(f"**趨勢定性：** <span class='{trend_tag}'>{trend_text}</span>", unsafe_allow_html=True)
                    
                    st.markdown("#### 1. 指標共振 (Confluence)")
                    for r in analysis['reasons']:
                        st.markdown(f"- {r}")
                        
                    st.markdown("#### 2. 斐波那契結構")
                    st.markdown(f"- **當前波段：** {fib_data['trend']} ({fib_data['low']:.2f} -> {fib_data['high']:.2f})")
                    st.markdown(f"- **0.618 重點位：** {fib_data['levels']['0.618']:.2f}")
                    
                    if analysis['in_zone']:
                        st.success("✅ 價格進入結構性反轉區 (PZR)，密切關注 K 線反轉訊號！")
                    else:
                        st.info("ℹ️ 等待價格回調至關鍵斐波那契區域。")
                        
                    st.markdown("#### 3. 最終操作建議")
                    if "做多" in analysis['action']:
                         st.markdown(f"<div style='background:#3d1818; padding:10px; border-radius:5px; border-left:4px solid #DC3545;'>🔥 <b>{analysis['action']}</b></div>", unsafe_allow_html=True)
                    elif "做空" in analysis['action']:
                         st.markdown(f"<div style='background:#183d20; padding:10px; border-radius:5px; border-left:4px solid #28A745;'>📉 <b>{analysis['action']}</b></div>", unsafe_allow_html=True)
                    else:
                         st.markdown(f"<div style='background:#2d2d2d; padding:10px; border-radius:5px; border-left:4px solid gray;'>👀 <b>{analysis['action']}</b></div>", unsafe_allow_html=True)

            else:
                st.error("無法獲取足夠數據進行分析，請檢查標的是否存在或縮短週期。")
    else:
        st.markdown("""
        ### 👋 歡迎來到 AI 專業操盤室
        請在左側選擇市場與標的，系統將自動為您執行以下專業流程：
        
        1. **識別 Swing High/Low**：自動繪製斐波那契回撤網格。
        2. **MACD & RSI 雙重過濾**：確認動能與趨勢方向。
        3. **計算風險回報比 (R:R)**：給出精確的進場、止盈、止損位。
        
        ---
        *Designed for Pro Traders.*
        """)

if __name__ == "__main__":
    main()
