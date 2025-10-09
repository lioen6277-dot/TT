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
# 1. 全局配置與資產映射 (Global Configuration & Asset Map)
# ==============================================================================

st.set_page_config(
    page_title="AI趨勢分析📈", 
    page_icon="🚀", 
    layout="wide"
)

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
    # A. 美股核心 (US Stocks) - 個股 & ETF（以代碼英文排序）
    # ----------------------------------------------------
    "AAPL": {"name": "蘋果", "keywords": ["蘋果", "Apple", "AAPL"]},
    "ADBE": {"name": "Adobe", "keywords": ["Adobe", "ADBE"]},
    "AMD": {"name": "超微", "keywords": ["超微", "AMD"]},
    "AMZN": {"name": "亞馬遜", "keywords": ["亞馬遜", "Amazon", "AMZN"]},
    "CAT": {"name": "開拓重工", "keywords": ["開拓重工", "Caterpillar", "CAT"]},
    "COST": {"name": "好市多", "keywords": ["好市多", "Costco", "COST"]},
    "CRM": {"name": "Salesforce", "keywords": ["Salesforce", "CRM"]},
    "GOOGL": {"name": "谷歌/Alphabet", "keywords": ["谷歌", "Alphabet", "GOOGL", "GOOG"]},
    "HD": {"name": "家得寶", "keywords": ["家得寶", "HomeDepot", "HD"]},
    "INTC": {"name": "英特爾", "keywords": ["英特爾", "Intel", "INTC"]},
    "JPM": {"name": "摩根大通", "keywords": ["摩根大通", "JPMorgan", "JPM"]},
    "KO": {"name": "可口可樂", "keywords": ["可口可樂", "CocaCola", "KO"]},
    "LLY": {"name": "禮來", "keywords": ["禮來", "EliLilly", "LLY"]},
    "MCD": {"name": "麥當勞", "keywords": ["麥當勞", "McDonalds", "MCD"]},
    "META": {"name": "Meta/臉書", "keywords": ["臉書", "Meta", "FB", "META"]},
    "MSFT": {"name": "微軟", "keywords": ["微軟", "Microsoft", "MSFT"]},
    "NFLX": {"name": "網飛", "keywords": ["網飛", "Netflix", "NFLX"]},
    "NVDA": {"name": "輝達", "keywords": ["輝達", "英偉達", "AI", "NVDA", "Nvidia"]},
    "ORCL": {"name": "甲骨文", "keywords": ["甲骨文", "Oracle", "ORCL"]},
    "PEP": {"name": "百事", "keywords": ["百事", "Pepsi", "PEP"]},
    "PG": {"name": "寶潔", "keywords": ["寶潔", "P&G", "PG"]},
    "QCOM": {"name": "高通", "keywords": ["高通", "Qualcomm", "QCOM"]},
    "SPY": {"name": "SPDR 標普500 ETF", "keywords": ["SPY", "標普ETF"]},
    "QQQ": {"name": "Invesco QQQ Trust", "keywords": ["QQQ", "納斯達克ETF"]},
    "TSLA": {"name": "特斯拉", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "UNH": {"name": "聯合健康", "keywords": ["聯合健康", "UNH"]},
    "V": {"name": "Visa", "keywords": ["Visa", "V"]},
    "VOO": {"name": "Vanguard 標普500 ETF", "keywords": ["VOO", "Vanguard"]},
    "WMT": {"name": "沃爾瑪", "keywords": ["沃爾瑪", "Walmart", "WMT"]},
    "^DJI": {"name": "道瓊工業指數", "keywords": ["道瓊", "DowJones", "^DJI"]},
    "^GSPC": {"name": "S&P 500 指數", "keywords": ["標普", "S&P500", "^GSPC", "SPX"]},
    "^IXIC": {"name": "NASDAQ 綜合指數", "keywords": ["納斯達克", "NASDAQ", "^IXIC"]},

    # ----------------------------------------------------
    # B. 台灣市場 (TW Stocks/ETFs/Indices) - 依代碼數字排序
    # ----------------------------------------------------
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "台灣五十"]},
    "0056.TW": {"name": "元大高股息", "keywords": ["高股息", "0056"]},
    "00878.TW": {"name": "國泰永續高股息", "keywords": ["00878", "國泰永續"]},
    "1101.TW": {"name": "台泥", "keywords": ["台泥", "1101"]},
    "1301.TW": {"name": "台塑", "keywords": ["台塑", "1301"]},
    "2308.TW": {"name": "台達電", "keywords": ["台達電", "2308", "Delta"]},
    "2317.TW": {"name": "鴻海", "keywords": ["鴻海", "2317", "Foxconn"]},
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "2330", "TSMC"]},
    "2357.TW": {"name": "華碩", "keywords": ["華碩", "2357"]},
    "2379.TW": {"name": "瑞昱", "keywords": ["瑞昱", "2379"]},
    "2382.TW": {"name": "廣達", "keywords": ["廣達", "2382"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "2454", "MediaTek"]},
    "2603.TW": {"name": "長榮", "keywords": ["長榮", "2603", "航運"]},
    "2609.TW": {"name": "陽明", "keywords": ["陽明", "2609", "航運"]},
    "2615.TW": {"name": "萬海", "keywords": ["萬海", "2615", "航運"]},
    "2881.TW": {"name": "富邦金", "keywords": ["富邦金", "2881"]},
    "2882.TW": {"name": "國泰金", "keywords": ["國泰金", "2882"]},
    "2891.TW": {"name": "中信金", "keywords": ["中信金", "2891"]},
    "3017.TW": {"name": "奇鋐", "keywords": ["奇鋐", "3017", "散熱"]},
    "3231.TW": {"name": "緯創", "keywords": ["緯創", "3231"]},
    "^TWII": {"name": "台股指數", "keywords": ["台股指數", "加權指數", "^TWII"]},

    # ----------------------------------------------------
    # C. 加密貨幣 (Crypto) - 以英文名稱排序
    # ----------------------------------------------------
    "ADA-USD": {"name": "Cardano", "keywords": ["Cardano", "ADA", "ADA-USDT"]},
    "ASTER-USD": {"name": "Aster", "keywords": ["Aster", "ASTER-USD"]},
    "AVAX-USD": {"name": "Avalanche", "keywords": ["Avalanche", "AVAX", "AVAX-USDT"]},
    "BNB-USD": {"name": "幣安幣", "keywords": ["幣安幣", "BNB", "BNB-USDT"]},
    "BTC-USD": {"name": "比特幣", "keywords": ["比特幣", "BTC", "bitcoin", "BTC-USDT"]},
    "DOGE-USD": {"name": "狗狗幣", "keywords": ["狗狗幣", "DOGE", "DOGE-USDT"]},
    "DOT-USD": {"name": "Polkadot", "keywords": ["Polkadot", "DOT", "DOT-USDT"]},
    "ETH-USD": {"name": "以太坊", "keywords": ["以太坊", "ETH", "ethereum", "ETH-USDT"]},
    "LINK-USD": {"name": "Chainlink", "keywords": ["Chainlink", "LINK", "LINK-USDT"]},
    "SOL-USD": {"name": "Solana", "keywords": ["Solana", "SOL", "SOL-USDT"]},
    "XRP-USD": {"name": "瑞波幣", "keywords": ["瑞波幣", "XRP", "XRP-USDT"]},
}

# 建立第二層選擇器映射
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

# ==============================================================================
# 2. 數據獲取與基本資訊處理 (Data Fetching & Info)
# ==============================================================================

def get_symbol_from_query(query: str) -> str:
    """ 🎯 代碼解析函數：同時檢查 FULL_SYMBOLS_MAP 中的代碼和關鍵字 """
    query = query.strip()
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_upper == code: return code
        if any(query_upper == kw.upper() for kw in data["keywords"]): return code 
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]: return code
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        tw_code = f"{query}.TW"
        if tw_code in FULL_SYMBOLS_MAP: return tw_code
        return tw_code
    return query

@st.cache_data(ttl=3600, show_spinner="正在從 Yahoo Finance 獲取數據...")
def get_stock_data(symbol, period, interval):
    """ 獲取股價歷史數據，並進行數據清理 """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty: return pd.DataFrame()
        
        # 統一列名格式並篩選
        df.columns = [col.capitalize() for col in df.columns] 
        df.index.name = 'Date'
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # 確保數據時間戳是唯一的並刪除最後一行（通常是未完成的 K 線）
        df = df[~df.index.duplicated(keep='first')]
        df = df.iloc[:-1] 
        
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    """ 獲取公司名稱、所屬類別及貨幣代碼 """
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
        category = "未分類"
        if symbol.endswith(".TW"): category = "台股 (TW)"
        elif symbol.endswith("-USD"): category = "加密貨幣 (Crypto)"
        elif symbol.startswith("^"): category = "指數"
        elif currency == "USD": category = "美股 (US)"
        return {"name": name, "category": category, "currency": currency}
    except:
        return {"name": symbol, "category": "未分類", "currency": "USD"}

@st.cache_data
def get_currency_symbol(symbol):
    """ 根據代碼獲取貨幣符號 """
    currency_code = get_company_info(symbol).get('currency', 'USD')
    if currency_code == 'TWD': return 'NT$'
    elif currency_code == 'USD': return '$'
    elif currency_code == 'HKD': return 'HK$'
    else: return currency_code + ' '

# ==============================================================================
# 3. 多策略止損止盈函數 (SL/TP Strategy Functions) - 保持原始設計
# ==============================================================================

def support_resistance(df, lookback=60):
    df['Support'] = df['Low'].rolling(window=lookback).min() * 0.98
    df['Resistance'] = df['High'].rolling(window=lookback).max() * 1.02
    df['Volume_Filter'] = df['Volume'] > df['Volume'].rolling(50).mean() * 1.3
    df['SL'] = df['Support'].where(df['Volume_Filter'], df['Close'])
    df['TP'] = df['Resistance'].where(df['Volume_Filter'], df['Close'])
    return df

def bollinger_bands(df, period=50, dev=2.5):
    # 策略內部計算指標，保持原始設計
    df['SMA'] = df['Close'].rolling(window=period).mean()
    df['STD'] = df['Close'].rolling(window=period).std()
    df['Upper'] = df['SMA'] + (df['STD'] * dev)
    df['Lower'] = df['SMA'] - (df['STD'] * dev)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['Volume_Filter'] = df['Volume'] > df['Volume'].rolling(50).mean() * 1.2
    df['SL'] = df['Lower'].where((df['RSI'] < 30) & df['Volume_Filter'], df['Close'])
    df['TP'] = df['Upper'].where((df['RSI'] > 70) & df['Volume_Filter'], df['Close'])
    return df

def atr_stop(df, period=21, multiplier_sl=2.5, multiplier_tp=5):
    # 策略內部計算指標，保持原始設計
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=period)
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['SL'] = df['Close'] - (df['ATR'] * multiplier_sl)
    df['TP'] = df['Close'] + (df['ATR'] * multiplier_tp)
    df['Trend_Filter'] = df['ADX'] > 25
    df['SL'] = df['SL'].where(df['Trend_Filter'], df['Close'])
    df['TP'] = df['TP'].where(df['Trend_Filter'], df['Close'])
    return df

def donchian_channel(df, period=50):
    df['Upper'] = df['High'].rolling(window=period).max()
    df['Lower'] = df['Low'].rolling(window=period).min()
    macd = ta.trend.macd(df['Close'])
    df['MACD'] = macd
    df['Volume_Filter'] = df['Volume'] > df['Volume'].rolling(50).mean() * 1.3
    df['SL'] = df['Lower'].where((df['MACD'] < 0) & df['Volume_Filter'], df['Close'])
    df['TP'] = df['Upper'].where((df['MACD'] > 0) & df['Volume_Filter'], df['Close'])
    return df

def keltner_channel(df, period=30, atr_multiplier=2.5):
    # 策略內部計算指標，保持原始設計
    ema = ta.trend.ema_indicator(df['Close'], window=period)
    atr = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['Upper'] = ema + (atr * atr_multiplier)
    df['Lower'] = ema - (atr * atr_multiplier)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    obv = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['OBV_Filter'] = obv > obv.shift(1)
    df['SL'] = df['Lower'].where((df['RSI'] < 30) & df['OBV_Filter'], df['Close'])
    df['TP'] = df['Upper'].where((df['RSI'] > 70) & df['OBV_Filter'], df['Close'])
    return df

def ichimoku_cloud(df):
    # 策略內部計算指標，保持原始設計
    adx = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    volume_filter = df['Volume'] > df['Volume'].rolling(20).mean() * 1.2
    ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
    df['Senkou_A'] = ichimoku.ichimoku_a()
    df['Senkou_B'] = ichimoku.ichimoku_b()
    df['SL'] = df['Senkou_B'].where((df['Close'] < df['Senkou_B']) & (adx > 25) & volume_filter, df['Close'])
    df['TP'] = df['Senkou_A'].where((df['Close'] > df['Senkou_A']) & (adx > 25) & volume_filter, df['Close'])
    return df

def ma_crossover(df, fast=20, slow=50):
    # 策略內部計算指標，保持原始設計
    fast_ema = ta.trend.ema_indicator(df['Close'], window=fast)
    slow_ema = ta.trend.ema_indicator(df['Close'], window=slow)
    macd = ta.trend.macd(df['Close'])
    obv = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    obv_filter = obv > obv.shift(1)
    df['SL'] = slow_ema.where((fast_ema < slow_ema) & (macd < 0) & obv_filter, df['Close'])
    df['TP'] = fast_ema.where((fast_ema > slow_ema) & (macd > 0) & obv_filter, df['Close'])
    return df

def vwap(df):
    # 策略內部計算指標，保持原始設計
    df['VWAP'] = ta.volume.volume_weighted_average_price(df['High'], df['Low'], df['Close'], df['Volume'])
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    volume_filter = df['Volume'] > df['Volume'].rolling(20).mean() * 1.2
    df['SL'] = df['VWAP'].where((df['Close'] < df['VWAP']) & (df['RSI'] < 30) & volume_filter, df['Close'])
    df['TP'] = df['VWAP'].where((df['Close'] > df['VWAP']) & (df['RSI'] > 70) & volume_filter, df['Close'])
    return df

def parabolic_sar(df):
    # 策略內部計算指標，保持原始設計
    sar = ta.trend.psar_down(df['High'], df['Low'], df['Close'])
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    volume_filter = df['Volume'] > df['Volume'].rolling(20).mean() * 1.2
    df['SL'] = sar.where((df['Close'] < sar) & (df['RSI'] < 30) & volume_filter, df['Close'])
    df['TP'] = sar.where((df['Close'] > sar) & (df['RSI'] > 70) & volume_filter, df['Close'])
    return df

STRATEGY_FUNCTIONS = {
    "支撐阻力": support_resistance,
    "布林通道": bollinger_bands,
    "ATR停損": atr_stop,
    "唐奇安通道": donchian_channel,
    "肯特納通道": keltner_channel,
    "一目均衡表": ichimoku_cloud,
    "均線交叉": ma_crossover,
    "VWAP": vwap,
    "拋物線SAR": parabolic_sar,
}

def get_consensus_levels(df, current_price):
    """ 多策略共識 SL/TP 計算 """
    all_results = {}
    sl_list, tp_list = [], []
    for name, func in STRATEGY_FUNCTIONS.items():
        try:
            # 使用副本確保原始 DF 不被策略函數修改
            df_copy = df.copy() 
            res = func(df_copy)
            sl = res['SL'].iloc[-1] if 'SL' in res.columns else np.nan
            tp = res['TP'].iloc[-1] if 'TP' in res.columns else np.nan
            sl_valid = sl if pd.notna(sl) and abs(sl-current_price) > 0.01 else np.nan
            tp_valid = tp if pd.notna(tp) and abs(tp-current_price) > 0.01 else np.nan
            all_results[name] = {'SL': sl_valid, 'TP': tp_valid}
            if pd.notna(sl_valid): sl_list.append(sl_valid)
            if pd.notna(tp_valid): tp_list.append(tp_valid)
        except Exception:
            all_results[name] = {'SL': np.nan, 'TP': np.nan}
    
    # 計算共識均值
    consensus_sl = np.nanmean(sl_list) if sl_list else np.nan
    consensus_tp = np.nanmean(tp_list) if tp_list else np.nan
    return consensus_sl, consensus_tp, {k:[v['SL'],v['TP']] for k,v in all_results.items()}


# ==============================================================================
# 4. 核心技術指標與基本面計算 (Core Indicators & Fundamentals)
# ==============================================================================

def calculate_comprehensive_indicators(df):
    """
    【核心修正：指標計算統一】
    整合原始的 calculate_all_indicators 和 calculate_technical_indicators 兩組指標參數，
    確保所有下游功能（AI信號、技術分析表、回測）所需的所有指標欄位都被計算。
    """
    
    # --- 1. 趨勢指標 (Trend Indicators) ---
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20) 
    
    # MACD (AI Signal 參數: 12/26/9 - MACD_AI, Display 參數: 8/17/9 - MACD_DISP)
    macd_ai = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
    df['MACD_Line_AI'] = macd_ai.macd()
    df['MACD_Signal_AI'] = macd_ai.macd_signal()
    df['MACD_Hist_AI'] = macd_ai.macd_diff() # 原始 AI Signal 使用此名稱
    
    macd_disp = ta.trend.MACD(df['Close'], window_fast=8, window_slow=17, window_sign=9)
    df['MACD_Line'] = macd_disp.macd()      # 原始 Display 使用此名稱
    df['MACD_Signal'] = macd_disp.macd_signal()
    df['MACD'] = macd_disp.macd_diff()      # 原始 Display 使用此名稱 (柱狀圖)
    
    # ADX (AI Signal 參數: 14 - ADX_AI, Display 參數: 9 - ADX)
    df['ADX_AI'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=9)
    
    # Ichimoku (原始 AI Signal/Plotting 需求)
    ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
    df['Ichimoku_A'] = ichimoku.ichimoku_a()
    df['Ichimoku_B'] = ichimoku.ichimoku_b()
    
    # --- 2. 動能指標 (Momentum Indicators) ---
    # RSI (AI Signal 參數: 9, 14 - RSI_9, RSI_14; Display 參數: 9 - RSI)
    df['RSI_9'] = ta.momentum.rsi(df['Close'], window=9)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    df['RSI'] = df['RSI_9'] # 原始 Display 使用 RSI(9)
    
    # --- 3. 波動率指標 (Volatility Indicators) ---
    # Bollinger Bands (AI Signal/Display 參數: 20/2)
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    
    # ATR (AI Signal 參數: 14 - ATR_AI, Display 參數: 9 - ATR)
    df['ATR_AI'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=9)
    
    # --- 4. 量能指標 (Volume Indicators) ---
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['CMF'] = ta.volume.chaikin_money_flow(df['High'], df['Low'], df['Close'], df['Volume'], window=20)
    df['MFI'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'], window=14)
    
    return df

@st.cache_data(ttl=3600)
def get_fundamental_ratings(symbol):
    """
    【核心修正：基本面評分統一】
    整合原始的 calculate_advanced_fundamental_rating (AI Score) 
    和 calculate_fundamental_rating (Display Score) 邏輯。
    """
    results = {
        "AI_SCORE": {"score": 0, "summary": "不適用", "details": {}},
        "DISPLAY_SCORE": {"Combined_Rating": 0.0, "Message": "不適用：指數或加密貨幣無標準基本面數據。", "Details": None}
    }
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 排除指數和加密貨幣
        if info.get('quoteType') in ['INDEX', 'CRYPTOCURRENCY', 'ETF'] or symbol.startswith('^') or symbol.endswith('-USD'):
            return results

        # --- 1. 原始 Advanced Rating (AI Fusion Score) 邏輯 ---
        ai_score, ai_details = 0, {}
        roe = info.get('returnOnEquity')
        if roe and roe > 0.15: ai_score += 2; ai_details['ROE > 15%'] = f"✅ {roe:.2%}"
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity is not None and debt_to_equity < 50: ai_score += 2; ai_details['負債權益比 < 50'] = f"✅ {debt_to_equity:.2f}"
        revenue_growth = info.get('revenueGrowth')
        if revenue_growth and revenue_growth > 0.1: ai_score += 1; ai_details['營收年增 > 10%'] = f"✅ {revenue_growth:.2%}"
        pe = info.get('trailingPE')
        if pe and 0 < pe < 15: ai_score += 1; ai_details['P/E < 15'] = f"✅ {pe:.2f}"
        peg = info.get('pegRatio')
        if peg and 0 < peg < 1: ai_score += 1; ai_details['PEG < 1'] = f"✅ {peg:.2f}"
        ai_summary = "頂級優異" if ai_score >= 5 else "良好穩健" if ai_score >= 3 else "中性警示"
        results["AI_SCORE"] = {"score": ai_score, "summary": ai_summary, "details": ai_details}
        
        # --- 2. 原始 Display Rating (Display Score) 邏輯 ---
        
        # 準備變數
        trailingPE = info.get('trailingPE', 99)
        freeCashFlow = info.get('freeCashflow', 0)
        totalCash = info.get('totalCash', 0)
        totalDebt = info.get('totalDebt', 0)
        
        # 1. 成長與效率評分 (ROE) (總分 3)
        roe_score = 0
        if roe and roe > 0.15: roe_score = 3
        elif roe and roe > 0.10: roe_score = 2
        elif roe and roe > 0: roe_score = 1
        
        # 2. 估值評分 (PE) (總分 3)
        pe_score = 0
        if trailingPE and 0 < trailingPE < 15: pe_score = 3
        elif trailingPE and 0 < trailingPE < 25: pe_score = 2
        elif trailingPE and 0 < trailingPE < 35: pe_score = 1
        
        # 3. 現金流與償債能力 (總分 3)
        cf_score = 0
        cash_debt_ratio = (totalCash / totalDebt) if totalDebt and totalDebt != 0 else 100
        if freeCashFlow and freeCashFlow > 0 and cash_debt_ratio > 2: cf_score = 3
        elif freeCashFlow and freeCashFlow > 0 and cash_debt_ratio > 1: cf_score = 2
        elif freeCashFlow and freeCashFlow > 0: cf_score = 1

        combined_rating = roe_score + pe_score + cf_score
        message = "頂級優異 (9分滿分)" if combined_rating >= 8 else "良好穩健" if combined_rating >= 5 else "中性警示" if combined_rating >= 3 else "基本面較弱"
        
        details = {
            "ROE 評分 (滿分3)": roe_score,
            "P/E 評分 (滿分3)": pe_score,
            "現金流/債務評分 (滿分3)": cf_score,
        }
        
        results["DISPLAY_SCORE"] = {
            "Combined_Rating": combined_rating, 
            "Message": message, 
            "Details": details
        }
        
        return results
        
    except Exception:
        return results

# ==============================================================================
# 5. AI 融合信號與技術分析解釋 (AI Signal & Interpretation)
# ==============================================================================

def generate_ai_fusion_signal(df, fa_rating, chips_news_data):
    """ 
    AI 融合信號：基於原始設計，需要確保使用 calculate_comprehensive_indicators 
    所產生的帶 '_AI' 或原始 AI 預期名稱的欄位。 
    """
    required_cols = ['EMA_10', 'EMA_50', 'EMA_200', 'RSI_9', 'MACD_Hist_AI', 'ADX_AI', 'CMF', 'MFI', 'BB_Low', 'BB_High']
    df_clean = df.dropna(subset=required_cols)
    if df_clean.empty or len(df_clean) < 2: 
        return {'action': '數據不足', 'score': 0, 'confidence': 0, 'ai_opinions': {'核心問題': '數據點不足以生成可靠信號'}}
    
    last, prev = df_clean.iloc[-1], df_clean.iloc[-2]
    opinions = {}
    trend_score, momentum_score, volume_score, volatility_score = 0, 0, 0, 0
    
    # 趨勢分析
    if last['EMA_10'] > last['EMA_50'] > last['EMA_200']: trend_score += 2; opinions['趨勢分析 (MA)'] = '✅ 強多頭排列'
    elif last['EMA_10'] < last['EMA_50'] < last['EMA_200']: trend_score -= 2; opinions['趨勢分析 (MA)'] = '❌ 強空頭排列'
    if last['ADX_AI'] > 25: trend_score *= 1.2; opinions['趨勢強度 (ADX)'] = '✅ 強趨勢確認'
    
    # 動能分析
    if last['RSI_9'] > 50: momentum_score += 1; opinions['動能 (RSI)'] = '✅ 多頭區域'
    else: momentum_score -= 1
    if last['MACD_Hist_AI'] > 0 and last['MACD_Hist_AI'] > prev['MACD_Hist_AI']: momentum_score += 1.5; opinions['動能 (MACD)'] = '✅ 多頭動能增強'
    elif last['MACD_Hist_AI'] < 0 and last['MACD_Hist_AI'] < prev['MACD_Hist_AI']: momentum_score -= 1.5; opinions['動能 (MACD)'] = '❌ 空頭動能增強'
    
    # 量能分析
    if last['CMF'] > 0: volume_score += 1; opinions['資金流 (CMF)'] = '✅ 資金淨流入'
    else: volume_score -=1
    if last['MFI'] < 20: volume_score += 1.5; opinions['資金流 (MFI)'] = '✅ 資金超賣區'
    elif last['MFI'] > 80: volume_score -= 1.5; opinions['資金流 (MFI)'] = '❌ 資金超買區'
    
    # 波動率分析
    if last['Close'] < last['BB_Low']: volatility_score += 1; opinions['波動率 (BB)'] = '✅ 觸及下軌 (潛在反彈)'
    elif last['Close'] > last['BB_High']: volatility_score -= 1; opinions['波動率 (BB)'] = '❌ 觸及上軌 (潛在回調)'
    
    # 融合計算
    ta_score = trend_score + momentum_score + volume_score + volatility_score
    # 使用 AI_SCORE (滿分7分制)
    fa_score = ((fa_rating.get('score', 0) / 7.0) - 0.5) * 8.0 
    # 原始程式碼中的籌碼數據 (此處假設 chips_news_data 已被外部獲取)
    chips_score = (chips_news_data.get('inst_hold_pct', 0) - 0.4) * 5 
    
    total_score = ta_score * 0.55 + fa_score * 0.25 + chips_score * 0.20
    confidence = min(100, 40 + abs(total_score) * 7)
    
    action = '中性/觀望'
    if total_score > 4: action = '強力買進'
    elif total_score > 1.5: action = '買進'
    elif total_score < -4: action = '強力賣出'
    elif total_score < -1.5: action = '賣出'
    
    return {'action': action, 'score': total_score, 'confidence': confidence, 'ai_opinions': opinions}

def get_technical_data_df(df):
    """獲取最新的技術指標數據和AI結論，並根據您的進階原則進行判讀。"""
    
    COLOR_MAP = {
        "red": "#FA8072", 
        "green": "#6BE279",
        "orange": "#FFD700",
        "blue": "#ADD8E6",
        "grey": "#A9A9A9",
    }
    
    if df.empty or len(df) < 200: return pd.DataFrame()
    df_clean = df.dropna().copy()
    if df_clean.empty: return pd.DataFrame()
    
    last_row = df_clean.iloc[-1]
    prev_row = df_clean.iloc[-2] if len(df_clean) >= 2 else last_row

    required_cols = ['EMA_10', 'EMA_50', 'EMA_200', 'RSI', 'MACD', 'ADX', 'ATR', 'BB_High', 'BB_Low']
    if not all(col in last_row for col in required_cols):
        return pd.DataFrame()

    indicators = {}
    indicators['價格 vs. EMA 10/50/200'] = last_row['Close']
    indicators['RSI (9) 動能'] = last_row['RSI']
    indicators['MACD (8/17/9) 柱狀圖'] = last_row['MACD']
    indicators['ADX (9) 趨勢強度'] = last_row['ADX']
    indicators['ATR (9) 波動性'] = last_row['ATR']
    indicators['布林通道 (BB: 20/2)'] = last_row['Close']
    
    data = []
    
    for name, value in indicators.items():
        conclusion, color_key = "", "grey"

        if 'EMA 10/50/200' in name:
            # 趨勢分析
            ema_10 = last_row['EMA_10']
            ema_50 = last_row['EMA_50']
            ema_200 = last_row['EMA_200']
            if ema_10 > ema_50 and ema_50 > ema_200:
                conclusion, color_key = f"**強多頭：MA 多頭排列** (10>50>200)", "red"
            elif ema_10 < ema_50 and ema_50 < ema_200:
                conclusion, color_key = f"**強空頭：MA 空頭排列** (10<50<200)", "green"
            elif ema_10 > ema_50 or ema_50 > ema_200:
                 conclusion, color_key = "中性偏多：MA 偏多排列", "orange"
            else:
                conclusion, color_key = "盤整：MA 交錯", "blue"
            
        elif 'RSI' in name:
            # 動能分析 (RSI 9)
            if value > 70:
                conclusion, color_key = "空頭：超買區域 (> 70)，潛在回調", "green" 
            elif value < 30:
                conclusion, color_key = "多頭：超賣區域 (< 30)，潛在反彈", "red"
            elif value > 50:
                conclusion, color_key = "多頭：RSI > 50，位於強勢區間", "red"
            else:
                conclusion, color_key = "空頭：RSI < 50，位於弱勢區間", "green"
        
        elif 'MACD' in name:
            # 動能趨勢 (MACD 柱狀圖)
            if value > 0 and value > prev_row['MACD']:
                conclusion, color_key = "強化：多頭動能增強 (紅柱放大)", "red"
            elif value < 0 and value < prev_row['MACD']:
                conclusion, color_key = "強化：空頭動能增強 (綠柱放大)", "green"
            elif value > 0 and value < prev_row['MACD']:
                 conclusion, color_key = "中性：多頭動能收縮 (潛在回調)", "orange"
            elif value < 0 and value > prev_row['MACD']:
                 conclusion, color_key = "中性：空頭動能收縮 (潛在反彈)", "orange"
            else:
                conclusion, color_key = "中性：動能盤整 (柱狀收縮)", "blue"
        
        elif 'ADX' in name:
            # 趨勢強度 (ADX 9)
            if value >= 40:
                conclusion, color_key = f"**強趨勢：極強趨勢** (ADX >= 40)", "red"
            elif value >= 25:
                conclusion, color_key = f"趨勢：趨勢確認 (ADX >= 25)", "orange"
            else:
                conclusion, color_key = f"盤整：弱勢或橫盤整理 (ADX < 25)", "blue"
        
        elif 'ATR' in name:
            # 波動性 (ATR 9) - 增加判斷以提供更有用的訊息
            atr_ratio = value / last_row['Close'] * 100
            atr_mean = df_clean['ATR'].mean()
            if value > atr_mean * 1.5:
                conclusion, color_key = f"高波動：{atr_ratio:.2f}% (潛在機會/風險)", "orange"
            elif value < atr_mean * 0.75:
                conclusion, color_key = f"低波動：{atr_ratio:.2f}% (潛在突破/沉寂)", "blue"
            else:
                conclusion, color_key = f"中性：正常波動性 ({atr_ratio:.2f}% 寬度)", "blue"

        elif '布林通道' in name:
            # 布林通道 (BB 20, 2)
            bb_width_pct = (last_row['BB_High'] - last_row['BB_Low']) / last_row['Close'] * 100
            
            if value > last_row['BB_High']:
                conclusion, color_key = f"**空頭：突破上軌** (潛在回調)", "green"
            elif value < last_row['BB_Low']:
                conclusion, color_key = f"**多頭：跌破下軌** (潛在反彈)", "red"
            else:
                conclusion, color_key = f"中性：在上下軌間 ({bb_width_pct:.2f}% 寬度)", "blue"

        # 應用顏色樣式到結論文本
        colored_conclusion = f"<span style='color: {COLOR_MAP.get(color_key, COLOR_MAP['grey'])}; font-weight: bold;'><strong>{conclusion}</strong></span>"
        # 將指標名稱、原始值、帶有顏色的結論文本、以及用於背景色的 'color_key' 存入
        data.append([name, value, colored_conclusion, color_key])

    technical_df = pd.DataFrame(data, columns=['指標名稱', '最新值', '分析結論', '顏色'])
    return technical_df

# ==============================================================================
# 6. 回測與繪圖邏輯 (Backtest & Plotting)
# ==============================================================================
def run_backtest(df, initial_capital=100000, commission_rate=0.001):
    """ 
    執行基於 SMA 20 / EMA 50 交叉的簡單回測。
    策略: 黃金交叉買入 (做多)，死亡交叉清倉 (賣出)。
    """
    if df.empty or len(df) < 51: 
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "數據不足 (少於 51 週期) 或計算錯誤。"}

    data = df.copy()
    
    # 確保 SMA_20 和 EMA_50 已計算
    if 'SMA_20' not in data.columns or 'EMA_50' not in data.columns:
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20) 
        data['EMA_50'] = ta.trend.ema_indicator(data['Close'], window=50)

    # 黃金/死亡交叉信號
    data['Prev_MA_State'] = (data['SMA_20'].shift(1) > data['EMA_50'].shift(1))
    data['Current_MA_State'] = (data['SMA_20'] > data['EMA_50'])
    data['Signal'] = np.where( 
        (data['Current_MA_State'] == True) & (data['Prev_MA_State'] == False), 1, 0 # Buy
    )
    data['Signal'] = np.where(
        (data['Current_MA_State'] == False) & (data['Prev_MA_State'] == True), -1, data['Signal'] # Sell
    )
    
    data = data.dropna()
    if data.empty: 
        return {"total_return": 0, "win_rate": 0, "max_drawdown": 0, "total_trades": 0, "message": "指標計算後數據不足。"}

    # --- 模擬交易邏輯 (原樣保留) ---
    capital = [initial_capital]
    position = 0
    buy_price = 0
    trades = []
    current_capital = initial_capital
    
    for i in range(1, len(data)):
        current_close = data['Close'].iloc[i]

        # 1. Buy Signal
        if data['Signal'].iloc[i] == 1 and position == 0:
            position = 1
            buy_price = current_close
            current_capital -= current_capital * commission_rate

        # 2. Sell Signal (Exit Trade)
        elif data['Signal'].iloc[i] == -1 and position == 1:
            sell_price = current_close
            profit = (sell_price - buy_price) / buy_price
            
            trades.append({ 
                'entry_date': data.index[i], 
                'exit_date': data.index[i], 
                'profit_pct': profit, 
                'is_win': profit > 0 
            })
            current_capital *= (1 + profit)
            current_capital -= current_capital * commission_rate
            position = 0
            
        current_value = current_capital
        if position == 1:
            current_value = current_capital * (current_close / buy_price)
            
        capital.append(current_value)

    # 3. Handle open position (清倉) - 確保最終資金曲線反映實際淨值
    if position == 1:
        sell_price = data['Close'].iloc[-1]
        profit = (sell_price - buy_price) / buy_price
        
        trades.append({ 
            'entry_date': data.index[-1], 
            'exit_date': data.index[-1], 
            'profit_pct': profit, 
            'is_win': profit > 0 
        })
        current_capital *= (1 + profit)
        current_capital -= current_capital * commission_rate
        
        # 將最終清倉後的淨值更新到 capital 列表的最後一個元素
        if capital:
            capital[-1] = current_capital 
    
    # 由於 capital 列表包含 initial_capital，其長度應為 len(data)
    index_to_use = data.index[:len(capital)]
    capital_series = pd.Series(capital[:len(index_to_use)], index=index_to_use)

    # --- 應用使用者要求的計算邏輯 ---
    # total_return 應計算最終淨值與初始資金的差異，而不是您提供的靜態值。
    # 我已根據標準回測原則，將您的計算公式調整為使用 `current_capital`。
    total_return = ((current_capital - initial_capital) / initial_capital) * 100
    total_trades = len(trades)
    win_rate = (sum(1 for t in trades if t['is_win']) / total_trades) * 100 if total_trades > 0 else 0
    
    # 最大回撤計算
    max_value = capital_series.expanding(min_periods=1).max()
    drawdown = (capital_series - max_value) / max_value
    max_drawdown = abs(drawdown.min()) * 100
    
    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "total_trades": total_trades,
        "message": f"回測區間 {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}。",
        "capital_curve": capital_series
        "trades_list": trades
    }

def plot_chart(df, symbol_name, period_name, sl_tp_levels, strategy_details, backtest_curve):
    """
    K線、技術指標與交易目標繪圖
    (此函數假設 Streamlit 介面和 Plotly 繪圖邏輯從原始檔案末端延續並正確使用所有指標)
    """
    
    # 確保 DF 包含所有核心指標欄位
    df = df.dropna(subset=['SMA_20', 'EMA_50', 'BB_High', 'BB_Low', 'MACD', 'RSI']) 

    # 創建主圖 (K線/MA/BB) 和三個子圖 (MACD, RSI, Volume)
    fig = make_subplots(
        rows=4, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.5, 0.15, 0.15, 0.20] # 調整子圖高度比例
    )

    # --- Row 1: K線圖, MA, BB, SL/TP ---
    
    # 1. K線圖
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=f'{symbol_name} K線'
        ),
        row=1, col=1
    )

    # 2. 移動平均線 (SMA 20, EMA 50, EMA 200)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='blue', width=1), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='purple', width=1), name='EMA 200'), row=1, col=1)

    # 3. 布林通道 (BB)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=0.5), name='BB Upper', opacity=0.5), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=0.5), name='BB Lower', opacity=0.5, fill='tonexty', fillcolor='rgba(128,128,128,0.05)'), row=1, col=1)

    # 4. SL/TP 共識線 (來自 get_consensus_levels)
    if pd.notna(sl_tp_levels['SL']):
        fig.add_trace(go.Scatter(x=[df.index[-1]], y=[sl_tp_levels['SL']], mode='lines+markers', line=dict(dash='dash', color='green'), name=f'共識 SL ({sl_tp_levels["SL"]:,.2f})', marker=dict(symbol='triangle-down', size=8, color='green')), row=1, col=1)
    if pd.notna(sl_tp_levels['TP']):
        fig.add_trace(go.Scatter(x=[df.index[-1]], y=[sl_tp_levels['TP']], mode='lines+markers', line=dict(dash='dash', color='red'), name=f'共識 TP ({sl_tp_levels["TP"]:,.2f})', marker=dict(symbol='triangle-up', size=8, color='red')), row=1, col=1)
    
    # --- Row 2: MACD ---
    fig.add_trace(go.Bar(x=df.index, y=df['MACD'], name='MACD Hist', marker_color=np.where(df['MACD'] >= 0, 'red', 'green')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Line'], line=dict(color='blue'), name='MACD Line'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='orange'), name='MACD Signal'), row=2, col=1)

    # --- Row 3: RSI ---
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI (9)'), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0, row=3, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=3, col=1)

    # --- Row 4: Volume (OBV, CMF, MFI, Volume) ---
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='rgba(0,0,0,0.5)', opacity=0.5), row=4, col=1)
    
    # 更新佈局
    fig.update_layout(
        title=f'<b style="color: #FA8072;">{symbol_name}</b> {period_name} K線與技術分析',
        xaxis_rangeslider_visible=False,
        height=900,
        showlegend=True,
        template='plotly_white',
    )
    
    fig.update_xaxes(showgrid=False, row=1, col=1)
    fig.update_yaxes(title_text='價格', row=1, col=1)
    fig.update_yaxes(title_text='MACD', row=2, col=1)
    fig.update_yaxes(title_text='RSI', range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text='量能', row=4, col=1)
    
    # 增加資金曲線子圖 (原設計的一部分)
    if backtest_curve is not None and not backtest_curve.empty:
        # 在 Streamlit 中，通常會將資金曲線獨立出來或在主圖中以折線圖呈現。
        # 為了完整性，這裡假定它獨立繪製。
        st.subheader("💰 回測資金曲線")
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(x=backtest_curve.index, y=backtest_curve.values, mode='lines', name='資金淨值曲線', line=dict(color='green', width=2)))
        fig_curve.update_layout(
            title='SMA 20 / EMA 50 交叉策略資金淨值變化',
            yaxis_title='淨值',
            height=300
        )
        st.plotly_chart(fig_curve, use_container_width=True)
        
    return fig

# ==============================================================================
# 7. STREAMLIT 主應用邏輯 (Main Streamlit Logic)
# ==============================================================================

def display_homepage():
    st.markdown("<h1 style='color: #FA8072;'>🚀 歡迎使用 AI 趨勢分析</h1>", unsafe_allow_html=True)
    st.markdown(
        "請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 "
        "<span style='color: #FA8072; font-weight: bold;'>『📊 執行AI分析』</span> 按鈕開始。",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.subheader("📝 使用步驟：")
    st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
    st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
    st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分` (短期)、`1 日` (中長線)）。")
    st.markdown(
        "4. **執行分析**：點擊 <span style='color: #FA8072; font-weight: bold;'>『📊 執行AI分析』</span>，"
        "AI將融合多種策略，提供最精準的交易參考價位。",
        unsafe_allow_html=True
    )

def main():
    # -----------------------------
    # 初始化 Session State
    # -----------------------------
    if 'last_search_symbol' not in st.session_state:
        st.session_state.last_search_symbol = None
    if 'data_df' not in st.session_state:
        st.session_state.data_df = pd.DataFrame()
    if 'symbol_info' not in st.session_state:
        st.session_state.symbol_info = {}
    if 'fa_ratings' not in st.session_state:
        st.session_state.fa_ratings = {}
    if 'ai_signal' not in st.session_state:
        st.session_state.ai_signal = {}
    if 'sl_tp_levels' not in st.session_state:
        st.session_state.sl_tp_levels = {}
    if 'strategy_details' not in st.session_state:
        st.session_state.strategy_details = {}
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = {}

    # -----------------------------
    # 側邊欄：參數設定
    # -----------------------------
    st.sidebar.title("參數設定區")

    # 1. 選擇資產類別（預期 CATEGORY_HOT_OPTIONS 已定義）
    category_selection = st.sidebar.selectbox(
        "選擇資產類別:",
        list(CATEGORY_HOT_OPTIONS.keys())
    )

# 2. 熱門標的選擇
hot_options = CATEGORY_HOT_OPTIONS.get(category_selection, {})
option_list = list(hot_options.keys())

# 嘗試找到「台積電」在 option_list 的 index（或包含 '2330'）
found_idx = None
for i, key in enumerate(option_list):
    key_lower = str(key)
    if '台積電' in key_lower or '2330' in key_lower:
        found_idx = i
        break

# selectbox 的 list 包含一個空選項在最前面，所以 index 需要 +1
default_index = (found_idx + 1) if found_idx is not None else 0

selected_option = st.sidebar.selectbox(
    "或從熱門清單選擇:",
    [""] + option_list,
    index=default_index
)

    # 3. 自行輸入
    default_symbol = hot_options[selected_option] if selected_option else st.session_state.get('last_input', "")
    search_query = st.sidebar.text_input("或直接輸入代碼/名稱 (例如: 2330, NVDA)", value=default_symbol).strip()

    # 4. 週期選擇（預期 PERIOD_MAP 已定義）
    period_name = st.sidebar.selectbox(
        "K線週期選擇:",
        list(PERIOD_MAP.keys()),
        index=2  # 預設為 '1 日'
    )
    period, interval = PERIOD_MAP[period_name]

    st.sidebar.markdown("---")

    # 5. 執行按鈕
    if st.sidebar.button("📊 執行AI分析") and search_query:
        st.session_state.last_input = search_query

        # 取得 symbol 與公司資訊（由使用者提供的 helper functions）
        symbol = get_symbol_from_query(search_query)
        st.session_state.last_search_symbol = symbol
        info = get_company_info(symbol)
        st.session_state.symbol_info = info

        st.title(f"【{info['name']} ({symbol})】AI 趨勢分析報告")
        st.markdown(f"**類別：** {info['category']} | **週期：** {period_name}")
        st.markdown("---")

        # 主計算流程（用 spinner 包裝）
        with st.spinner(f"正在獲取 {info['name']} 的數據並進行運算..."):
            # 取得歷史價格資料
            df = get_stock_data(symbol, period, interval)

            if df.empty:
                st.error(f"無法獲取 {symbol} 的數據。請檢查代碼或稍後再試。")
                st.session_state.data_df = pd.DataFrame()
                return

            # 指標計算與狀態存放
            df = calculate_comprehensive_indicators(df)
            st.session_state.data_df = df
            current_price = df['Close'].iloc[-1]

            # 基本面評分
            fa_ratings = get_fundamental_ratings(symbol)
            st.session_state.fa_ratings = fa_ratings
            ai_rating = fa_ratings.get('AI_SCORE', {})

            # SL/TP 共識與策略細節
            consensus_sl, consensus_tp, strategy_details = get_consensus_levels(df.copy(), current_price)
            st.session_state.sl_tp_levels = {'SL': consensus_sl, 'TP': consensus_tp}
            st.session_state.strategy_details = strategy_details

            # AI 融合信號
            ai_signal = generate_ai_fusion_signal(df, ai_rating, {'inst_hold_pct': 0})
            st.session_state.ai_signal = ai_signal

            # 幣別符號
            currency = get_currency_symbol(symbol)

            # 回測
            backtest_results = run_backtest(df.copy())
            st.session_state.backtest_results = backtest_results

        # ============================
        # 報告區塊（依你希望的順序呈現）
        # ============================

        # 1. 核心行動與量化評分 (AI Fusion Signal)
        st.header("核心行動與量化評分")
        col_signal, col_price = st.columns([2, 1])

        with col_signal:
            st.subheader("🤖 AI 融合信號")
            score_str = f"({ai_signal.get('score', 0):+.2f})"
            action = ai_signal.get('action', '無明確建議')
            confidence = ai_signal.get('confidence', 0.0)

            if '買進' in action:
                st.success(f"**{action}** {score_str}")
            elif '賣出' in action:
                st.error(f"**{action}** {score_str}")
            else:
                st.warning(f"**{action}** {score_str}")
            st.caption(f"信心水準: **{confidence:.1f}%** (AI 綜合判斷力)")

        with col_price:
            st.subheader("📌 當前價格")
            st.info(f"**{currency} {current_price:,.2f}**")
            display_rating = fa_ratings.get('DISPLAY_SCORE', {'Message': 'N/A', 'Combined_Rating': 0})
            st.caption(f"基本面評級: {display_rating.get('Message', 'N/A')} ({display_rating.get('Combined_Rating', 0):.1f}/9.0)")

        st.markdown("---")

# 2. 交易策略與風險控制 (顯示建議入場、TP、SL、ATR 等)
st.header("2️⃣ 🛡️ 精確交易策略與風險控制")
# 基本共識 TP/SL
col_left, col_right = st.columns([1, 1])
with col_left:
    st.metric(
        label="🚀 建議止盈價 (TP)",
        value=f"{currency} {consensus_tp:,.2f}" if pd.notna(consensus_tp) else "N/A",
        delta=f"{((consensus_tp - current_price) / current_price * 100):.2f} %" if pd.notna(consensus_tp) else None
    )
with col_right:
    st.metric(
        label="🛑 建議止損價 (SL)",
        value=f"{currency} {consensus_sl:,.2f}" if pd.notna(consensus_sl) else "N/A",
        delta=f"{((consensus_sl - current_price) / current_price * 100):.2f} %" if pd.notna(consensus_sl) else None,
        delta_color="inverse"
    )

# 計算建議進場與 R:R 與 ATR
atr_val = df['ATR'].iloc[-1] if 'ATR' in df.columns and not df['ATR'].isna().all() else None
# 建議進場價：若 TP/SL 都存在，取中間值；否則以當前價為建議
if pd.notna(consensus_tp) and pd.notna(consensus_sl):
    suggested_entry = (consensus_tp + consensus_sl) / 2.0
else:
    suggested_entry = current_price

# 進場容許範圍（用 ATR 做參考，容許 ±0.32 ATR）
if atr_val is not None:
    tol = atr_val * 0.32
else:
    tol = max( (abs(suggested_entry - consensus_sl) * 0.1) if pd.notna(consensus_sl) else suggested_entry*0.01, 0.0)

# 計算 R:R（若可計算）
rr_ratio = None
if pd.notna(consensus_tp) and pd.notna(consensus_sl) and (suggested_entry - consensus_sl) != 0:
    rr_ratio = (consensus_tp - suggested_entry) / (suggested_entry - consensus_sl)
    rr_ratio = round(rr_ratio, 2)

# 顯示建議卡片
st.markdown(f"""
**建議操作:** {ai_signal.get('action', '中性/觀望')}
**建議進場價:** {currency} {suggested_entry:,.2f} (範圍: {currency} {suggested_entry - tol:,.2f} ~ {currency} {suggested_entry + tol:,.2f})
**止盈價 (TP):** {currency} {consensus_tp:,.2f}  
**止損價 (SL):** {currency} {consensus_sl:,.2f}  
**波動單位 (ATR):** {atr_val:,.4f}  
**⚖️ 風險/回報比 (R:R):** {rr_ratio if rr_ratio is not None else 'N/A'}
""")

st.markdown("---")

# 3. TP/SL 策略細節（先 TP 再 SL）
st.header("3️⃣ TP/SL 策略細節 (多策略參考)")
try:
    # strategy_details 目前為 {策略名稱: [SL, TP]} 的形式（來源 get_consensus_levels）
    # 我們要轉成欄位順序 TP -> SL
    rows = []
    for strat, vals in strategy_details.items():
        sl_val = vals[0] if isinstance(vals, (list, tuple)) and len(vals) >= 1 else np.nan
        tp_val = vals[1] if isinstance(vals, (list, tuple)) and len(vals) >= 2 else np.nan
        rows.append({'策略': strat, 'TP': tp_val, 'SL': sl_val})

    details_df = pd.DataFrame(rows).set_index('策略')
    # 格式化顯示
    details_df = details_df.applymap(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
    st.dataframe(details_df[['TP','SL']], use_container_width=True)
except Exception:
    st.write("無法顯示策略細節（資料格式需為 dict of lists/numbers）。")

        # 4. 技術指標狀態表（含 AI 解讀）與基本面 / AI 細節
        st.header("關鍵技術指標數據")
        tab_tech_table, tab_fa_details, tab_ai_opinion = st.tabs(
            ["📊 技術指標 AI 解讀", "📜 基本面/籌碼評級", "💡 AI 判斷意見"]
        )

  with tab_tech_table:
            st.subheader("技術指標狀態與 AI 解讀")
            tech_df = get_technical_data_df(df)
            
            if not tech_df.empty:
                # 數值格式化
                tech_df['最新值'] = tech_df['最新值'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
                
                # --- 新增/調整顏色映射，用於HTML背景色 ---
                # 定義 AI 結論顏色與對應的輕量背景色
                BG_COLOR_MAP = {
                    "red": "rgba(250, 128, 114, 0.15)",  # Light salmon with opacity
                    "green": "rgba(107, 226, 121, 0.15)", # Light green with opacity
                    "orange": "rgba(255, 215, 0, 0.15)", # Light gold with opacity
                    "blue": "rgba(173, 216, 230, 0.15)", # Light blue with opacity
                    "grey": "rgba(169, 169, 169, 0.05)",
                }
                # --- 顏色映射結束 ---
                
                # 準備顯示數據 (包含顏色鍵)
                display_data = tech_df[['指標名稱', '最新值', '分析結論', '顏色']].reset_index(drop=True)
                
                # 使用 HTML 渲染，以便套用背景色
                html_table = f"""
                <table style='width:100%; border-collapse: collapse; font-size: 14px;'>
                    <tr style='background-color: #f0f0f0;'>
                        <th style='padding: 10px; border: 1px solid #ddd; text-align: left; width: 30%;'>指標名稱</th>
                        <th style='padding: 10px; border: 1px solid #ddd; text-align: right; width: 20%;'>最新值</th>
                        <th style='padding: 10px; border: 1px solid #ddd; text-align: left; width: 50%;'>分析結論</th>
                    </tr>
                """
html = "<table style='width:100%; border-collapse: collapse;'>"
html += "<thead><tr style='text-align:left;'><th style='padding:6px; border:1px solid #ddd;'>指標名稱</th><th style='padding:6px; border:1px solid #ddd; text-align:right;'>最新值</th><th style='padding:6px; border:1px solid #ddd;'>分析結論</th></tr></thead><tbody>"

for idx, row in tech_df.iterrows():
    name = idx
    val = row['最新值']
    # 數字格式化
    val_str = f"{val:,.2f}" if pd.notna(val) else "N/A"
    concl_html = row['分析結論']  # 這裡已包含 <span>...<strong>...</strong></span>
    html += (
        "<tr>"
        f"<td style='padding: 8px; border: 1px solid #ddd;'>{name}</td>"
        f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{val_str}</td>"
        f"<td style='padding: 8px; border: 1px solid #ddd;'>{concl_html}</td>"
        "</tr>"
    )

html += "</tbody></table>"
st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("數據不足，無法生成技術指標解讀。")

        with tab_fa_details:
            st.subheader("基本面評級詳情")
            display_rating = fa_ratings.get('DISPLAY_SCORE', {})
            st.markdown(f"**綜合評級:** **{display_rating.get('Message','N/A')}** ({display_rating.get('Combined_Rating',0):.1f}/9.0)")
            if display_rating.get('Details'):
                details_data = [[k, v] for k, v in display_rating['Details'].items()]
                st.table(pd.DataFrame(details_data, columns=['評分項目', '分數']))

            st.subheader("AI 模型依賴的關鍵財務數據")
            ai_details = fa_ratings.get('AI_SCORE', {}).get('details', {})
            if ai_details:
                details_data = [[k, v] for k, v in ai_details.items()]
                st.table(pd.DataFrame(details_data, columns=['指標', '數值']))
            else:
                st.write("無 AI 財務細節資料。")

        with tab_ai_opinion:
            st.subheader("AI 融合信號細節意見")
            opinions = ai_signal.get('ai_opinions', {})
            if opinions:
                opinions_data = [[k, v] for k, v in opinions.items()]
                st.table(pd.DataFrame(opinions_data, columns=['分析模組', '結論']))
            else:
                st.write("無 AI 模組細節。")

        st.markdown("---")

        # 5. 策略回測報告
        st.header("5️⃣ 策略回測報告 (SMA 20 / EMA 50 交叉)")
        
        tab_summary, tab_trades = st.tabs(["📈 回測概要與曲線", "📜 交易細節列表"]) 
        
        with tab_summary:
            if backtest_results['total_trades'] > 0:
                st.success(f"回測週期內總報酬率: **{backtest_results['total_return']:,.2f}%**", icon="📈")
                col_b1, col_b2, col_b3 = st.columns(3)
                col_b1.metric("交易次數", backtest_results['total_trades'])
                col_b2.metric("勝率", f"{backtest_results['win_rate']:,.2f}%")
                col_b3.metric("最大回撤", f"{backtest_results['max_drawdown']:,.2f}%", delta_color="inverse")
                st.caption(backtest_results['message'])
                
                plot_chart(pd.DataFrame(), "", "", {}, st.session_state.backtest_results.get('capital_curve'))
            else:
                st.warning(backtest_results['message'])
                
        with tab_trades: 
            st.subheader("完整交易紀錄 (Entry/Exit Price)")
            trades_df = pd.DataFrame(backtest_results.get('trades_list', []))
            if not trades_df.empty:
                trades_df['Profit_Pct'] = (trades_df['Profit_Pct'] * 100).apply(lambda x: f"{x:+.2f}%")
                trades_df['Entry_Price'] = trades_df['Entry_Price'].apply(lambda x: f"{x:,.2f}")
                trades_df['Exit_Price'] = trades_df['Exit_Price'].apply(lambda x: f"{x:,.2f}")
                trades_df['Is_Win'] = trades_df['Is_Win'].apply(lambda x: '✅ 獲利' if x else '❌ 虧損')
                trades_df = trades_df.rename(columns={
                    'Entry_Date': '進場時間', 'Exit_Date': '出場時間', 
                    'Entry_Price': '進場價格', 'Exit_Price': '出場價格', 
                    'Profit_Pct': '單筆回報', 'Is_Win': '結果'
                })
                
                st.dataframe(trades_df.iloc[::-1], use_container_width=True)
            else:
                st.info("回測週期內無交易發生。")
        
        st.markdown("---")

        # 6. 完整技術分析圖表（置於最後）
        st.header("完整技術分析圖表")
        # 主圖（將策略細節或 sl/tp 放入 plot）
        try:
            plot_fig = plot_chart(df, info['name'], period_name, st.session_state.sl_tp_levels, st.session_state.strategy_details, st.session_state.backtest_results.get('capital_curve'))
            st.plotly_chart(plot_fig, use_container_width=True)
        except Exception:
            # 若 plot_chart 簡單版本
            try:
                plot_fig = plot_chart(df, info['name'], period_name, st.session_state.sl_tp_levels, st.session_state.strategy_details)
                st.plotly_chart(plot_fig, use_container_width=True)
            except Exception as e:
                st.write("無法繪製圖表：請確認 plot_chart 函式的實作。")
    else:
        display_homepage()

if __name__ == '__main__':
    main()

    # 🚨 綜合免責聲明區塊
    st.markdown("---")
    st.markdown("⚠️ **綜合風險與免責聲明 (Risk & Disclaimer)**", unsafe_allow_html=True)
    st.markdown("本AI趨勢分析模型，是基於**量化集成學習 (Ensemble)**的專業架構。其分析結果**僅供參考用途**")
    st.markdown("投資涉及風險，所有交易決策應基於您個人的**獨立研究和財務狀況**，並強烈建議諮詢**專業金融顧問**。", unsafe_allow_html=True)
    st.markdown("📊 **數據來源:** Yahoo Finance | 🛠️ **技術指標:** TA 庫 | 💻 **APP優化:** 專業程式碼專家")



