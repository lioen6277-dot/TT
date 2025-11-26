import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

# --- 配置 Streamlit 頁面 ---
st.set_page_config(
    page_title="AI 趨勢分析儀與交易計算器",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 AI 趨勢分析儀")
st.markdown("---")

# 設置中文字體樣式，讓圖表顯示中文
# 由於 Streamlit 環境可能無法直接載入外部字體，這裡先使用基礎設定
# 如果運行時中文顯示為方塊，需要配置運行環境的字體。

# --- AI 趨勢分析儀 (主體) ---

st.header("📈 趨勢預測模擬")

# 1. 用戶輸入和控制項
with st.sidebar:
    st.header("⚙️ 分析參數設定")
    
    # 模擬的資產選擇
    symbol = st.selectbox(
        "選擇分析標的",
        ["AAPL (蘋果)", "TSLA (特斯拉)", "BTC (比特幣)", "NVDA (輝達)"],
        index=0
    )
    
    # 模擬數據量
    data_points = st.slider("歷史數據點數量 (天)", 100, 500, 300)
    
    # 模擬 AI 模型的「信心」或「趨勢偏見」
    # 這個參數將影響預測的坡度
    ai_bias = st.slider(
        "AI 預測趨勢強度 (模擬)",
        -0.5, 0.5, 0.1, 0.05,
        help="正值代表 AI 預測強勁上漲趨勢，負值代表下跌趨勢。"
    )
    
    # 預測的天數
    forecast_days = st.slider("預測期天數", 5, 60, 30)

# 2. 數據生成函數 (模擬歷史價格和 AI 預測)
@st.cache_data
def generate_data(points, bias, forecast):
    """生成模擬的歷史價格和 AI 預測數據。"""
    
    # 歷史數據 (基於隨機遊走，模擬股價波動)
    dates = pd.to_datetime(pd.date_range(end=datetime.date.today() - datetime.timedelta(days=1), periods=points))
    np.random.seed(42)
    # 價格從 100 開始，加入隨機變動
    prices = 100 + np.cumsum(np.random.randn(points) * 0.5)
    
    history_df = pd.DataFrame({
        'Date': dates,
        'Price': prices,
        'Type': '歷史數據'
    })
    
    # 模擬 AI 預測
    # 預測從歷史數據的最後一天開始
    last_date = history_df['Date'].max()
    last_price = history_df['Price'].iloc[-1]
    
    forecast_dates = pd.to_datetime(pd.date_range(start=last_date + datetime.timedelta(days=1), periods=forecast))
    
    # 預測價格：基於最後價格，加上一個受 ai_bias 影響的趨勢項，以及輕微的隨機雜訊
    forecast_prices = []
    current_price = last_price
    for i in range(forecast):
        # 趨勢項: 每日微幅變化 + 偏見
        change = (0.1 + bias * 2) + np.random.randn() * 0.1
        current_price += change
        forecast_prices.append(current_price)

    forecast_df = pd.DataFrame({
        'Date': forecast_dates,
        'Price': forecast_prices,
        'Type': 'AI 預測路徑'
    })
    
    # 結合數據
    combined_df = pd.concat([history_df, forecast_df]).reset_index(drop=True)
    
    return history_df, forecast_df, combined_df

# 生成數據
history_data, forecast_data, combined_data = generate_data(data_points, ai_bias, forecast_days)

# 3. 繪製圖表
st.subheader(f"{symbol} 價格走勢與 AI 預測 ({data_points} 天歷史數據 + {forecast_days} 天預測)")

# Altair 基礎圖表
base = alt.Chart(combined_data).encode(
    x=alt.X('Date:T', title="日期"),
    y=alt.Y('Price:Q', title="價格 (模擬)")
).properties(
    title=f"{symbol} AI 趨勢分析"
).interactive() # 允許縮放和平移

# 歷史數據線 (藍色)
history_line = base.mark_line().encode(
    color=alt.condition(
        alt.datum.Type == '歷史數據', 
        alt.value('rgb(59, 130, 246)'), # 藍色 for history
        alt.value('transparent')
    ),
    tooltip=['Date', 'Price', 'Type']
).transform_filter(
    alt.datum.Type == '歷史數據'
)

# AI 預測線 (橙色/紅色虛線)
forecast_line = base.mark_line(strokeDash=[5, 5]).encode(
    color=alt.condition(
        alt.datum.Type == 'AI 預測路徑', 
        alt.value('rgb(249, 115, 22)'), # 橙色 for forecast
        alt.value('transparent')
    ),
    tooltip=['Date', 'Price', 'Type']
).transform_filter(
    alt.datum.Type == 'AI 預測路徑'
)

# 連接歷史和預測的點 (最後一個歷史點)
connector_point = alt.Chart(history_data.iloc[-1:]).mark_circle(size=80, color='red').encode(
    x='Date:T',
    y='Price:Q',
    tooltip=['Date', alt.Tooltip('Price', format='.2f')]
)

# 組合圖表
chart = (history_line + forecast_line + connector_point).properties(
    height=500
).configure_axis(
    grid=True
)

st.altair_chart(chart, use_container_width=True)

st.subheader("📊 模擬預測結果")
# 顯示一些關鍵預測點
st.markdown(f"**當前 (歷史數據最後一天):** {history_data['Date'].max().strftime('%Y-%m-%d')}，價格：**{history_data['Price'].iloc[-1]:.2f}**")
st.markdown(f"**預測期結束 ({forecast_days} 天後):** {forecast_data['Date'].max().strftime('%Y-%m-%d')}，AI 預測價格：**{forecast_data['Price'].iloc[-1]:.2f}**")

# ----------------------------------------
# --- 交易計算器 (輔助功能，放置於側邊欄) ---
# ----------------------------------------

with st.sidebar:
    st.markdown("---")
    st.header("🧮 交易損益計算器")
    st.markdown("---")

    # 輸入項
    try:
        default_entry = history_data['Price'].iloc[-1]
    except:
        default_entry = 100.0 # 數據生成失敗時的備用值
        
    entry_price = st.number_input(
        "進場價格 (Entry Price)",
        min_value=0.01,
        value=float(f"{default_entry:.2f}"),
        step=0.1,
        format="%.2f",
        key='entry_price'
    )
    
    # 預設離場價格為 AI 預測結束時的價格
    try:
        default_exit = forecast_data['Price'].iloc[-1]
    except:
        default_exit = 105.0
        
    exit_price = st.number_input(
        "離場價格 (Exit Price)",
        min_value=0.01,
        value=float(f"{default_exit:.2f}"),
        step=0.1,
        format="%.2f",
        key='exit_price'
    )
    
    position_size = st.number_input(
        "頭寸規模 (Position Size / 股數)",
        min_value=1,
        value=100,
        step=1,
        key='position_size'
    )
    
    # 執行計算
    if st.button("計算損益"):
        # 計算價差
        price_difference = exit_price - entry_price
        # 計算總損益
        total_pnl = price_difference * position_size
        
        st.subheader("計算結果")
        
        # 顯示結果
        if total_pnl > 0:
            st.success(f"🎉 預計總盈餘 (Profit):")
            st.markdown(f"## + {total_pnl:,.2f} USD")
        elif total_pnl < 0:
            st.error(f"📉 預計總虧損 (Loss):")
            st.markdown(f"## - {-total_pnl:,.2f} USD")
        else:
            st.info("🤷‍♂️ 損益平衡 (Break-Even): 0.00 USD")
            
        st.markdown(f"**每股盈虧:** {price_difference:.2f} USD")
        st.markdown(f"**總頭寸:** {position_size} 股")

st.markdown("---")
st.caption("備註：本應用程式中的價格數據及 AI 預測均為模擬生成，僅用於展示和教育目的，不構成任何投資建議。")
