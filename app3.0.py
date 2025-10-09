import re
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

# ==============================================================================
# 1. 頁面配置與全局設定
# ==============================================================================

st.set_page_config(
    page_title="AI趨勢分析📈",
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

# 🚀 您的【所有資產清單】(與您提供的一致，此處省略以節省空間)
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
# 2. 核心數據與分析函式
# ==============================================================================
def sync_text_input_from_selection():
    try:
        selected_category = st.session_state.category_selector
        selected_hot_key = st.session_state.hot_target_selector
        symbol_code = CATEGORY_HOT_OPTIONS[selected_category][selected_hot_key]
        st.session_state.sidebar_search_input = symbol_code
    except Exception:
        pass

def get_symbol_from_query(query: str) -> str:
    query = query.strip()
    query_upper = query.upper()
    for code, data in FULL_SYMBOLS_MAP.items():
        if query_upper == code.upper(): return code
        if any(query_upper == kw.upper() for kw in data["keywords"]): return code
    for code, data in FULL_SYMBOLS_MAP.items():
        if query == data["name"]: return code
    if re.fullmatch(r'\d{4,6}', query) and not any(ext in query_upper for ext in ['.TW', '.HK', '.SS', '-USD']):
        return f"{query}.TW"
    return query

@st.cache_data(ttl=300, show_spinner="正在從 Yahoo Finance 獲取最新市場數據...")
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
        if symbol.endswith(".TW") or symbol.startswith("^TWII"): category, currency = "台股 (TW)", "TWD"
        elif symbol.endswith("-USD"): category, currency = "加密貨幣 (Crypto)", "USD"
        else: category, currency = "美股 (US)", "USD"
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


# ==============================================================================
# 3. 專業級 TP/SL 策略函式 (全部自動運行)
# ==============================================================================

def pandas_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).fillna(0)
    loss = -delta.where(delta < 0, 0).fillna(0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def pandas_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.ewm(alpha=1/period, adjust=False).mean()

def pandas_macd(close, fast=8, slow=17, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - macd_signal
    return macd_line, macd_signal, macd_hist

def support_resistance(df, lookback=60):
    df['SL'] = df['Low'].rolling(window=lookback).min() * 0.98
    df['TP'] = df['High'].rolling(window=lookback).max() * 1.02
    return df

def bollinger_bands_strategy(df, period=50, dev=2.5):
    df['SMA'] = df['Close'].rolling(window=period).mean()
    df['STD'] = df['Close'].rolling(window=period).std()
    upper = df['SMA'] + (df['STD'] * dev)
    lower = df['SMA'] - (df['STD'] * dev)
    if df['Close'].iloc[-1] > df['SMA'].iloc[-1]:
        df['SL'] = lower
        df['TP'] = upper
    else:
        df['SL'] = upper
        df['TP'] = lower
    return df

def atr_stop(df, period=21, multiplier_sl=2.5, multiplier_tp=5):
    df['ATR'] = pandas_atr(df, period=period)
    df['SL'] = df['Close'] - (df['ATR'] * multiplier_sl)
    df['TP'] = df['Close'] + (df['ATR'] * multiplier_tp)
    return df

def donchian_channel(df, period=50):
    df['SL'] = df['Low'].rolling(window=period).min()
    df['TP'] = df['High'].rolling(window=period).max()
    return df

def keltner_channel(df, period=30, atr_multiplier=2.5, atr_period=14):
    df['EMA'] = df['Close'].ewm(span=period, adjust=False).mean()
    df['ATR'] = pandas_atr(df, period=atr_period)
    df['TP'] = df['EMA'] + (df['ATR'] * atr_multiplier)
    df['SL'] = df['EMA'] - (df['ATR'] * atr_multiplier)
    return df

def ichimoku_cloud(df):
    high_9, low_9 = df['High'].rolling(9).max(), df['High'].rolling(9).min()
    df['Tenkan'] = (high_9 + low_9) / 2
    high_26, low_26 = df['High'].rolling(26).max(), df['Low'].rolling(26).min()
    df['Kijun'] = (high_26 + low_26) / 2
    df['Senkou_A'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(26)
    high_52, low_52 = df['High'].rolling(52).max(), df['Low'].rolling(52).min()
    df['Senkou_B'] = ((high_52 + low_52) / 2).shift(26)
    
    price = df['Close']
    senkou_a, senkou_b = df['Senkou_A'], df['Senkou_B']
    if price.iloc[-1] > senkou_a.iloc[-1] and price.iloc[-1] > senkou_b.iloc[-1]:
        df['SL'] = df[['Senkou_A', 'Senkou_B']].min(axis=1)
        df['TP'] = price + (price - df['SL']) * 1.5
    else:
        df['TP'] = df[['Senkou_A', 'Senkou_B']].min(axis=1)
        df['SL'] = df[['Senkou_A', 'Senkou_B']].max(axis=1)
    return df

def ma_crossover(df, fast=20, slow=50):
    df['Fast_MA'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['Slow_MA'] = df['Close'].ewm(span=slow, adjust=False).mean()
    if df['Fast_MA'].iloc[-1] > df['Slow_MA'].iloc[-1]: # Golden Cross
        df['SL'] = df['Slow_MA']
        df['TP'] = df['Close'] * 1.1 # Simple 10% target
    else: # Death Cross
        df['TP'] = df['Slow_MA']
        df['SL'] = df['Close'] * 1.1 
    return df

def vwap_strategy(df):
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    df['SL'] = df['VWAP'] * 0.98
    df['TP'] = df['VWAP'] * 1.02
    return df

def trailing_stop(df, atr_period=14, atr_multiplier=3):
    df['ATR'] = pandas_atr(df, period=atr_period)
    df['SL'] = df['Close'] - (df['ATR'] * atr_multiplier)
    df['TP'] = df['Close'] + (df['ATR'] * 2 * atr_multiplier)
    return df

def chandelier_exit(df, period=22, atr_multiplier=3.5):
    df['ATR'] = pandas_atr(df, period=14)
    high_max = df['High'].rolling(window=period).max()
    low_min = df['Low'].rolling(window=period).min()
    
    sl_long = high_max - df['ATR'] * atr_multiplier
    sl_short = low_min + df['ATR'] * atr_multiplier
    
    if df['Close'].iloc[-1] > df['Close'].iloc[-period]:
        df['SL'] = sl_long
        df['TP'] = df['Close'] + (df['Close'] - sl_long) * 1.5
    else:
        df['SL'] = sl_short
        df['TP'] = df['Close'] - (sl_short - df['Close']) * 1.5
    return df

def supertrend(df, period=14, multiplier=3.5):
    df['ATR'] = pandas_atr(df, period=period)
    upper_band = ((df['High'] + df['Low']) / 2) + (multiplier * df['ATR'])
    lower_band = ((df['High'] + df['Low']) / 2) - (multiplier * df['ATR'])
    
    st = lower_band.copy()
    for i in range(1, len(df)):
        if df['Close'].iloc[i-1] <= st.iloc[i-1]:
            st.iloc[i] = min(upper_band.iloc[i], st.iloc[i-1])
        else:
            st.iloc[i] = max(lower_band.iloc[i], st.iloc[i-1])
            
    if df['Close'].iloc[-1] > st.iloc[-1]:
        df['SL'] = st
        df['TP'] = df['Close'] + (df['Close'] - st) * 2
    else:
        df['SL'] = st
        df['TP'] = df['Close'] - (st - df['Close']) * 2
    return df

def pivot_points(df):
    pivot = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
    s1 = (2 * pivot) - df['High'].shift(1)
    r1 = (2 * pivot) - df['Low'].shift(1)
    if df['Close'].iloc[-1] > pivot.iloc[-1]:
        df['SL'] = s1
        df['TP'] = r1
    else:
        df['SL'] = r1
        df['TP'] = s1
    return df

# 策略字典
STRATEGY_FUNCTIONS = {
    "支撐與阻力": support_resistance,
    "布林通道策略": bollinger_bands_strategy,
    "ATR 停損": atr_stop,
    "唐奇安通道": donchian_channel,
    "肯特納通道": keltner_channel,
    "一目均衡表": ichimoku_cloud,
    "均線交叉": ma_crossover,
    "VWAP 策略": vwap_strategy,
    "移動止損": trailing_stop,
    "吊燈停損": chandelier_exit,
    "超級趨勢": supertrend,
    "樞軸點": pivot_points,
}

# ==============================================================================
# 4. 核心分析與指標計算
# ==============================================================================

def pandas_adx(df, period=14):
    atr = pandas_atr(df, period)
    up_move = df['High'].diff()
    down_move = -df['Low'].diff() # Note the negative sign
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / atr)
    
    dx = 100 * (np.abs(plus_di - minus_di) / np.where(plus_di + minus_di == 0, 1, plus_di + minus_di))
    return dx.ewm(alpha=1/period, adjust=False).mean()
    
def calculate_technical_indicators(df):
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    
    df['MACD_Line'], df['MACD_Signal'], df['MACD_Hist'] = pandas_macd(df['Close'])
    df['RSI'] = pandas_rsi(df['Close'], period=9)
    
    sma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BB_High'] = sma20 + (std20 * 2)
    df['BB_Low'] = sma20 - (std20 * 2)
    
    df['ATR'] = pandas_atr(df, period=9)
    df['ADX'] = pandas_adx(df, period=9)
    
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    df['OBV_MA_20'] = df['OBV'].rolling(window=20).mean()
    return df

def get_consensus_levels(df, current_price):
    sl_candidates, tp_candidates, all_results = [], [], {}
    
    for name, func in STRATEGY_FUNCTIONS.items():
        try:
            df_strat = func(df.copy())
            sl = df_strat.iloc[-1].get('SL')
            tp = df_strat.iloc[-1].get('TP')
            all_results[name] = {'SL': sl, 'TP': tp}
            if pd.notna(sl) and sl < current_price:
                sl_candidates.append(sl)
            if pd.notna(tp) and tp > current_price:
                tp_candidates.append(tp)
        except Exception:
            continue
            
    if not sl_candidates or not tp_candidates:
        return np.nan, np.nan, all_results

    # 演算法：SL取最高的三個平均（找關鍵支撐），TP取最低的三個平均（找現實壓力）
    sl_candidates.sort(reverse=True)
    tp_candidates.sort()
    
    consensus_sl = np.mean(sl_candidates[:3]) if sl_candidates else np.nan
    consensus_tp = np.mean(tp_candidates[:3]) if tp_candidates else np.nan
    
    return consensus_sl, consensus_tp, all_results

@st.cache_data(ttl=3600)
def get_chips_and_news_analysis(symbol):
    try:
        ticker = yf.Ticker(symbol)
        inst_holders = ticker.institutional_holders
        inst_hold_pct = 0
        if inst_holders is not None and not inst_holders.empty:
            value = inst_holders.iloc[0, 2]
            inst_hold_pct = float(str(value).replace('%','')) / 100 if isinstance(value, str) else float(value)

        news = ticker.news
        headlines = [f"- {item['title']}" for item in news[:5]] if news else ["無"]
        return {"inst_hold_pct": inst_hold_pct, "news_summary": "\n".join(headlines)}
    except Exception:
        return {"inst_hold_pct": 0, "news_summary": "無法獲取新聞。"}

@st.cache_data(ttl=3600)
def calculate_advanced_fundamental_rating(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if info.get('quoteType') in ['INDEX', 'CRYPTOCURRENCY', 'ETF']:
            return {"score": 0, "summary": "不適用", "details": {}}
        score, details = 0, {}
        roe = info.get('returnOnEquity')
        if roe and roe > 0.15: score += 2; details['ROE > 15%'] = f"✅ {roe:.2%}"
        
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity is not None and debt_to_equity < 50: score += 2; details['負債權益比 < 50'] = f"✅ {debt_to_equity:.2f}"
        
        revenue_growth = info.get('revenueGrowth')
        if revenue_growth and revenue_growth > 0.1: score += 1; details['營收年增 > 10%'] = f"✅ {revenue_growth:.2%}"

        pe = info.get('trailingPE')
        if pe and 0 < pe < 15: score += 1; details['P/E < 15'] = f"✅ {pe:.2f}"
        
        peg = info.get('pegRatio')
        if peg and 0 < peg < 1: score += 1; details['PEG < 1'] = f"✅ {peg:.2f}"
        
        summary = "頂級優異" if score >= 5 else "良好穩健" if score >= 3 else "中性警示"
        return {"score": score, "summary": summary, "details": details}
    except Exception:
        return {"score": 0, "summary": "無法獲取", "details": {}}

def generate_ai_fusion_signal(df, fa_rating, chips_news_data):
    df_clean = df.dropna(subset=['EMA_10', 'EMA_50', 'EMA_200', 'RSI', 'MACD_Hist', 'ADX', 'OBV', 'OBV_MA_20'])
    if df_clean.empty or len(df_clean) < 2: return {'action': '數據不足', 'score': 0, 'confidence': 0, 'ai_opinions': {}}
    
    last, prev = df_clean.iloc[-1], df_clean.iloc[-2]
    opinions = {}
    ta_score = 0
    if last['EMA_10'] > last['EMA_50'] > last['EMA_200']: ta_score += 2; opinions['趨勢分析 (MA)'] = '✅ 強多頭排列'
    elif last['EMA_10'] < last['EMA_50'] < last['EMA_200']: ta_score -= 2; opinions['趨勢分析 (MA)'] = '❌ 強空頭排列'
    
    if last['RSI'] > 70: ta_score -= 1.5; opinions['動能分析 (RSI)'] = '❌ 超買'
    elif last['RSI'] < 30: ta_score += 1.5; opinions['動能分析 (RSI)'] = '✅ 超賣'
    
    if last['MACD_Hist'] > 0 and last['MACD_Hist'] > prev['MACD_Hist']: ta_score += 1.5; opinions['動能分析 (MACD)'] = '✅ 多頭動能增強'
    elif last['MACD_Hist'] < 0 and last['MACD_Hist'] < prev['MACD_Hist']: ta_score -= 1.5; opinions['動能分析 (MACD)'] = '❌ 空頭動能增強'
        
    if last['ADX'] > 25: ta_score *= 1.2; opinions['趨勢強度 (ADX)'] = f'✅ 強趨勢'
    else: ta_score *= 0.8; opinions['趨勢強度 (ADX)'] = f'⚠️ 盤整'

    fa_score = ((fa_rating.get('score', 0) / 7.0) - 0.5) * 8.0
    chips_score = (chips_news_data.get('inst_hold_pct', 0) - 0.4) * 4
    volume_score = 1 if last['OBV'] > last['OBV_MA_20'] else -1
    opinions['成交量 (OBV)'] = '✅ OBV 在均線之上' if volume_score > 0 else '❌ OBV 在均線之下'
    
    total_score = ta_score * 0.5 + fa_score * 0.25 + (chips_score + volume_score) * 0.25
    confidence = min(100, 50 + abs(total_score) * 8)
    
    action = '中性/觀望'
    if total_score > 4: action = '買進 (Buy)'
    elif total_score > 1.5: action = '中性偏買 (Hold/Buy)'
    elif total_score < -4: action = '賣出 (Sell/Short)'
    elif total_score < -1.5: action = '中性偏賣 (Hold/Sell)'
    
    return {'action': action, 'score': total_score, 'confidence': confidence, 'ai_opinions': opinions}

# ==============================================================================
# 5. 回測與圖表繪製
# ==============================================================================
def run_backtest(df, initial_capital=100000):
    try:
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        if df['SMA_20'].isna().all() or df['EMA_50'].isna().all(): return {"total_trades": 0, "message": "數據不足無法回測"}

        df['position'] = np.where(df['SMA_20'] > df['EMA_50'], 1, -1)
        df['returns'] = df['Close'].pct_change()
        df['strategy_returns'] = df['returns'] * df['position'].shift(1)
        
        cumulative_returns = (1 + df['strategy_returns'].fillna(0)).cumprod()
        total_return = (cumulative_returns.iloc[-1] - 1) * 100
        
        trades = df['position'].diff().ne(0)
        total_trades = trades.sum()
        if total_trades < 2: return {"total_trades": 0, "message": "無足夠交易信號"}
            
        trade_returns = df['strategy_returns'][trades]
        win_rate = (trade_returns > 0).sum() / total_trades * 100
        
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        return {
            "total_return": f"{total_return:.2f}", "win_rate": f"{win_rate:.2f}",
            "max_drawdown": f"{max_drawdown:.2f}", "total_trades": total_trades,
            "capital_curve": initial_capital * cumulative_returns, "message": "相對初始資金"
        }
    except Exception as e:
        return {"total_trades": 0, "message": f"回測錯誤: {e}"}

def create_comprehensive_chart(df, symbol, period_key):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_10'], mode='lines', name='EMA 10', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], mode='lines', name='EMA 200', line=dict(color='red', width=2)), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=np.where(df['MACD_Hist'] > 0, 'green', 'red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.2, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.2, row=3, col=1)
    fig.update_layout(title=f'{symbol} 技術分析圖 ({period_key})', xaxis_rangeslider_visible=False, height=700)
    return fig

# ==============================================================================
# 6. UI 呈現與主邏輯
# ==============================================================================
def main():
    if 'run_analysis' not in st.session_state: st.session_state['run_analysis'] = False

    st.sidebar.title("🚀 AI 趨勢分析")
    st.sidebar.markdown("---")
    
    selected_category = st.sidebar.selectbox('1. 選擇資產類別', list(CATEGORY_HOT_OPTIONS.keys()), index=2, key='category_selector')
    hot_options_map = CATEGORY_HOT_OPTIONS.get(selected_category, {})
    default_index = list(hot_options_map.keys()).index('SOL-USD - Solana') if 'SOL-USD - Solana' in hot_options_map else 0
    
    st.sidebar.selectbox('2. 選擇熱門標的', list(hot_options_map.keys()), index=default_index, key='hot_target_selector', on_change=sync_text_input_from_selection)
    st.sidebar.text_input('...或手動輸入代碼/名稱:', st.session_state.get('sidebar_search_input', 'SOL-USD'), key='sidebar_search_input')
    
    st.sidebar.markdown("---")
    selected_period_key = st.sidebar.selectbox('3. 選擇分析週期', list(PERIOD_MAP.keys()), index=2)
    st.sidebar.markdown("---")
    
    if st.sidebar.button('📊 執行AI分析', use_container_width=True):
        st.session_state['run_analysis'] = True
        st.session_state['symbol_to_analyze'] = get_symbol_from_query(st.session_state.sidebar_search_input)
        st.session_state['period_key'] = selected_period_key

    if st.session_state.get('run_analysis', False):
        final_symbol = st.session_state['symbol_to_analyze']
        period_key = st.session_state['period_key']
        period, interval = PERIOD_MAP[period_key]

        with st.spinner(f"🔍 正在啟動AI模型，分析 **{final_symbol}**..."):
            df_raw = get_stock_data(final_symbol, period, interval)
            
            if df_raw.empty or len(df_raw) < 52:
                st.error(f"❌ **數據不足或代碼無效：** {final_symbol}。AI模型至少需要52個數據點才能進行精準分析。")
            else:
                info = get_company_info(final_symbol)
                fa_rating = calculate_advanced_fundamental_rating(final_symbol)
                chips_data = get_chips_and_news_analysis(final_symbol)
                
                df_tech = calculate_technical_indicators(df_raw.copy())
                analysis = generate_ai_fusion_signal(df_tech, fa_rating, chips_data)
                
                price = df_raw['Close'].iloc[-1]
                consensus_sl, consensus_tp, all_strategy_results = get_consensus_levels(df_tech, price)

                st.header(f"📈 {info['name']} ({final_symbol}) AI趨勢分析報告")

                if info.get('category') in ["加密貨幣 (Crypto)", "指數"]:
                    st.markdown(f"**分析週期:** {period_key} | **標的類型:** {info.get('category')} (不適用基本面分析)")
                else:
                    st.markdown(f"**分析週期:** {period_key} | **FA評級:** **{fa_rating.get('score',0):.1f}/7.0** ({fa_rating.get('summary','N/A')})")
                st.markdown("---")
                
                st.subheader("💡 核心行動與量化評分")
                prev_close = df_raw['Close'].iloc[-2]
                change, pct = price - prev_close, (price - prev_close) / prev_close * 100
                currency_symbol = get_currency_symbol(final_symbol)
                pf = ".4f" if price < 100 and currency_symbol != 'NT$' else ".2f"
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💰 當前價格", f"{currency_symbol}{price:{pf}}", f"{change:{pf}} ({pct:+.2f}%)")
                c2.metric("🎯 AI 行動建議", analysis['action'])
                c3.metric("🔥 AI 總量化評分", f"{analysis['score']:.2f}")
                c4.metric("🛡️ AI 信心指數", f"{analysis['confidence']:.0f}%")
                
                st.markdown("---")
                st.subheader("🛡️ AI 綜合策略與風險控制")
                s1, s2, s3 = st.columns(3)
                s1.metric("建議進場價 (參考):", f"{currency_symbol}{price:{pf}}")
                s2.metric("🚀 共識止盈價 (TP):", f"{currency_symbol}{consensus_tp:{pf}}" if pd.notna(consensus_tp) else "N/A")
                s3.metric("🛑 共識止損價 (SL):", f"{currency_symbol}{consensus_sl:{pf}}" if pd.notna(consensus_sl) else "N/A")

                with st.expander("詳細查看各策略的計算結果"):
                    results_df = pd.DataFrame.from_dict(all_strategy_results, orient='index').reset_index()
                    results_df.columns = ['策略名稱', '止損價 (SL)', '止盈價 (TP)']
                    st.dataframe(results_df.style.format({'止損價 (SL)': '{:.4f}', '止盈價 (TP)': '{:.4f}'}), use_container_width=True)

                st.markdown("---")
                st.subheader("📊 AI判讀細節")
                opinions = list(analysis['ai_opinions'].items())
                if fa_rating['details']:
                    for k, v in fa_rating['details'].items(): opinions.append([f"基本面 - {k}", str(v)])
                st.dataframe(pd.DataFrame(opinions, columns=['分析維度', '判斷結果']), use_container_width=True)
                
                st.markdown("---")
                st.subheader("🧪 策略回測報告 (SMA 20/EMA 50 交叉)")
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
                
                st.markdown("---")
                st.subheader(f"📊 完整技術分析圖表")
                st.plotly_chart(create_comprehensive_chart(df_tech, final_symbol, period_key), use_container_width=True)
                with st.expander("📰 點此查看近期相關新聞"): st.markdown(chips_data['news_summary'].replace("\n", "\n\n"))

    else:
        st.markdown("<h1 style='color: #FA8072;'>🚀 歡迎使用 AI 趨勢分析</h1>", unsafe_allow_html=True)
        st.markdown(f"請在左側選擇或輸入您想分析的標的（例如：**2330.TW**、**NVDA**、**BTC-USD**），然後點擊 <span style='color: #FA8072; font-weight: bold;'>『📊 執行AI分析』</span> 按鈕開始。", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📝 使用步驟：")
        st.markdown("1. **選擇資產類別**：在左側欄選擇 `美股`、`台股` 或 `加密貨幣`。")
        st.markdown("2. **選擇標的**：使用下拉選單快速選擇熱門標的，或直接在輸入框中鍵入代碼或名稱。")
        st.markdown("3. **選擇週期**：決定分析的長度（例如：`30 分` (短期)、`1 日` (中長線)）。")
        st.markdown(f"4. **執行分析**：點擊 <span style='color: #FA8072; font-weight: bold;'>『📊 執行AI分析』</span>，AI將融合多種策略，提供最精準的交易參考價位。", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    st.markdown("---")
    st.markdown("⚠️ **免責聲明**")
    st.caption("本分析模型包含AI的量化觀點，並結合多種技術分析策略，但僅供教育與參考用途。投資涉及風險，所有交易決策應基於您個人的獨立研究和財務狀況，並建議諮詢專業金融顧問。")
    st.markdown("📊 **數據來源:** Yahoo Finance")
