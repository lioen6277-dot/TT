<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票交易指標卡片分析</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* 使用 Inter 字體 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0d1117; /* Dark background */
        }
        /* 自定義光暈效果 CSS */
        .glow-effect-entry {
            box-shadow: 0 4px 6px -1px rgba(253, 164, 175, 0.4), 0 2px 4px -2px rgba(253, 164, 175, 0.4), 0 0 20px 0 rgba(253, 164, 175, 0.5); /* 鮭魚粉 */
        }
        .glow-effect-tp {
            box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.4), 0 2px 4px -2px rgba(239, 68, 68, 0.4), 0 0 20px 0 rgba(239, 68, 68, 0.5); /* 紅色 */
        }
        .glow-effect-sl {
            box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.4), 0 2px 4px -2px rgba(34, 197, 94, 0.4), 0 0 20px 0 rgba(34, 197, 94, 0.5); /* 綠色 */
        }
    </style>
</head>
<body class="p-4 md:p-8 text-white min-h-screen">

    <!-- 主標題與介紹 -->
    <header class="mb-10 text-center">
        <h1 class="text-4xl font-extrabold text-blue-400">股票交易分析儀表板</h1>
        <p class="text-gray-400 mt-2">基於 K 線形態、VSA 及 ATR/R 倍數的動態風險管理策略</p>
    </header>

    <div id="app-container" class="max-w-7xl mx-auto">
        <!-- 策略建議卡片區 (主要指標卡片) -->
        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6 border-b border-gray-700 pb-2 text-indigo-300">📈 策略建議 (R 倍數風險管理)</h2>
            <div id="strategy-cards" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- 卡片將由 JS 渲染 -->
            </div>
        </section>

        <!-- K 線和 VSA 分析區 (輔助分析) -->
        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6 border-b border-gray-700 pb-2 text-indigo-300">🔍 形態與價量分析</h2>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                <!-- K 線形態卡片 -->
                <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 class="text-xl font-semibold mb-4 text-pink-300 border-b border-gray-600 pb-2">K 線形態分析</h3>
                    <div id="kline-analysis" class="space-y-3 text-sm">
                        <!-- 數據將由 JS 渲染 -->
                    </div>
                </div>

                <!-- VSA 價量分析卡片 -->
                <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 class="text-xl font-semibold mb-4 text-pink-300 border-b border-gray-600 pb-2">VSA 價量分析</h3>
                    <div id="vsa-analysis" class="space-y-3 text-sm">
                        <!-- 數據將由 JS 渲染 -->
                    </div>
                </div>
            </div>
        </section>

        <!-- 數據片段區 (Raw Data) -->
        <section>
            <h2 class="text-3xl font-bold mb-6 border-b border-gray-700 pb-2 text-indigo-300">📊 數據片段 (最新5筆)</h2>
            <div id="data-snippet" class="bg-gray-800/50 p-4 rounded-xl overflow-x-auto border border-gray-700">
                <!-- 數據表格將由 JS 渲染 -->
            </div>
        </section>
        
    </div>

    <script>
        // 模擬您的 Python 腳本成功執行的 JSON 輸出
        // 由於我們無法直接運行 Python，這段 JSON 結構來自於您的 `stock_analysis.py` 腳本的最終輸出。
        const analysisData = {
            "AnalysisTitle": "股票交易指標卡片分析結果",
            "DataSnippet": [
                { "Date": "2025-03-16", "Close": 103.11, "Volume": 250000, "ATR": 0.8251 },
                { "Date": "2025-03-17", "Close": 104.55, "Volume": 310000, "ATR": 0.8305 },
                { "Date": "2025-03-18", "Close": 104.80, "Volume": 450000, "ATR": 0.8600 },
                { "Date": "2025-03-19", "Close": 105.15, "Volume": 150000, "ATR": 0.8577 },
                { "Date": "2025-03-20", "Close": 105.50, "Volume": 380000, "ATR": 0.8540 }
            ],
            "KLineAnalysis": [
                { "Date": "2025-03-17", "Close": 104.55, "Pattern": "多頭吞噬 (Bullish Engulfing)" },
                { "Date": "2025-03-18", "Close": 104.80, "Pattern": "未檢測到" }
            ],
            "VSAAnalysis": [
                { "Date": "2025-03-19", "Close": 105.15, "Volume": 150000, "VSA_Signal": "潛在供應測試 (Testing Supply)" }
            ],
            "StrategyRecommendations": {
                "LongEntry": {
                    "EntryDate": "2025-03-20",
                    "Details": {
                        "Status": "成功",
                        "入場類型": "Long",
                        "入場價格": 105.50,
                        "當前ATR (14期)": 0.8540,
                        "R單位實際值": 1.2810,
                        "止損價格 (SL)": 104.22,
                        "目標 R 倍數": "4.0R",
                        "目標價格 (TP)": 110.63,
                        "風險回報比 (R:R)": "1:4.0"
                    }
                },
                "ShortEntry": {
                    "EntryDate": "2025-03-19",
                    "Details": {
                        "Status": "成功",
                        "入場類型": "Short",
                        "入場價格": 104.80,
                        "當前ATR (14期)": 0.8600,
                        "R單位實際值": 1.7200,
                        "止損價格 (SL)": 106.52,
                        "目標 R 倍數": "2.5R",
                        "目標價格 (TP)": 100.55,
                        "風險回報比 (R:R)": "1:2.5"
                    }
                }
            }
        };

        // 價格點的顏色和光暈配置
        const priceConfig = {
            '入場價格': { label: '進場價 (Entry)', color: 'text-pink-400', glow: 'glow-effect-entry', bgColor: 'bg-pink-500/10', borderColor: 'border-pink-500' },
            '目標價格 (TP)': { label: '止盈價 (Take Profit)', color: 'text-red-400', glow: 'glow-effect-tp', bgColor: 'bg-red-500/10', borderColor: 'border-red-500' },
            '止損價格 (SL)': { label: '止損價 (Stop Loss)', color: 'text-green-400', glow: 'glow-effect-sl', bgColor: 'bg-green-500/10', borderColor: 'border-green-500' },
        };

        /**
         * 渲染策略卡片 (Entry, TP, SL)
         * @param {string} entryKey - 'LongEntry' or 'ShortEntry'
         */
        function renderStrategyCard(entryKey) {
            const data = analysisData.StrategyRecommendations[entryKey];
            if (!data || data.Details.Status !== '成功') return '';

            const details = data.Details;
            const entryType = details['入場類型'];
            const title = entryType === 'Long' ? '多頭入場策略 (Long)' : '空頭入場策略 (Short)';
            const headerColor = entryType === 'Long' ? 'text-emerald-400' : 'text-orange-400';
            const icon = entryType === 'Long' ? '🚀' : '🔻';

            // 提取並格式化關鍵價格點
            const keyPrices = [
                { key: '入場價格', value: details['入場價格'] },
                { key: '目標價格 (TP)', value: details['目標價格 (TP)'] },
                { key: '止損價格 (SL)', value: details['止損價格 (SL)'] },
            ];

            // 渲染三個價格指標卡片
            const priceCardsHTML = keyPrices.map(item => {
                const config = priceConfig[item.key];
                const isEntry = item.key === '入場價格';
                
                return `
                    <div class="p-4 rounded-xl border-2 ${config.borderColor} ${config.bgColor} ${isEntry ? 'glow-effect-entry' : (item.key.includes('TP') ? 'glow-effect-tp' : 'glow-effect-sl')} transition-all duration-300 hover:scale-[1.02] transform">
                        <p class="text-sm text-gray-400">${config.label}</p>
                        <p class="text-3xl font-bold mt-1 ${config.color}">
                            $${item.value.toFixed(2)}
                        </p>
                    </div>
                `;
            }).join('');

            return `
                <div class="bg-gray-800/70 p-6 rounded-2xl border border-gray-700 shadow-xl space-y-4">
                    <h3 class="text-2xl font-bold ${headerColor} flex items-center gap-2">
                        ${icon} ${title}
                        <span class="text-sm text-gray-500 ml-auto">@ ${data.EntryDate}</span>
                    </h3>
                    
                    <!-- 關鍵價格指標卡片區 -->
                    <div class="grid grid-cols-3 gap-4">
                        ${priceCardsHTML}
                    </div>

                    <!-- 風險回報詳情 -->
                    <div class="pt-4 border-t border-gray-700">
                        <div class="flex justify-between items-center text-md">
                            <span class="text-gray-400">ATR (14 期):</span>
                            <span class="font-medium text-blue-300">${details['當前ATR (14期)'].toFixed(4)}</span>
                        </div>
                        <div class="flex justify-between items-center text-md">
                            <span class="text-gray-400">風險單位 R:</span>
                            <span class="font-medium text-yellow-300">$${details['R單位實際值'].toFixed(4)}</span>
                        </div>
                        <div class="flex justify-between items-center text-lg mt-2 font-semibold">
                            <span class="text-gray-300">目標 / 風險比 (R:R):</span>
                            <span class="text-pink-400">${details['目標 R 倍數']} (${details['風險回報比 (R:R)']})</span>
                        </div>
                    </div>
                </div>
            `;
        }

        /**
         * 渲染K線和VSA分析結果
         * @param {string} containerId - DOM ID
         * @param {Array<Object>} data - KLineAnalysis or VSAAnalysis array
         */
        function renderAnalysisResults(containerId, data) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (data.length === 1 && data[0].Message) {
                container.innerHTML = `<p class="text-gray-500 text-center py-4">${data[0].Message}</p>`;
                return;
            }

            container.innerHTML = data.map(item => {
                const signal = item.Pattern || item.VSA_Signal;
                const date = item.Date;
                const close = item.Close.toFixed(2);
                
                let signalColor = 'text-gray-300';
                if (signal.includes('多頭') || signal.includes('需求')) signalColor = 'text-green-400';
                if (signal.includes('空頭') || signal.includes('供應')) signalColor = 'text-red-400';

                return `
                    <div class="flex justify-between p-3 bg-gray-700/50 rounded-lg transition-colors hover:bg-gray-700">
                        <span class="text-sm text-gray-400">${date} @ $${close}</span>
                        <span class="font-medium ${signalColor}">${signal}</span>
                    </div>
                `;
            }).join('');
        }

        /**
         * 渲染數據片段表格
         */
        function renderDataSnippet() {
            const data = analysisData.DataSnippet;
            const container = document.getElementById('data-snippet');
            if (!container || !data.length) return;

            const tableHeader = `
                <table class="min-w-full text-left text-sm text-gray-300">
                    <thead class="text-xs uppercase bg-gray-700/80">
                        <tr>
                            <th scope="col" class="py-3 px-4 rounded-tl-lg">日期</th>
                            <th scope="col" class="py-3 px-4 text-right">收盤價</th>
                            <th scope="col" class="py-3 px-4 text-right">成交量</th>
                            <th scope="col" class="py-3 px-4 rounded-tr-lg text-right">ATR (14)</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            const tableRows = data.map(row => `
                <tr class="border-b border-gray-700 hover:bg-gray-700/30 transition-colors">
                    <td class="py-3 px-4 font-medium">${row.Date}</td>
                    <td class="py-3 px-4 text-right">$${row.Close.toFixed(2)}</td>
                    <td class="py-3 px-4 text-right">${row.Volume.toLocaleString()}</td>
                    <td class="py-3 px-4 text-right text-yellow-400">${row.ATR.toFixed(4)}</td>
                </tr>
            `).join('');

            const tableFooter = `
                    </tbody>
                </table>
            `;

            container.innerHTML = tableHeader + tableRows + tableFooter;
        }

        // 啟動渲染
        document.addEventListener('DOMContentLoaded', () => {
            const strategyContainer = document.getElementById('strategy-cards');
            if (strategyContainer) {
                strategyContainer.innerHTML = 
                    renderStrategyCard('LongEntry') +
                    renderStrategyCard('ShortEntry');
            }

            renderAnalysisResults('kline-analysis', analysisData.KLineAnalysis);
            renderAnalysisResults('vsa-analysis', analysisData.VSAAnalysis);
            renderDataSnippet();
        });
    </script>
</body>
</html>
