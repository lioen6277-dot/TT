# -*- coding: utf-8 -*-
"""
AI 專業操盤策略系統 (Pro Trader Strategy Framework) - V4.1 Optimized
優化重點：
1. 新增 Volume Profile (VRVP) 籌碼分佈圖
2. 新增斐波那契回溯期自定義 (Swing Sensitivity)
3. 強化 EMA200 對新上市標的的容錯率
4. 優化圖表視覺體驗

開發者：AI 協作 (基於 User 策略優化)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# 1. 頁面配置與 CSS 視覺優化
# ==============================================================================

st.set_page_config(
    page_title="AI 專業操盤策略室 (Pro)",
    page_icon="🦅",
    layout="wide"
)

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
        flex-wrap: wrap; /* 允許手機版換行 */
    }
    
    /* 通用卡片樣式 */
    .trade-card {
        background-color: #1E222D;
        border-radius: 10px;
        padding: 20px;
        flex: 1;
        min-width: 140px; /* 防止太窄 */
        text-align: center;
        border: 1px solid #333;
        transition: transform 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .trade-card:hover { transform: translateY(-3px); }

    .card-title { font-size: 0.9em; color: #A0A0A0; margin-bottom: 8px; letter-spacing: 0.5px; }
    .card-value { font-size: 1.5em; font-weight: 700; color: #FFFFFF; font-family: 'Roboto Mono', monospace; }
    .card-sub { font-size: 0.75em; margin-top: 8px; opacity: 0.7; }

    /* --- 光暈特效 (Glow Effects) - 台灣操盤色系 --- */
    /* Entry: 鮭魚粉 */
    .glow-entry { border-bottom: 3px solid #FA8072; box-shadow: 0 8px 20px -5px rgba(250, 128, 114, 0.25); }
    .text-entry { color: #FA8072 !important; }

    /* TP: 紅色 (獲利) */
    .glow-tp { border-bottom: 3px solid #DC3545; box-shadow: 0 8px 20px -5px rgba(220, 53, 69, 0.25); }
    .text-tp { color: #FF4B4B !important; }

    /* SL: 綠色 (虧損/風險) */
    .glow-sl { border-bottom: 3px solid #28A745; box-shadow: 0 8px 20px -5px rgba(40, 167, 69, 0.25); }
    .text-sl { color: #28A745 !important; }

    /* R:R: 藍色/中性 */
    .glow-rr { border-bottom: 3px solid #3498DB; box-shadow: 0 8px 20px -5px rgba(52, 152, 219, 0.25); }
    
    /* 標籤樣式 */
    .bullish-tag { background-color: rgba(220, 53, 69, 0.15); color: #FF6B6B; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; border: 1px solid rgba(220, 53, 69, 0.5); }
    .bearish-tag { background-color: rgba(40, 167, 69, 0.15); color: #5DD55D; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; border: 1px solid rgba(40, 167, 69, 0.5); }
    .neutral-tag { background-color: rgba(128, 128, 128, 0.15); color: #A0A0A0; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; border: 1px solid rgba(128, 128, 128, 0.5); }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. 全域設定與資料映射
# ==============================================================================

FULL_SYMBOLS_MAP = {
    "TSLA": {"name": "特斯拉", "keywords": ["TSLA"]}, "NVDA": {"name": "輝達", "keywords": ["NVDA"]},
    "AAPL": {"name": "蘋果", "keywords": ["AAPL"]}, "AMD": {"name": "超微", "keywords": ["AMD"]},
    "MSFT": {"name": "微軟", "keywords": ["MSFT"]}, "GOOGL": {"name": "谷歌", "keywords": ["GOOGL"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["AMZN"]}, "META": {"name": "Meta", "keywords": ["META"]},
    "SPY": {"name": "S&P 500 ETF", "keywords": ["SPY"]}, "QQQ": {"name": "納斯達克 ETF", "keywords": ["QQQ"]},
    "TQQQ": {"name": "三倍做多納指", "keywords": ["TQQQ"]}, "SOXL": {"name": "三倍做多半導體", "keywords": ["SOXL"]},
    "MSTR": {"name": "MicroStrategy", "keywords": ["MSTR"]}, "COIN": {"name": "Coinbase", "keywords": ["COIN"]},
    
    "2330.TW": {"name": "台積電", "keywords": ["2330"]}, "2317.TW": {"name": "鴻海", "keywords": ["2317"]},
    "2454.TW": {"name": "聯發科", "keywords": ["2454"]}, "2382.TW": {"name": "廣達", "keywords": ["2382"]},
    "3231.TW": {"name": "緯創", "keywords": ["3231"]}, "2603.TW": {"name": "長榮", "keywords": ["2603"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["0050"]}, "^TWII": {"name": "加權指數", "keywords": ["TWII"]},
    
    "BTC-USD": {"name": "比特幣", "keywords": ["BTC"]}, "ETH-USD": {"name": "以太坊", "keywords": ["ETH"]},
    "SOL-USD": {"name": "Solana", "keywords": ["SOL"]}, "BNB-USD": {"name": "幣安幣", "keywords": ["BNB"]},
    "DOGE-USD": {"name": "狗狗幣", "keywords": ["DOGE"]}, "XRP-USD": {"name": "瑞波幣", "keywords": ["XRP"]},
}

CATEGORY_MAP = {
    "美股 (US)": [k for k in FULL_SYMBOLS_MAP if not k.endswith((".TW", "-USD")) and not k.startswith("^")],
    "台股 (TW)": [k for k in FULL_SYMBOLS_MAP if k.endswith(".TW") or k.startswith("^TWII")],
    "加密貨幣 (Crypto)": [k for k in FULL_SYMBOLS_MAP if k.endswith("-USD")]
}

PERIOD_MAP = {
    "短線 (15分)": ("1mo", "15m"),
    "中線 (1小時)": ("3mo", "60m"),
    "中長線 (4小時)": ("1y", "60m"),
    "長線 (日線)": ("2y", "1d")
}

# ==============================================================================
# 3. 核心功能與指標計算
# ==============================================================================

def get_symbol_name(symbol):
    return FULL_SYMBOLS_MAP.get(symbol, {}).get("name", symbol)

@st.cache_data(ttl=300)
def get_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty: return None
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = [c.capitalize() for c in df.columns]
        # 移除 Volume 為 0 的行 (可能是休市數據)
        df = df[df['Volume'] > 0]
        return df
    except Exception: return None

def calculate_advanced_indicators(df):
    # 1. 趨勢 EMA
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    
    # 針對新上市股票，如果資料不足 200 根，則不計算或給 NaN，避免報錯
    if len(df) >= 200:
        df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    else:
        df['EMA_200'] = np.nan
    
    # 2. 動能 RSI (14)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # 3. MACD (12, 26, 9)
    macd = ta.trend.MACD(df['Close'])
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    # 4. 風控 ATR (14)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    # 5. 成交量 SMA
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    
    # 清洗：EMA200 可能有 NaN，但我們不希望因為它刪掉最近的資料
    # 所以這裡只 drop 必要的 NaN (如 EMA50, RSI)
    df.dropna(subset=['EMA_50', 'RSI', 'MACD_Hist'], inplace=True)
    return df

def get_volume_profile(df, bins=20):
    """計算可見範圍的 Volume Profile (簡單版)"""
    price_min = df['Low'].min()
    price_max = df['High'].max()
    price_range = price_max - price_min
    if price_range == 0: return None
    
    bin_size = price_range / bins
    
    # 建立分佈
    profile = []
    for i in range(bins):
        bin_low = price_min + (i * bin_size)
        bin_high = bin_low + bin_size
        
        # 找出在此價格區間內的 K 線，加總其成交量
        # 簡易邏輯：假設 K 線中點落在區間內，則該 K 線成交量歸入此區間
        mask = (df['Close'] >= bin_low) & (df['Close'] < bin_high)
        vol_sum = df.loc[mask, 'Volume'].sum()
        profile.append({'price': (bin_low + bin_high)/2, 'volume': vol_sum})
        
    return pd.DataFrame(profile)

def find_fibonacci_levels(df, lookback=60):
    """
    動態尋找 Swing High/Low
    lookback: 用戶可調整的靈敏度
    """
    # 確保 lookback 不超過資料長度
    lookback = min(lookback, len(df))
    recent_data = df.tail(lookback)
    
    high_price = recent_data['High'].max()
    low_price = recent_data['Low'].min()
    
    idx_high = recent_data['High'].idxmax()
    idx_low = recent_data['Low'].idxmin()
    
    trend_direction = "UP" if idx_high > idx_low else "DOWN"
    
    levels = {}
    diff = high_price - low_price
    if diff == 0: return None # 避免除以零
    
    if trend_direction == "UP":
        # 上升趨勢的回調
        levels['0.0'] = high_price
        levels['0.382'] = high_price - 0.382 * diff
        levels['0.5'] = high_price - 0.5 * diff
        levels['0.618'] = high_price - 0.618 * diff
        levels['0.786'] = high_price - 0.786 * diff
        levels['1.0'] = low_price
        levels['Ext_1.618'] = high_price + 0.618 * diff
        entry_zone_high = levels['0.5']
        entry_zone_low = levels['0.786']
    else:
        # 下跌趨勢的反彈
        levels['0.0'] = low_price
        levels['0.382'] = low_price + 0.382 * diff
        levels['0.5'] = low_price + 0.5 * diff
        levels['0.618'] = low_price + 0.618 * diff
        levels['0.786'] = low_price + 0.786 * diff
        levels['1.0'] = high_price
        levels['Ext_1.618'] = low_price - 0.618 * diff
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
    latest = df.iloc[-1]
    
    score = 0
    reasons = []
    
    # 1. 趨勢
    trend_score = 0
    if latest['MACD_Hist'] > 0: trend_score += 1
    else: trend_score -= 1
        
    if latest['RSI'] > 50: trend_score += 1
    else: trend_score -= 1
        
    if latest['Close'] > latest['EMA_50']: trend_score += 1
    else: trend_score -= 1

    # 2. 結構
    price = latest['Close']
    in_entry_zone = False
    
    if fib_data['trend'] == "UP":
        if fib_data['levels']['0.786'] <= price <= fib_data['levels']['0.5']:
            in_entry_zone = True
            reasons.append("價格位於 0.5 - 0.786 潛在支撐區。")
    else:
        if fib_data['levels']['0.5'] <= price <= fib_data['levels']['0.786']:
            in_entry_zone = True
            reasons.append("價格位於 0.5 - 0.786 潛在壓力區。")
            
    # 3. 驗證 (簡單成交量)
    if latest['Volume'] > latest['Vol_SMA']:
        reasons.append("當前成交量高於 20MA，動能增強。")
    
    # 綜合建議
    action = "觀望 (Neutral)"
    sentiment_color = "neutral"
    
    if trend_score > 0 and in_entry_zone and fib_data['trend'] == "UP":
        action = "做多 (Long)"
        sentiment_color = "bullish"
    elif trend_score < 0 and in_entry_zone and fib_data['trend'] == "DOWN":
        action = "做空 (Short)"
        sentiment_color = "bearish"
    elif abs(trend_score) >= 2:
        action = "順勢持有 (Trend Following)"
        sentiment_color = "bullish" if trend_score > 0 else "bearish"
        
    return {'action': action, 'reasons': reasons, 'trend_score': trend_score, 'sentiment': sentiment_color, 'in_zone': in_entry_zone}

def calculate_trade_setup(df, fib_data, action):
    current_price = df.iloc[-1]['Close']
    atr = df.iloc[-1]['ATR']
    setup = {'entry': current_price, 'sl': 0, 'tp1': 0, 'tp2': 0, 'rr': 0, 'valid': False}
    
    if "做多" in action or ("持有" in action and fib_data['trend'] == "UP"):
        sl_structural = fib_data['low'] - (atr * 0.5)
        sl_fib = fib_data['levels']['0.786'] - (atr * 1.0)
        setup['sl'] = min(sl_structural, sl_fib)
        setup['tp2'] = fib_data['levels']['Ext_1.618']
        risk = current_price - setup['sl']
        reward = setup['tp2'] - current_price
    elif "做空" in action or ("持有" in action and fib_data['trend'] == "DOWN"):
        sl_structural = fib_data['high'] + (atr * 0.5)
        sl_fib = fib_data['levels']['0.786'] + (atr * 1.0)
        setup['sl'] = max(sl_structural, sl_fib)
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

def plot_pro_chart(df, fib_data, symbol_name, vp_data):
    fig = make_subplots(rows=2, cols=2, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3],
                        column_widths=[0.85, 0.15], # 右側留給 Volume Profile
                        horizontal_spacing=0.02,
                        specs=[[{}, {}], [{"colspan": 2}, None]], # 下方 MACD 跨兩欄
                        subplot_titles=(f"{symbol_name} 結構與籌碼分佈", "", "MACD 動能震盪"))

    # 1. K線圖
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    
    # EMA
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA 50'), row=1, col=1)
    if 'EMA_200' in df.columns and not df['EMA_200'].isna().all():
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='purple', width=1, dash='dash'), name='EMA 200'), row=1, col=1)
    
    # 斐波那契
    colors = ['gray', 'skyblue', 'yellow', 'salmon', 'red', 'gray', '#00FF00']
    fib_levels = [
        ('0.0', fib_data['levels']['0.0'], colors[0]),
        ('0.382', fib_data['levels']['0.382'], colors[1]),
        ('0.5', fib_data['levels']['0.5'], colors[2]),
        ('0.618', fib_data['levels']['0.618'], colors[3]),
        ('0.786', fib_data['levels']['0.786'], colors[4]),
        ('1.0', fib_data['levels']['1.0'], colors[5]),
        ('TP 1.618', fib_data['levels']['Ext_1.618'], colors[6])
    ]
    
    start_date = df.index[0] # 全域畫線
    end_date = df.index[-1]
    
    for label, value, color in fib_levels:
        fig.add_shape(type="line", x0=start_date, y0=value, x1=end_date, y1=value,
                      line=dict(color=color, width=1, dash="dot"), row=1, col=1)
        # 標註文字
        fig.add_annotation(x=end_date, y=value, text=f"{label}",
                           showarrow=False, xanchor="left", font=dict(color=color, size=9), row=1, col=1)

    # 2. Volume Profile (右側 Bar Chart)
    if vp_data is not None:
        # 找出最大成交量用於歸一化顏色
        max_vol = vp_data['volume'].max()
        # POC (Point of Control)
        poc_price = vp_data.loc[vp_data['volume'].idxmax(), 'price']
        
        fig.add_trace(go.Bar(
            y=vp_data['price'], 
            x=vp_data['volume'], 
            orientation='h',
            marker=dict(color=vp_data['volume'], colorscale='Jet', opacity=0.5),
            name='Vol Profile',
            showlegend=False
        ), row=1, col=2)
        
        # 標註 POC
        fig.add_shape(type="line", x0=0, x1=max_vol, y0=poc_price, y1=poc_price,
                      line=dict(color="white", width=1), row=1, col=2)

    # 3. MACD
    colors_macd = np.where(df['MACD_Hist'] > 0, '#DC3545', '#28A745')
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_macd, name='MACD Hist'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='#FAFAFA', width=1), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FFA500', width=1), name='Signal'), row=2, col=1)

    # Layout 設定
    fig.update_layout(template="plotly_dark", height=750, margin=dict(l=10, r=10, t=40, b=10))
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    # 隱藏右側 VP 的 X 軸與 Y 軸標籤
    fig.update_xaxes(showticklabels=False, row=1, col=2)
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    
    return fig

# ==============================================================================
# 5. 主程式
# ==============================================================================

def main():
    st.sidebar.header("🦅 操盤控制台 (Pro+)")
    
    # 資產選擇
    cat = st.sidebar.selectbox("1. 市場類別", list(CATEGORY_MAP.keys()))
    symbols = CATEGORY_MAP[cat]
    display_symbols = [f"{s} - {FULL_SYMBOLS_MAP[s]['name']}" for s in symbols]
    selected_display = st.sidebar.selectbox("2. 選擇標的", display_symbols)
    symbol = selected_display.split(" - ")[0]
    
    # 週期與靈敏度
    p_label = st.sidebar.selectbox("3. 時間架構", list(PERIOD_MAP.keys()), index=2)
    period, interval = PERIOD_MAP[p_label]
    
    st.sidebar.markdown("---")
    # 優化功能：回溯期滑桿
    fib_lookback = st.sidebar.slider("🌊 波段回溯 K 線數 (Swing Sensitivity)", 
                                     min_value=30, max_value=200, value=100, step=10,
                                     help="數值越大，抓取的波段結構越大（適合長線）；數值越小，對短期波動越敏感。")
    
    run_btn = st.sidebar.button("🚀 執行策略分析", type="primary")

    if run_btn:
        with st.spinner(f"AI 正在計算 {symbol} 的籌碼分佈與斐波那契結構..."):
            df = get_data(symbol, period, interval)
            
            if df is not None and len(df) > fib_lookback:
                # 計算
                df = calculate_advanced_indicators(df)
                fib_data = find_fibonacci_levels(df, lookback=fib_lookback)
                
                if fib_data is None:
                    st.error("無法識別有效波段結構，請嘗試調整回溯期或更換週期。")
                    return

                analysis = analyze_strategy(df, fib_data)
                setup = calculate_trade_setup(df, fib_data, analysis['action'])
                vp_data = get_volume_profile(df)
                
                # --- UI ---
                curr_price = df.iloc[-1]['Close']
                price_chg = curr_price - df.iloc[-2]['Close']
                chg_color = "#DC3545" if price_chg > 0 else "#28A745"
                
                st.markdown(f"## {get_symbol_name(symbol)} ({symbol}) - {p_label} 結構分析")
                st.markdown(f"<h3 style='color:{chg_color}'>${curr_price:,.2f} <small>({price_chg:+.2f})</small></h3>", unsafe_allow_html=True)
                
                # 交易卡片
                if setup['valid']:
                    st.markdown(f"""
                    <div class="trade-card-container">
                        <div class="trade-card glow-entry">
                            <div class="card-title">建議進場 (Entry)</div>
                            <div class="card-value text-entry">${setup['entry']:,.2f}</div>
                            <div class="card-sub">Fib {fib_data['levels']['0.618']:.2f} 附近</div>
                        </div>
                        <div class="trade-card glow-tp">
                            <div class="card-title">目標止盈 (TP)</div>
                            <div class="card-value text-tp">${setup['tp2']:,.2f}</div>
                            <div class="card-sub">Fib 1.618 擴展</div>
                        </div>
                        <div class="trade-card glow-sl">
                            <div class="card-title">結構止損 (SL)</div>
                            <div class="card-value text-sl">${setup['sl']:,.2f}</div>
                            <div class="card-sub">前低 ± ATR</div>
                        </div>
                        <div class="trade-card glow-rr">
                            <div class="card-title">盈虧比 (R:R)</div>
                            <div class="card-value">{setup['rr']:.2f}</div>
                            <div class="card-sub">目標 > 2.0</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("⚠️ 盈虧比未達標或未出現進場訊號，建議觀望。")
                    
                # 圖表與觀點
                col_chart, col_desc = st.columns([2.2, 0.8])
                
                with col_chart:
                    fig = plot_pro_chart(df, fib_data, get_symbol_name(symbol), vp_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_desc:
                    st.markdown("### 🦅 操盤手觀點")
                    # 標籤
                    tag_class = "bullish-tag" if analysis['sentiment'] == "bullish" else "bearish-tag" if analysis['sentiment'] == "bearish" else "neutral-tag"
                    st.markdown(f"**市場定性：** <span class='{tag_class}'>{analysis['action']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("#### 1. 結構 (Structure)")
                    st.markdown(f"- **趨勢方向**: {fib_data['trend']}")
                    st.markdown(f"- **波段高點**: {fib_data['high']:.2f}")
                    st.markdown(f"- **波段低點**: {fib_data['low']:.2f}")
                    st.markdown(f"- **0.618 支撐**: {fib_data['levels']['0.618']:.2f}")
                    
                    st.markdown("#### 2. 共振 (Confluence)")
                    for r in analysis['reasons']:
                        st.markdown(f"✅ {r}")
                    
                    if analysis['in_zone']:
                        st.success("🎯 價格位於關鍵擊球區 (PZR)")
                    else:
                        st.warning("⏳ 等待回調/反彈")

            else:
                st.error("數據不足，請更換標的或縮短回溯期。")
    else:
        st.info("👋 請在左側點擊 **『🚀 執行策略分析』** 開始。")
        st.markdown("""
        #### V4.1 更新亮點：
        - 📊 **VRVP 籌碼分佈**：圖表右側新增成交量分佈條，協助識別籌碼密集區。
        - 🌊 **波段靈敏度**：透過側邊欄滑桿調整斐波那契的取樣範圍。
        - 🛡️ **更穩定的計算**：優化了新股 EMA 計算邏輯。
        """)

if __name__ == "__main__":
    main()
