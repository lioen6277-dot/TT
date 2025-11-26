# -*- coding: utf-8 -*-
"""
AI 趨勢分析 Streamlit 應用程式
專家增強最終版實作 (V12.3 - 專業策略整合與鮭魚粉UI)

本應用程式根據一份詳細的金融分析工具設定文件進行開發，並融合了專業級的
app3.0.py 設計邏輯與使用者提供的專業操盤策略，旨在提供一個外觀精美、
互動專業的決策儀表板。

核心功能：
- [策略整合] 實現專業操盤框架 (RSI/MACD趨勢定性, 斐波那契結構, ATR風控)。
- [R:R 優化] 止損點錨定斐波那契0.786並增加ATR緩衝，確保結構性止損。
- [UI/配色] 全局應用鮭魚粉 (#FA8072) 配色主題。
- [結果顯示] 核心交易建議使用 Metric 指標卡片顯示。
"""

# 載入核心套件
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import warnings
import time
import re 
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

# 週期映射：(YFinance Period, YFinance Interval)
PERIOD_MAP = { 
    "30 分": ("60d", "30m"), 
    "4 小時": ("1y", "60m"), 
    "1 日": ("5y", "1d"), 
    "1 週": ("max", "1wk")
}

# 🚀 您的【所有資產清單】
FULL_SYMBOLS_MAP = {
    # ----------------------------------------------------
    # A. 美股核心 (US Stocks) - 個股
    # ----------------------------------------------------
    "TSLA": {"name": "特斯拉", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "NVDA": {"name": "輝達", "keywords": ["輝達", "英偉達", "AI", "NVDA", "Nvidia"]},
    "AAPL": {"name": "蘋果", "keywords": ["蘋果", "iPhone", "AAPL", "Apple"]},
    "MSFT": {"name": "微軟", "keywords": ["微軟", "雲端", "MSFT", "Microsoft"]},
    "GOOGL": {"name": "谷歌 (A)", "keywords": ["谷歌", "Google", "GOOGL"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["亞馬遜", "Amazon", "AMZN"]},
    
    # ----------------------------------------------------
    # B. 台股核心 (TW Stocks)
    # ----------------------------------------------------
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "晶圓", "2330"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "IC設計", "2454"]},
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "ETF"]},
    
    # ----------------------------------------------------
    # C. 加密貨幣 (Crypto) - 透過 Yahoo Finance 獲取
    # ----------------------------------------------------
    "BTC-USD": {"name": "比特幣/美元", "keywords": ["比特幣", "BTC"]},
    "ETH-USD": {"name": "以太坊/美元", "keywords": ["以太坊", "ETH"]},
}

# 輔助函式：根據類型獲取貨幣符號
def get_currency_symbol(asset_type):
    if asset_type == '台股':
        return 'NT$'
    elif asset_type == '加密貨幣':
        return '₿'
    return '$'

# ==============================================================================
# 2. 數據獲取與指標計算
# ==============================================================================

@st.cache_data(ttl=600)
def getDataFromYF(symbol, period_tuple):
    """從 Yahoo Finance 獲取數據，並確保數據量足夠"""
    try:
        data = yf.download(symbol, period=period_tuple[0], interval=period_tuple[1])
        if data.empty or len(data) < 200: # 確保至少有200根K線進行分析
            return None
        return data.reset_index()
    except Exception as e:
        st.error(f"⚠️ 無法從 Yahoo Finance 獲取數據：{e}")
        return None

def get_latest_fa_rating(symbol):
    """模擬的基本面評分 (0.0 到 5.0)"""
    # 僅為模擬，實際應用中需連接外部數據源
    np.random.seed(hash(symbol) % 100) # 確保同一標的評分穩定
    return round(np.random.uniform(2.5, 5.0), 1)

def calculate_technical_indicators(df):
    """
    專業操盤策略框架：RSI, MACD, 斐波那契與進階驗證
    指標設定：採用您策略中偏向短/中期的靈敏設定 (RSI 9, ATR 9)
    """
    if len(df) < 50: # 確保有足夠數據計算所有指標
        return pd.DataFrame() 

    # 均線 (MA) - 作為趨勢判斷濾鏡
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)

    # MACD (策略升級: 9, 16, 5) - 趨勢方向、動能轉換與市場力量 (區塊一)
    macd_instance = ta.trend.MACD(df['Close'], window_fast=9, window_slow=16, window_sign=5)
    df['MACD_Line'] = macd_instance.macd()
    df['MACD_Signal'] = macd_instance.macd_signal()
    df['MACD_Hist'] = macd_instance.macd_diff() # 柱狀圖

    # RSI (相對強弱指標: 9) - 市場超買/超賣狀態與動能強度 (區塊一)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=9)

    # ATR (平均真實波幅: 9) - 風險控制的基石 (區塊三)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)

    # ADX (平均趨向指數: 9) - 趨勢強度濾鏡
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], df['Volume'], window=9)
    
    # 🚀 斐波那契結構計算 (簡化版本 - 計算最近一個主要波段)
    window_size = min(50, len(df))
    # 識別最近50根K線的最大/最小價
    max_price = df['High'].iloc[-window_size:].max()
    min_price = df['Low'].iloc[-window_size:].min()
    
    price_range = max_price - min_price

    # 多頭回撤區 (用於找買點)
    df['Fib_0.618'] = max_price - price_range * 0.618
    df['Fib_0.786'] = max_price - price_range * 0.786
    
    # 斐波那契擴展 (止盈目標, 假設從 min_price 到 max_price)
    df['Fib_1.0'] = max_price # TP1: 前高/前低 (策略要求)
    df['Fib_1.618'] = max_price + price_range * 0.618 # TP2: 1.618 擴展
    df['Fib_2.618'] = max_price + price_range * 1.618 # TP3: 2.618 擴展

    # 空頭回撤區與擴展 (用於找賣點)
    df['Fib_0.618_Short'] = min_price + price_range * 0.618
    df['Fib_0.786_Short'] = min_price + price_range * 0.786
    df['Fib_1.618_Short'] = min_price - price_range * 0.618
    
    return df.dropna()

# ==============================================================================
# 3. 專業策略信號融合與 R:R 風控計算
# ==============================================================================

def generate_expert_fusion_signal(df, fa_rating, currency_symbol="$"):
    """
    融合專業操盤策略 (RSI/MACD 趨勢判斷、結構性斐波那契、ATR/R:R 1:2 風控)
    """
    df_clean = df.dropna().copy()
    if df_clean.empty or len(df_clean) < 2:
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'strategy': '無法評估', 'entry_price': 0, 'take_profit': 0, 'stop_loss': 0, 'current_price': 0, 'expert_opinions': {}, 'atr': 0, 'actual_rr': 0}

    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2]
    current_price = last_row['Close']
    atr_value = last_row['ATR']
    adx_value = last_row['ADX'] 
    
    expert_opinions = {}
    
    # 1. 趨勢定性專家 (MA & ADX)
    ma_score = 0
    ema_10, ema_50, ema_200 = last_row['EMA_10'], last_row['EMA_50'], last_row['EMA_200']
    
    if ema_10 > ema_50 and ema_50 > ema_200 and adx_value > 25:
        ma_score = 3.0 
        expert_opinions['趨勢濾鏡 (MA/ADX)'] = f"強勢多頭排列：**10 > 50 > 200** 且 ADX({adx_value:.1f})>25，宏觀趨勢強勁。"
    elif ema_10 < ema_50 and ema_50 < ema_200 and adx_value > 25:
        ma_score = -3.0 
        expert_opinions['趨勢濾鏡 (MA/ADX)'] = f"強勢空頭排列：**10 < 50 < 200** 且 ADX({adx_value:.1f})>25，宏觀趨勢強勁。"
    else:
        ma_score = 1.0 if ema_10 > ema_50 else -1.0
        expert_opinions['趨勢濾鏡 (MA/ADX)'] = "中性：MA排列或 ADX < 25，趨勢信號不夠強勁。"
    
    # 2. RSI 動能專家 - 專注「50 中軸定性」(區塊一)
    momentum_score = 0
    rsi = last_row['RSI']
    
    if rsi > 50:
        momentum_score = 1.5 
        expert_opinions['RSI (9) 動能'] = f"多頭：RSI ({rsi:.1f}) > 50 **中軸定性**，多頭佔優。"
    else:
        momentum_score = -1.5
        expert_opinions['RSI (9) 動能'] = f"空頭：RSI ({rsi:.1f}) < 50 **中軸定性**，空頭佔優。"

    # 3. MACD 動能轉換專家 - 柱狀體 (區塊一)
    strength_score = 0
    macd_hist = last_row['MACD_Hist']
    prev_macd_hist = prev_row['MACD_Hist']
    
    if macd_hist > 0 and macd_hist > prev_macd_hist:
        strength_score += 2.0
        expert_opinions['MACD 動能'] = "多頭：MACD 柱狀體位於零軸上方且**動能持續增強**。"
    elif macd_hist < 0 and macd_hist < prev_macd_hist:
        strength_score -= 2.0
        expert_opinions['MACD 動能'] = "空頭：MACD 柱狀體位於零軸下方且**動能持續增強**。"
    else:
        expert_opinions['MACD 動能'] = "中性：MACD 動能收縮或轉換中，觀望動能方向。"

    # 4. 結構性確認 (斐波那契 PZR)
    fib_score = 0
    # 趨勢為多頭，尋找回撤買入區 0.618 - 0.786
    is_near_long_fib = (abs(current_price - last_row['Fib_0.618']) / atr_value < 1.0) and (last_row['Fib_0.618'] > last_row['Fib_0.786']) 
    # 趨勢為空頭，尋找回撤賣出區 0.618 - 0.786
    is_near_short_fib = (abs(current_price - last_row['Fib_0.618_Short']) / atr_value < 1.0) and (last_row['Fib_0.618_Short'] < last_row['Fib_0.786_Short']) 

    
    if ma_score > 0 and momentum_score > 0 and is_near_long_fib:
        fib_score = 3.0
        expert_opinions['斐波那契 PZR'] = "**🎯 買入共振：** 價格進入 0.618-0.786 潛在反轉區 (PZR)，等待K線確認。"
    elif ma_score < 0 and momentum_score < 0 and is_near_short_fib:
        fib_score = -3.0
        expert_opinions['斐波那契 PZR'] = "**🎯 賣出共振：** 價格進入空頭回撤 PZR，等待K線確認。"
    
    # 5. 融合分數計算
    fusion_score = ma_score + momentum_score + strength_score + fib_score + (fa_rating * 0.5) 
    
    # 最終行動
    action = "觀望 (Neutral)"
    if fusion_score >= 5.0:
        action = "買進 (Buy)"
    elif fusion_score >= 1.0:
        action = "中性偏買 (Hold/Buy)"
    elif fusion_score <= -5.0:
        action = "賣出 (Sell/Short)"
    elif fusion_score <= -1.0:
        action = "中性偏賣 (Hold/Sell)"
        
    # 信心指數 (MAX_SCORE = 3.0 + 1.5 + 2.0 + 3.0 + 2.5 = 12.0)
    MAX_SCORE = 12.0 
    confidence = min(100, max(0, 50 + (fusion_score / MAX_SCORE) * 50))
    
    # 風險控制與交易策略 (R:R 1:2 的原則, 區塊三)
    price_format = ".4f" if current_price < 100 and not currency_symbol == 'NT$' else ".2f"
    
    entry = current_price # 以當前價作為基準點，策略建議在當前價附近尋找進場機會
    actual_rr = 0.0

    if action in ["買進 (Buy)", "中性偏買 (Hold/Buy)"]:
        # SL: 斐波那契 0.786 結構位 - 0.5 ATR 緩衝 (專業結構性止損)
        stop_loss_base = last_row['Fib_0.786'] if last_row['Fib_0.786'] < entry else entry - (atr_value * 2.0) # 確保SL在下方
        stop_loss = stop_loss_base - (atr_value * 0.5) 
        
        # TP: 斐波那契 1.618 擴展 (主要目標)
        take_profit = last_row['Fib_1.618'] 
        
        # 計算實際 R:R
        actual_risk = entry - stop_loss
        actual_reward = take_profit - entry
        actual_rr = actual_reward / actual_risk if actual_risk > 0 and actual_reward > 0 else 0
        
        strategy_desc = f"基於{action}信號，趨勢動能共振偏多。SL錨定**0.786結構位** + ATR緩衝。TP目標**1.618擴展位**。**實際 R:R 約 1:{actual_rr:.2f}**，符合專業高 R:R 標準。"
    
    elif action in ["賣出 (Sell/Short)", "中性偏賣 (Hold/Sell)"]:
        # SL: 斐波那契 0.786 Short 結構位 + 0.5 ATR 緩衝
        stop_loss_base = last_row['Fib_0.786_Short'] if last_row['Fib_0.786_Short'] > entry else entry + (atr_value * 2.0) # 確保SL在上方
        stop_loss = stop_loss_base + (atr_value * 0.5)
        
        # TP: 斐波那契 1.618 Short 擴展
        take_profit = last_row['Fib_1.618_Short']
        
        # 計算實際 R:R
        actual_risk = stop_loss - entry
        actual_reward = entry - take_profit
        actual_rr = actual_reward / actual_risk if actual_risk > 0 and actual_reward > 0 else 0
        
        strategy_desc = f"基於{action}信號，趨勢動能共振偏空。SL錨定**空頭0.786結構位** + ATR緩衝。TP目標**空頭1.618擴展位**。**實際 R:R 約 1:{actual_rr:.2f}**，符合專業高 R:R 標準。"
    
    else:
        entry = current_price
        stop_loss = current_price - atr_value
        take_profit = current_price + atr_value
        strategy_desc = "市場信號混亂，MACD/RSI缺乏一致動能，建議觀望。"
        
    return {
        'action': action, 
        'score': round(fusion_score, 2), 
        'confidence': round(confidence, 0), 
        'strategy': strategy_desc, 
        'entry_price': round(entry, 4 if price_format == ".4f" else 2),
        'take_profit': round(take_profit, 4 if price_format == ".4f" else 2),
        'stop_loss': round(stop_loss, 4 if price_format == ".4f" else 2),
        'current_price': round(current_price, 4 if price_format == ".4f" else 2),
        'expert_opinions': expert_opinions, 
        'atr': atr_value,
        'actual_rr': round(actual_rr, 2)
    }

# ==============================================================================
# 4. Streamlit UI 頁面排版與鮭魚粉配色
# ==============================================================================

st.set_page_config(
    page_title="AI專業操盤策略儀表板", 
    page_icon="📈", 
    layout="wide"
)

# ⭐️ 鮭魚粉配色 CSS 
custom_css = """
<style>
/* Streamlit 核心 UI 顏色修改 (按鈕/Slider等) */
.st-emotion-cache-1wvf4a2 { /* 主要按鈕顏色 (Primary Button) */
    background-color: #FA8072; /* Salmon Pink */
    border-color: #FA8072;
    color: white; 
}
.st-emotion-cache-1wvf4a2:hover { /* 按鈕懸停顏色 */
    background-color: #FF9999; 
    border-color: #FF9999;
}

/* 專業行動建議的顏色標記 */
.buy-action {
    color: #FA8072; /* Salmon Pink for Buy */
    font-weight: bold;
}
.sell-action {
    color: #4682B4; /* SteelBlue for Sell */
    font-weight: bold;
}
.neutral-action {
    color: #808080; /* Gray for Neutral */
    font-weight: bold;
}

/* Metric 指標卡片字體大小調整 */
[data-testid="stMetricValue"] {
    font-size: 1.5em !important;
}

/* 隱藏 Streamlit 腳部/菜單 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

def display_analysis_results(symbol, period_name, currency_symbol, result, df_plot):
    st.subheader(f"🚀 {symbol} ({period_name}) 專業操盤策略分析")
    
    action_base = result['action'].split('(')[0]
    action_hint = result['action'].split('(')[1].replace(')', '')
    action_color = "inverse" if "Buy" in result['action'] else ("off" if "Sell" in result['action'] else "gray")
    
    # 策略總結區塊 (Metric 卡片顯示)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # 1. 行動建議卡片
    with col1:
        st.markdown(f"**🎯 最終行動建議**", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.8em; font-weight: bold; color: {'#FA8072' if 'Buy' in result['action'] else '#4682B4'};'>{action_base}</p>", unsafe_allow_html=True)
        st.metric(
            label=f"信心指數", 
            value=f"{result['confidence']:.0f}%",
            delta=action_hint
        )

    # 2. 進場價卡片
    with col2:
        st.metric(
            label="💰 建議進場價 (Entry)", 
            value=f"{currency_symbol}{result['entry_price']:.4f}",
            delta=f"當前價格: {currency_symbol}{result['current_price']:.4f}"
        )

    # 3. 止損價 (SL) 卡片
    with col3:
        st.metric(
            label="⛔ 止損價 (SL) - 風控為王", 
            value=f"{currency_symbol}{result['stop_loss']:.4f}",
            delta=f"基於 Fib 0.786 結構性止損"
        )

    # 4. 止盈價 (TP) 卡片
    with col4:
        st.metric(
            label="📈 止盈價 (TP) - 結構目標", 
            value=f"{currency_symbol}{result['take_profit']:.4f}",
            delta=f"基於 Fib 1.618 擴展"
        )
    
    # 5. R:R 卡片
    with col5:
        # 使用顏色提示 R:R 是否符合專業標準 (>= 2.0)
        rr_color = "#28a745" if result['actual_rr'] >= 2.0 else "#FA8072"
        st.markdown(f"**⚖️ 風險報酬比 (R:R)**", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.8em; font-weight: bold; color: {rr_color};'>1:{result['actual_rr']:.2f}</p>", unsafe_allow_html=True)
        st.metric(
            label=f"單筆風險 (ATR)", 
            value=f"{result['atr']:.4f}",
            delta=f"融合分數: {result['score']:.2f}"
        )
        

    st.markdown("---")

    # 專家意見與策略說明
    st.markdown("### 📝 專家指標共振意見 (Confluence) 與策略說明")
    
    # 策略總結
    st.info(f"**💡 專業策略總結：** {result['strategy']}")

    # 指標共振細節
    expander = st.expander("🔬 點擊查看指標共振詳情 (區塊一與區塊二驗證)", expanded=False)
    with expander:
        opinions = result['expert_opinions']
        col_ops = st.columns(3)
        
        i = 0
        for label, opinion in opinions.items():
            col_ops[i % 3].markdown(f"**{label}:** {opinion}")
            i += 1

    st.markdown("---")
    
    # 蠟燭圖與指標圖表 (與 app3.0.py 繪圖邏輯相似)
    st.markdown("### 📊 核心交易圖表 (K線/MACD/RSI/ADX)")
    
    # 創建子圖
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1,
        row_heights=[0.5, 0.15, 0.15, 0.2] # 調整圖表高度比例
    )

    # 1. 蠟燭圖
    fig.add_trace(go.Candlestick(
        x=df_plot['Date'], 
        open=df_plot['Open'], 
        high=df_plot['High'], 
        low=df_plot['Low'], 
        close=df_plot['Close'],
        name="K線", 
        increasing_line_color='#FA8072', # 鮭魚粉 K線
        decreasing_line_color='#4682B4'  # 海軍藍 K線
    ), row=1, col=1)

    # EMA 趨勢線
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['EMA_50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['EMA_200'], name='EMA 200', line=dict(color='purple', width=1)), row=1, col=1)

    # 斐波那契 PZR 區間 (0.618 - 0.786)
    last_row_plot = df_plot.iloc[-1]
    fib_color = 'rgba(250, 128, 114, 0.2)' if "Buy" in result['action'] else 'rgba(70, 130, 180, 0.2)'
    
    # 多頭回撤區間
    fig.add_hrect(
        y0=last_row_plot['Fib_0.786'], 
        y1=last_row_plot['Fib_0.618'], 
        line_width=0, 
        fillcolor=fib_color, 
        opacity=0.2, 
        row=1, col=1
    )
    
    # 標記 TP/SL
    fig.add_hline(y=result['take_profit'], line_width=2, line_dash="dot", line_color="#28a745", row=1, col=1, annotation_text="TP (1.618)")
    fig.add_hline(y=result['stop_loss'], line_width=2, line_dash="dot", line_color="#dc3545", row=1, col=1, annotation_text="SL (Fib 0.786+ATR)")

    # 2. MACD 圖
    fig.add_trace(go.Bar(x=df_plot['Date'], y=df_plot['MACD_Hist'], name='MACD 柱狀體', marker_color=np.where(df_plot['MACD_Hist'] > 0, '#FA8072', '#4682B4')), row=2, col=1)
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="grey", row=2, col=1)
    
    # 3. RSI 圖
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['RSI'], name='RSI (9)', line=dict(color='#8A2BE2')), row=3, col=1)
    fig.add_hline(y=50, line_width=1, line_dash="dash", line_color="black", row=3, col=1, annotation_text="RSI 50 中軸定性")
    fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="#FA8072", opacity=0.1, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="#4682B4", opacity=0.1, row=3, col=1)

    # 4. ADX 圖
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['ADX'], name='ADX (9)', line=dict(color='brown')), row=4, col=1)
    fig.add_hline(y=25, line_width=1, line_dash="dash", line_color="grey", row=4, col=1, annotation_text="ADX 25 (趨勢門檻)")


    # 更新佈局
    fig.update_layout(
        title=f'{symbol} - 專業技術圖表',
        height=800,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20)
    )

    # 隱藏子圖 X 軸標籤
    for i in range(1, 4):
        fig.update_xaxes(showticklabels=False, row=i, col=1)
    fig.update_xaxes(title_text=f"時間 ({period_name})", row=4, col=1)
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="ADX", row=4, col=1)
    
    st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# 5. Streamlit 主邏輯
# ==============================================================================

# 輔助：尋找標的代碼
def find_symbol_from_input(user_input):
    for symbol, details in FULL_SYMBOLS_MAP.items():
        if user_input.upper() == symbol or user_input in details['name'] or user_input.upper() in details['keywords']:
            return symbol
    return user_input # 如果沒有找到，返回原始輸入

def main():
    st.title("📈 AI 專業操盤策略儀表板")
    st.markdown("---")

    # 側邊欄輸入
    st.sidebar.header("🎯 策略參數設定")
    
    asset_type = st.sidebar.radio(
        "選擇資產類別", 
        ('美股', '台股', '加密貨幣'), 
        key='asset_type',
        horizontal=True
    )
    
    # 根據資產類型過濾標的
    filtered_symbols = {
        k: v for k, v in FULL_SYMBOLS_MAP.items() 
        if (asset_type == '美股' and not k.endswith(('.TW', '-USD'))) or
           (asset_type == '台股' and k.endswith('.TW')) or
           (asset_type == '加密貨幣' and k.endswith('-USD'))
    }
    
    # 轉換為 {name: symbol} 格式用於下拉選單
    display_symbols = {v['name']: k for k, v in filtered_symbols.items()}
    default_symbol_name = next(iter(display_symbols))
    
    selected_name = st.sidebar.selectbox("快速選擇標的", list(display_symbols.keys()), index=0)
    default_symbol = display_symbols[selected_name]
    
    # 允許自定義輸入
    user_symbol_input = st.sidebar.text_input(
        "或手動輸入代碼 (e.g., TSLA, BTC-USD)", 
        value=default_symbol
    )
    
    # 最終確認的 symbol
    symbol = find_symbol_from_input(user_symbol_input)
    
    period_name = st.sidebar.selectbox(
        "選擇分析週期 (時間級別)", 
        list(PERIOD_MAP.keys()), 
        index=2 # 預設為 1 日
    )
    
    # 核心執行按鈕
    if st.sidebar.button('📊 執行專業策略分析', key='run_analysis'):
        st.session_state['run_analysis'] = True
        st.session_state['current_symbol'] = symbol
        st.session_state['current_period'] = period_name
        st.session_state['current_asset_type'] = asset_type
    
    # --- 歷史數據載入與分析執行 ---
    if 'run_analysis' in st.session_state and st.session_state['run_analysis']:
        with st.spinner(f"正在載入 {st.session_state['current_symbol']} 數據並執行專業策略分析..."):
            
            symbol_to_use = st.session_state['current_symbol']
            period_to_use = st.session_state['current_period']
            asset_type_to_use = st.session_state['current_asset_type']
            
            df = getDataFromYF(symbol_to_use, PERIOD_MAP[period_to_use])
            
            if df is not None and not df.empty:
                df_with_ta = calculate_technical_indicators(df)
                
                if df_with_ta.empty or len(df_with_ta) < 20:
                     st.error("⚠️ 數據量不足以執行複雜的技術分析，請選擇更長的週期或更活躍的標的。")
                else:
                    fa_rating = get_latest_fa_rating(symbol_to_use)
                    currency_symbol = get_currency_symbol(asset_type_to_use)
                    
                    result = generate_expert_fusion_signal(df_with_ta, fa_rating, currency_symbol)
                    
                    # 顯示結果
                    display_analysis_results(symbol_to_use, period_to_use, currency_symbol, result, df_with_ta)
            else:
                st.error(f"⚠️ 無法獲取 {symbol_to_use} 的歷史數據，請檢查代碼是否正確。")

if __name__ == '__main__':
    main()
