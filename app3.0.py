import streamlit as st
import requests
import time
import json
from urllib.parse import urlparse

# --- 1. 配置與常數 ---
# 警告: 在實際部署時，請將 API Key 設置為 Streamlit Secrets 或環境變數
API_KEY = "" # 請在此處填入您的 Gemini API Key
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
MAX_RETRIES = 5

# --- 2. 輔助函式: 帶有指數退避的 API 呼叫 ---

def fetch_with_retry(url, headers, payload, max_retries=MAX_RETRIES):
    """使用指數退避策略調用 Gemini API"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # 對於 4xx/5xx 狀態碼拋出異常
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                delay = 2 ** attempt
                # print(f"API 呼叫失敗 ({response.status_code})。將在 {delay} 秒後重試...")
                time.sleep(delay)
            else:
                # 重新拋出錯誤，或處理最終失敗
                st.error(f"API 呼叫在 {max_retries} 次嘗試後仍失敗。錯誤: {e}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"網絡請求錯誤: {e}")
            return None
    return None

# --- 3. 核心邏輯: AI 分析 (Gemini API) ---

def get_ai_analysis(query):
    """調用 Gemini API 進行市場趨勢分析並啟用 Google Search 接地"""
    if not API_KEY:
        st.warning("請在程式碼中填入您的 API_KEY 才能啟用 AI 分析功能。")
        return "API Key 未設置，AI 分析功能無法使用。", []

    system_prompt = "您是一位專門且中立的金融市場趨勢分析師。請基於最新的市場資訊和數據，提供關於使用者查詢標的物的趨勢分析，重點關注近期動能和結構性變化，並以一個精簡、專業的單一自然段落中文總結。使用 Markdown 格式化輸出。"
    
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{"google_search": {}}], # 啟用 Google 搜尋接地
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    url_with_key = f"{MODEL_URL}?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    with st.spinner("⏳ 正在進行 AI 趨勢分析..."):
        result = fetch_with_retry(url_with_key, headers, payload)

    if not result:
        return "分析失敗，請檢查 API Key 或網路連線。", []

    try:
        candidate = result.get('candidates', [{}])[0]
        text = candidate.get('content', {}).get('parts', [{}])[0].get('text', '未能獲取分析文本。')
        
        # 提取資料來源 (Grounding Sources)
        sources = []
        grounding_metadata = candidate.get('groundingMetadata', {})
        if grounding_metadata and grounding_metadata.get('groundingAttributions'):
            sources = [
                {
                    'uri': attr.get('web', {}).get('uri'),
                    'title': attr.get('web', {}).get('title')
                }
                for attr in grounding_metadata['groundingAttributions']
                if attr.get('web', {}).get('uri') and attr.get('web', {}).get('title')
            ]
        
        return text, sources

    except Exception as e:
        st.error(f"處理 API 回應時發生錯誤: {e}")
        return "回應解析失敗。", []

# --- 4. 核心邏輯: 專業操盤計算器 ---

def calculate_rr_ratio(entry_price, swing_anchor, atr_value, atr_multiplier, tp_target, is_long=True):
    """計算最終止損價位、風險、回報和風險報酬比 (R:R)"""
    
    # 1. 計算 ATR 緩衝區
    atr_buffer = atr_value * atr_multiplier

    if is_long:
        # 多單 (買入): 止損在結構錨點下方，止盈在開單價位上方
        structural_sl = swing_anchor
        final_sl = structural_sl - atr_buffer
        
        # 風險: 入場價到最終止損價的距離 (正值)
        risk = entry_price - final_sl
        # 回報: 止盈目標價到入場價的距離 (正值)
        reward = tp_target - entry_price
        
    else: # 賣空 (Short)
        # 賣空: 止損在結構錨點上方，止盈在開單價位下方
        structural_sl = swing_anchor
        final_sl = structural_sl + atr_buffer
        
        # 風險: 最終止損價到入場價的距離 (正值)
        risk = final_sl - entry_price
        # 回報: 入場價到止盈目標價的距離 (正值)
        reward = entry_price - tp_target
    
    # 計算風險報酬比 (R:R)
    # 確保風險和回報都是正值，且風險 > 0
    risk = max(0, risk)
    reward = max(0, reward)
    rr_ratio = reward / risk if risk > 0 else 0

    return final_sl, risk, reward, rr_ratio

# --- 5. Streamlit 應用程式佈局 ---

def main():
    st.set_page_config(
        page_title="AI 趨勢分析與專業操盤策略框架",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📈 AI 趨勢分析與專業策略驗證器")
    st.markdown("---")

    col_trend, col_calc = st.columns([3, 2], gap="large")

    # ===============================================
    # 區塊一: AI 趨勢分析 (佔 3/5 寬度)
    # ===============================================
    with col_trend:
        st.header("🔮 區塊一: AI 趨勢判斷與市場定性")
        st.markdown("輸入標的物名稱（例如：`NASDAQ 100 最新季度走勢`、`TSLA 股價潛力`），讓 AI 提供客觀的趨勢分析。")

        # 交易方向選擇（影響計算器邏輯，但 AI 分析不直接需要）
        direction = st.radio(
            "選擇交易方向：",
            ["做多 (Long)", "做空 (Short)"],
            horizontal=True,
            help="選擇此方向將應用於右側的風險報酬計算。"
        )
        is_long = direction == "做多 (Long)"
        
        ai_prompt = st.text_area(
            "輸入 AI 分析指令:",
            placeholder="例如: 蘋果公司 (AAPL) 在未來六個月的潛在走勢和風險因素。",
            height=100
        )

        if st.button("🚀 開始 AI 趨勢分析"):
            if ai_prompt:
                analysis_text, sources = get_ai_analysis(ai_prompt)
                
                st.session_state['analysis_text'] = analysis_text
                st.session_state['sources'] = sources
            else:
                st.warning("請輸入有效的查詢內容。")

        st.subheader("分析結果")
        if 'analysis_text' in st.session_state:
            st.markdown(st.session_state['analysis_text'])
            
            st.markdown("---")
            st.markdown("**資料來源 (Grounding Sources):**")
            if 'sources' in st.session_state and st.session_state['sources']:
                for idx, source in enumerate(st.session_state['sources']):
                    if source['uri'] and source['title']:
                        st.markdown(f"- {idx + 1}. [{source['title']}]({source['uri']})")
            else:
                st.markdown("- 無外部資料來源引用。")
        else:
            st.info("AI 分析結果將顯示在此處。")


    # ===============================================
    # 區塊二: 風控與目標設定驗證 (佔 2/5 寬度)
    # ===============================================
    with col_calc:
        st.header("💰 區塊二: 風控與目標設定驗證")
        st.markdown("專業交易策略的基石：用結構錨點和波動率 (ATR) 驗證您的 R:R 比例。")

        # --- 輸入參數 ---
        st.subheader("輸入參數")
        
        col_input_1, col_input_2 = st.columns(2)
        
        with col_input_1:
            entry_price = st.number_input("1. 開單價位 (Entry Price):", value=100.00, min_value=0.01, step=0.01, format="%.2f", help="您的預期入場價格")
            atr_value = st.number_input("3. ATR 波動值 (Value):", value=0.50, min_value=0.01, step=0.01, format="%.2f", help="例如 14 週期 ATR 的數值")
        
        with col_input_2:
            swing_anchor = st.number_input(
                f"2. 止損結構錨點 ({'低點' if is_long else '高點'}):", 
                value=95.00 if is_long else 105.00, 
                min_value=0.01, 
                step=0.01, 
                format="%.2f",
                help=f"用於止損的結構點（做多為前低點，做空為前高點）"
            )
            atr_multiplier = st.number_input("4. ATR 緩衝倍數 (Multiplier):", value=1.5, min_value=0.1, step=0.1, format="%.1f", help="您願意為緩衝區設定的 ATR 倍數 (通常為 1.5 - 2.0)")
            
        tp_target = st.number_input("5. 主要止盈目標 (TP Target):", value=125.00, min_value=0.01, step=0.01, format="%.2f", help="例如 Fibonacci 擴展 1.618 或關鍵阻力位")

        # --- 計算並顯示結果 ---
        final_sl, risk, reward, rr_ratio = calculate_rr_ratio(
            entry_price, swing_anchor, atr_value, atr_multiplier, tp_target, is_long
        )

        st.markdown("---")
        st.subheader("計算結果與驗證")

        # R:R 驗證結果
        rr_color = "green" if rr_ratio >= 2.0 else ("orange" if rr_ratio >= 1.0 else "red")
        rr_emoji = "✅" if rr_ratio >= 2.0 else ("⚠️" if rr_ratio >= 1.0 else "❌")
        rr_message = ""
        
        if rr_ratio >= 2.0:
            rr_message = "符合專業交易標準 (R:R ≥ 2.0)。"
        elif rr_ratio >= 1.0:
            rr_message = "風險報酬比低於 2.0，需審慎評估。建議尋找更高的止盈目標或更緊密的結構。 "
        else:
            rr_message = "風險大於回報，不建議開單。"

        st.markdown(
            f"<div style='background-color: {'#166534' if rr_color == 'green' else ('#f59e0b' if rr_color == 'orange' else '#b91c1c')}; padding: 15px; border-radius: 10px; text-align: center; color: white; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
            f"<p style='font-size: 16px; margin: 0;'>風險報酬比 (R:R Ratio)</p>"
            f"<p style='font-size: 32px; margin: 5px 0 0;'>{rr_emoji} {rr_ratio:.2f} : 1</p>"
            f"<p style='font-size: 14px; margin-top: 5px;'>{rr_message}</p>"
            f"</div>", 
            unsafe_allow_html=True
        )

        st.markdown("---")

        col_result_1, col_result_2 = st.columns(2)
        
        # 結果詳細數據
        col_result_1.metric(
            "最終止損價位 (SL)", 
            f"${final_sl:.2f}", 
            help=f"結構錨點 ({swing_anchor:.2f}) 加上/減去 ATR 緩衝 ({atr_multiplier}x{atr_value:.2f}={atr_value * atr_multiplier:.2f})"
        )
        col_result_1.metric(
            "單次交易風險 (Risk)", 
            f"${risk:.2f}", 
            delta_color="inverse",
            delta=f"佔入場價 {(risk / entry_price * 100):.2f}%"
        )
        
        col_result_2.metric(
            "潛在回報 (Reward)", 
            f"${reward:.2f}",
            delta_color="normal",
            delta=f"佔入場價 {(reward / entry_price * 100):.2f}%"
        )
        col_result_2.metric(
            "總回報目標 (TP Target)", 
            f"${tp_target:.2f}"
        )


if __name__ == "__main__":
    main()
