import pandas as pd
import numpy as np
import json # 新增：用於格式化結構化輸出

# --- 數據準備與輔助函數 ---

def generate_mock_ohlcv(start_date='2025-01-01', periods=100, initial_price=100.0, volatility_factor=0.01):
    """
    生成模擬的 OHLCV 股價數據 (Open, High, Low, Close, Volume)。
    用於測試分析功能。
    """
    dates = pd.date_range(start_date, periods=periods, freq='D')
    
    # 模擬股價走勢
    np.random.seed(42)
    price_changes = np.random.normal(0, volatility_factor, periods)
    prices = initial_price * np.exp(np.cumsum(price_changes))
    
    # 模擬 OHLCV
    ohlc = pd.DataFrame(index=dates)
    ohlc['Close'] = prices
    ohlc['Open'] = ohlc['Close'].shift(1) * (1 + np.random.uniform(-0.005, 0.005, periods))
    ohlc['High'] = ohlc[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0.001, 0.008, periods))
    ohlc['Low'] = ohlc[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0.001, 0.008, periods))
    ohlc['Volume'] = np.random.randint(100000, 500000, periods)
    
    # 清理第一個 NaN 行
    ohlc = ohlc.dropna().round(2)
    
    return ohlc

def calculate_atr(df, period=14):
    """
    計算平均真實波動區間 (Average True Range, ATR)。
    用於動態風險管理。
    """
    # 1. 計算 True Range (TR)
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = np.abs(df['High'] - df['Close'].shift(1))
    df['Low-PrevClose'] = np.abs(df['Low'] - df['Close'].shift(1))
    
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    
    # 2. 計算 ATR (Wilder's smoothing method for initial values, then simple moving average)
    df['ATR'] = df['TR'].ewm(span=period, adjust=False).mean()
    
    df.drop(columns=['High-Low', 'High-PrevClose', 'Low-PrevClose', 'TR'], inplace=True)
    return df

# --- 核心分析函數 ---

def analyze_price_action(df):
    """
    基於 K線形態 的分析。
    檢查常見的 K線反轉/延續形態，這裡以 吞噬形態 為例。
    """
    df['K_Action'] = ''
    
    # 確保有足夠的數據進行比較 (前一根K線)
    if len(df) < 2:
        return df

    prev_open = df['Open'].shift(1)
    prev_close = df['Close'].shift(1)
    
    # 判斷多頭吞噬 (Bullish Engulfing)
    # 條件: 當前收盤 > 當前開盤 且 當前K線實體完全覆蓋前一根K線實體
    bull_engulfing = (df['Close'] > df['Open']) & \
                     (df['Close'] > prev_open) & \
                     (df['Open'] < prev_close) & \
                     (df['Close'] > prev_close) & \
                     (df['Open'] < prev_open)
    
    # 判斷空頭吞噬 (Bearish Engulfing)
    # 條件: 當前開盤 > 當前收盤 且 當前K線實體完全覆蓋前一根K線實體
    bear_engulfing = (df['Open'] > df['Close']) & \
                     (df['Close'] < prev_open) & \
                     (df['Open'] > prev_close) & \
                     (df['Close'] < prev_close) & \
                     (df['Open'] > prev_open)

    df.loc[bull_engulfing, 'K_Action'] = '多頭吞噬 (Bullish Engulfing)'
    df.loc[bear_engulfing, 'K_Action'] = '空頭吞噬 (Bearish Engulfing)'
    
    return df

def analyze_volume_price(df, volume_sma_period=20):
    """
    基於 VSA (Volume Spread Analysis) 原理的分析。
    檢查價量關係，尋找供給或需求失衡的跡象。
    """
    df['VSA_Action'] = ''
    
    # 計算平均成交量
    df['Avg_Volume'] = df['Volume'].rolling(window=volume_sma_period).mean()
    
    # 價格波動區間 (Spread)
    df['Spread'] = df['High'] - df['Low']
    df['Avg_Spread'] = df['Spread'].rolling(window=volume_sma_period).mean()

    # VSA 範例 1: 供應測試 (Testing Supply)
    # 條件: 
    # 1. 價格為下跌或窄幅波動 (當前收盤 < 當前開盤，或實體極小)
    # 2. 成交量遠低於平均值 (例如 < 50% Avg_Volume)
    # 3. 波動區間窄 (例如 < 50% Avg_Spread)
    testing_supply = (df['Close'] < df['Open']) & \
                     (df['Volume'] < 0.5 * df['Avg_Volume'].shift(1)) & \
                     (df['Spread'] < 0.5 * df['Avg_Spread'].shift(1))
    
    df.loc[testing_supply, 'VSA_Action'] = '潛在供應測試 (Testing Supply)'

    # VSA 範例 2: 努力無結果 (Effort Without Result - 可能是拋售高潮/吸籌結束)
    # 條件:
    # 1. 成交量非常高 (例如 > 200% Avg_Volume)
    # 2. 波動區間窄，且收盤位置與開盤相近 (努力推動，但價格變化不大)
    effort_no_result = (df['Volume'] > 2.0 * df['Avg_Volume'].shift(1)) & \
                       (df['Spread'] < 1.0 * df['Avg_Spread'].shift(1)) & \
                       (np.abs(df['Open'] - df['Close']) < 0.2 * df['Spread'])
    
    df.loc[effort_no_result, 'VSA_Action'] = df.loc[effort_no_result, 'VSA_Action'] + '; 努力無結果'
    
    df.drop(columns=['Avg_Volume', 'Spread', 'Avg_Spread'], inplace=True)
    return df

def calculate_r_multiple_strategy(df, atr_period=14, entry_index=-1, entry_type='Long', risk_atr_multiplier=1.5, reward_r_multiple=3.0):
    """
    升級後的 R 倍數策略計算。
    使用 ATR 結合 R 倍數策略實施動態風險管理。

    :param df: 包含 ATR 數據的 DataFrame。
    :param entry_index: 交易發生的數據索引 (例如最後一根K線的索引)。
    :param entry_type: 'Long' (買入) 或 'Short' (賣空)。
    :param risk_atr_multiplier: 止損距離是 ATR 的多少倍。
    :param reward_r_multiple: 目標利潤是風險單位 (R) 的多少倍。
    :return: 包含策略參數的字典。
    """
    
    # 確保 ATR 已經計算
    if 'ATR' not in df.columns or df['ATR'].isnull().iloc[entry_index]:
        return {"Status": "錯誤", "Message": "ATR 數據缺失或為 NaN，請先計算 ATR。"}

    # 獲取當前數據
    current_data = df.iloc[entry_index]
    entry_price = current_data['Close']
    current_atr = current_data['ATR']
    
    # 1. 定義風險單位 (R)
    # R = ATR * 風險乘數 (決定了止損距離)
    risk_unit_r = current_atr * risk_atr_multiplier
    
    # 2. 計算止損價格 (SL)
    if entry_type == 'Long':
        # 多頭: 止損在入場價下方 R 距離
        stop_loss_price = entry_price - risk_unit_r
        # 使用低點來確定更保守的止損，但為了示範純粹的ATR策略，我們使用計算值
        # stop_loss_level = current_data['Low'] - current_atr * 0.5 
    elif entry_type == 'Short':
        # 空頭: 止損在入場價上方 R 距離
        stop_loss_price = entry_price + risk_unit_r
        # stop_loss_level = current_data['High'] + current_atr * 0.5
    else:
        return {"Status": "錯誤", "Message": "不支援的入場類型。請使用 'Long' 或 'Short'。"}

    # 3. 計算目標利潤價格 (TP)
    if entry_type == 'Long':
        # 多頭: 目標在入場價上方 R * R_multiple 距離
        take_profit_price = entry_price + (risk_unit_r * reward_r_multiple)
    else: # Short
        # 空頭: 目標在入場價下方 R * R_multiple 距離
        take_profit_price = entry_price - (risk_unit_r * reward_r_multiple)
        
    # 確保價格保留兩位小數
    entry_price = round(entry_price, 2)
    stop_loss_price = round(stop_loss_price, 2)
    take_profit_price = round(take_profit_price, 2)
    risk_unit_r = round(risk_unit_r, 4)

    return {
        "Status": "成功",
        "入場類型": entry_type,
        "入場價格": entry_price,
        "當前ATR (14期)": round(current_atr, 4),
        "風險單位 R (ATR x {})": risk_atr_multiplier,
        "R單位實際值": risk_unit_r,
        "止損價格 (SL)": stop_loss_price,
        "目標 R 倍數": f'{reward_r_multiple}R',
        "目標價格 (TP)": take_profit_price,
        "風險回報比 (R:R)": f'1:{reward_r_multiple}'
    }

# --- 運行示範：將輸出轉換為結構化字典 ---

if __name__ == '__main__':
    # 總結果容器
    final_results = {
        "AnalysisTitle": "股票交易指標卡片分析結果",
        "DataSnippet": [],
        "KLineAnalysis": [],
        "VSAAnalysis": [],
        "StrategyRecommendations": {
            "LongEntry": {},
            "ShortEntry": {}
        }
    }

    # 1. 生成和預處理數據
    df = generate_mock_ohlcv(periods=50)
    df = calculate_atr(df, period=14)
    
    # 獲取原始數據片段 (作為指標卡片的一部分)
    data_snippet = df[['Close', 'Volume', 'ATR']].tail(5).reset_index()
    data_snippet.rename(columns={'index': 'Date'}, inplace=True)
    final_results["DataSnippet"] = [
        {"Date": row['Date'].strftime('%Y-%m-%d'), 
         "Close": row['Close'], 
         "Volume": row['Volume'], 
         "ATR": round(row['ATR'], 4)} 
        for index, row in data_snippet.iterrows()
    ]


    # 2. 應用 K 線形態分析
    df = analyze_price_action(df)
    
    # 提取 K 線形態結果
    action_results = df[df['K_Action'] != ''][['Close', 'K_Action']].tail(5).reset_index()
    final_results["KLineAnalysis"] = [
        {"Date": row['index'].strftime('%Y-%m-%d'), 
         "Close": row['Close'], 
         "Pattern": row['K_Action']} 
        for index, row in action_results.iterrows()
    ]
    
    if not final_results["KLineAnalysis"]:
        final_results["KLineAnalysis"].append({"Message": "未檢測到常見的 K 線形態 (多頭/空頭吞噬)。"})


    # 3. 應用 VSA 價量分析
    df = analyze_volume_price(df)
    
    # 提取 VSA 價量結果
    vsa_results = df[df['VSA_Action'] != ''][['Close', 'Volume', 'VSA_Action']].tail(5).reset_index()
    final_results["VSAAnalysis"] = [
        {"Date": row['index'].strftime('%Y-%m-%d'), 
         "Close": row['Close'], 
         "Volume": row['Volume'],
         "VSA_Signal": row['VSA_Action']} 
        for index, row in vsa_results.iterrows()
    ]
    
    if not final_results["VSAAnalysis"]:
        final_results["VSAAnalysis"].append({"Message": "未檢測到明顯的 VSA 行為。"})


    # 4. 運行升級後的 R 倍數策略 (Long)
    strategy_params_long = calculate_r_multiple_strategy(
        df, 
        entry_index=-1, 
        entry_type='Long', 
        risk_atr_multiplier=1.5, 
        reward_r_multiple=4.0      
    )
    final_results["StrategyRecommendations"]["LongEntry"] = {
        "EntryDate": df.index[-1].strftime('%Y-%m-%d'),
        "Details": strategy_params_long
    }
    

    # 5. 運行升級後的 R 倍數策略 (Short)
    strategy_params_short = calculate_r_multiple_strategy(
        df, 
        entry_index=-2, 
        entry_type='Short', 
        risk_atr_multiplier=2.0, 
        reward_r_multiple=2.5      
    )
    final_results["StrategyRecommendations"]["ShortEntry"] = {
        "EntryDate": df.index[-2].strftime('%Y-%m-%d'),
        "Details": strategy_params_short
    }
    
    # 輸出最終的結構化指標卡片 (JSON格式)
    print(json.dumps(final_results, indent=4, ensure_ascii=False))
