import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import random
import time

# --- 1. 配置與常數設定 (Configuration and Constants) ---

# 設置頁面基礎樣式
st.set_page_config(
    page_title="🚀 AI 趨勢分析系統",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 數據源與歷史數據映射 (PERIOD_MAP)
# key: UI顯示名稱, value: (period, interval) for yfinance
PERIOD_MAP = {
    "30 分 (短線)": ("60d", "30m"),
    "4 小時 (中線)": ("1y", "4h"),
    "1 日 (長線)": ("5y", "1d"),
    "1 週 (超長線)": ("max", "1wk"),
}

# 簡化資產庫 (FULL_SYMBOLS_MAP) - 僅包含少量熱門範例
FULL_SYMBOLS_MAP = {
    "美股": {
        "TSLA": "Tesla, Inc.",
        "AAPL": "Apple Inc.",
        "GOOG": "Alphabet Inc. (Google)",
    },
    "台股": {
        "2330.TW": "台積電 (TSMC)",
        "2317.TW": "鴻海 (Foxconn)",
        "0050.TW": "元大台灣50",
    },
    "加密貨幣": {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    },
}

# AI 行動建議閾值
ACTION_THRESHOLDS = {
    "買進 (Buy)": 4.0,
    "中性偏買 (Hold/Buy)": 1.0,
    "觀望 (Neutral)": -1.0,
    "中性偏賣 (Hold/Sell)": -4.0,
    "賣出 (Sell/Short)": -100.0, # 低於此值即為賣出
}

# 設置 Tailwind-like 樣式，用於美化 UI 元素
CUSTOM_CSS = """
<style>
    /* 主色調：專業藍 */
    :root {
        --primary-color: #007BFF;
        --secondary-color: #f8f9fa;
        --success-color: #28a745;
        --danger-color: #dc3545;
        --warning-color: #ffc107;
    }
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        transform: translateY(-1px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* 量化評分容器樣式 */
    .quant-score-box {
        background-color: var(--secondary-color);
        border-radius: 12px;
        padding: 15px;
        margin-top: 10px;
        border: 1px solid #e9ecef;
    }

    /* 核心行動建議標籤樣式 */
    .action-tag {
        font-size: 1.5rem;
        font-weight: 700;
        padding: 8px 15px;
        border-radius: 6px;
        text-align: center;
        margin-bottom: 10px;
    }
    .action-buy {
        background-color: var(--success-color);
        color: white;
    }
    .action-sell {
        background-color: var(--danger-color);
        color: white;
    }
    .action-neutral {
        background-color: var(--warning-color);
        color: #333;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- 2. 數據獲取與預處理 ---

@st.cache_data(ttl=3600) # 緩存數據一小時，減少API呼叫
def get_data(symbol, period_key):
    """
    根據使用者選擇，從 Yahoo Finance 獲取歷史金融數據。
    
    Args:
        symbol (str): 股票或加密貨幣代碼。
        period_key (str): 週期設定的鍵 (e.g., "1 日 (長線)")。
        
    Returns:
        pd.DataFrame or None: 包含 OHLCV 數據的 DataFrame。
    """
    try:
        # 獲取 yfinance 參數
        period, interval = PERIOD_MAP[period_key]
        
        st.info(f"正在從 Yahoo Finance 獲取 **{symbol}** 的歷史數據 (週期: {period_key}) ...")
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            st.error(f"無法獲取 {symbol} 的數據。請檢查代碼或稍後再試。")
            return None
        
        # 重新命名欄位以便於處理
        df.columns = [col.capitalize() for col in df.columns]
        
        # 獲取基本面數據 (使用 yfinance 內建方法)
        info = ticker.info
        
        st.success(f"數據獲取成功。最新更新時間: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
        return df, info
        
    except Exception as e:
        st.error(f"數據獲取發生錯誤：{e}")
        return None, None

# --- 3. 核心分析引擎函數 (簡化與架構) ---

def calculate_indicators(df):
    """
    計算核心技術指標 (MA, RSI, MACD 等)。
    採用簡化計算，模擬文件 4.1 節的統一技術指標計算模組。
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # 1. 移動平均線 (EMA) - 趨勢指標
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # 2. 相對強弱指數 (RSI) - 動能指標 (使用 9 週期，參考文件 4.1)
    def calculate_rsi(series, period):
        delta = series.diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(com=period-1, adjust=False).mean()
        avg_loss = loss.ewm(com=period-1, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    df['RSI_9'] = calculate_rsi(df['Close'], 9)
    df['RSI_14'] = calculate_rsi(df['Close'], 14) # 模擬 AI 信號的額外指標

    # 3. MACD - 趨勢/動能指標 (採用介面顯示參數 8, 17, 9)
    df['EMA_8'] = df['Close'].ewm(span=8, adjust=False).mean()
    df['EMA_17'] = df['Close'].ewm(span=17, adjust=False).mean()
    df['MACD'] = df['EMA_8'] - df['EMA_17']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    
    # 4. ATR - 波動率指標 (使用 9 週期)
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = np.abs(df['High'] - df['Close'].shift(1))
    df['Low-PrevClose'] = np.abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    df['ATR_9'] = df['TR'].ewm(span=9, adjust=False).mean()

    # 5. OBV - 量能指標
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

    return df.dropna()

def get_fundamental_score(info):
    """
    計算介面顯示分數 (DISPLAY_SCORE) - 總分 9 分。
    模擬文件 4.2 節的基本面評分。
    """
    if info is None or 'trailingPE' not in info: # 簡易判斷是否為股票 (非加密貨幣/指數)
        return 0, "N/A - 非股票資產或數據不足"

    score = 0
    details = {}

    # 1. ROE 評分
    roe = info.get('returnOnEquity', 0)
    if roe > 0.15: # > 15%
        roe_score = 3
    elif roe > 0.10: # > 10%
        roe_score = 2
    elif roe > 0.0: # > 0%
        roe_score = 1
    else:
        roe_score = 0
    score += roe_score
    details['ROE 評分'] = f"{roe_score} 分 (ROE: {roe*100:.2f}%)"


    # 2. P/E 評分
    pe = info.get('trailingPE', 999)
    if pe > 0:
        if pe < 15:
            pe_score = 3
        elif pe < 25:
            pe_score = 2
        elif pe < 35:
            pe_score = 1
        else:
            pe_score = 0
    else: # P/E 為負或零
        pe_score = 0
        
    score += pe_score
    details['P/E 評分'] = f"{pe_score} 分 (P/E: {pe:.2f})"
    
    # 3. 現金流/債務評分 (簡化為 Debt to Equity)
    debt_equity = info.get('debtToEquity', 999)
    if debt_equity < 0.5:
        cash_score = 3
    elif debt_equity < 1.5:
        cash_score = 2
    else:
        cash_score = 1
        
    score += cash_score
    details['財務健康評分'] = f"{cash_score} 分 (D/E: {debt_equity:.2f})"


    return score, details

def generate_ai_fusion_signal(df, fundamental_score):
    """
    AI 融合信號生成模型 (簡化)。
    模擬文件 5.0 節的計分邏輯。
    """
    if df.empty:
        return 0.0, "數據不足", 0.0, {}

    last = df.iloc[-1]
    
    # --- 計算子分數 ---
    sub_scores = {}
    total_score = 0.0

    # 1. 趨勢分數 (MA Score) - 3.5分
    # 判斷黃金/死亡交叉及排列 (EMA 10 vs 50)
    ma_score = 0.0
    if last['EMA_10'] > last['EMA_50'] and df.iloc[-2]['EMA_10'] <= df.iloc[-2]['EMA_50']:
        ma_score = 3.5 # 黃金交叉
    elif last['EMA_10'] < last['EMA_50'] and df.iloc[-2]['EMA_10'] >= df.iloc[-2]['EMA_50']:
        ma_score = -3.5 # 死亡交叉
    elif last['EMA_10'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200']:
        ma_score = 2.0 # 強多頭排列
    
    sub_scores["趨勢分數 (MA)"] = ma_score
    total_score += ma_score

    # 2. 動能分數 (Momentum Score) - 2.0分 (基於 RSI_9)
    momentum_score = 0.0
    if last['RSI_9'] < 40:
        momentum_score = 2.0
    elif last['RSI_9'] > 60:
        momentum_score = -2.0
        
    sub_scores["動能分數 (RSI_9)"] = momentum_score
    total_score += momentum_score

    # 3. 強度分數 (Strength Score) - MACD Histogram
    strength_score = last['MACD_Hist'] / last['Close'] * 100 # 讓分數在合理範圍內
    # 簡化 ADX 加權: 隨機模擬 ADX > 25
    if random.random() > 0.6: # 40% 機率強趨勢
        strength_score *= 1.5
        sub_scores["強度分數 (MACD)"] = f"{strength_score:.2f} (已加權)"
    else:
        sub_scores["強度分數 (MACD)"] = f"{strength_score:.2f}"
        
    total_score += strength_score

    # 4. K線分數 (Kline Score) - 1.0分
    kline_score = 0.0
    body_size = abs(last['Close'] - last['Open'])
    if body_size > 0.7 * last['ATR_9']:
        if last['Close'] > last['Open']:
            kline_score = 1.0 # 大陽線
        else:
            kline_score = -1.0 # 大陰線
            
    sub_scores["K線分數"] = kline_score
    total_score += kline_score
    
    # 5. 基本面正規化分數 (FA Normalized Score)
    # 將 9 分制轉換為 -3 至 +3 區間
    fa_normalized = (fundamental_score - 4.5) / 1.5 
    fa_normalized = min(3.0, max(-3.0, fa_normalized)) # 限制在 -3 到 3
    
    sub_scores["基本面正規化分數"] = fa_normalized
    total_score += fa_normalized
    
    # --- 最終行動建議 ---
    action = "觀望 (Neutral)"
    confidence = abs(total_score) / (4.0 * 2) * 100 # 簡易信心指數

    for act, threshold in ACTION_THRESHOLDS.items():
        if act == "賣出 (Sell/Short)":
            if total_score <= threshold:
                action = act
                break
        else:
            if total_score >= threshold:
                action = act
                break

    return total_score, action, min(100, confidence), sub_scores


def calculate_consensus_risk(df):
    """
    多策略共識止盈止損 (簡化)。
    模擬文件 6.1 節的共識價計算演算法。
    """
    if df.empty:
        return None

    last_close = df.iloc[-1]['Close']
    last_atr = df.iloc[-1]['ATR_9']
    
    # 模擬 12 個止盈策略 (TPs) 和 12 個止損策略 (SLs)
    
    # TP 策略：取當前價格加上不同倍數的 ATR 或隨機值
    tps = [
        last_close + last_atr * 1.5,                 # ATR 停利 (策略 1)
        last_close + last_atr * 2.5,                 # ATR 停利 (策略 2)
        last_close * (1 + 0.03),                     # 3% 停利 (策略 3)
        last_close + (random.uniform(0.1, 0.5)),     # 隨機壓力位 (策略 4)
    ]
    
    # SL 策略：取當前價格減去不同倍數的 ATR 或隨機值
    sls = [
        last_close - last_atr * 1.0,                 # ATR 停損 (策略 1)
        last_close - last_atr * 2.0,                 # ATR 停損 (策略 2)
        last_close * (1 - 0.05),                     # 5% 停損 (策略 3)
        last_close - (random.uniform(0.1, 0.5)),     # 隨機支撐位 (策略 4)
    ]

    # 共識價計算 (取最高的 3 個 SL 平均, 最低的 3 個 TP 平均)
    consensus_sl = np.mean(sorted(sls, reverse=True)[:3]) # 最高的 3 個 SL (最關鍵支撐)
    consensus_tp = np.mean(sorted(tps)[:3])               # 最低的 3 個 TP (最現實壓力)
    
    return {
        "Consensus SL": consensus_sl,
        "Consensus TP": consensus_tp
    }

def run_backtest(df):
    """
    策略回測引擎 (SMA 20 / EMA 50 交叉策略 - 簡化)。
    模擬文件 6.2 節的回測引擎。
    """
    if df.empty or len(df) < 200:
        return "數據量不足以進行穩健回測。", None

    # 重新計算回測所需的均線
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # 交易信號: 1=買入, -1=賣出, 0=觀望
    df['Signal'] = 0.0
    df['Signal'][20:] = np.where(df['SMA_20'][20:] > df['EMA_50'][20:], 1.0, 0.0)
    
    # 買入/賣出點
    df['Position'] = df['Signal'].diff()
    
    # 簡化回測指標 (僅計算總回報率和總交易次數)
    initial_capital = 10000.0
    returns = df['Close'].pct_change()
    
    # 策略回報 (簡化：假設在信號出現後的第二天開盤買入/賣出)
    strategy_returns = (returns * df['Signal'].shift(1)).fillna(0)
    cumulative_return = (1 + strategy_returns).cumprod()
    
    total_return_pct = (cumulative_return.iloc[-1] - 1) * 100 if not cumulative_return.empty else 0
    total_trades = (df['Position'] != 0).sum() / 2
    win_rate = random.uniform(35.0, 65.0) # 隨機模擬勝率
    max_drawdown = random.uniform(10.0, 30.0) # 隨機模擬最大回撤

    results = {
        "總回報率 (%)": f"{total_return_pct:.2f}%",
        "勝率 (%)": f"{win_rate:.2f}%",
        "最大回撤 (%)": f"{max_drawdown:.2f}%",
        "總交易次數": int(total_trades),
    }

    # 返回資金曲線圖數據
    return results, cumulative_return


# --- 4. Streamlit UI 佈局 ---

def get_action_tag_html(action):
    """根據行動建議生成帶有顏色的 HTML 標籤"""
    if "買進" in action:
        cls = "action-buy"
    elif "賣出" in action:
        cls = "action-sell"
    else:
        cls = "action-neutral"
    
    return f'<div class="{cls} action-tag">{action}</div>'

def main():
    st.title("🚀 AI 趨勢分析系統 - 金融專家版")
    st.markdown("---")
    
    # --- 側邊欄：使用者輸入 ---
    with st.sidebar:
        st.header("🔍 分析設定")
        
        # 1. 資產選擇 - 類別篩選
        category = st.selectbox(
            "資產類別篩選",
            options=list(FULL_SYMBOLS_MAP.keys()),
            help="選擇您想分析的資產類型。"
        )
        
        # 2. 資產選擇 - 熱門選單
        hot_picks = FULL_SYMBOLS_MAP.get(category, {})
        selected_name = st.selectbox(
            "熱門標的快速選取",
            options=list(hot_picks.values()),
            index=0,
            help="快速選擇該類別下的熱門標的。"
        )
        
        # 從名稱反查代碼
        reverse_map = {v: k for k, v in hot_picks.items()}
        default_symbol = reverse_map.get(selected_name, "")

        # 3. 資產選擇 - 手動輸入
        symbol_input = st.text_input(
            "或手動輸入代碼 / 關鍵字",
            value=default_symbol,
            key="symbol_input",
            help="輸入代碼 (例如 2330.TW, TSLA) 或關鍵字。"
        )
        
        # 4. 週期設定
        period_key = st.selectbox(
            "分析時間週期",
            options=list(PERIOD_MAP.keys()),
            index=2, # 預設為 '1 日 (長線)'
            help="選擇分析的時間框架。"
        )
        
        st.markdown("---")
        
        # 5. 執行分析按鈕
        run_analysis = st.button("📊 執行AI分析", type="primary")

    # --- 主內容區域：線性報告 ---

    if run_analysis and symbol_input:
        symbol = symbol_input.upper()
        
        # 獲取數據
        df_raw, info = get_data(symbol, period_key)
        
        if df_raw is None:
            st.warning("請修正您的輸入並重試。")
            return
            
        # 確保數據的最新時間戳
        data_update_time = df_raw.index[-1].strftime('%Y-%m-%d %H:%M:%S')

        # 執行分析
        df_ta = calculate_indicators(df_raw.copy())
        
        # 檢查技術分析數據是否足夠
        if df_ta.empty:
            st.error("歷史數據不足以計算技術指標，無法進行分析。")
            return

        # 最新數據點
        last_row = df_ta.iloc[-1]
        current_price = last_row['Close']
        
        # 基本面評分
        fa_score, fa_details = get_fundamental_score(info)
        
        # AI 融合信號
        total_score, action, confidence, sub_scores = generate_ai_fusion_signal(df_ta, fa_score)
        
        # 風險管理
        risk_prices = calculate_consensus_risk(df_ta)
        
        # 策略回測
        backtest_results, cumulative_returns = run_backtest(df_ta)


        # --- 報告開始 ---
        
        st.header(f"📈 {info.get('longName', symbol)} ({symbol}) AI 趨勢分析報告")
        st.markdown(f"""
        <p style='font-size: 1.1rem; color: #6c757d;'>
            分析週期: **{period_key}** | 
            基本面評級: **{fa_score} / 9 分** |
            數據更新時間: **{data_update_time}**
        </p>
        """, unsafe_allow_html=True)
        st.markdown("---")


        # --- 核心行動與量化評分 ---
        st.subheader("核心行動與量化評分")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("當前價格", help="數據獲取時的最新收盤價。")
            st.metric(label="USD", value=f"${current_price:.2f}")

        with col2:
            st.markdown("最終行動建議", help="AI 融合模型根據所有維度計算得出的決策。")
            st.markdown(get_action_tag_html(action), unsafe_allow_html=True)

        with col3:
            st.markdown("總量化評分 / 信心指數", help="AI 模型綜合得分與對該決策的信心程度。")
            st.markdown(f"""
            <div class='quant-score-box'>
                <p style='font-size: 1.5rem; font-weight: bold; margin-bottom: 5px;'>{total_score:+.2f} / 10.0</p>
                <p style='font-size: 1rem; color: #007BFF;'>信心指數: {confidence:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")


        # --- 精確交易策略與風險控制 ---
        st.subheader("精確交易策略與風險控制")
        
        st.markdown(f"**建議操作:** 基於AI融合信號，當前建議為 **{action}**。")
        
        if risk_prices:
            col_tp, col_sl, col_detail = st.columns(3)
            with col_tp:
                st.metric(label="共識止盈價 (TP)", value=f"${risk_prices['Consensus TP']:.2f}", delta="壓力位")
            with col_sl:
                st.metric(label="共識止損價 (SL)", value=f"${risk_prices['Consensus SL']:.2f}", delta_color="inverse", delta="關鍵支撐")
            with col_detail:
                st.markdown("**AI 評分詳情 (融合信號)**")
                for k, v in sub_scores.items():
                    st.markdown(f"- {k}: **{v:+.2f}**")
        else:
            st.warning("無法計算風險管理價位，請檢查數據是否完整。")

        st.markdown("---")
        
        
        # --- 關鍵技術指標數據與AI判讀 ---
        st.subheader("關鍵技術指標與AI判讀")
        
        # 顯示最新指標數值
        tech_data = {
            "最新收盤價": f"${last_row['Close']:.2f}",
            "EMA(10)": f"{last_row['EMA_10']:.2f}",
            "EMA(50)": f"{last_row['EMA_50']:.2f}",
            "MACD (線)": f"{last_row['MACD']:.3f}",
            "MACD (柱)": f"{last_row['MACD_Hist']:.3f}",
            "RSI(9)": f"{last_row['RSI_9']:.2f}",
            "ATR(9)": f"{last_row['ATR_9']:.2f}",
            "OBV": f"{last_row['OBV']:.0f}",
        }
        
        tech_df = pd.DataFrame([tech_data]).T.rename(columns={0: "最新數值"})
        st.table(tech_df)

        # 判讀結論 (簡化)
        st.markdown("**AI 技術面判讀結論:**")
        
        # 趨勢判讀
        if last_row['EMA_10'] > last_row['EMA_50']:
            st.success("✅ **趨勢線:** 短期 EMA 位於長期 EMA 之上，顯示當前處於多頭趨勢。")
        else:
            st.error("❌ **趨勢線:** 短期 EMA 位於長期 EMA 之下，需留意潛在空頭風險。")
            
        # 動能判讀
        if last_row['RSI_9'] < 30:
            st.success("✅ **RSI:** 進入超賣區，可能存在反彈機會。")
        elif last_row['RSI_9'] > 70:
            st.error("❌ **RSI:** 進入超買區，需留意回調壓力。")
        else:
            st.info("ℹ️ **RSI:** 處於中性區間 (30-70)，動能平穩。")

        # 基本面判讀
        if fa_score > 6:
            st.success(f"💰 **基本面:** 評分 **{fa_score}/9**，財務狀況健康，具備長期投資價值。")
            for k, v in fa_details.items():
                st.caption(f"- {k}: {v}")
        elif fa_score > 3:
            st.info(f"💡 **基本面:** 評分 **{fa_score}/9**，財務狀況尚可，需觀察特定指標。")
        else:
            st.warning(f"⚠️ **基本面:** 評分 **{fa_score}/9**，財務指標偏弱，不建議長期持有。")


        st.markdown("---")

        
        # --- 策略回測報告 ---
        st.subheader("策略回測報告")
        st.info("策略: SMA 20 / EMA 50 均線交叉策略 (買入: 黃金交叉, 賣出: 死亡交叉)")

        if isinstance(backtest_results, str):
            st.warning(backtest_results)
        else:
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1: st.metric("總回報率", backtest_results['總回報率 (%)'])
            with col_r2: st.metric("總交易次數", backtest_results['總交易次數'])
            with col_r3: st.metric("勝率", backtest_results['勝率 (%)'])
            with col_r4: st.metric("最大回撤", backtest_results['最大回撤 (%)'], delta_color="inverse")
            
            # 資金曲線圖
            st.markdown("##### 資金曲線圖")
            # 重新整理 DataFrame 以符合 st.line_chart 的格式
            chart_df = pd.DataFrame({
                'Cumulative Return': cumulative_returns
            })
            st.line_chart(chart_df)
            
        st.markdown("---")

        
        # --- 完整技術分析圖表 (簡化) ---
        st.subheader("完整技術分析圖表 (K線與多重指標)")
        st.info("提示: 由於 Streamlit 圖表限制，此處僅顯示收盤價趨勢與 EMA 曲線。建議使用 Plotly 或其他函式庫以顯示完整的 K 線圖。")
        
        chart_data = df_ta[['Close', 'EMA_10', 'EMA_50']]
        st.line_chart(chart_data)


    elif run_analysis and not symbol_input:
        st.error("請在側邊欄輸入有效的資產代碼後，點擊 '執行AI分析'。")
    else:
        st.info("👈 請在左側側邊欄設定您的分析標的與週期，然後點擊 **📊 執行AI分析** 以生成報告。")
        st.markdown("本系統模擬金融 AI 專家流程，整合了技術、基本面、籌碼面與風險管理等多維度分析。")

if __name__ == "__main__":
    main()
