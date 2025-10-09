import re
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

st.set_page_config(
    page_title="AI趨勢分析📈 (Expert)",
    page_icon="🚀",
    layout="wide"
)

# 週期映射
PERIOD_MAP = { 
    "30 分": ("60d", "30m"), 
    "4 小時": ("1y", "60m"), 
    "1 日": ("5y", "1d"), 
    "1 週": ("max", "1wk")
}

# 🚀 您的【所有資產清單】
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

# =====================================================================
# 2. 核心數據與分析輔助函式
# =====================================================================
def get_symbol_from_query(query: str) -> str:
    query = query.strip()
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_upper == code or any(query_upper == kw.upper() for kw in data["keywords"]):
            return code
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]:
            return code
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        tw_code = f"{query}.TW"
        if tw_code in FULL_SYMBOLS_MAP: return tw_code
        return tw_code
    return query

@st.cache_data(ttl=3600)
def get_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df.empty: return pd.DataFrame()
        df.columns = [col.capitalize() for col in df.columns]
        df.index.name = 'Date'
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df[~df.index.duplicated(keep='first')]
        if len(df) > 1: df = df.iloc[:-1]
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    info = FULL_SYMBOLS_MAP.get(symbol, {})
    if info:
        if symbol.endswith(".TW") or symbol.startswith("^TWII"):
            category, currency = "台股 (TW)", "TWD"
        elif symbol.endswith("-USD"):
            category, currency = "加密貨幣 (Crypto)", "USD"
        else:
            category, currency = "美股 (US)", "USD"
        return {"name": info['name'], "category": category, "currency": currency}
    try:
        ticker = yf.Ticker(symbol)
        yf_info = ticker.info
        name = yf_info.get('longName') or yf_info.get('shortName') or symbol
        currency = yf_info.get('currency') or "USD"
        quote_type = yf_info.get('quoteType', '')
        if quote_type == 'CRYPTOCURRENCY': category = "加密貨幣 (Crypto)"
        elif quote_type == 'INDEX': category = "指數"
        elif symbol.endswith(".TW"): category = "台股 (TW)"
        else: category = "美股 (US)"
        return {"name": name, "category": category, "currency": currency}
    except Exception:
        return {"name": symbol, "category": "未分類", "currency": "USD"}

@st.cache_data
def get_currency_symbol(symbol):
    currency_code = get_company_info(symbol).get('currency', 'USD')
    return 'NT$' if currency_code == 'TWD' else '$' if currency_code == 'USD' else currency_code + ' '

# =====================================================================
# 3. 趨勢判斷與止盈止損策略 (融合所有版本)
# =====================================================================
def support_resistance(df, lookback=60):
    df['Support'] = df['Low'].rolling(window=lookback).min() * 0.98
    df['Resistance'] = df['High'].rolling(window=lookback).max() * 1.02
    df['Volume_Filter'] = df['Volume'] > df['Volume'].rolling(50).mean() * 1.3
    df['SL'] = df['Support'].where(df['Volume_Filter'], df['Close'])
    df['TP'] = df['Resistance'].where(df['Volume_Filter'], df['Close'])
    return df

def bollinger_bands(df, period=50, dev=2.5):
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
    adx = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    volume_filter = df['Volume'] > df['Volume'].rolling(20).mean() * 1.2
    ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
    df['Senkou_A'] = ichimoku.ichimoku_a()
    df['Senkou_B'] = ichimoku.ichimoku_b()
    df['SL'] = df['Senkou_B'].where((df['Close'] < df['Senkou_B']) & (adx > 25) & volume_filter, df['Close'])
    df['TP'] = df['Senkou_A'].where((df['Close'] > df['Senkou_A']) & (adx > 25) & volume_filter, df['Close'])
    return df

def ma_crossover(df, fast=20, slow=50):
    fast_ema = ta.trend.ema_indicator(df['Close'], window=fast)
    slow_ema = ta.trend.ema_indicator(df['Close'], window=slow)
    macd = ta.trend.macd(df['Close'])
    obv = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    obv_filter = obv > obv.shift(1)
    df['SL'] = slow_ema.where((fast_ema < slow_ema) & (macd < 0) & obv_filter, df['Close'])
    df['TP'] = fast_ema.where((fast_ema > slow_ema) & (macd > 0) & obv_filter, df['Close'])
    return df

def vwap(df):
    df['VWAP'] = ta.volume.volume_weighted_average_price(df['High'], df['Low'], df['Close'], df['Volume'])
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    volume_filter = df['Volume'] > df['Volume'].rolling(20).mean() * 1.2
    df['SL'] = df['VWAP'].where((df['Close'] < df['VWAP']) & (df['RSI'] < 30) & volume_filter, df['Close'])
    df['TP'] = df['VWAP'].where((df['Close'] > df['VWAP']) & (df['RSI'] > 70) & volume_filter, df['Close'])
    return df

def parabolic_sar(df):
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
    all_results = {}
    sl_list, tp_list = [], []
    for name, func in STRATEGY_FUNCTIONS.items():
        try:
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
    consensus_sl = np.nanmean(sl_list) if sl_list else np.nan
    consensus_tp = np.nanmean(tp_list) if tp_list else np.nan
    return consensus_sl, consensus_tp, {k:[v['SL'],v['TP']] for k,v in all_results.items()}

def calculate_all_indicators(df):
    df['EMA_10'] = ta.trend.ema_indicator(df['Close'], window=10)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    macd = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
    df['MACD_Line'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    df['RSI_9'] = ta.momentum.rsi(df['Close'], window=9)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    df['ATR_14'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['ADX_14'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    df['CMF'] = ta.volume.chaikin_money_flow(df['High'], df['Low'], df['Close'], df['Volume'], window=20)
    df['MFI'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'], window=14)
    ichimoku = ta.trend.IchimokuIndicator(df['High'], df['Low'], window1=9, window2=26, window3=52)
    df['Ichimoku_A'] = ichimoku.ichimoku_a()
    df['Ichimoku_B'] = ichimoku.ichimoku_b()
    return df

def sync_text_input_from_selection():
    selected_category = st.session_state.category_selector
    selected_hot_key = st.session_state.hot_target_selector
    # hot_target_selector填的是顯示名, 要查 map
    symbol_code = CATEGORY_HOT_OPTIONS[selected_category][selected_hot_key]
    st.session_state.sidebar_search_input = symbol_code

# =====================================================================
# 4. UI 主流程 (融合所有版本)
# =====================================================================
def main():
    st.sidebar.markdown("<span style='color: #FA8072; font-weight: bold;'>🚀 AI 趨勢分析</span>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    selected_category = st.sidebar.selectbox('1. 資產類別', list(CATEGORY_HOT_OPTIONS.keys()), index=0)
    hot_options_map = CATEGORY_HOT_OPTIONS.get(selected_category, {})
    default_symbol_key = list(hot_options_map.keys())[0] if hot_options_map else None
    default_index = 0
    st.sidebar.selectbox('2. 熱門標的', list(hot_options_map.keys()), index=default_index, key='hot_target_selector')
    st.sidebar.text_input('...或手動輸入代碼/名稱:', '', key='sidebar_search_input')
    st.sidebar.text_input(
        "...或手動輸入代碼/名稱:",
        value=st.session_state.get('sidebar_search_input', hot_options_map[default_symbol]),
        key='sidebar_search_input'
    )
    st.sidebar.markdown("---")
    selected_period_key = st.sidebar.selectbox('3. 週期', list(PERIOD_MAP.keys()), index=2)
    st.sidebar.markdown("---")
    if st.sidebar.button('📊 執行AI分析', use_container_width=True):
        st.session_state['run_analysis'] = True
        st.session_state['symbol_to_analyze'] = get_symbol_from_query(st.session_state.sidebar_search_input or list(hot_options_map.values())[0])
        st.session_state['period_key'] = selected_period_key

    if st.session_state.get('run_analysis', False):
        symbol = st.session_state['symbol_to_analyze']
        period_key = st.session_state['period_key']
        period, interval = PERIOD_MAP[period_key]
        with st.spinner(f"🔍 正在分析 {symbol} ..."):
            df_raw = get_stock_data(symbol, period, interval)
            if df_raw.empty or len(df_raw) < 60:
                st.error(f"❌ 數據不足或代碼無效：{symbol}。至少需要60個數據點。")
            else:
                info = get_company_info(symbol)
                df_tech = calculate_all_indicators(df_raw.copy())
                price = df_raw['Close'].iloc[-1]
                consensus_sl, consensus_tp, all_strategy_results = get_consensus_levels(df_tech, price)
                currency_symbol = get_currency_symbol(symbol)
                pf = ".4f" if price < 100 and currency_symbol != 'NT$' else ".2f"
                prev_close = df_raw['Close'].iloc[-2] if len(df_raw) > 1 else price
                change, pct = price - prev_close, (price - prev_close) / prev_close * 100 if prev_close != 0 else 0

                st.header(f"📈 {info['name']} ({symbol}) AI趨勢分析報告")
                st.markdown(f"**分析週期:** {period_key}")
                st.markdown("---")
                st.subheader("💡 價格資訊")
                c1, c2, c3 = st.columns(3)
                c1.metric("💰 當前價格", f"{currency_symbol}{price:{pf}}", f"{change:+.{pf}} ({pct:+.2f}%)")
                c2.metric("🚀 共識止盈 (TP)", f"{currency_symbol}{consensus_tp:{pf}}" if pd.notna(consensus_tp) else "N/A")
                c3.metric("🛑 共識止損 (SL)", f"{currency_symbol}{consensus_sl:{pf}}" if pd.notna(consensus_sl) else "N/A")
                with st.expander("各策略計算結果"):
                    results_df = pd.DataFrame.from_dict(all_strategy_results, orient='index').reset_index()
                    results_df.columns = ['策略名稱', '止損價 (SL)', '止盈價 (TP)']
                    st.dataframe(results_df.style.format({'止損價 (SL)': '{:.4f}', '止盈價 (TP)': '{:.4f}'}), use_container_width=True)
                st.markdown("---")
                st.subheader("📊 技術分析圖表")
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                fig.add_trace(go.Candlestick(x=df_raw.index, open=df_raw['Open'], high=df_raw['High'], low=df_raw['Low'], close=df_raw['Close'], name='K線'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_raw.index, y=df_tech['EMA_10'], mode='lines', name='EMA 10', line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_raw.index, y=df_tech['EMA_50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_raw.index, y=df_tech['EMA_200'], mode='lines', name='EMA 200', line=dict(color='red', width=2)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_raw.index, y=df_tech['MACD_Hist'], name='MACD Histogram', marker_color=np.where(df_tech['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)
                fig.add_trace(go.Scatter(x=df_raw.index, y=df_tech['RSI_9'], name='RSI (9)', line=dict(color='purple')), row=3, col=1)
                fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.2, row=3, col=1)
                fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.2, row=3, col=1)
                fig.update_layout(title=f'{symbol} 技術分析圖 ({period_key})', xaxis_rangeslider_visible=False, height=700, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<h1 style='color: #FA8072;'>🚀 歡迎使用 AI 趨勢分析</h1>", unsafe_allow_html=True)
        st.markdown("請在左側選擇或輸入您想分析的標的（例如：2330.TW、NVDA、BTC-USD），然後點擊 <span style='color: #FA8072; font-weight: bold;'>『📊 執行AI分析』</span> 開始。", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📝 使用步驟：")
        st.markdown("1. 選擇資產類別")
        st.markdown("2. 選擇標的")
        st.markdown("3. 選擇週期")
        st.markdown("4. 點擊『📊 執行AI分析』")

if __name__ == "__main__":
    main()
    st.markdown("---")
    st.markdown("⚠️ **免責聲明**")
    st.caption("本分析模型僅供參考用途。投資涉及風險，請審慎評估。")
    st.markdown("📊 數據來源: Yahoo Finance | 技術指標: TA 庫 | APP優化: 專業程式碼專家")
