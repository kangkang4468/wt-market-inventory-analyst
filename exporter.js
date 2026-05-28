/**
 * Gaijin Marketplace Inventory Exporter (Gaijin 市场仓库载具数据导出脚本)
 * 
 * 使用方法：
 * 1. 在 Chrome 中打开 https://trade.gaijin.net/inventory 并登录您的账户。
 * 2. 按 F12 打开开发者工具，切换到 "Console" (控制台) 选项卡。
 * 3. 将此脚本复制并粘贴到控制台中，然后按 Enter 键运行。
 * 4. 脚本会扫描所有仓库分页，并在抓取各详情页数据后自动下载 JSON 数据文件。
 */

(async () => {
    // ---------------- 配置参数 ----------------
    const CONCURRENCY = 3;     // 并发抓取数（建议保持在 3-5，防止被 Gaijin 暂时风控）
    const DELAY_MS = 500;      // 抓取完每个物品后的基础防风控延迟（毫秒）
    // ------------------------------------------

    const LOG_STYLE_HEADER = 'color: #e0a96d; font-weight: bold; background: #1a1a1e; padding: 6px 12px; border-radius: 4px; border: 1px solid #e0a96d; font-size: 13px;';
    const LOG_STYLE_INFO = 'color: #a8aab2;';
    const LOG_STYLE_SUCCESS = 'color: #7ee787; font-weight: bold;';
    const LOG_STYLE_WARN = 'color: #ff7b72; font-weight: bold;';
    const LOG_STYLE_EMPHASIS = 'color: #e0a96d; font-weight: bold;';

    console.log("%c[Gaijin Market Analyst] 仓库载具数据导出脚本启动", LOG_STYLE_HEADER);
    console.log("%c正在自动扫描仓库列表，请保持该页面为当前活动标签页，不要关闭...", LOG_STYLE_INFO);

    // 辅助睡眠函数
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    // 自动平滑滚动以触发图片和 DOM 懒加载
    async function triggerLazyLoad() {
        const distance = 200; // 每次滑动的距离(px)
        const delay = 40;     // 每次滑动的间隔(ms)
        while (window.scrollY + window.innerHeight < document.documentElement.scrollHeight) {
            window.scrollBy(0, distance);
            await sleep(delay);
        }
        // 平滑滚回顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
        await sleep(600); // 等待滚动回弹和渲染
    }

    // 动态获取真正的 trade_server 地址
    function getTradeServer() {
        try {
            if (window.SettingsInjections && typeof window.SettingsInjections.getUsedCircuit === 'function') {
                const circuit = window.SettingsInjections.getUsedCircuit();
                if (circuit && circuit.trade_server) {
                    return circuit.trade_server;
                }
            }
        } catch (e) {
            console.log("%c[警告] 无法通过 SettingsInjections 动态获取 trade_server, 将使用默认值", LOG_STYLE_WARN);
        }
        return "https://market-proxy.gaijin.net/web";
    }

    // 递归获取元素中所有叶子文本节点（跳过 button、script、style 等）并清洗零宽字符
    function getLeafTexts(el) {
        const texts = [];

        function traverse(node) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                if (tagName === 'button' || tagName === 'script' || tagName === 'style') {
                    return;
                }
            }

            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                // 去除所有的零宽字符和前后空白
                const cleanText = text.replace(/[\u200b\u200c\u200d\ufeff]/g, '').trim();
                if (cleanText) {
                    texts.push(cleanText);
                }
            } else {
                for (let child of node.childNodes) {
                    traverse(child);
                }
            }
        }

        traverse(el);
        return texts;
    }

    // 寻找下一页按钮
    function findNextPageButton() {
        const nextSelectors = [
            'button.next', 'a.next',
            '.pagination-next', '.pagination .next',
            '[class*="pagination"] [class*="next"]',
            '.pager-next', 'a[rel="next"]'
        ];
        for (const selector of nextSelectors) {
            const btn = document.querySelector(selector);
            if (btn && !btn.classList.contains('disabled') && btn.getAttribute('aria-disabled') !== 'true') {
                return btn;
            }
        }

        // 基于文本内容的兜底查找
        const allButtons = document.querySelectorAll('button, a, span');
        for (const el of allButtons) {
            const text = el.innerText.trim();
            if ((text === '>' || text.toLowerCase().includes('next') || text.includes('下一页')) &&
                el.offsetWidth > 0 && el.offsetHeight > 0) {
                if (!el.classList.contains('disabled') && !el.hasAttribute('disabled')) {
                    return el;
                }
            }
        }
        return null;
    }

    // 抓取当前页面卡片数据的函数
    function scrapeCurrentPage(itemsMap) {
        // 选择器兼容现代 CSS Module 结构
        const itemCards = document.querySelectorAll('a.lot.inventory, a[href*="/market/"], .lot.inventory');
        let pageItemsCount = 0;

        itemCards.forEach(el => {
            let href = el.getAttribute('href');
            if (!href && el.tagName !== 'A') {
                const anchor = el.querySelector('a');
                if (anchor) href = anchor.getAttribute('href');
            }

            if (!href || !href.includes('/market/')) return;

            // 清洗详情页 URL（移除 ?assetId=... 等参数）
            const cleanPath = href.split('?')[0];
            const fullUrl = new URL(cleanPath, window.location.origin).toString();

            // 深度优先提取所有叶子文本节点，避免行内元素拼接导致文本黏连
            const texts = getLeafTexts(el);

            // 过滤掉 "War Thunder" 等无关高频分类词
            const cleanParts = texts.filter(t => t !== "War Thunder");
            if (cleanParts.length === 0) return;

            let quantity = 1;
            let itemName = "";
            let sellOrders = 0;
            let sellPrice = null;

            // 1. 解析数量（如果第一项是纯数字且总数组长度大于等于3）
            let nameStartIndex = 0;
            if (cleanParts.length >= 3 && /^\d+$/.test(cleanParts[0])) {
                quantity = parseInt(cleanParts[0], 10);
                nameStartIndex = 1;
            }

            // 2. 解析物品名称
            itemName = cleanParts[nameStartIndex];
            if (!itemName) return;

            // 3. 最低售价（最后一项，通常是带小数的价格数字，如 1230.00）
            if (cleanParts.length > nameStartIndex + 1) {
                const lastPart = cleanParts[cleanParts.length - 1];
                const priceVal = parseFloat(lastPart.replace(/[^\d.]/g, ''));
                if (!isNaN(priceVal)) {
                    sellPrice = priceVal;
                }
            }

            // 4. 在售订单数（DOM 卡片无此数据，初始化为 0，由后续 API 接口权威覆盖写入）
            sellOrders = 0;

            // 5. 提取图片链接
            const imgEl = el.querySelector('img');
            const imageUrl = imgEl ? imgEl.src : '';

            // 更新或追加到 Map
            if (itemsMap.has(itemName)) {
                const existing = itemsMap.get(itemName);
                existing.quantity += quantity;
                if (sellPrice !== null) existing.sellPrice = sellPrice;
                if (sellOrders > 0) existing.sellOrders = sellOrders;
            } else {
                itemsMap.set(itemName, {
                    name: itemName,
                    url: fullUrl,
                    imageUrl: imageUrl,
                    quantity: quantity,
                    sellPrice: sellPrice,
                    sellOrders: sellOrders
                });
            }
            pageItemsCount++;
        });

        return pageItemsCount;
    }

    // 1. 开始多页扫描
    const itemsMap = new Map();
    let pageNum = 1;

    while (true) {
        console.log(`%c正在扫描第 ${pageNum} 页的载具卡片...`, LOG_STYLE_INFO);
        // 先触发平滑滚动加载，防止图片懒加载导致抓取到的图片 URL 为空
        await triggerLazyLoad();
        const count = scrapeCurrentPage(itemsMap);
        console.log(`%c第 ${pageNum} 页扫描完毕，提取到 ${count} 个合规物品。当前累计独特物品数: ${itemsMap.size}`, LOG_STYLE_INFO);

        const nextBtn = findNextPageButton();
        if (!nextBtn) {
            console.log("%c未发现可点击的下一页按钮，结束列表扫描。", LOG_STYLE_SUCCESS);
            break;
        }

        // 获取当前页第一个物品的文本，用于比对翻页后是否成功刷新
        const firstCard = document.querySelector('a.lot.inventory, a[href*="/market/"]');
        const firstCardTextBefore = firstCard ? firstCard.innerText : '';

        console.log("%c检测到下一页，正在模拟点击翻页...", LOG_STYLE_INFO);
        nextBtn.click();

        // 轮询等待新页面加载
        let loaded = false;
        for (let attempt = 0; attempt < 25; attempt++) {
            await sleep(200);
            const currentFirstCard = document.querySelector('a.lot.inventory, a[href*="/market/"]');
            const firstCardTextAfter = currentFirstCard ? currentFirstCard.innerText : '';
            if (firstCardTextAfter && firstCardTextAfter !== firstCardTextBefore) {
                loaded = true;
                break;
            }
        }

        if (!loaded) {
            await sleep(1000); // 兜底再等 1s
            const currentFirstCard = document.querySelector('a.lot.inventory, a[href*="/market/"]');
            const firstCardTextAfter = currentFirstCard ? currentFirstCard.innerText : '';
            if (firstCardTextAfter === firstCardTextBefore) {
                console.log("%c点击翻页后页面未见刷新或加载超时，停止翻页扫描。", LOG_STYLE_WARN);
                break;
            }
        }

        pageNum++;
        await sleep(500); // 翻页缓冲
    }

    const itemsList = Array.from(itemsMap.values());

    if (itemsList.length === 0) {
        console.log("%c[错误] 未能在仓库中找到任何有效的交易卡片。请确认您已登录且位于 https://trade.gaijin.net/inventory 页面。", LOG_STYLE_WARN);
        return;
    }

    console.log(`%c[成功] 扫描完成！共识别到 ${itemsList.length} 种独特物品/载具。`, LOG_STYLE_SUCCESS);
    console.log("%c开始抓取各物品的买盘深度及历史均价曲线，每次抓取随机延迟 1.5s - 2.0s 防止触发风控...", LOG_STYLE_INFO);

    // 2. 获取 auth token，并依次拉取详情数据，补充买一价、求购单数和走势数据
    let token = null;
    let rawTokenPair = null;
    try {
        const tokenPairStr = window.localStorage.getItem('MarketApp,auth,tokenPair');
        if (tokenPairStr) {
            rawTokenPair = JSON.parse(tokenPairStr);
            token = rawTokenPair.token || rawTokenPair.gseaToken;
        }
    } catch (e) {
        console.log("%c[警告] 无法从 localStorage 中解析 tokenPair", LOG_STYLE_WARN);
    }
    if (token) {
        console.log(`%c[成功] 成功提取到登录 Token (前10位: ${token.substring(0, 10)}..., 长度: ${token.length})`, LOG_STYLE_SUCCESS);
        if (!rawTokenPair.token && rawTokenPair.gseaToken) {
            console.log("%c[提示] 当前仅成功提取到 gseaToken，如后续数据抓取仍失败，请在控制台输入 localStorage.getItem('MarketApp,auth,tokenPair') 自查本地存储结构。", LOG_STYLE_WARN);
        }
    } else {
        console.log("%c[错误] 未找到任何登录 Token！请先登录 Gaijin 市场并刷新页面后再试。\n自查方法：按 F12 打开开发者工具，在 Console 中执行 localStorage.getItem('MarketApp,auth,tokenPair') 检查输出并反馈给开发人员。", LOG_STYLE_WARN);
    }

    const inventoryData = [];
    let completed = 0;
    const totalCount = itemsList.length;

    // 估算并报告需要抓取的总时长
    const estSec = ((itemsList.length * (DELAY_MS + 350)) / CONCURRENCY / 1000).toFixed(0);
    const estMin = (estSec / 60).toFixed(1);
    console.log(`%c[优化版] 启动并发管道机制，并发数: ${CONCURRENCY}，基础延迟: ${DELAY_MS}ms。\n预估总计需要约 ${estSec} 秒 (${estMin} 分钟)，请保持此页面打开状态...`, LOG_STYLE_INFO);

    // 自研精炼极速通道并发池
    async function worker(queue) {
        while (queue.length > 0) {
            const item = queue.shift();
            if (!item) continue;

            try {
                // 解析出 appid 和 market_name
                const urlObj = new URL(item.url);
                const pathParts = urlObj.pathname.split('/').filter(Boolean); // ["market", "1067", "id50257_object_292_ussr"]
                const appid = pathParts[1] || "1067";
                const market_name = decodeURIComponent(pathParts[pathParts.length - 1]);

                let buyPrice = null;
                let buyOrders = 0;
                let priceHistory = [];

                // 1. 调用 cln_books_brief 获取求购报价参数
                const paramsBrief = new URLSearchParams();
                paramsBrief.append("appid", appid);
                paramsBrief.append("market_name", market_name);
                if (token) {
                    paramsBrief.append("token", token);
                }
                paramsBrief.append("action", "cln_books_brief");

                // 2. 调用 cln_get_pair_stat 获取历史价格走势参数
                const paramsStat = new URLSearchParams();
                paramsStat.append("appid", appid);
                paramsStat.append("market_name", market_name);
                paramsStat.append("currencyid", "gjn");
                if (token) {
                    paramsStat.append("token", token);
                }
                paramsStat.append("action", "cln_get_pair_stat");

                // 核心提升：两个独立网络请求并行发送 (Promise.all)
                const fetchBrief = fetch(getTradeServer(), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: paramsBrief.toString()
                }).then(r => r.ok ? r.json() : null).catch(() => null);

                const fetchStat = fetch(getTradeServer(), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: paramsStat.toString()
                }).then(r => r.ok ? r.json() : null).catch(() => null);

                const [dataBrief, dataStat] = await Promise.all([fetchBrief, fetchStat]);

                // 读取简报数据
                if (dataBrief && (dataBrief.success || dataBrief.result || dataBrief.response)) {
                    const result = dataBrief.result || dataBrief.response || dataBrief;

                    // 读取买盘（求购）数据
                    if (result.BUY && result.BUY.length > 0) {
                        // result.BUY[0] 格式为 [price, count, date_stamp]，价格需除以 10000 换算为 GJN 浮点数
                        buyPrice = parseFloat(result.BUY[0][0]) / 10000;
                    } else if (result.ordersBuy && result.ordersBuy.length > 0) {
                        // 兼容旧接口命名
                        buyPrice = parseFloat(result.ordersBuy[0].price);
                    }

                    if (result.depth && result.depth.BUY !== undefined) {
                        buyOrders = parseInt(result.depth.BUY, 10);
                    } else if (result.totalBuyDepth !== undefined) {
                        buyOrders = parseInt(result.totalBuyDepth, 10);
                    } else if (result.BUY) {
                        buyOrders = result.BUY.length;
                    } else if (result.ordersBuy) {
                        buyOrders = result.ordersBuy.length;
                    }

                    // 权威覆盖在售卖盘数据
                    if (result.SELL && result.SELL.length > 0) {
                        const apiSellPrice = parseFloat(result.SELL[0][0]) / 10000;
                        item.sellPrice = apiSellPrice; // 无条件以 API 返回的最新挂单价为准
                    }
                    if (result.depth && result.depth.SELL !== undefined) {
                        item.sellOrders = parseInt(result.depth.SELL, 10); // 无条件以 API 返回的挂单数为准
                    } else if (result.SELL) {
                        item.sellOrders = result.SELL.length;
                    } else {
                        item.sellOrders = 0;
                    }
                    console.log(
                        `%c[抓取结果] 载具 "${item.name}" 解析结果: 求购价=${buyPrice}, 求购数量=${buyOrders}, 在售价=${item.sellPrice}, 在售数量=${item.sellOrders}`,
                        'color: #00bcd4;'
                    );
                } else {
                    console.log(`%c[警告] 获取 "${item.name}" 简报接口解析失败`, LOG_STYLE_WARN);
                }

                // 读取历史走势数据
                if (dataStat && (dataStat.success || dataStat.result || dataStat.response)) {
                    const result = dataStat.result || dataStat.response || dataStat;
                    const rawHistory = result["1d"] || [];
                    priceHistory = rawHistory.map(pt => {
                        // pt 结构: [timestamp_seconds, price, volume]
                        // 转换时需要将秒时间戳乘以 1000 转换为毫秒时间戳，并提取 [timestamp_ms, price]，且价格需除以 10000 换算为 GJN 浮点数
                        return [pt[0] * 1000, parseFloat(pt[1]) / 10000];
                    });
                } else {
                    console.log(`%c[警告] 获取 "${item.name}" 历史走势接口解析失败`, LOG_STYLE_WARN);
                }

                // 如果依然没有拿到求购价或走势图，打印调试信息
                if (buyPrice === null || priceHistory.length === 0) {
                    console.log(`%c[调试] "${item.name}" 抓取情况: 走势点数=${priceHistory.length}, 求购价=${buyPrice}`, LOG_STYLE_WARN);
                }

                inventoryData.push({
                    ...item,
                    buyPrice: buyPrice,
                    buyOrders: buyOrders,
                    history: priceHistory,
                    scrapedAt: new Date().toISOString()
                });

            } catch (err) {
                console.log(`%c[警告] "${item.name}" 数据抓取失败: ${err.message}`, LOG_STYLE_WARN);
                inventoryData.push({
                    ...item,
                    buyPrice: null,
                    buyOrders: 0,
                    history: [],
                    error: err.message,
                    scrapedAt: new Date().toISOString()
                });
            }

            completed++;
            const progress = ((completed / totalCount) * 100).toFixed(0);
            console.log(`%c[${completed}/${totalCount} - ${progress}%] %c${item.name} %c抓取补充完毕`, LOG_STYLE_INFO, LOG_STYLE_EMPHASIS, LOG_STYLE_SUCCESS);

            // 配合通道的防风控延迟
            const delay = DELAY_MS + Math.random() * 200;
            await sleep(delay);
        }
    }

    // 启动多 Worker 管道并发提取
    const queue = [...itemsList];
    const workers = [];
    for (let i = 0; i < CONCURRENCY; i++) {
        workers.push(worker(queue));
    }
    await Promise.all(workers);


    console.log("%c所有库存载具数据抓取完毕！正在下载数据文件...", LOG_STYLE_SUCCESS);

    // 3. 导出 JSON 并下载
    const blob = new Blob([JSON.stringify(inventoryData, null, 4)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const dateStr = new Date().toISOString().split('T')[0];
    const filename = `gaijin_inventory_${dateStr}.json`;

    const downloadAnchor = document.createElement('a');
    downloadAnchor.href = url;
    downloadAnchor.download = filename;
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    document.body.removeChild(downloadAnchor);
    URL.revokeObjectURL(url);

    console.log(`%c[完成] 仓库数据文件 "${filename}" 已成功下载并保存至本地浏览器默认下载文件夹。`, LOG_STYLE_SUCCESS);
    console.log("%c请将其复制到您的本地 Python 脚本工作区，并运行 'python analyze.py' 生成最新的图表报告！", LOG_STYLE_EMPHASIS);
})();
