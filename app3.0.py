import re
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf
from plotly.subplots import make_subplots
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

# 🚀 您的【所有資產清單】(整合所有版本)
FULL_SYMBOLS_MAP = {
    # 美股/ETF/指數
    "ACN": {"name": "Accenture (埃森哲)", "keywords": ["Accenture", "ACN", "諮詢", "科技服務"]},
    "ADBE": {"name": "Adobe", "keywords": ["Adobe", "ADBE"]},
    "AAPL": {"name": "蘋果 (Apple)", "keywords": ["蘋果", "Apple", "AAPL"]},
    "AMD": {"name": "超微 (Advanced Micro Devices)", "keywords": ["超微", "AMD", "半導體"]},
    "AMZN": {"name": "亞馬遜 (Amazon)", "keywords": ["亞馬遜", "Amazon", "AMZN", "電商"]},
    "ARKG": {"name": "方舟基因體革命ETF (ARK Genomic)", "keywords": ["ARKG", "基因科技", "生物科技ETF"]},
    "ARKK": {"name": "方舟創新ETF (ARK Innovation)", "keywords": ["ARKK", "CathieWood", "創新ETF", "木頭姐"]},
    "BA": {"name": "波音 (Boeing)", "keywords": ["波音", "Boeing", "BA", "工業股", "航太"]},
    "BAC": {"name": "美國銀行 (Bank of America)", "keywords": ["美國銀行", "BankOfAmerica", "BAC", "金融股"]},
    "BND": {"name": "Vanguard總體債券市場ETF", "keywords": ["BND", "總體債券", "債券ETF"]},
    "BRK-B": {"name": "波克夏海瑟威 B (Berkshire Hathaway)", "keywords": ["波克夏", "巴菲特", "BRKB", "保險", "投資"]},
    "CAT": {"name": "開拓重工 (Caterpillar)", "keywords": ["開拓重工", "Caterpillar", "CAT"]},
    "CVX": {"name": "雪佛龍 (Chevron)", "keywords": ["雪佛龍", "Chevron", "CVX", "能源股", "石油"]},
    "KO": {"name": "可口可樂 (Coca-Cola)", "keywords": ["可口可樂", "CocaCola", "KO"]},
    "COST": {"name": "好市多 (Costco)", "keywords": ["好市多", "Costco", "COST"]},
    "CRM": {"name": "Salesforce", "keywords": ["Salesforce", "CRM", "雲端", "SaaS"]},
    "DE": {"name": "迪爾公司 (Deere & Co.)", "keywords": ["迪爾", "Deere", "DE", "農業機械"]},
    "DIA": {"name": "SPDR 道瓊工業ETF (Dow Jones ETF)", "keywords": ["DIA", "道瓊ETF"]},
    "DIS": {"name": "迪士尼 (Disney)", "keywords": ["迪士尼", "Disney", "DIS", "媒體", "娛樂"]},
    "^DJI": {"name": "道瓊工業指數 (Dow Jones Industrial Average)", "keywords": ["道瓊", "DowJones", "^DJI", "指數"]},
    "DXY": {"name": "美元指數 (Dollar Index)", "keywords": ["美元指數", "DXY", "外匯", "USD"]},
    "EEM": {"name": "iShares 新興市場ETF (Emerging Markets)", "keywords": ["EEM", "新興市場", "新興市場ETF"]},
    "XOM": {"name": "埃克森美孚 (ExxonMobil)", "keywords": ["埃克森美孚", "ExxonMobil", "XOM", "能源股"]},
    "^FTSE": {"name": "富時100指數 (FTSE 100)", "keywords": ["富時", "倫敦股市", "^FTSE", "指數"]},
    "FUTY": {"name": "富時公用事業ETF (Utilities ETF)", "keywords": ["FUTY", "公用事業", "防禦股"]},
    "^GDAXI": {"name": "德國DAX指數", "keywords": ["DAX", "德國股市", "^GDAXI", "指數"]},
    "GLD": {"name": "SPDR黃金ETF (Gold ETF)", "keywords": ["GLD", "黃金ETF", "避險資產"]},
    "GOOG": {"name": "谷歌/Alphabet C股 (Google C)", "keywords": ["谷歌C", "Alphabet C", "GOOG"]},
    "GOOGL": {"name": "谷歌/Alphabet A股 (Google A)", "keywords": ["谷歌", "Alphabet", "GOOGL", "GOOG"]},
    "^GSPC": {"name": "S&P 500 指數", "keywords": ["標普", "S&P500", "^GSPC", "SPX", "指數"]},
    "GS": {"name": "高盛集團 (Goldman Sachs)", "keywords": ["高盛", "GoldmanSachs", "GS", "投行", "金融股"]},
    "HD": {"name": "家得寶 (Home Depot)", "keywords": ["家得寶", "HomeDepot", "HD"]},
    "INTC": {"name": "英特爾 (Intel)", "keywords": ["英特爾", "Intel", "INTC", "半導體"]},
    "IJR": {"name": "iShares 核心標普小型股ETF (Small Cap)", "keywords": ["IJR", "小型股ETF", "Russell2000"]},
    "IYR": {"name": "iShares 美國房地產ETF (Real Estate)", "keywords": ["IYR", "房地產ETF", "REITs"]},
    "JNJ": {"name": "嬌生 (Johnson & Johnson)", "keywords": ["嬌生", "Johnson&Johnson", "JNJ", "醫療保健"]},
    "JPM": {"name": "摩根大通 (JPMorgan Chase)", "keywords": ["摩根大通", "JPMorgan", "JPM", "金融股"]},
    "LLY": {"name": "禮來 (Eli Lilly)", "keywords": ["禮來", "EliLilly", "LLY", "製藥"]},
    "LMT": {"name": "洛克希德·馬丁 (Lockheed Martin)", "keywords": ["洛克希德馬丁", "LMT", "軍工", "國防"]},
    "LULU": {"name": "Lululemon", "keywords": ["Lululemon", "LULU", "運動服飾", "消費股"]},
    "MA": {"name": "萬事達卡 (Mastercard)", "keywords": ["萬事達卡", "Mastercard", "MA", "支付"]},
    "MCD": {"name": "麥當勞 (McDonald's)", "keywords": ["麥當勞", "McDonalds", "MCD"]},
    "META": {"name": "Meta/臉書 (Facebook)", "keywords": ["臉書", "Meta", "FB", "META", "Facebook"]},
    "MGM": {"name": "美高梅國際酒店集團 (MGM Resorts)", "keywords": ["美高梅", "MGM", "娛樂", "博彩"]},
    "MSFT": {"name": "微軟 (Microsoft)", "keywords": ["微軟", "Microsoft", "MSFT", "雲端", "AI"]},
    "MS": {"name": "摩根士丹利 (Morgan Stanley)", "keywords": ["摩根士丹利", "MorganStanley", "MS", "投行"]},
    "MRNA": {"name": "莫德納 (Moderna)", "keywords": ["莫德納", "Moderna", "MRNA", "生物科技", "疫苗"]},
    "MSCI": {"name": "MSCI ACWI ETF", "keywords": ["MSCI", "全球股票ETF"]},
    "^IXIC": {"name": "NASDAQ 綜合指數", "keywords": ["納斯達克", "NASDAQ", "^IXIC", "指數", "科技股"]},
    "^N225": {"name": "日經225指數 (Nikkei 225)", "keywords": ["日經", "Nikkei", "^N225", "日本股市", "指數"]},
    "NFLX": {"name": "網飛 (Netflix)", "keywords": ["網飛", "Netflix", "NFLX"]},
    "NKE": {"name": "耐克 (Nike)", "keywords": ["耐克", "Nike", "NKE", "運動用品"]},
    "NOW": {"name": "ServiceNow", "keywords": ["ServiceNow", "NOW", "SaaS", "企業軟體"]},
    "NVDA": {"name": "輝達 (Nvidia)", "keywords": ["輝達", "英偉達", "AI", "NVDA", "Nvidia", "GPU", "半導體"]},
    "ORCL": {"name": "甲骨文 (Oracle)", "keywords": ["甲骨文", "Oracle", "ORCL"]},
    "PEP": {"name": "百事 (PepsiCo)", "keywords": ["百事", "Pepsi", "PEP"]},
    "PFE": {"name": "輝瑞 (Pfizer)", "keywords": ["輝瑞", "Pfizer", "PFE", "製藥", "疫苗"]},
    "PG": {"name": "寶潔 (Procter & Gamble)", "keywords": ["寶潔", "P&G", "PG"]},
    "PYPL": {"name": "PayPal", "keywords": ["PayPal", "PYPL", "金融科技", "Fintech"]},
    "QCOM": {"name": "高通 (Qualcomm)", "keywords": ["高通", "Qualcomm", "QCOM", "半導體"]},
    "QQQM": {"name": "Invesco NASDAQ 100 ETF (低費率)", "keywords": ["QQQM", "納斯達克ETF", "科技股ETF"]},
    "QQQ": {"name": "Invesco QQQ Trust", "keywords": ["QQQ", "納斯達克ETF", "科技股ETF"]},
    "RTX": {"name": "雷神技術 (Raytheon Technologies)", "keywords": ["雷神", "Raytheon", "RTX", "軍工", "航太國防"]},
    "SCHD": {"name": "Schwab美國高股息ETF (High Dividend)", "keywords": ["SCHD", "高股息ETF", "美股派息"]},
    "SBUX": {"name": "星巴克 (Starbucks)", "keywords": ["星巴克", "Starbucks", "SBUX", "消費股"]},
    "SIRI": {"name": "Sirius XM", "keywords": ["SiriusXM", "SIRI", "媒體", "廣播"]},
    "SMH": {"name": "VanEck Vectors半導體ETF", "keywords": ["SMH", "半導體ETF", "晶片股"]},
    "SPY": {"name": "SPDR 標普500 ETF", "keywords": ["SPY", "標普ETF"]},
    "TLT": {"name": "iShares 20年期以上公債ETF (Treasury Bond)", "keywords": ["TLT", "美債", "公債ETF"]},
    "TSLA": {"name": "特斯拉 (Tesla)", "keywords": ["特斯拉", "電動車", "TSLA", "Tesla"]},
    "UNH": {"name": "聯合健康 (UnitedHealth Group)", "keywords": ["聯合健康", "UNH", "醫療保健"]},
    "USO": {"name": "美國石油基金ETF (Oil Fund)", "keywords": ["USO", "石油ETF", "原油"]},
    "V": {"name": "Visa", "keywords": ["Visa", "V"]},
    "VGT": {"name": "Vanguard資訊科技ETF (Tech ETF)", "keywords": ["VGT", "科技ETF", "資訊科技"]},
    "^VIX": {"name": "恐慌指數 (VIX)", "keywords": ["VIX", "恐慌指數", "波動率指數"]},
    "VNQ": {"name": "Vanguard房地產ETF (Real Estate)", "keywords": ["VNQ", "房地產ETF", "REITs"]},
    "VOO": {"name": "Vanguard 標普500 ETF", "keywords": ["VOO", "Vanguard"]},
    "VTI": {"name": "Vanguard整體股市ETF (Total Market)", "keywords": ["VTI", "整體股市", "TotalMarket"]},
    "VZ": {"name": "威瑞森 (Verizon)", "keywords": ["威瑞森", "Verizon", "VZ", "電信股"]},
    "WBA": {"name": "沃爾格林 (Walgreens Boots Alliance)", "keywords": ["沃爾格林", "Walgreens", "WBA", "藥品零售"]},
    "WFC": {"name": "富國銀行 (Wells Fargo)", "keywords": ["富國銀行", "WellsFargo", "WFC", "金融股"]},
    "WMT": {"name": "沃爾瑪 (Walmart)", "keywords": ["沃爾瑪", "Walmart", "WMT"]},
    # 台股/ETF/指數
    "0050.TW": {"name": "元大台灣50", "keywords": ["台灣50", "0050", "台灣五十", "ETF"]},
    "0051.TW": {"name": "元大中型100", "keywords": ["中型100", "0051", "ETF"]},
    "0055.TW": {"name": "元大MSCI金融", "keywords": ["元大金融", "0055", "金融股ETF"]},
    "0056.TW": {"name": "元大高股息", "keywords": ["高股息", "0056", "ETF"]},
    "006208.TW": {"name": "富邦台50", "keywords": ["富邦台50", "006208", "台灣五十ETF"]},
    "00679B.TW": {"name": "元大美債20年", "keywords": ["00679B", "美債ETF", "債券ETF"]},
    "00687B.TW": {"name": "國泰20年美債", "keywords": ["00687B", "美債ETF", "債券ETF"]},
    "00713.TW": {"name": "元大台灣高息低波", "keywords": ["00713", "高息低波", "ETF"]},
    "00878.TW": {"name": "國泰永續高股息", "keywords": ["00878", "國泰永續", "ETF"]},
    "00888.TW": {"name": "永豐台灣ESG", "keywords": ["00888", "ESG", "ETF"]},
    "00891.TW": {"name": "富邦特選高股息30", "keywords": ["00891", "高股息30", "ETF"]},
    "00919.TW": {"name": "群益台灣精選高股息", "keywords": ["00919", "群益高股息", "ETF"]},
    "00929.TW": {"name": "復華台灣科技優息", "keywords": ["00929", "科技優息", "月配息", "ETF"]},
    "00939.TW": {"name": "統一台灣高息動能", "keywords": ["00939", "高息動能", "ETF"]},
    "00940.TW": {"name": "元大臺灣價值高息", "keywords": ["00940", "臺灣價值高息", "ETF"]},
    "1101.TW": {"name": "台泥", "keywords": ["台泥", "1101"]},
    "1216.TW": {"name": "統一", "keywords": ["統一", "1216", "食品股", "集團股"]},
    "1301.TW": {"name": "台塑", "keywords": ["台塑", "1301", "塑化股"]},
    "1303.TW": {"name": "南亞", "keywords": ["南亞", "1303", "台塑集團"]},
    "1504.TW": {"name": "東元", "keywords": ["東元", "1504", "電機", "重電"]},
    "1710.TW": {"name": "東聯", "keywords": ["東聯", "1710", "塑化", "遠東集團"]},
    "2002.TW": {"name": "中鋼", "keywords": ["中鋼", "2002", "鋼鐵"]},
    "2201.TW": {"name": "裕隆", "keywords": ["裕隆", "2201", "汽車", "電動車"]},
    "2301.TW": {"name": "光寶科", "keywords": ["光寶科", "2301", "電源供應器", "光電"]},
    "2303.TW": {"name": "聯電", "keywords": ["聯電", "2303", "UMC", "晶圓", "半導體"]},
    "2308.TW": {"name": "台達電", "keywords": ["台達電", "2308", "Delta"]},
    "2317.TW": {"name": "鴻海", "keywords": ["鴻海", "2317", "Foxconn"]},
    "2327.TW": {"name": "國巨", "keywords": ["國巨", "2327", "被動元件"]},
    "2330.TW": {"name": "台積電", "keywords": ["台積電", "2330", "TSMC", "晶圓", "半導體"]},
    "2344.TW": {"name": "華邦電", "keywords": ["華邦電", "2344", "DRAM", "Flash", "記憶體"]},
    "2345.TW": {"name": "智邦", "keywords": ["智邦", "2345", "網通設備", "交換器"]},
    "2353.TW": {"name": "宏碁", "keywords": ["宏碁", "2353", "Acer", "PC"]},
    "2357.TW": {"name": "華碩", "keywords": ["華碩", "2357"]},
    "2379.TW": {"name": "瑞昱", "keywords": ["瑞昱", "2379", "RTL"]},
    "2382.TW": {"name": "廣達", "keywords": ["廣達", "2382", "AI伺服器"]},
    "2408.TW": {"name": "南亞科", "keywords": ["南亞科", "2408", "DRAM"]},
    "2409.TW": {"name": "友達", "keywords": ["友達", "2409", "面板股", "顯示器"]},
    "2454.TW": {"name": "聯發科", "keywords": ["聯發科", "2454", "MediaTek"]},
    "2455.TW": {"name": "全新", "keywords": ["全新", "2455", "砷化鎵", "PA"]},
    "2474.TW": {"name": "可成", "keywords": ["可成", "2474", "金屬機殼"]},
    "2498.TW": {"name": "宏達電", "keywords": ["宏達電", "2498", "HTC", "VR", "元宇宙"]},
    "2603.TW": {"name": "長榮", "keywords": ["長榮", "2603", "航運"]},
    "2609.TW": {"name": "陽明", "keywords": ["陽明", "2609", "航運"]},
    "2615.TW": {"name": "萬海", "keywords": ["萬海", "2615", "航運"]},
    "2834.TW": {"name": "臺企銀", "keywords": ["臺企銀", "2834", "金融股", "公股"]},
    "2880.TW": {"name": "華南金", "keywords": ["華南金", "2880", "金融股"]},
    "2881.TW": {"name": "富邦金", "keywords": ["富邦金", "2881", "金融股"]},
    "2882.TW": {"name": "國泰金", "keywords": ["國泰金", "2882", "金融股"]},
    "2884.TW": {"name": "玉山金", "keywords": ["玉山金", "2884", "金融股"]},
    "2886.TW": {"name": "兆豐金", "keywords": ["兆豐金", "2886", "金融股"]},
    "2890.TW": {"name": "永豐金", "keywords": ["永豐金", "2890", "金融股"]},
    "2891.TW": {"name": "中信金", "keywords": ["中信金", "2891", "金融股"]},
    "2892.TW": {"name": "第一金", "keywords": ["第一金", "2892", "金融股", "公股銀行"]},
    "3008.TW": {"name": "大立光", "keywords": ["大立光", "3008", "光學鏡頭"]},
    "3017.TW": {"name": "奇鋐", "keywords": ["奇鋐", "3017", "散熱"]},
    "3037.TW": {"name": "欣興", "keywords": ["欣興", "3037", "ABF載板", "PCB"]},
    "3231.TW": {"name": "緯創", "keywords": ["緯創", "3231", "AI伺服器"]},
    "3711.TW": {"name": "日月光投控", "keywords": ["日月光", "3711", "封裝測試", "半導體後段"]},
    "4938.TW": {"name": "和碩", "keywords": ["和碩", "4938", "代工", "電子組裝"]},
    "5880.TW": {"name": "合庫金", "keywords": ["合庫金", "5880", "金融股"]},
    "6239.TW": {"name": "力積電", "keywords": ["力積電", "6239", "DRAM", "晶圓代工"]},
    "6415.TW": {"name": "創意", "keywords": ["M31", "創意電子", "6415", "IP"]},
    "6669.TW": {"name": "緯穎", "keywords": ["緯穎", "6669", "AI伺服器", "資料中心"]},
    "^TWII": {"name": "台股指數", "keywords": ["台股指數", "加權指數", "^TWII", "指數"]},
    # 加密貨幣
    "AAVE-USD": {"name": "Aave", "keywords": ["Aave", "AAVE", "DeFi", "借貸協議"]},
    "ADA-USD": {"name": "Cardano", "keywords": ["Cardano", "ADA", "ADA-USDT"]},
    "ALGO-USD": {"name": "Algorand", "keywords": ["Algorand", "ALGO", "公鏈"]},
    "APT-USD": {"name": "Aptos", "keywords": ["Aptos", "APT", "Layer1", "公鏈"]},
    "ARB-USD": {"name": "Arbitrum", "keywords": ["Arbitrum", "ARB", "Layer2", "擴容"]},
    "ATOM-USD": {"name": "Cosmos", "keywords": ["Cosmos", "ATOM", "跨鏈"]},
    "AVAX-USD": {"name": "Avalanche", "keywords": ["Avalanche", "AVAX", "AVAX-USDT"]},
    "AXS-USD": {"name": "Axie Infinity", "keywords": ["Axie", "AXS", "GameFi", "遊戲"]},
    "BCH-USD": {"name": "比特幣現金 (Bitcoin Cash)", "keywords": ["比特幣現金", "BCH"]},
    "BNB-USD": {"name": "幣安幣 (Binance Coin)", "keywords": ["幣安幣", "BNB", "BNB-USDT", "交易所幣"]},
    "BTC-USD": {"name": "比特幣 (Bitcoin)", "keywords": ["比特幣", "BTC", "bitcoin", "BTC-USDT", "加密貨幣之王"]},
    "DAI-USD": {"name": "Dai", "keywords": ["Dai", "DAI", "穩定幣", "MakerDAO"]},
    "DOGE-USD": {"name": "狗狗幣 (Dogecoin)", "keywords": ["狗狗幣", "DOGE", "DOGE-USDT", "迷因幣"]},
    "DOT-USD": {"name": "Polkadot", "keywords": ["Polkadot", "DOT", "DOT-USDT"]},
    "ETC-USD": {"name": "以太坊經典 (Ethereum Classic)", "keywords": ["以太坊經典", "ETC", "EthereumClassic"]},
    "ETH-USD": {"name": "以太坊 (Ethereum)", "keywords": ["以太坊", "ETH", "ethereum", "ETH-USDT", "智能合約"]},
    "FIL-USD": {"name": "Filecoin", "keywords": ["Filecoin", "FIL", "去中心化儲存"]},
    "FTM-USD": {"name": "Fantom", "keywords": ["Fantom", "FTM", "公鏈"]},
    "HBAR-USD": {"name": "Hedera", "keywords": ["Hedera", "HBAR", "分散式帳本"]},
    "ICP-USD": {"name": "Internet Computer", "keywords": ["ICP", "網際網路電腦"]},
    "IMX-USD": {"name": "ImmutableX", "keywords": ["ImmutableX", "IMX", "GameFi", "NFT L2"]},
    "INJ-USD": {"name": "Injective Protocol", "keywords": ["Injective", "INJ", "DeFi", "去中心化交易"]},
    "LDO-USD": {"name": "Lido DAO", "keywords": ["Lido", "LDO", "ETH質押", "DeFi"]},
    "LINK-USD": {"name": "Chainlink", "keywords": ["Chainlink", "LINK", "LINK-USDT", "預言機"]},
    "LTC-USD": {"name": "萊特幣 (Litecoin)", "keywords": ["萊特幣", "LTC", "數位白銀"]},
    "LUNA1-USD": {"name": "Terra 2.0 (LUNA)", "keywords": ["LUNA", "Terra 2.0"]},
    "MANA-USD": {"name": "Decentraland", "keywords": ["Decentraland", "MANA", "元宇宙", "虛擬土地"]},
    "MATIC-USD": {"name": "Polygon", "keywords": ["Polygon", "MATIC", "Layer2", "側鏈"]},
    "MKR-USD": {"name": "Maker", "keywords": ["Maker", "MKR", "DAI發行", "DeFi"]},
    "NEAR-USD": {"name": "Near Protocol", "keywords": ["Near", "NEAR", "公鏈"]},
    "OP-USD": {"name": "Optimism", "keywords": ["Optimism", "OP", "Layer2", "擴容"]},
    "SAND-USD": {"name": "The Sandbox", "keywords": ["TheSandbox", "SAND", "元宇宙", "NFT"]},
    "SHIB-USD": {"name": "柴犬幣 (Shiba Inu)", "keywords": ["柴犬幣", "SHIB", "迷因幣", "Shiba"]},
    "SOL-USD": {"name": "Solana", "keywords": ["Solana", "SOL", "SOL-USDT"]},
    "SUI-USD": {"name": "Sui", "keywords": ["Sui", "SUI", "Layer1", "公鏈"]},
    "TIA-USD": {"name": "Celestia", "keywords": ["Celestia", "TIA", "模組化區塊鏈"]},
    "TRX-USD": {"name": "Tron", "keywords": ["波場", "TRX", "Tron"]},
    "UNI-USD": {"name": "Uniswap", "keywords": ["Uniswap", "UNI", "去中心化交易所", "DEX"]},
    "USDC-USD": {"name": "USD Coin", "keywords": ["USDC", "穩定幣", "美元幣"]},
    "USDT-USD": {"name": "泰達幣 (Tether)", "keywords": ["泰達幣", "USDT", "穩定幣", "Tether"]},
    "VET-USD": {"name": "VeChain", "keywords": ["VeChain", "VET", "供應鏈"]},
    "WLD-USD": {"name": "Worldcoin", "keywords": ["Worldcoin", "WLD", "AI", "身份驗證"]},
    "XMR-USD": {"name": "門羅幣 (Monero)", "keywords": ["門羅幣", "Monero", "XMR", "隱私幣"]},
    "XRP-USD": {"name": "瑞波幣 (Ripple)", "keywords": ["瑞波幣", "XRP", "XRP-USDT"]},
    "XTZ-USD": {"name": "Tezos", "keywords": ["Tezos", "XTZ", "公鏈"]},
    "ZEC-USD": {"name": "大零幣 (ZCash)", "keywords": ["大零幣", "ZCash", "ZEC", "隱私幣"]},
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

# ==============================================================================
# 2. 數據獲取與基本資訊處理 (Data Fetching & Info)
# ==============================================================================

def sync_text_input_from_selection():
    """當下拉選單變動時，觸發此函式，更新文字輸入框的值。"""
    try:
        selected_category = st.session_state.category_selector
        selected_hot_key = st.session_state.hot_target_selector
        symbol_code = CATEGORY_HOT_OPTIONS[selected_category][selected_hot_key]
        st.session_state.sidebar_search_input = symbol_code
    except Exception:
        pass # 忽略可能因快速切換選單產生的暫時性錯誤

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

@st.cache_data(ttl=3600)
def get_chips_and_news_analysis(symbol):
    """
    獲取籌碼面 (機構持股) 和消息面 (新聞) 數據。
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # 籌碼面: 機構持股比例
        inst_holders = ticker.institutional_holders
        inst_hold_pct = 0
        if inst_holders is not None and not inst_holders.empty and '% of Shares Held by Institutions' in inst_holders.columns:
            # 嘗試從 yfinance 的不同欄位獲取數據
            try:
                value = inst_holders.loc[0, '% of Shares Held by Institutions']
                inst_hold_pct = float(str(value).strip('%')) / 100 if isinstance(value, str) else float(value)
            except (KeyError, IndexError):
                # 如果上述欄位不存在，嘗試其他可能的欄位
                if not inst_holders.empty and len(inst_holders.columns) > 2:
                    value = inst_holders.iloc[0, 2] # 假設在第三欄
                    inst_hold_pct = float(str(value).replace('%','')) / 100 if isinstance(value, str) else float(value)

        # 消息面: 近期新聞
        news = ticker.news
        headlines = [f"- {item['title']}" for item in news[:5]] if news else ["近期無相關新聞"]
        
        return {"inst_hold_pct": inst_hold_pct, "news_summary": "\n".join(headlines)}
    except Exception:
        return {"inst_hold_pct": 0, "news_summary": "無法獲取新聞數據。"}

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
            ema_10, ema_50, ema_200 = last_row['EMA_10'], last_row['EMA_50'], last_row['EMA_200']
            if ema_10 > ema_50 and ema_50 > ema_200:
                conclusion, color_key = f"**強多頭：MA 多頭排列** (10>50>200)", "red"
            elif ema_10 < ema_50 and ema_50 < ema_200:
                conclusion, color_key = f"**強空頭：MA 空頭排列** (10<50<200)", "green"
            elif ema_10 > ema_50 or ema_50 > ema_200:
                conclusion, color_key = "中性偏多：MA 偏多排列", "orange"
            else:
                conclusion, color_key = "盤整：MA 交錯", "blue"
            
        elif 'RSI' in name:
            if value > 70:
                conclusion, color_key = "空頭：超買區域 (> 70)，潛在回調", "green" 
            elif value < 30:
                conclusion, color_key = "多頭：超賣區域 (< 30)，潛在反彈", "red"
            elif value > 50:
                conclusion, color_key = "多頭：RSI > 50，位於強勢區間", "red"
            else:
                conclusion, color_key = "空頭：RSI < 50，位於弱勢區間", "green"
        
        elif 'MACD' in name:
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
            if value >= 40:
                conclusion, color_key = f"**強趨勢：極強趨勢** (ADX >= 40)", "red"
            elif value >= 25:
                conclusion, color_key = f"趨勢：趨勢確認 (ADX >= 25)", "orange"
            else:
                conclusion, color_key = f"盤整：弱勢或橫盤整理 (ADX < 25)", "blue"
        
        elif 'ATR' in name:
            atr_ratio = value / last_row['Close'] * 100
            atr_mean = df_clean['ATR'].mean()
            if value > atr_mean * 1.5:
                conclusion, color_key = f"高波動：{atr_ratio:.2f}% (潛在機會/風險)", "orange"
            elif value < atr_mean * 0.75:
                conclusion, color_key = f"低波動：{atr_ratio:.2f}% (潛在突破/沉寂)", "blue"
            else:
                conclusion, color_key = f"中性：正常波動性 ({atr_ratio:.2f}% 寬度)", "blue"

        elif '布林通道' in name:
            bb_width_pct = (last_row['BB_High'] - last_row['BB_Low']) / last_row['Close'] * 100
            if value > last_row['BB_High']:
                conclusion, color_key = f"**空頭：突破上軌** (潛在回調)", "green"
            elif value < last_row['BB_Low']:
                conclusion, color_key = f"**多頭：跌破下軌** (潛在反彈)", "red"
            else:
                conclusion, color_key = f"中性：在上下軌間 ({bb_width_pct:.2f}% 寬度)", "blue"

        data.append([name, value, conclusion, color_key])

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

    total_return = ((capital_series.iloc[-1] - initial_capital) / initial_capital) * 100 if not capital_series.empty else 0
    total_trades = len(trades)
    win_rate = (sum(1 for t in trades if t['is_win']) / total_trades) * 100 if total_trades > 0 else 0
    
    # 最大回撤計算
    max_value = capital_series.expanding(min_periods=1).max()
    drawdown = (capital_series - max_value) / max_value
    max_drawdown = abs(drawdown.min()) * 100 if not drawdown.empty else 0
    
    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "total_trades": total_trades,
        "message": f"回測區間 {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}。",
        "capital_curve": capital_series
    }

def create_comprehensive_chart(df, symbol, period_key):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_10'], mode='lines', name='EMA 10', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], mode='lines', name='EMA 200', line=dict(color='red', width=2, dash='dot')), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD Histogram', marker_color=np.where(df['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_9'], name='RSI (9)', line=dict(color='purple')), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.2, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.2, row=3, col=1)
    fig.update_layout(title=f'{symbol} 技術分析圖 ({period_key})', xaxis_rangeslider_visible=False, height=700, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
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
        st.session_state.last_search_symbol = "2330.TW" # 預設值
    if 'data_df' not in st.session_state:
        st.session_state.data_df = pd.DataFrame()
    if 'run_analysis' not in st.session_state:
        st.session_state.run_analysis = False

    # -----------------------------
    # 側邊欄：參數設定
    # -----------------------------
    st.sidebar.markdown("<h2 style='color: #FA8072;'>🚀 AI 趨勢分析</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # 1. 選擇資產類別
    selected_category = st.sidebar.selectbox(
        '1. 選擇資產類別', 
        list(CATEGORY_HOT_OPTIONS.keys()), 
        index=1, 
        key='category_selector'
    )
    hot_options_map = CATEGORY_HOT_OPTIONS.get(selected_category, {})

    # 2. 熱門標的選擇
    default_symbol_key = '2330.TW - 台積電'
    if default_symbol_key not in hot_options_map:
        default_symbol_key = list(hot_options_map.keys())[0] if hot_options_map else None
    
    default_index = list(hot_options_map.keys()).index(default_symbol_key) if default_symbol_key else 0
    
    st.sidebar.selectbox(
        '2. 選擇熱門標的', 
        list(hot_options_map.keys()), 
        index=default_index, 
        key='hot_target_selector', 
        on_change=sync_text_input_from_selection
    )

    # 3. 自行輸入
    st.sidebar.text_input(
        '...或手動輸入代碼/名稱:', 
        st.session_state.get('sidebar_search_input', '2330.TW'), 
        key='sidebar_search_input'
    )

    # 4. 週期選擇
    selected_period_key = st.sidebar.selectbox(
        '3. 選擇分析週期', 
        list(PERIOD_MAP.keys()), 
        index=2
    )
    st.sidebar.markdown("---")

    # 5. 執行按鈕
    if st.sidebar.button('📊 執行AI分析', use_container_width=True):
        st.session_state.run_analysis = True
        st.session_state.symbol_to_analyze = get_symbol_from_query(st.session_state.sidebar_search_input)
        st.session_state.period_key = selected_period_key

    # -----------------------------
    # 主頁面：分析結果或歡迎頁
    # -----------------------------
    if st.session_state.get('run_analysis', False):
        final_symbol = st.session_state.symbol_to_analyze
        period_key = st.session_state.period_key
        period, interval = PERIOD_MAP[period_key]

        with st.spinner(f"🔍 正在啟動AI模型，分析 **{final_symbol}**..."):
            df_raw = get_stock_data(final_symbol, period, interval)
            
            if df_raw.empty or len(df_raw) < 60:
                st.error(f"❌ **數據不足或代碼無效：** {final_symbol}。AI模型至少需要60個數據點才能進行精準分析。")
            else:
                info = get_company_info(final_symbol)
                fa_ratings = get_fundamental_ratings(final_symbol)
                chips_data = get_chips_and_news_analysis(final_symbol)
                
                df_tech = calculate_comprehensive_indicators(df_raw.copy())
                analysis = generate_ai_fusion_signal(df_tech, fa_ratings['AI_SCORE'], chips_data)
                
                price = df_raw['Close'].iloc[-1]
                consensus_sl, consensus_tp, all_strategy_results = get_consensus_levels(df_tech, price)

                st.header(f"📈 {info['name']} ({final_symbol}) AI趨勢分析報告")
                
                display_fa = fa_ratings['DISPLAY_SCORE']
                st.markdown(f"**分析週期:** {period_key} | **FA評級:** **{display_fa.get('Combined_Rating',0):.1f}/9.0** ({display_fa.get('Message','N/A')})")
                st.markdown("---")
                
                st.subheader("💡 核心行動與量化評分")
                prev_close = df_raw['Close'].iloc[-2] if len(df_raw) > 1 else price
                change, pct = price - prev_close, (price - prev_close) / prev_close * 100 if prev_close != 0 else 0
                currency_symbol = get_currency_symbol(final_symbol)
                pf = ".4f" if price < 100 and currency_symbol != 'NT$' else ".2f"
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💰 當前價格", f"{currency_symbol}{price:{pf}}", f"{change:+.{pf}} ({pct:+.2f}%)")
                c2.metric("🎯 AI 行動建議", analysis['action'])
                c3.metric("🔥 AI 總量化評分", f"{analysis['score']:.2f}")
                c4.metric("🛡️ AI 信心指數", f"{analysis['confidence']:.0f}%")
                
                st.markdown("---")
                st.subheader("🛡️ AI 綜合策略與風險控制")
                s1, s2, s3 = st.columns(3)
                s1.metric("建議進場價 (參考):", f"{currency_symbol}{price:{pf}}")
                s2.metric("🚀 共識止盈價 (TP):", f"{currency_symbol}{consensus_tp:{pf}}" if pd.notna(consensus_tp) else "N/A", help="綜合多種策略計算得出的共識目標價")
                s3.metric("🛑 共識止損價 (SL):", f"{currency_symbol}{consensus_sl:{pf}}" if pd.notna(consensus_sl) else "N/A", help="綜合多種策略計算得出的共識風險控制價")

                with st.expander("詳細查看各止盈止損策略的計算結果"):
                    results_df = pd.DataFrame.from_dict(all_strategy_results, orient='index').reset_index()
                    results_df.columns = ['策略名稱', '止損價 (SL)', '止盈價 (TP)']
                    st.dataframe(results_df.style.format({'止損價 (SL)': '{:.4f}', '止盈價 (TP)': '{:.4f}'}), use_container_width=True)

                st.markdown("---")
                
                tab1, tab2, tab3, tab4 = st.tabs(["📊 AI判讀細節", "🧪 策略回測報告", "🛠️ 技術指標狀態表", "📰 近期新聞"])
                
                with tab1:
                    st.subheader("AI 判讀細節")
                    opinions = list(analysis['ai_opinions'].items())
                    ai_fa_details = fa_ratings.get('AI_SCORE', {}).get('details')
                    if ai_fa_details:
                        for k, v in ai_fa_details.items(): opinions.append([f"基本面 - {k}", str(v)])
                    st.dataframe(pd.DataFrame(opinions, columns=['分析維度', '判斷結果']), use_container_width=True)

                with tab2:
                    st.subheader("策略回測報告 (SMA 20/EMA 50 交叉)")
                    bt = run_backtest(df_raw.copy())
                    if bt.get("total_trades", 0) > 0:
                        b1, b2, b3, b4 = st.columns(4)
                        b1.metric("📊 總回報率", f"{bt['total_return']}%", delta=bt['message'], delta_color='off')
                        b2.metric("📈 勝率", f"{bt['win_rate']}%")
                        b3.metric("📉 最大回撤", f"{bt['max_drawdown']}%")
                        b4.metric("🤝 交易次數", f"{bt['total_trades']} 次")
                        if 'capital_curve' in bt and not bt['capital_curve'].empty:
                            fig = go.Figure(go.Scatter(x=bt['capital_curve'].index, y=bt['capital_curve'], name='資金曲線'))
                            fig.update_layout(title='SMA 20/EMA 50 交叉策略資金曲線', height=300)
                            st.plotly_chart(fig, use_container_width=True)
                    else: st.warning(f"回測無法執行：{bt.get('message', '錯誤')}")
                
                with tab3:
                    st.subheader("技術指標狀態表")
                    technical_df = get_technical_data_df(df_tech)
                    st.dataframe(technical_df.set_index('指標名稱')[['最新值', '分析結論']].style.apply(
                        lambda s: s.map(lambda v: f"color: {'red' if '多頭' in str(v) or '強化' in str(v) else 'green' if '空頭' in str(v) or '削弱' in str(v) else 'orange' if '警告' in str(v) else 'grey'}"),
                        subset=['分析結論']
                    ), use_container_width=True)

                with tab4:
                    st.subheader("近期相關新聞")
                    st.markdown(chips_data['news_summary'].replace("\n", "\n\n"))

                st.markdown("---")
                st.subheader(f"📊 完整技術分析圖表")
                st.plotly_chart(create_comprehensive_chart(df_tech, final_symbol, period_key), use_container_width=True)

    else:
        display_homepage()

if __name__ == "__main__":
    # 初始化 Session State
    if 'last_search_symbol' not in st.session_state:
        st.session_state.last_search_symbol = "2330.TW"
    if 'data_df' not in st.session_state:
        st.session_state.data_df = pd.DataFrame()
    if 'run_analysis' not in st.session_state:
        st.session_state.run_analysis = False
    
    main()
st.markdown("---")
st.markdown("⚠️ **免責聲明**")
st.caption("本分析模型包含AI的量化觀點，但僅供教育與參考用途。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
st.markdown("📊 **數據來源:** Yahoo Finance | **技術指標:** TA 庫 | **APP優化:** 專業程式碼專家")

