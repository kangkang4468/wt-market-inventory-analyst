import os
import sys

TARGET_DIR = r"e:\个人源码\wt-market-analyst"

if not os.path.exists(TARGET_DIR):
    print(f"[错误] 目标目录不存在: {TARGET_DIR}")
    sys.exit(1)

# 1. 写入 analyze.py
ANALYZE_PY = '''import os
import json
import glob
from datetime import datetime, timedelta
import sys
import re

# 尝试在 Windows 下启用 UTF-8 输出，防止控制台中文乱码
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ==========================================
# 核心数据分析与智能分类算法 (纯 Python 标准库实现)
# ==========================================

def classify_item(name):
    """
    智能识别 Gaijin 市场物品类别: 载具 / 涂装 / 箱子 / 道具/挂饰 / 活动材料 / 其他
    """
    if not name:
        return '其他'
    n = name.strip()
    
    # 1. 箱子 / 战利品 (Crates / Trophies / Chests)
    if any(k in n for k in ['百宝箱', '物资箱', '战利品', '箱', 'Trophy', 'Chest', 'Crate', 'Container']):
        return '箱子'
        
    # 2. 涂装 / 迷彩 (Camouflages / Skins)
    if any(k in n for k in ['涂装', '迷彩', 'camo', 'Camo', 'Skin', 'skin', 'Squadron', 'Regiment', 'Régiment', 'Marine Corps', 'Battalion', 'Chutai', 'Sensha-gun', 'Red Devils', 'Red Arrows', 'HMS Bulldog', 'Cat Squadron', 'division', 'PLA', 'Indonesian']):
        return '涂装'
    if "'" in n or "‘" in n or "’" in n:
        return '涂装'
    if ':' in n and any(k in n for k in ['冬季', '夏季', '斑点', '双色', '三色', '沙漠', '林地', '历史', '非标准', '迷彩', '涂装']):
        return '涂装'
        
    # 3. 活动材料 / 零件 / 工具 (Crafting / Event Materials)
    if any(k in n for k in ['材料', '零件', '工具', 'Toolkit', 'Material', '蓝图', 'Blueprint', '方案', '升级套件', '订单', '合同', 'Contract', 'Order']):
        return '活动材料'
        
    # 4. 道具 / 挂饰 / 贴花 / 头像 / 钥匙 (Decorators / Decals / Avatars / Items)
    if any(k in n for k in [
        '钥匙', 'Key', '贴花', 'Decal', '徽标', '涂鸦', '头像', '资料头像', 'Avatar', 'Icon', '头衔', 'Title', '挂饰', 'Decorator',
        '机枪', '步枪', '骑枪', '防弹衣', '背心', '足球', '仙女棒', '风筝', '圣诞老人', '战士', '九头蛇', '斯芬克斯',
        '女巫', '哈比', '马头鱼尾兽', '仙女', '旗帜', 'Flag', '冻人飞霜', '即兴炫技', '圣火', '探索不止', '攀登新高峰',
        '树不会走路', '汉斯·踹普', '滑翔风筝', '灼痛吐息', '炙烈印记', '炽热火焰', '焰色华彩', '燎原火星', '爆燃烈焰', '雪地会说话'
    ]):
        return '道具/挂饰'
        
    # 5. 载具判定 (Vehicles)
    country_tags = [
        '（苏联）', '（德国）', '（美国）', '（英国）', '（中国）', '（法国）', '（日本）', '（意大利）', '（瑞典）', '（以色列）',
        '(USSR)', '(USA)', '(Germany)', '(Britain)', '(China)', '(France)', '(Japan)', '(Italy)', '(Sweden)', '(Israel)'
    ]
    if any(tag in n for tag in country_tags):
        return '载具'
    if any(k in n for k in [
        '坦克', '工程', '战斗机', '直升机', '巡洋舰', '驱逐舰', '战列舰', '舰', '型', '现代化', '豹', '虎', '狼',
        '百夫长', '丘吉尔', '拳师犬', '掠夺者', '美洲', '幼狮', '米格', 'F-', 'T-', 'Sd.Kfz.', 'M6', 'M4', 'IS-', 'PT-'
    ]):
        return '载具'
        
    return '其他'

def calculate_linear_regression(history):
    """
    计算价格历史数据的线性回归斜率和均价
    history: [[timestamp_ms, price_f, (volume)], ...]
    返回: (daily_slope, avg_price)
    """
    if not history or len(history) < 2:
        return 0.0, 0.0
    
    # 按照时间戳升序排序
    sorted_history = sorted(history, key=lambda x: x[0])
    
    # 将时间戳转换为相对于首个数据点的天数，避免时间戳过大导致溢出
    t0 = sorted_history[0][0]
    x = []
    y = []
    
    for pt in sorted_history:
        # 毫秒转换为天数
        t_days = (pt[0] - t0) / (1000.0 * 60 * 60 * 24)
        x.append(t_days)
        y.append(pt[1])
        
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi * xi for xi in x)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    
    denom = (n * sum_xx - sum_x * sum_x)
    if denom == 0:
        return 0.0, sum_y / n
        
    slope = (n * sum_xy - sum_x * sum_y) / denom
    avg_price = sum_y / n
    return slope, avg_price

def calculate_recent_ma(history, days=7):
    """
    计算最近几天 (自然天) 的成交移动平均线
    """
    if not history:
        return None
    sorted_history = sorted(history, key=lambda x: x[0], reverse=True)
    t_latest = sorted_history[0][0]
    
    # 过滤出最近 days 天的数据点
    cutoff = t_latest - (days * 24 * 60 * 60 * 1000)
    recent_pts = [pt[1] for pt in sorted_history if pt[0] >= cutoff]
    return sum(recent_pts) / len(recent_pts) if recent_pts else None

def calculate_fair_price(sell_price, buy_price, ma30, spread):
    """
    计算公允估值 (Fair Price)：
    如果挂单价过高（如虚高挂单/无买盘承接的大价差），进行保守公允估值折价，避免总资产虚高
    """
    if sell_price is None or sell_price <= 0:
        return 0.0
    
    if spread is None or spread <= 0.25:
        return sell_price
    
    # 当价差 > 25% 时，存在一定流动性折价或挂单泡沫
    if buy_price and buy_price > 0:
        if ma30 and ma30 > 0:
            anchor = max(buy_price, ma30 * 1.05)
            fair = min(sell_price, anchor)
        else:
            fair = min(sell_price, buy_price * 1.20)
    else:
        if ma30 and ma30 > 0:
            fair = min(sell_price, ma30 * 1.10)
        else:
            fair = sell_price * 0.80
            
    return round(fair, 2)

def detect_last_crash(history):
    """
    分析历史价格数据，寻找最近一次在 30 天内价格大跌超 30% 的事件
    history: [[timestamp_ms, price_f, ...], ...]
    返回: (crash_date, crash_drop_pct)
    """
    if not history or len(history) < 2:
        return "暂无大跌记录", 0.0
        
    # 按照时间戳升序排序
    sorted_history = sorted(history, key=lambda x: x[0])
    
    max_drops = [] # [(valley_time, drop_pct), ...]
    window_ms = 30 * 24 * 60 * 60 * 1000 # 30天
    
    for i in range(len(sorted_history)):
        t_i, p_i = sorted_history[i][0], sorted_history[i][1]
        if p_i <= 0:
            continue
            
        # 寻找 i 之后 30 天内的最低价格点
        min_p = p_i
        min_t = t_i
        for j in range(i + 1, len(sorted_history)):
            t_j, p_j = sorted_history[j][0], sorted_history[j][1]
            if t_j - t_i > window_ms:
                break
            if p_j < min_p:
                min_p = p_j
                min_t = t_j
                
        drop = (p_i - min_p) / p_i
        if drop >= 0.30: # 跌幅超 30%
            max_drops.append((min_t, drop))
            
    if not max_drops:
        return "未检测到大跌", 0.0
        
    # 找到最近的一个大跌低谷（时间戳最大）
    max_drops.sort(key=lambda x: x[0], reverse=True)
    latest_valley_time, latest_drop = max_drops[0]
    
    try:
        crash_date = datetime.fromtimestamp(latest_valley_time / 1000.0).strftime('%Y-%m-%d')
    except Exception:
        crash_date = "格式错误"
        
    return crash_date, latest_drop * 100.0

def predict_future_valleys(base_date, n=2):
    """
    基于 base_date (datetime对象) 预测未来 n 个官方大促低谷日期
    四大周期（中值）：胜利日(5-8)、夏活(8-20)、周年庆(11-1)、冬活(12-28)
    """
    year = base_date.year
    
    events = [
        ("春季胜利日大促", (5, 8)),
        ("夏季马拉松活动", (8, 20)),
        ("周年庆狂欢大促", (11, 1)),
        ("冬季圣诞特惠活动", (12, 28))
    ]
    
    future_events = []
    # 考虑今年和明年的活动
    for y in [year, year + 1]:
        for name, (m, d) in events:
            evt_date = datetime(y, m, d)
            if evt_date >= base_date:
                future_events.append((name, evt_date))
                
    # 按名称去重，保留日期最早的
    unique_events = {}
    for name, dt in future_events:
        if name not in unique_events or dt < unique_events[name]:
            unique_events[name] = dt
            
    sorted_events = sorted(unique_events.items(), key=lambda x: x[1])
    return sorted_events[:n]

def evaluate_item(item, current_date_str=None):
    """
    运行重构后的 5 因子量化评估模型 (含全市场公允估值、防天花板抑制与智能品类感知)，生成精准评分与大盘操作建议
    """
    if not current_date_str:
        current_date_str = datetime.now().strftime('%Y-%m-%d')
    current_date = datetime.strptime(current_date_str, '%Y-%m-%d')

    item_name = item.get('name', '')
    category = item.get('category') or classify_item(item_name)
    item['category'] = category

    sell_price = item.get('sellPrice')
    buy_price = item.get('buyPrice')
    sell_orders = item.get('sellOrders') or 0
    buy_orders = item.get('buyOrders') or 0
    raw_history = item.get('history') or []
    
    # 清洗历史数据：兼容 2 元组 [t, p] 与 3 元组 [t, p, volume]
    history = []
    for pt in raw_history:
        if len(pt) >= 2:
            t = pt[0]
            p = float(pt[1])
            # 兼容自适应逻辑：如果历史价格 pt[1] 大于 10000 (因为单个售卖上限是 2000 GJN)，则除以 10000
            if p > 10000.0:
                p = p / 10000.0
            
            if len(pt) >= 3:
                v = int(pt[2])
                history.append([t, p, v])
            else:
                history.append([t, p])
            
    item['history'] = history
    
    # 计算价差比率 (买卖贴合度)
    spread = None
    if sell_price and buy_price and sell_price > 0:
        spread = (sell_price - buy_price) / sell_price

    # 历史趋势基本分析
    slope, avg_price = calculate_linear_regression(history)
    ma7 = calculate_recent_ma(history, days=7) or (sell_price or 0.0)
    ma30 = calculate_recent_ma(history, days=30) or (sell_price or 0.0)
    
    # 归一化日均斜率收益率（去除绝对价格量纲影响）
    norm_daily_slope = (slope / avg_price) if avg_price > 0 else 0.0
    
    recent_trend_pct = 0.0
    if ma7 and avg_price > 0:
        recent_trend_pct = (ma7 - avg_price) / avg_price

    # 公允价值估算
    fair_price = calculate_fair_price(sell_price, buy_price, ma30, spread)
    is_near_ceiling = bool(sell_price and sell_price >= 1800.0)

    # 分析时间跨度与首次挂载
    first_listed_date = "暂无数据"
    first_listed_days = -1.0
    if history:
        sorted_history_asc = sorted(history, key=lambda x: x[0])
        first_timestamp_ms = sorted_history_asc[0][0]
        
        try:
            first_listed_date = datetime.fromtimestamp(first_timestamp_ms / 1000.0).strftime('%Y-%m-%d')
        except Exception:
            first_listed_date = "格式错误"
            
        try:
            first_listed_days = round((datetime.now().timestamp() * 1000.0 - first_timestamp_ms) / (1000.0 * 60 * 60 * 24), 1)
            if first_listed_days < 0:
                first_listed_days = 0.0
        except Exception:
            first_listed_days = -1.0

    # 兜底判定：如果没有有效的成交历史，给出稳健的默认评测指标
    if not history or sell_price is None or sell_price <= 0:
        return {
            "category": category,
            "spread": spread,
            "dailySlope": 0.0,
            "normDailySlope": 0.0,
            "avgPrice": sell_price or 0.0,
            "fairPrice": sell_price or 0.0,
            "isNearCeiling": is_near_ceiling,
            "recentTrendPct": 0.0,
            "growthScore": 40.0,
            "action": "HOLD_NEUTRAL",
            "firstListedDate": first_listed_date,
            "firstListedDays": first_listed_days,
            "lastCrashDate": "未检测到大跌",
            "lastCrashDrop": 0.0,
            "nextValleyEvent": "官方胜利日大促",
            "nextValleyDate": "2026-05-08",
            "nextValleyDays": 0,
            "suggestedBuyDate": current_date_str,
            "suggestedSellDate": current_date_str
        }

    sorted_history = sorted(history, key=lambda x: x[0])
    p_current = sell_price
    min_price = min(pt[1] for pt in sorted_history)
    max_price = max(pt[1] for pt in sorted_history)

    # ==========================================
    # 核心 5 因子动态量化模型 (0 - 100分)
    # ==========================================

    # A. 稀缺度与供应因子 (Scarcity Factor) —— 权重 25%
    if sell_orders <= 3:
        f_scarcity = 100.0
    elif sell_orders <= 10:
        f_scarcity = 100.0 - (sell_orders - 3) * 2.5 # 10 -> 82.5
    elif sell_orders <= 30:
        f_scarcity = 82.5 - (sell_orders - 10) * 1.5 # 30 -> 52.5
    elif sell_orders <= 80:
        f_scarcity = 52.5 - (sell_orders - 30) * 0.65 # 80 -> 20.0
    elif sell_orders <= 150:
        f_scarcity = 20.0 - (sell_orders - 80) * 0.25 # 150 -> 2.5
    else:
        f_scarcity = 0.0

    # B. 真实买盘承接力与流动性质量 (Demand & Liquidity Factor) —— 权重 20%
    if spread is not None and sell_price > 0:
        if spread <= 0.05:
            spread_score = 100.0
        elif spread <= 0.35:
            spread_score = 100.0 - ((spread - 0.05) / 0.30) * 70.0
        else:
            spread_score = max(5.0, 30.0 - (spread - 0.35) * 60.0)
    else:
        spread_score = 40.0
        
    latest_t = sorted_history[-1][0]
    cutoff_30d = latest_t - 30 * 24 * 60 * 60 * 1000
    recent_pts_count = sum(1 for pt in sorted_history if pt[0] >= cutoff_30d)
    activity_score = min(100.0, (recent_pts_count / 8.0) * 100.0)
    f_demand = 0.60 * spread_score + 0.40 * activity_score

    # C. 归一化趋势动量因子 (Trend Momentum Factor) —— 权重 20%
    slope_score = 50.0 + (norm_daily_slope * 25000.0)
    slope_score = max(0.0, min(100.0, slope_score))
    
    ma_bias = (ma7 - ma30) / ma30 if ma30 > 0 else 0.0
    bias_score = 50.0 + (ma_bias * 250.0)
    bias_score = max(0.0, min(100.0, bias_score))
    
    f_momentum = 0.50 * slope_score + 0.50 * bias_score

    # D. 估值分位与安全边际因子 (Valuation & Safety Factor) —— 权重 20%
    all_prices = sorted([pt[1] for pt in sorted_history])
    if all_prices and len(all_prices) >= 2:
        rank = sum(1 for p in all_prices if p <= p_current) / len(all_prices)
        f_safety = 100.0 - (rank * 70.0)
        f_safety = max(10.0, min(100.0, f_safety))
    else:
        f_safety = 50.0

    # E. 2000 GJN 交易所硬顶抑制因子 (Ceiling Headroom Factor) —— 权重 15%
    if p_current >= 1900.0:
        f_ceiling = 10.0
    elif p_current >= 1600.0:
        f_ceiling = 60.0 - ((p_current - 1600.0) / 300.0) * 50.0
    elif p_current >= 800.0:
        f_ceiling = 90.0 - ((p_current - 800.0) / 800.0) * 30.0
    else:
        f_ceiling = 100.0

    # 综合潜力得分
    growth_score = (
        0.25 * f_scarcity +
        0.20 * f_demand +
        0.20 * f_momentum +
        0.20 * f_safety +
        0.15 * f_ceiling
    )

    # 惩罚项：如果高供给(>40)且价差过大(>35%)，说明流动性黑洞与泡沫，重扣 15 分
    if sell_orders > 40 and spread and spread > 0.35:
        growth_score = max(0.0, growth_score - 15.0)

    # 特殊品类规则校准：
    if category == '箱子':
        # 箱子长期无限掉落通胀，增长潜力受限
        growth_score = min(growth_score, 35.0)
    elif category == '活动材料':
        growth_score = min(growth_score, 25.0)

    growth_score = round(max(0.0, min(100.0, growth_score)), 1)

    # ==========================================
    # 决策树与行动建议 (Action Decision Tree)
    # ==========================================
    is_heavy_supply = sell_orders >= 100
    is_deep_valley = (p_current <= min_price * 1.12) or (avg_price > 0 and p_current <= avg_price * 0.85)

    if category == '活动材料':
        action = "QUICK_SELL" # 活动材料时效性强，尽快变现
    elif category == '箱子':
        action = "GRADUAL_SELL" if p_current > 0.15 else "HOLD_NEUTRAL"
    elif is_near_ceiling:
        action = "GRADUAL_SELL" # 触及 2000 GJN 极值天花板，分批止盈
    elif growth_score >= 72 and not is_heavy_supply:
        action = "STRONG_HOLD"  # 高评分+稀缺通缩：强力持有
    elif is_deep_valley and not is_heavy_supply and growth_score >= 48:
        action = "HOLD_DIP"     # 处于底部区域：低位吸筹/持有
    elif growth_score < 40 and p_current > (avg_price * 1.15):
        action = "GRADUAL_SELL" # 估值偏高且潜力衰竭：建议分批止盈
    elif is_heavy_supply and norm_daily_slope < -0.002:
        action = "QUICK_SELL"   # 供应泛滥且持续走跌：即刻变现止损
    elif growth_score >= 50:
        action = "HOLD_NEUTRAL" # 稳健观察
    elif norm_daily_slope < -0.0015:
        action = "GRADUAL_SELL" # 持续下行：减仓
    else:
        action = "HOLD_NEUTRAL"
        
    # 检测最近大跌
    crash_date, crash_drop = detect_last_crash(history)
    
    # 预测未来的活动低谷
    future_valleys = predict_future_valleys(current_date, 2)
    next_valley = future_valleys[0]
    next_next_valley = future_valleys[1] if len(future_valleys) > 1 else future_valleys[0]
    
    next_valley_date_str = next_valley[1].strftime('%Y-%m-%d')
    days_to_next_valley = (next_valley[1] - current_date).days
    
    # 建议买入日期：
    if action in ["STRONG_HOLD", "HOLD_DIP"] or is_deep_valley:
        suggested_buy_date = current_date_str
    else:
        suggested_buy_date = next_valley_date_str

    # 建议卖出日期：
    if action in ["GRADUAL_SELL", "QUICK_SELL"] or is_near_ceiling or category == '活动材料':
        suggested_sell_date = current_date_str
    elif action == "STRONG_HOLD":
        # 强力持有：锁定大促后的主升浪，在下下个大促前 20 天锁定利润
        target_date = next_next_valley[1] - timedelta(days=20)
        if target_date <= current_date:
            target_date = next_next_valley[1] + timedelta(days=40)
        suggested_sell_date = target_date.strftime('%Y-%m-%d')
    else:
        # 稳健持有 / 低谷等待
        # 如果距离下一次大促已不足 15 天，市场正处于恐慌砸盘期，严禁此时割肉，应建议在反弹窗口期卖出
        if days_to_next_valley <= 15:
            target_date = next_valley[1] + timedelta(days=35)
        else:
            target_date = next_valley[1] - timedelta(days=15)
        suggested_sell_date = target_date.strftime('%Y-%m-%d')
        
    return {
        "category": category,
        "spread": spread,
        "dailySlope": slope,
        "normDailySlope": norm_daily_slope,
        "avgPrice": avg_price,
        "fairPrice": fair_price,
        "isNearCeiling": is_near_ceiling,
        "recentTrendPct": recent_trend_pct,
        "growthScore": growth_score,
        "action": action,
        "firstListedDate": first_listed_date,
        "firstListedDays": first_listed_days,
        "lastCrashDate": crash_date,
        "lastCrashDrop": round(crash_drop, 1),
        "nextValleyEvent": next_valley[0],
        "nextValleyDate": next_valley_date_str,
        "nextValleyDays": days_to_next_valley,
        "suggestedBuyDate": suggested_buy_date,
        "suggestedSellDate": suggested_sell_date
    }

def analyze_single_file(file_path, meta_data):
    """
    分析单个大盘JSON快照文件，输出分析物品列表与大盘汇总数据 (含挂牌市值与公允估值双口径)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"[警告] 读取文件失败 {file_path}: {str(e)}")
        return [], {}
        
    if not isinstance(raw_data, list):
        return [], {}
        
    analyzed_list = []
    
    opportunity_count = 0
    scarce_count = 0
    crash_count = 0
    total_val = 0.0
    total_fair = 0.0
    
    # 提取快照日期作为基准日期进行自适应评估
    h_date_str = datetime.now().strftime('%Y-%m-%d')
    match = re.search(r'gaijin_market_(\\\\d{4}-\\\\d{2}-\\\\d{2})', file_path)
    if match:
        h_date_str = match.group(1)
        
    for item in raw_data:
        metrics = evaluate_item(item, h_date_str)
        
        # 融合大盘数据
        analyzed_item = {
            **item,
            **metrics,
            "addedDate": meta_data["added_dates"].get(item['name'], "")
        }
        analyzed_list.append(analyzed_item)
        
        sell_price = item.get('sellPrice') or 0.0
        fair_price = metrics.get('fairPrice') or sell_price
        total_val += sell_price
        total_fair += fair_price
        
        if metrics['action'] in ['STRONG_HOLD', 'HOLD_DIP']:
            opportunity_count += 1
            
        sell_orders = item.get('sellOrders') or 0
        buy_orders = item.get('buyOrders') or 0
        if (sell_orders > 0 and sell_orders <= 10) or (sell_orders == 0 and buy_orders > 0):
            scarce_count += 1
            
        if metrics['lastCrashDrop'] >= 30.0:
            crash_count += 1
        
    summary = {
        "totalVehicles": len(analyzed_list),
        "opportunityCount": opportunity_count,
        "scarceCount": scarce_count,
        "crashCount": crash_count,
        "totalSellValue": round(total_val, 2),
        "totalFairValue": round(total_fair, 2),
        "netValue": round(total_val * 0.85, 2),
        "netFairValue": round(total_fair * 0.85, 2)
    }
    
    return analyzed_list, summary

# ==========================================
# 主流程控制
# ==========================================

def main():
    print("=" * 50)
    print("      Gaijin 全市场大盘载具分析脚本启动 (v4.1 智能分类与量化版)")
    print("=" * 50)
    
    # 1. 查找所有的数据导出文件
    json_files = [f for f in glob.glob(os.path.join("daily_json", "gaijin_market_*.json")) if not f.endswith('.bak')]
    
    if not json_files:
        print("\\n[错误] 未找到任何导出的市场 JSON 数据文件。")
        print("\\n请按以下步骤操作：")
        print("1. 用 Chrome 浏览器登录 https://trade.gaijin.net/?category=vehicles")
        print("2. 按 F12 打开开发者工具，在 Console (控制台) 中运行 exporter.js 脚本")
        print("3. 将下载的 JSON 数据文件移动到当前脚本所在目录的 daily_json 文件夹下:")
        print(f"   {os.path.join(os.getcwd(), 'daily_json')}")
        print("4. 重新运行此 Python 脚本。")
        return
        
    # 2. 读取元数据文件
    meta_path = "market_meta.json"
    meta_data = {"added_dates": {}, "purchase_prices": {}}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as mf:
                meta_data = json.load(mf)
                if not isinstance(meta_data, dict):
                    meta_data = {"added_dates": {}, "purchase_prices": {}}
                if "added_dates" not in meta_data:
                    meta_data["added_dates"] = {}
                if "purchase_prices" not in meta_data:
                    meta_data["purchase_prices"] = {}
        except Exception as e:
            print(f"[警告] 读取元数据文件失败: {str(e)}")

    # 3. 升序排序历史文件，建立资产增值时间走势
    history_files = sorted(json_files)
    history_trend = []
    history_snapshots = {}
    
    print(f"[信息] 正在构建多版本历史大盘账本...")
    for h_file in history_files:
        h_date = datetime.now().strftime('%Y-%m-%d')
        match = re.search(r'gaijin_market_(\d{4}-\d{2}-\d{2})', h_file)
        if match:
            h_date = match.group(1)
            
        print(f"      - 分析历史快照: {h_file} [{h_date}]")
        h_list, h_summary = analyze_single_file(h_file, meta_data)
        if h_list:
            history_snapshots[h_date] = h_list
            history_trend.append({
                "date": h_date,
                **h_summary
            })
            
    if not history_trend:
        print("[错误] 未能成功解析任何有效的大盘快照数据。")
        return
        
    # 最新版数据
    latest_date = history_trend[-1]["date"]
    analyzed_data = history_snapshots[latest_date]
    latest_summary = history_trend[-1]
    
    # 4. 获取次新数据进行差量比对
    prev_items = {}
    prev_file = None
    if len(history_trend) >= 2:
        prev_date = history_trend[-2]["date"]
        prev_file = next((f for f in json_files if prev_date in f), None)
        prev_items = {item['name']: item for item in history_snapshots[prev_date]}
        
    latest_items = {item['name']: item for item in analyzed_data if 'name' in item}
    meta_dirty = False
    added_list = []
    removed_list = []
    
    # 5. 双向差异比对（新增上架 / 售罄下架）
    all_names = set(list(latest_items.keys()) + list(prev_items.keys()))
    for name in all_names:
        in_latest = name in latest_items
        in_prev = name in prev_items
        
        is_brand_new = (not in_prev and in_latest)
        
        item_added_date = meta_data["added_dates"].get(name)
        if is_brand_new and not item_added_date:
            item_added_date = latest_date
            meta_data["added_dates"][name] = latest_date
            meta_dirty = True
            
        if in_latest:
            latest_items[name]["addedDate"] = item_added_date if item_added_date else ""
            
        if prev_file:
            if in_latest and not in_prev:
                item = latest_items[name]
                added_list.append({
                    "name": name,
                    "imageUrl": item.get("imageUrl", ""),
                    "url": item.get("url", ""),
                    "quantity": 1,
                    "isBrandNew": is_brand_new,
                    "sellPrice": item.get("sellPrice"),
                    "category": item.get("category", "其他"),
                    "addedDate": item_added_date if item_added_date else latest_date
                })
            elif in_prev and not in_latest:
                item = prev_items[name]
                removed_list.append({
                    "name": name,
                    "imageUrl": item.get("imageUrl", ""),
                    "url": item.get("url", ""),
                    "quantity": 1,
                    "isFullySold": True,
                    "sellPrice": item.get("sellPrice"),
                    "category": item.get("category", "其他")
                })
        else:
            if in_latest:
                item = latest_items[name]
                added_list.append({
                    "name": name,
                    "imageUrl": item.get("imageUrl", ""),
                    "url": item.get("url", ""),
                    "quantity": 1,
                    "isBrandNew": True,
                    "sellPrice": item.get("sellPrice"),
                    "category": item.get("category", "其他"),
                    "addedDate": item_added_date if item_added_date else latest_date
                })
                
    # 如果元数据被更新，回写文件
    if meta_dirty:
        try:
            with open(meta_path, 'w', encoding='utf-8') as mf:
                json.dump(meta_data, mf, ensure_ascii=False, indent=4)
            print(f"[成功] 自动检测到新上市载具，已更新本地元数据文件: {meta_path}")
        except Exception as e:
            print(f"[警告] 写入元数据文件失败: {str(e)}")
            
    # 5.5 计算真实在售价跨快照波动与潜力微调
    print(f"[信息] 正在分析跨快照最低售价真实波动趋势并校准潜力得分...")
    vehicle_snapshots_prices = {}
    for h_date in sorted(history_snapshots.keys()):
        for item in history_snapshots[h_date]:
            name = item.get("name")
            sell_price = item.get("sellPrice")
            if name and sell_price is not None and sell_price > 0:
                if name not in vehicle_snapshots_prices:
                    vehicle_snapshots_prices[name] = []
                vehicle_snapshots_prices[name].append([h_date, sell_price])
                
    # 修正最新快照的潜力分与行动建议
    for item in analyzed_data:
        name = item.get("name")
        prices = vehicle_snapshots_prices.get(name, [])
        
        growth_pct = 0.0
        growth_mod = 0.0
        volatility = 0.0
        
        if len(prices) >= 2:
            p_first = prices[0][1]
            p_last = prices[-1][1]
            if p_first > 0:
                growth_pct = (p_last - p_first) / p_first
                growth_mod = max(-10.0, min(10.0, growth_pct * 25.0))
                
            p_avg = sum(pt[1] for pt in prices) / len(prices)
            if p_avg > 0:
                p_var = sum((pt[1] - p_avg) ** 2 for pt in prices) / len(prices)
                p_std = p_var ** 0.5
                volatility = p_std / p_avg
                
        item["snapshotGrowthPct"] = round(growth_pct * 100.0, 1)
        item["snapshotVolatility"] = round(volatility * 100.0, 1)
        item["snapshotPriceHistoryCount"] = len(prices)
        
        # 修正潜力分并限制在 [0.0, 100.0]
        orig_score = item.get("growthScore", 50.0)
        new_score = max(0.0, min(100.0, orig_score + growth_mod))
        item["growthScore"] = round(new_score, 1)
        
        # 联动校准行动建议
        category = item.get("category", "其他")
        sell_orders = item.get('sellOrders') or 0
        sell_price = item.get('sellPrice')
        avg_price = item.get('avgPrice') or 0.0
        norm_daily_slope = item.get('normDailySlope', 0.0)
        is_scarce = (sell_orders > 0 and sell_orders <= 15)
        is_heavy_supply = sell_orders >= 100
        is_near_ceiling = item.get("isNearCeiling", False)
        
        if category == '载具' and sell_price is not None:
            if is_near_ceiling:
                item["action"] = "GRADUAL_SELL"
            elif is_scarce and new_score >= 65 and not is_near_ceiling:
                item["action"] = "STRONG_HOLD"
            elif new_score >= 72 and norm_daily_slope >= 0.0003 and not is_heavy_supply:
                item["action"] = "STRONG_HOLD"
            elif new_score < 38 and sell_price > (avg_price * 1.15):
                item["action"] = "GRADUAL_SELL"

    print(f"[分析完成] 当前最新大盘日期: {latest_date}")
    print(f"[分析完成] 大盘载具/物品数: {latest_summary['totalVehicles']} 种")
    print(f"[分析完成] 大盘最低挂牌总额: {latest_summary['totalSellValue']:.2f} GJN (税后净值: {latest_summary['netValue']:.2f} GJN)")
    print(f"[分析完成] 大盘保守公允估值: {latest_summary['totalFairValue']:.2f} GJN (公允净值: {latest_summary['netFairValue']:.2f} GJN)")
    print(f"[分析完成] 超跌与低估机会: {latest_summary['opportunityCount']} 种 | 极度稀缺: {latest_summary['scarceCount']} 种")
    print(f"[分析完成] 历史回溯: 累积分析了 {len(history_trend)} 期快照")
    if prev_file:
        print(f"[分析完成] 变动对比: 新增上架 {len(added_list)} 种，售罄/下架 {len(removed_list)} 种")
        
    # 6. 读取 HTML 模板并合并生成最终报告
    template_path = "report_template.html"
    report_path = "report.html"
    
    if not os.path.exists(template_path):
        print(f"[错误] 未找到 HTML 模板文件 {template_path}，无法生成分析面板。")
        return
        
    try:
        with open(template_path, 'r', encoding='utf-8') as tf:
            template_content = tf.read()
            
        # 将分析的数据序列化为 JSON 字符串
        json_data_str = json.dumps(analyzed_data, ensure_ascii=False)
        
        diff_data = {
            "added": added_list,
            "removed": removed_list
        }
        json_diff_str = json.dumps(diff_data, ensure_ascii=False)
        json_meta_str = json.dumps(meta_data, ensure_ascii=False)
        
        # 序列化历史相关数据
        json_trend_str = json.dumps(history_trend, ensure_ascii=False)
        json_snapshots_str = json.dumps(history_snapshots, ensure_ascii=False)
        
        # 替换模板占位符
        final_content = template_content.replace("{{INVENTORY_DATA_JSON}}", json_data_str)
        final_content = final_content.replace("{{INVENTORY_DIFF_JSON}}", json_diff_str)
        final_content = final_content.replace("{{INVENTORY_META_JSON}}", json_meta_str)
        final_content = final_content.replace("{{HISTORY_TREND_JSON}}", json_trend_str)
        final_content = final_content.replace("{{HISTORY_SNAPSHOTS_JSON}}", json_snapshots_str)
        
        # 写入 report.html 同时也更新 index.html 确保看板最新
        for path in [report_path, "index.html"]:
            with open(path, 'w', encoding='utf-8') as rf:
                rf.write(final_content)
            
        print("\\n" + "=" * 50)
        print(f"[成功] 可视化分析报告已同步生成: {report_path} & index.html")
        print("请在浏览器中直接双击打开 report.html 或 index.html 查看全市场黑金量化分析面板！")
        print("=" * 50)
        
    except Exception as e:
        print(f"[错误] 合并 HTML 报表失败: {str(e)}")

if __name__ == "__main__":
    main()
'''

# 写入 analyze.py
with open(os.path.join(TARGET_DIR, "analyze.py"), "w", encoding="utf-8") as f:
    f.write(ANALYZE_PY)
print("[成功] 已同步写入: wt-market-analyst/analyze.py")

# 2. 同步并更新 exporter.js
exporter_path = os.path.join(TARGET_DIR, "exporter.js")
if os.path.exists(exporter_path):
    with open(exporter_path, "r", encoding="utf-8") as f:
        exp_code = f.read()
    # 替换价格走势解析以保留成交量 pt[2]
    old_parse = "priceHistory = rawHistory.map(pt => {\n                        return [pt[0] * 1000, parseFloat(pt[1]) / 10000];\n                    });"
    new_parse = "priceHistory = rawHistory.map(pt => {\n                        return pt.length >= 3 ? [pt[0] * 1000, parseFloat(pt[1]) / 10000, parseInt(pt[2])] : [pt[0] * 1000, parseFloat(pt[1]) / 10000];\n                    });"
    if old_parse in exp_code:
        exp_code = exp_code.replace(old_parse, new_parse)
    else:
        exp_code = re.sub(
            r'priceHistory\s*=\s*rawHistory\.map\([^)]*\)\s*=>\s*\{[^}]*\[pt\[0\]\s*\*\s*1000,\s*parseFloat\(pt\[1\]\)\s*/\s*10000\];\s*\}\);',
            'priceHistory = rawHistory.map(pt => (pt.length >= 3 ? [pt[0] * 1000, parseFloat(pt[1]) / 10000, parseInt(pt[2])] : [pt[0] * 1000, parseFloat(pt[1]) / 10000]));',
            exp_code
        )
    with open(exporter_path, "w", encoding="utf-8") as f:
        f.write(exp_code)
    print("[成功] 已同步更新: wt-market-analyst/exporter.js (成交量 volume 保留)")

# 3. 同步并更新 scraper.py
scraper_path = os.path.join(TARGET_DIR, "scraper.py")
if os.path.exists(scraper_path):
    with open(scraper_path, "r", encoding="utf-8") as f:
        scr_code = f.read()
    scr_code = scr_code.replace(
        "price_history = [[pt[0] * 1000, float(pt[1]) / 10000] for pt in raw_history]",
        "price_history = [[pt[0] * 1000, float(pt[1]) / 10000, int(pt[2])] if len(pt) >= 3 else [pt[0] * 1000, float(pt[1]) / 10000] for pt in raw_history]"
    )
    with open(scraper_path, "w", encoding="utf-8") as f:
        f.write(scr_code)
    print("[成功] 已同步更新: wt-market-analyst/scraper.py (成交量 volume 保留)")

# 4. 同步升级 report_template.html
template_path = os.path.join(TARGET_DIR, "report_template.html")
# 我们从头生成一套完美的针对全市场大盘的 report_template.html
REPORT_TEMPLATE_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gaijin 市场大盘分析与量化投资仪表盘</title>
    <!-- 引入高质感现代字体 -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
    <!-- 引入 Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0f1013;
            --card-bg: #15171e;
            --card-border: rgba(224, 169, 109, 0.12);
            --card-border-hover: rgba(224, 169, 109, 0.4);
            --gold: #e0a96d;
            --gold-dark: #b88655;
            --gold-light: #f5d6b3;
            --text-main: #ffffff;
            --text-muted: #c9d1d9;
            --text-dark: #8b949e;
            --green: #4ade80;
            --green-bg: rgba(74, 222, 128, 0.1);
            --red: #f87171;
            --red-bg: rgba(248, 113, 113, 0.1);
            --blue: #60a5fa;
            --blue-bg: rgba(96, 165, 250, 0.1);
            --orange: #fb923c;
            --orange-bg: rgba(251, 146, 60, 0.1);
            --table-header: #1b1e26;
            --table-row-hover: #1e212b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        #particle-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            pointer-events: none;
        }

        body {
            background: transparent;
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 24px;
            min-height: 100vh;
            line-height: 1.5;
        }

        /* 自定义滚动条 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0f1013;
        }
        ::-webkit-scrollbar-thumb {
            background: #252836;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--gold-dark);
        }

        /* 顶部导航 */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            flex-wrap: wrap;
            gap: 16px;
        }

        .logo-section h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1px;
            background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 50%, var(--gold-dark) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-section p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* 红色徽章脉冲式呼吸光晕效果 */
        @keyframes pulse {
            0% { opacity: 0.8; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { opacity: 1; box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
            100% { opacity: 0.8; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        /* 下拉卡片样式 */
        .custom-dropdown {
            position: relative;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
        }
        .dropdown-trigger {
            background: rgba(21, 23, 30, 0.85);
            border: 1px solid var(--gold);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            user-select: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(224, 169, 109, 0.1);
        }
        .dropdown-trigger:hover {
            border-color: var(--gold-light);
            box-shadow: 0 0 15px rgba(224, 169, 109, 0.25);
            transform: translateY(-1px);
        }
        .custom-dropdown.active .arrow-icon {
            transform: rotate(180deg);
        }
        .custom-dropdown.active .dropdown-trigger {
            border-color: var(--gold-light);
            background: rgba(26, 29, 38, 0.95);
        }
        .dropdown-menu {
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            width: 320px;
            max-height: 420px;
            overflow-y: auto;
            background: #181a22;
            border: 1px solid var(--gold);
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.8), 0 0 25px rgba(224, 169, 109, 0.2);
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px) scale(0.98);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .custom-dropdown.show-menu .dropdown-menu {
            opacity: 1;
            visibility: visible;
            transform: translateY(0) scale(1);
        }
        .dropdown-card-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .dropdown-card-item:hover {
            background: rgba(224, 169, 109, 0.08);
            border-color: rgba(224, 169, 109, 0.4);
            transform: translateX(4px);
        }
        .dropdown-card-item.active {
            background: rgba(224, 169, 109, 0.15);
            border-color: var(--gold);
            box-shadow: inset 0 0 10px rgba(224, 169, 109, 0.1);
        }

        /* 顶部统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }

        .stat-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--gold) 0%, transparent 100%);
        }

        .stat-card.opportunity::before {
            background: linear-gradient(90deg, var(--green) 0%, transparent 100%);
        }

        .stat-card.scarce::before {
            background: linear-gradient(90deg, var(--blue) 0%, transparent 100%);
        }

        .stat-card.crash::before {
            background: linear-gradient(90deg, var(--red) 0%, transparent 100%);
        }

        .stat-label {
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }

        .stat-value {
            font-family: 'Inter', sans-serif;
            font-size: 26px;
            font-weight: 700;
            color: var(--text-main);
            margin: 10px 0 4px 0;
            display: flex;
            align-items: baseline;
            gap: 6px;
        }

        .stat-value span:last-child {
            font-size: 14px;
            color: var(--text-dark);
            font-weight: normal;
        }

        .stat-desc {
            font-size: 12px;
            color: var(--text-dark);
        }

        /* 图表网格 */
        .dashboard-charts {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 1024px) {
            .dashboard-charts {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .chart-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-title svg {
            color: var(--gold);
        }

        .chart-select {
            background-color: #1a1c24;
            border: 1px solid var(--card-border);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
            cursor: pointer;
            transition: all 0.2s;
        }

        .chart-select:focus {
            border-color: var(--gold);
        }

        .chart-container {
            position: relative;
            flex-grow: 1;
            min-height: 260px;
            width: 100%;
        }

        /* 大跌与活动低谷预测面板 */
        .forecast-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px dashed rgba(224, 169, 109, 0.15);
        }

        .forecast-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .forecast-label {
            font-size: 11px;
            color: var(--text-dark);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .forecast-value {
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }

        .forecast-value .highlight-gold { color: var(--gold); }
        .forecast-value .highlight-orange { color: var(--orange); }
        .forecast-value .highlight-red { color: var(--red); }

        /* 选项卡 Tab 控制 */
        .tab-navigation {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 10px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-dark);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            padding: 8px 16px;
            position: relative;
            transition: all 0.3s;
        }

        .tab-btn:hover { color: var(--text-main); }
        .tab-btn.active { color: var(--gold); }
        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -11px;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--gold);
        }

        /* 变动比对面板样式 */
        .diff-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 900px) {
            .diff-panel { grid-template-columns: 1fr; }
        }

        .diff-column {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
        }

        .diff-column.added-col { border-top: 3px solid var(--green); }
        .diff-column.removed-col { border-top: 3px solid var(--red); }

        .diff-column-header {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .diff-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 500px;
            overflow-y: auto;
        }
        .diff-item {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(255, 255, 255, 0.02);
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.02);
        }
        .diff-item:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(224, 169, 109, 0.1);
        }
        .diff-item-name {
            font-weight: 500;
            font-size: 13px;
            color: var(--text-main);
            flex-grow: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* 过滤和检索面板 */
        .controls-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .search-wrapper {
            position: relative;
            flex-grow: 1;
            max-width: 420px;
        }

        .search-input {
            width: 100%;
            background-color: #1a1c24;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 16px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: all 0.3s;
        }

        .search-input:focus {
            border-color: var(--gold);
            box-shadow: 0 0 8px rgba(224, 169, 109, 0.15);
        }

        .filter-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }

        .filter-btn {
            background: #1e2230;
            border: 1px solid var(--card-border);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            user-select: none;
        }

        .filter-btn:hover {
            color: var(--text-main);
            border-color: var(--gold-dark);
            background: #242838;
        }

        .filter-btn.active {
            background: var(--gold);
            color: #0f1013;
            font-weight: 700;
            border-color: var(--gold);
            box-shadow: 0 2px 10px rgba(224, 169, 109, 0.3);
        }

        .filter-btn.active .filter-count {
            background: rgba(0, 0, 0, 0.25);
            color: #0f1013;
            font-weight: 700;
        }

        .filter-count {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 500;
        }

        .filter-section {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 4px;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .filter-row {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .filter-row-label {
            font-size: 12px;
            font-weight: 700;
            color: var(--gold-light);
            min-width: 75px;
            display: flex;
            align-items: center;
            gap: 4px;
            letter-spacing: 0.3px;
        }

        /* 数据表格面板 */
        .table-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 32px;
        }

        .table-responsive {
            overflow-x: auto;
            width: 100%;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
        }

        th {
            background-color: var(--table-header);
            padding: 14px 16px;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 13px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }

        th:hover {
            background-color: #242735;
            color: var(--text-main);
        }

        th.sort-asc::after { content: ' ▲'; font-size: 10px; color: var(--gold); }
        th.sort-desc::after { content: ' ▼'; font-size: 10px; color: var(--gold); }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            vertical-align: middle;
        }

        tr {
            transition: background 0.2s;
            cursor: pointer;
        }

        tr:hover {
            background-color: var(--table-row-hover);
        }

        tr.selected {
            background-color: rgba(224, 169, 109, 0.08);
            border-left: 3px solid var(--gold);
        }

        .item-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .item-image {
            width: 44px;
            height: 44px;
            border-radius: 6px;
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: #111;
        }

        .item-details {
            display: flex;
            flex-direction: column;
        }

        .item-name {
            font-weight: 500;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .market-link {
            display: inline-flex;
            align-items: center;
            color: var(--text-muted);
            text-decoration: none;
            transition: color 0.2s;
        }

        .market-link:hover {
            color: var(--gold);
        }

        .price-col {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 15px;
        }

        .price-gjn {
            color: var(--text-main);
        }

        .price-tax {
            font-size: 11px;
            color: var(--text-dark);
            margin-top: 2px;
        }

        /* 评分显示 */
        .score-bar-container {
            width: 100px;
            height: 6px;
            background: #252836;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 4px;
        }

        .score-bar {
            height: 100%;
            border-radius: 3px;
        }

        .score-value {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 13px;
        }

        /* Badge 徽章样式 */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .badge-hold-strong { background-color: var(--green-bg); color: var(--green); }
        .badge-hold-neutral { background-color: var(--blue-bg); color: var(--blue); }
        .badge-hold-dip { background-color: var(--orange-bg); color: var(--orange); }
        .badge-sell-gradual { background-color: var(--red-bg); color: var(--red); }
        .badge-sell-quick { background-color: rgba(244, 63, 94, 0.15); color: #f43f5e; }

        /* 物品分类徽章样式 */
        .badge-cat-vehicle { background: rgba(224, 169, 109, 0.15); color: var(--gold); border: 1px solid rgba(224, 169, 109, 0.35); }
        .badge-cat-camo { background: rgba(192, 132, 252, 0.15); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.35); }
        .badge-cat-box { background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.35); }
        .badge-cat-item { background: rgba(96, 165, 250, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.35); }
        .badge-cat-mat { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.35); }
        .badge-cat-other { background: rgba(156, 163, 175, 0.15); color: #9ca3af; border: 1px solid rgba(156, 163, 175, 0.35); }

        /* 评分等级颜色 */
        .color-high { color: var(--green); }
        .color-medium { color: var(--blue); }
        .color-low { color: var(--orange); }
        .color-poor { color: var(--red); }

        .bg-high { background-color: var(--green); }
        .bg-medium { background-color: var(--blue); }
        .bg-low { background-color: var(--orange); }
        .bg-poor { background-color: var(--red); }

        /* Toast 气泡通知 */
        .toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: rgba(21, 23, 30, 0.95);
            border: 1px solid var(--gold);
            padding: 14px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(224, 169, 109, 0.15);
            z-index: 9999;
            color: var(--text-main);
            font-size: 13px;
            max-width: 380px;
            backdrop-filter: blur(8px);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            pointer-events: none;
        }
        .toast-container.show {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }

        .empty-state {
            color: var(--text-dark);
            text-align: center;
            padding: 48px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <!-- 全屏科技感金色粒子背景 -->
    <canvas id="particle-canvas"></canvas>

    <!-- 顶栏区域 -->
    <header>
        <div class="logo-section">
            <h1>GAIJIN MARKET ANALYST</h1>
            <p>基于 5 因子动态量化算法的战雷全市场大盘评估与投资推荐面板 (v4.1 量化版)</p>
        </div>
        <div class="custom-dropdown" id="snapshotDropdown">
            <span id="snapshot-indicator" style="display: none; background: var(--red-bg); color: var(--red); border: 1px solid var(--red); font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold; animation: pulse 2s infinite;">[时光回溯中]</span>
            数据大盘版本: 
            <div class="dropdown-trigger" onclick="toggleDropdown(event)">
                <span id="dropdown-current-val">加载中...</span>
                <svg class="arrow-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="transition: transform 0.3s; color: var(--gold);"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div class="dropdown-menu" id="dropdownMenu">
                <!-- 动态填充的微缩快照卡片列表 -->
            </div>
        </div>
    </header>

    <!-- 顶部 KPI 卡片 -->
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-label">大盘收录总数</span>
            <div class="stat-value"><span id="total-vehicles">0</span><span>种</span></div>
            <div class="stat-desc">
                挂牌估值: <b id="total-sell-val" style="color:var(--gold);">0</b> GJN (公允: <b id="total-fair-val" style="color:var(--text-main);">0</b> G)
            </div>
        </div>
        <div class="stat-card opportunity">
            <span class="stat-label">超跌 / 低估机会数</span>
            <div class="stat-value" style="color: var(--green);"><span id="opportunity-count">0</span><span>种</span></div>
            <div class="stat-desc">
                建议强力买入或超跌低位抄底
            </div>
        </div>
        <div class="stat-card scarce">
            <span class="stat-label">极度稀缺在售</span>
            <div class="stat-value" style="color: var(--blue);"><span id="scarce-count">0</span><span>种</span></div>
            <div class="stat-desc">
                当前在售挂单极少（数量 &le; 10 辆）
            </div>
        </div>
        <div class="stat-card crash">
            <span class="stat-label">近期断崖暴跌</span>
            <div class="stat-value" style="color: var(--red);"><span id="crash-count">0</span><span>种</span></div>
            <div class="stat-desc">
                30 天内曾暴跌超 30% 仍处于低谷
            </div>
        </div>
    </div>

    <!-- 图表区域 -->
    <div class="dashboard-charts">
        <!-- 占比饼图 -->
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M7.5 8V4.5a.5.5 0 0 1 1 0V8h3.5a.5.5 0 0 1 0 1H8.5v3.5a.5.5 0 0 1-1 0V9H4a.5.5 0 0 1 0-1h3.5z"/></svg>
                    全市场载具行动建议分布大盘
                </div>
            </div>
            <div class="chart-container" id="pieChartContainer">
                <canvas id="pieChart"></canvas>
            </div>
        </div>

        <!-- 历史价格走势图 -->
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M0 0h1v15h15v1H0V0zm10 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V4.707L10.354 8.354a.5.5 0 0 1-.708 0L7.5 6.207l-4.146 4.147a.5.5 0 0 1-.708-.708l4.5-4.5a.5.5 0 0 1 .708 0L10 7.293l3.646-3.647H10.5a.5.5 0 0 1-.5-.5z"/></svg>
                    载具历史价格及大盘市值走势图
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    <select id="chartTypeSelect" class="chart-select" style="border-color: var(--gold); font-weight: 600;">
                        <option value="single" selected>单一载具最低市价</option>
                        <option value="portfolio">全大盘载具估值总额走势</option>
                    </select>
                    <select id="timeRangeSelect" class="chart-select">
                        <option value="7">近7天</option>
                        <option value="15">近15天</option>
                        <option value="30">近一个月</option>
                        <option value="90">近3个月</option>
                        <option value="180">近半年</option>
                        <option value="365">近一年</option>
                        <option value="all" selected>全周期</option>
                    </select>
                    <select id="vehicleSelect" class="chart-select">
                        <!-- JS动态加载 -->
                    </select>
                </div>
            </div>
            <div class="chart-container" id="trendChartContainer">
                <canvas id="trendChart"></canvas>
            </div>
            <!-- 大跌与活动低谷预测面板 -->
            <div class="forecast-panel" id="forecastPanel" style="display: none;">
                <div class="forecast-item">
                    <span class="forecast-label">历史最近价格断崖区间</span>
                    <div class="forecast-value">
                        <span id="crashDate" class="highlight-gold">-</span>
                        <span id="crashDrop" class="highlight-red" style="font-size: 11px;">(-%)</span>
                    </div>
                </div>
                <div class="forecast-item">
                    <span class="forecast-label">预计下一次官方活动低谷</span>
                    <div class="forecast-value">
                        <span id="valleyEvent" class="highlight-gold">-</span>
                        <span id="valleyDate" style="font-size: 11px; color: var(--text-dark);">(-)</span>
                        <span id="valleyCountdown" class="highlight-orange" style="margin-left: auto;">剩余 - 天</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 数据控制面板 -->
    <div class="controls-card">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div class="search-wrapper">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 搜索载具 / 涂装 / 箱子 / 道具挂饰名称...">
            </div>
        </div>

        <!-- 多维度联动筛选区域 -->
        <div class="filter-section">
            <!-- 类别筛选 -->
            <div class="filter-row">
                <span class="filter-row-label">🏷️ 物品类别:</span>
                <div class="filter-buttons" id="categoryFilterGroup">
                    <button class="filter-btn active" data-filter-type="category" data-val="all">全部类别 <span id="count-cat-all" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="载具">🚀 载具 <span id="count-cat-vehicle" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="涂装">🎨 涂装 <span id="count-cat-camo" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="箱子">📦 箱子 <span id="count-cat-box" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="道具/挂饰">🔑 道具/挂饰 <span id="count-cat-item" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="活动材料">⚙️ 活动材料 <span id="count-cat-mat" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="category" data-val="其他">📎 其他 <span id="count-cat-other" class="filter-count">0</span></button>
                </div>
            </div>

            <!-- 操作建议筛选 -->
            <div class="filter-row">
                <span class="filter-row-label">💡 投资建议:</span>
                <div class="filter-buttons" id="actionFilterGroup">
                    <button class="filter-btn active" data-filter-type="action" data-val="all">全部建议 <span id="count-act-all" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="action" data-val="STRONG_HOLD">🌟 强力持有 <span id="count-act-strong" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="action" data-val="HOLD_NEUTRAL">⚖️ 稳健持仓 <span id="count-act-neutral" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="action" data-val="HOLD_DIP">📉 低位等待 <span id="count-act-dip" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="action" data-val="GRADUAL_SELL">💰 建议卖出 <span id="count-act-gradual" class="filter-count">0</span></button>
                    <button class="filter-btn" data-filter-type="action" data-val="QUICK_SELL">⚡ 快速套现 <span id="count-act-quick" class="filter-count">0</span></button>
                </div>
            </div>

            <!-- 市场机会类型筛选 -->
            <div class="filter-row">
                <span class="filter-row-label">💎 市场机会:</span>
                <div class="filter-buttons" id="opportunityFilterGroup">
                    <button class="filter-btn active" data-filter-type="opp" data-val="all">全部机会</button>
                    <button class="filter-btn" data-filter-type="opp" data-val="dip">🚀 抄底机会</button>
                    <button class="filter-btn" data-filter-type="opp" data-val="scarce">💎 极度稀缺 (&le;10)</button>
                    <button class="filter-btn" data-filter-type="opp" data-val="crash">📉 近期断崖暴跌</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 导航选项卡 Tabs -->
    <div class="tab-navigation">
        <button class="tab-btn active" id="tabInventory" onclick="switchTab('inventory')">全市场大盘一览 (<span id="tab-inventory-count">0</span>)<span id="snapshot-indicator-tab" style="font-size: 11px; color: var(--red); font-weight: bold; margin-left: 6px; display: none;">[查看历史快照中]</span></button>
        <button class="tab-btn" id="tabDiff" onclick="switchTab('diff')">大盘最近新增与下架比对 (上架 <span id="tab-diff-added">0</span> / 下架 <span id="tab-diff-removed">0</span>)</button>
        <button class="tab-btn" id="tabHistorySnap" onclick="switchTab('historySnap')">历史快照大盘账本 (<span id="tab-history-count">0</span>)</button>
    </div>

    <!-- 变动比对面板 -->
    <div class="diff-panel" id="diffPanel" style="display: none;">
        <!-- 新增上架 -->
        <div class="diff-column added-col">
            <div class="diff-column-header">
                <span>最近大盘新增上架检测</span>
                <span class="badge badge-hold-strong" id="diff-added-badge">0 种</span>
            </div>
            <div class="diff-list" id="diffAddedList">
                <!-- 动态填充 -->
            </div>
        </div>
        <!-- 移除下架 -->
        <div class="diff-column removed-col">
            <div class="diff-column-header">
                <span>大盘已售罄或下架载具</span>
                <span class="badge badge-sell-quick" id="diff-removed-badge">0 种</span>
            </div>
            <div class="diff-list" id="diffRemovedList">
                <!-- 动态填充 -->
            </div>
        </div>
    </div>

    <!-- 历史快照面板 -->
    <div class="diff-panel" id="historySnapPanel" style="display: none; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        <!-- 动态填充 -->
    </div>

    <!-- 数据表格 -->
    <div class="table-card" id="inventoryTableCard">
        <div class="table-responsive">
            <table id="inventoryTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)" style="width: 18%">载具/物品</th>
                        <th onclick="sortTable(9)" style="width: 7%">类别</th>
                        <th onclick="sortTable(1)" style="width: 10%">收录与首次上架</th>
                        <th onclick="sortTable(2)" style="width: 11%">最低市价 (在售)</th>
                        <th onclick="sortTable(3)" style="width: 11%">最高求购 (求购)</th>
                        <th onclick="sortTable(4)" style="width: 6%">价差比率</th>
                        <th onclick="sortTable(5)" style="width: 8%">增值潜力</th>
                        <th onclick="sortTable(6)" style="width: 9%">大盘建议</th>
                        <th onclick="sortTable(7)" style="width: 10%">建议买入日期</th>
                        <th onclick="sortTable(8)" style="width: 10%">建议卖出日期</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- JS动态填充 -->
                </tbody>
            </table>
            <div id="emptyState" class="empty-state" style="display: none;">
                未找到匹配的载具物品
            </div>
        </div>
    </div>

    <!-- Toast 容器 -->
    <div id="toast" class="toast-container">
        <span id="toastText"></span>
    </div>

    <!-- 数据源 JSON 岛，防止模板占位符在 JS 中引起 IDE 语法报错 -->
    <script id="inventory-data-raw" type="application/json">{{INVENTORY_DATA_JSON}}</script>
    <script id="inventory-diff-raw" type="application/json">{{INVENTORY_DIFF_JSON}}</script>
    <script id="inventory-meta-raw" type="application/json">{{INVENTORY_META_JSON}}</script>
    <script id="history-trend-raw" type="application/json">{{HISTORY_TREND_JSON}}</script>
    <script id="history-snapshots-raw" type="application/json">{{HISTORY_SNAPSHOTS_JSON}}</script>

    <!-- 数据载入脚本 -->
    <script>
        const inventoryData = JSON.parse(document.getElementById('inventory-data-raw').textContent);
        const inventoryDiff = JSON.parse(document.getElementById('inventory-diff-raw').textContent);
        const inventoryMeta = JSON.parse(document.getElementById('inventory-meta-raw').textContent);
        const historyTrendData = JSON.parse(document.getElementById('history-trend-raw').textContent);
        const historySnapshots = JSON.parse(document.getElementById('history-snapshots-raw').textContent);

        let activeSnapshotDate = null; // 全局时空回溯标志
        let activeInventorySource = inventoryData; // 数据大盘指针

        // 定义常量和图表实例
        let pieChartInstance = null;
        let trendChartInstance = null;
        let currentVehicle = null;
        let currentSortColumn = -1;
        let isSortAsc = true;

        // ==========================================
        // 视觉交互特效库 (原生 Canvas 粒子及 3D 卡片系统)
        // ==========================================

        const easeOutQuad = t => t * (2 - t);

        function animateValue(id, start, end, duration, decimals = 0) {
            const obj = document.getElementById(id);
            if (!obj) return;
            
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                const easedProgress = easeOutQuad(progress);
                const currentVal = start + easedProgress * (end - start);
                
                obj.innerText = decimals > 0 ? currentVal.toFixed(decimals) : Math.floor(currentVal);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                } else {
                    obj.innerText = decimals > 0 ? end.toFixed(decimals) : end;
                }
            };
            window.requestAnimationFrame(step);
        }

        function initParticleBackground() {
            const canvas = document.getElementById('particle-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            let particles = [];
            
            const mouse = { x: null, y: null, radius: 160 };
            
            window.addEventListener('mousemove', (e) => {
                mouse.x = e.clientX;
                mouse.y = e.clientY;
            });
            
            window.addEventListener('mouseout', () => {
                mouse.x = null;
                mouse.y = null;
            });
            
            function resizeCanvas() {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);
            
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() * canvas.height;
                    this.vx = (Math.random() - 0.5) * 0.35;
                    this.vy = (Math.random() - 0.5) * 0.35;
                    this.radius = Math.random() * 1.5 + 1;
                    this.baseAlpha = Math.random() * 0.25 + 0.1;
                    this.alpha = this.baseAlpha;
                }
                
                draw() {
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(224, 169, 109, ${this.alpha})`;
                    ctx.fill();
                }
                
                update() {
                    if (this.x < 0 || this.x > canvas.width) this.vx = -this.vx;
                    if (this.y < 0 || this.y > canvas.height) this.vy = -this.vy;
                    
                    if (mouse.x !== null && mouse.y !== null) {
                        const dx = mouse.x - this.x;
                        const dy = mouse.y - this.y;
                        const dist = Math.hypot(dx, dy);
                        if (dist < mouse.radius) {
                            const force = (mouse.radius - dist) / mouse.radius;
                            this.x += (dx / dist) * force * 0.55;
                            this.y += (dy / dist) * force * 0.55;
                            this.alpha = Math.min(0.7, this.baseAlpha + force * 0.35);
                        } else {
                            this.alpha = this.baseAlpha;
                        }
                    } else {
                        this.alpha = this.baseAlpha;
                    }
                    
                    this.x += this.vx;
                    this.y += this.vy;
                }
            }
            
            const count = Math.min(90, Math.floor((canvas.width * canvas.height) / 16000));
            for (let i = 0; i < count; i++) {
                particles.push(new Particle());
            }
            
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                const grad = ctx.createRadialGradient(
                    canvas.width / 2, canvas.height / 2, 0,
                    canvas.width / 2, canvas.height / 2, Math.max(canvas.width, canvas.height) * 0.8
                );
                grad.addColorStop(0, '#15171e');
                grad.addColorStop(1, '#0f1013');
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                for (let i = 0; i < particles.length; i++) {
                    particles[i].update();
                    particles[i].draw();
                }
                
                for (let i = 0; i < particles.length; i++) {
                    for (let j = i + 1; j < particles.length; j++) {
                        const dx = particles[i].x - particles[j].x;
                        const dy = particles[i].y - particles[j].y;
                        const dist = Math.hypot(dx, dy);
                        
                        if (dist < 115) {
                            let linkAlpha = (115 - dist) / 115 * 0.12;
                            ctx.beginPath();
                            ctx.moveTo(particles[i].x, particles[i].y);
                            ctx.lineTo(particles[j].x, particles[j].y);
                            ctx.strokeStyle = `rgba(224, 169, 109, ${linkAlpha})`;
                            ctx.lineWidth = 0.6;
                            ctx.stroke();
                        }
                    }
                }
                
                requestAnimationFrame(animate);
            }
            
            animate();
        }

        function initCardEffects() {
            const cards = document.querySelectorAll('.stat-card, .chart-card');
            cards.forEach(card => {
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    card.style.setProperty('--x', `${x}px`);
                    card.style.setProperty('--y', `${y}px`);
                    
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const rotateX = -(y - centerY) / centerY * 6.5;
                    const rotateY = (x - centerX) / centerX * 6.5;
                    
                    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.025, 1.025, 1.025)`;
                    card.style.boxShadow = `0 18px 40px rgba(0, 0, 0, 0.5), 0 0 28px rgba(224, 169, 109, 0.09)`;
                });
                
                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
                    card.style.boxShadow = '';
                    card.style.setProperty('--x', '50%');
                    card.style.setProperty('--y', '50%');
                });
            });
        }

        function getScoreClass(score) {
            if (score >= 75) return 'high';
            if (score >= 50) return 'medium';
            if (score >= 30) return 'low';
            return 'poor';
        }

        // 根据类别获取 Badge
        function getCategoryBadge(category) {
            switch (category) {
                case '载具': return '<span class="badge badge-cat-vehicle">🚀 载具</span>';
                case '涂装': return '<span class="badge badge-cat-camo">🎨 涂装</span>';
                case '箱子': return '<span class="badge badge-cat-box">📦 箱子</span>';
                case '道具/挂饰': return '<span class="badge badge-cat-item">🔑 道具</span>';
                case '活动材料': return '<span class="badge badge-cat-mat">⚙️ 材料</span>';
                default: return `<span class="badge badge-cat-other">${category || '其他'}</span>`;
            }
        }

        function getActionBadge(action) {
            switch (action) {
                case 'STRONG_HOLD': return '<span class="badge badge-hold-strong">强力持有</span>';
                case 'HOLD_NEUTRAL': return '<span class="badge badge-hold-neutral">稳健持仓</span>';
                case 'HOLD_DIP': return '<span class="badge badge-hold-dip">低位等待</span>';
                case 'GRADUAL_SELL': return '<span class="badge badge-sell-gradual">建议卖出</span>';
                case 'QUICK_SELL': return '<span class="badge badge-sell-quick">快速套现</span>';
                default: return '<span class="badge">' + action + '</span>';
            }
        }

        function getActionText(action) {
            switch (action) {
                case 'STRONG_HOLD': return '强力持有';
                case 'HOLD_NEUTRAL': return '稳健持仓 稳定持有';
                case 'HOLD_DIP': return '低谷等待 低位等待 抄底';
                case 'GRADUAL_SELL': return '建议卖出 建议分批';
                case 'QUICK_SELL': return '快速套现 即刻变现';
                default: return action || '';
            }
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            const text = document.getElementById('toastText');
            text.innerHTML = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 6000);
        }

        function switchTab(tabName) {
            const tabInv = document.getElementById('tabInventory');
            const tabDiff = document.getElementById('tabDiff');
            const tabHistory = document.getElementById('tabHistorySnap');
            
            const invCard = document.getElementById('inventoryTableCard');
            const diffPanel = document.getElementById('diffPanel');
            const historyPanel = document.getElementById('historySnapPanel');
            
            if (tabName === 'inventory') {
                tabInv.classList.add('active');
                tabDiff.classList.remove('active');
                tabHistory.classList.remove('active');
                
                invCard.style.display = 'block';
                diffPanel.style.display = 'none';
                historyPanel.style.display = 'none';
                
                if (activeSnapshotDate !== null) {
                    activeSnapshotDate = null;
                    activeInventorySource = inventoryData;
                    document.getElementById('snapshot-indicator').style.display = 'none';
                    document.getElementById('snapshot-indicator-tab').style.display = 'none';
                    
                    calculateKPIs();
                    initFilterCounts(inventoryData);
                    filterData();
                    renderPieChart();
                    initHistorySnapPanel(); 
                    initSnapshotDropdown(); 
                    showToast("🕰️ <b>时光回溯已结束</b>，重归当前最新大盘状态！");
                }
            } else if (tabName === 'diff') {
                tabInv.classList.remove('active');
                tabDiff.classList.add('active');
                tabHistory.classList.remove('active');
                
                invCard.style.display = 'none';
                diffPanel.style.display = 'grid';
                historyPanel.style.display = 'none';
            } else if (tabName === 'historySnap') {
                tabInv.classList.remove('active');
                tabDiff.classList.remove('active');
                tabHistory.classList.add('active');
                
                invCard.style.display = 'none';
                diffPanel.style.display = 'none';
                historyPanel.style.display = 'grid';
                
                initHistorySnapPanel();
            }
        }

        function viewHistorySnapshot(dateStr) {
            activeSnapshotDate = dateStr;
            activeInventorySource = historySnapshots[dateStr];
            
            const indicator = document.getElementById('snapshot-indicator');
            if (indicator) indicator.style.display = 'inline';
            
            const indicatorTab = document.getElementById('snapshot-indicator-tab');
            if (indicatorTab) indicatorTab.style.display = 'inline';
            
            calculateKPIs(activeInventorySource);
            initFilterCounts(activeInventorySource);
            filterData();
            renderPieChart(activeInventorySource);
            
            initHistorySnapPanel();
            initSnapshotDropdown();
            switchTab('inventory');
            
            showToast(`🕰️ <b>已进入时光回溯！正在查看 ${dateStr} 的大盘快照！</b><br>顶部卡片与下方数据已切换为历史状态。点击【全市场大盘一览】可切回最新。`);
        }

        function initSnapshotDropdown() {
            const menu = document.getElementById('dropdownMenu');
            if (!menu) return;
            menu.innerHTML = '';
            
            const sortedTrend = [...historyTrendData].reverse();
            
            sortedTrend.forEach((snapshot, idx) => {
                const item = document.createElement('div');
                const isCurrentViewing = (snapshot.date === activeSnapshotDate || (activeSnapshotDate === null && idx === 0));
                
                item.className = 'dropdown-card-item' + (isCurrentViewing ? ' active' : '');
                item.setAttribute('data-date', snapshot.date);
                
                const isLatestToday = (snapshot.date === historyTrendData[historyTrendData.length - 1].date);
                
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:var(--text-muted); font-weight:700;">
                        <span>快照日期: <b style="color:var(--gold);">${snapshot.date}</b></span>
                        ${isLatestToday ? '<span class="badge badge-hold-strong" style="font-size: 8px; padding: 1px 4px; text-transform:none;">最新当前</span>' : '<span style="font-size: 8px; color:var(--text-dark); font-weight:normal;">历史大盘</span>'}
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline; margin-top: 4px;">
                        <span style="font-size: 15px; font-weight: bold; color: var(--text-main);">${snapshot.totalSellValue.toFixed(2)} <span style="font-size:10px; color:var(--text-dark);">GJN</span></span>
                        <span style="font-size: 10px; color: var(--text-muted);">收录: <b style="color:var(--blue);">${snapshot.totalVehicles} 种</b> | 机会: <b style="color:var(--green);">${snapshot.opportunityCount}</b></span>
                    </div>
                `;
                
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onSnapshotSelectChange(snapshot.date);
                    closeDropdown();
                });
                
                menu.appendChild(item);
            });
            
            updateDropdownTriggerText();
        }

        function updateDropdownTriggerText() {
            const triggerVal = document.getElementById('dropdown-current-val');
            if (!triggerVal) return;
            
            const latestDate = historyTrendData[historyTrendData.length - 1].date;
            if (activeSnapshotDate === null) {
                triggerVal.innerText = `最新当前 (${latestDate})`;
            } else {
                triggerVal.innerText = `时光回溯: ${activeSnapshotDate}`;
            }
        }

        function toggleDropdown(event) {
            event.stopPropagation();
            const dropdown = document.getElementById('snapshotDropdown');
            if (!dropdown) return;
            
            if (dropdown.classList.contains('show-menu')) {
                closeDropdown();
            } else {
                dropdown.classList.add('show-menu');
                dropdown.classList.add('active');
            }
        }

        function closeDropdown() {
            const dropdown = document.getElementById('snapshotDropdown');
            if (dropdown) {
                dropdown.classList.remove('show-menu');
                dropdown.classList.remove('active');
            }
        }

        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('snapshotDropdown');
            if (dropdown && !dropdown.contains(e.target)) {
                closeDropdown();
            }
        });

        function onSnapshotSelectChange(dateStr) {
            const latestDate = historyTrendData[historyTrendData.length - 1].date;
            if (dateStr === latestDate) {
                if (activeSnapshotDate !== null) {
                    activeSnapshotDate = null;
                    activeInventorySource = inventoryData;
                    document.getElementById('snapshot-indicator').style.display = 'none';
                    document.getElementById('snapshot-indicator-tab').style.display = 'none';
                    
                    calculateKPIs();
                    initFilterCounts(inventoryData);
                    filterData();
                    renderPieChart();
                    initHistorySnapPanel();
                    initSnapshotDropdown();
                    
                    showToast("🕰️ <b>时光回溯已结束</b>，重归当前最新大盘状态！");
                }
            } else {
                activeSnapshotDate = dateStr;
                activeInventorySource = historySnapshots[dateStr];
                
                const indicator = document.getElementById('snapshot-indicator');
                if (indicator) indicator.style.display = 'inline';
                
                const indicatorTab = document.getElementById('snapshot-indicator-tab');
                if (indicatorTab) indicatorTab.style.display = 'inline';
                
                calculateKPIs(activeInventorySource);
                initFilterCounts(activeInventorySource);
                filterData();
                renderPieChart(activeInventorySource);
                initHistorySnapPanel();
                initSnapshotDropdown();
                
                showToast(`🕰️ <b>已进入时光回溯！正在查看 ${dateStr} 的历史快照！</b>`);
            }
        }

        function initHistorySnapPanel() {
            const panel = document.getElementById('historySnapPanel');
            document.getElementById('tab-history-count').innerText = historyTrendData.length;
            
            panel.innerHTML = '';
            
            if (historyTrendData.length === 0) {
                panel.innerHTML = '<div style="color:var(--text-dark); text-align:center; padding: 40px; font-size:14px; grid-column:span 2;">暂无历史大盘账本</div>';
                return;
            }
            
            const sortedTrend = [...historyTrendData].reverse();
            
            sortedTrend.forEach(snapshot => {
                const card = document.createElement('div');
                card.className = 'stat-card';
                card.style.cursor = 'default';
                
                const isCurrentViewing = (snapshot.date === activeSnapshotDate);
                const isLatestToday = (snapshot.date === historyTrendData[historyTrendData.length - 1].date);
                
                if (isCurrentViewing) {
                    card.style.borderColor = 'var(--gold)';
                    card.style.boxShadow = '0 0 15px rgba(224, 169, 109, 0.25)';
                }
                
                card.innerHTML = `
                    <span class="stat-label" style="font-size: 14px; font-weight: 700; color: var(--gold); display: flex; justify-content: space-between; align-items: center;">
                        快照日期: ${snapshot.date}
                        ${isLatestToday ? '<span class="badge badge-hold-strong" style="font-size: 8px; padding: 2px 6px; text-transform:none;">最新大盘</span>' : ''}
                    </span>
                    <div class="stat-value" style="font-size: 26px; font-weight: 700; margin: 12px 0 6px 0;">
                        ${snapshot.totalSellValue.toFixed(2)} <span style="font-size:12px; color:var(--text-dark);">GJN</span>
                    </div>
                    <div style="font-size: 13px; color: var(--text-muted); display:flex; flex-direction:column; gap:4px; margin-bottom: 12px;">
                        <span>公允总值: <b style="color:var(--gold-light);">${snapshot.totalFairValue ? snapshot.totalFairValue.toFixed(2) : snapshot.totalSellValue.toFixed(2)} GJN</b></span>
                        <span>收录总数: <b style="color:var(--blue);">${snapshot.totalVehicles} 种</b> | 机会: <b style="color:var(--green);">${snapshot.opportunityCount} 种</b></span>
                    </div>
                    <button class="filter-btn active" style="width:100%; justify-content:center; padding: 8px; font-size:12px; ${isCurrentViewing ? 'background: var(--green-bg); color: var(--green); border: 1px solid var(--green);' : ''}"
                            onclick="event.stopPropagation(); viewHistorySnapshot('${snapshot.date}')">
                        🔍 ${isCurrentViewing ? '正在查看此大盘快照' : '查看此历史大盘'}
                    </button>
                `;
                panel.appendChild(card);
            });
            
            initCardEffects();
        }

        function renderPortfolioTrendChart() {
            const container = document.getElementById('trendChartContainer');
            if (trendChartInstance) {
                trendChartInstance.destroy();
                trendChartInstance = null;
            }
            container.innerHTML = '<canvas id="trendChart"></canvas>';
            const ctx = document.getElementById('trendChart').getContext('2d');
            
            document.getElementById('vehicleSelect').style.display = 'none';
            document.getElementById('forecastPanel').style.display = 'none';
            
            const labels = historyTrendData.map(pt => {
                const parts = pt.date.split('-');
                return `${parts[1]}/${parts[2]}`;
            });
            const sellValues = historyTrendData.map(pt => pt.totalSellValue);
            
            const grad = ctx.createLinearGradient(0, 0, 0, 300);
            grad.addColorStop(0, 'rgba(224, 169, 109, 0.28)');
            grad.addColorStop(1, 'rgba(224, 169, 109, 0.00)');
            
            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '全大盘最低估值总额 (GJN)',
                        data: sellValues,
                        borderColor: '#e0a96d',
                        backgroundColor: grad,
                        borderWidth: 2.5,
                        tension: 0.25,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#e0a96d'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1f2937',
                            titleColor: '#e0a96d',
                            bodyColor: '#f3f4f6',
                            borderColor: '#374151',
                            borderWidth: 1,
                            callbacks: {
                                title: function(context) {
                                    const idx = context[0].dataIndex;
                                    return `历史大盘快照: ${historyTrendData[idx].date}`;
                                },
                                label: function(context) {
                                    return ` 大盘挂载总值: ${context.raw.toFixed(2)} GJN`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255, 255, 255, 0.02)' }, ticks: { color: '#9ca3af' } },
                        y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, ticks: { color: '#9ca3af' } }
                    }
                }
            });
        }

        function initDiffPanel() {
            document.getElementById('tab-inventory-count').innerText = inventoryData.length;
            
            const added = inventoryDiff.added || [];
            const removed = inventoryDiff.removed || [];
            
            document.getElementById('tab-diff-added').innerText = added.length;
            document.getElementById('tab-diff-removed').innerText = removed.length;
            
            document.getElementById('diff-added-badge').innerText = `${added.length} 种`;
            document.getElementById('diff-removed-badge').innerText = `${removed.length} 种`;
            
            const addedList = document.getElementById('diffAddedList');
            const removedList = document.getElementById('diffRemovedList');
            
            addedList.innerHTML = '';
            removedList.innerHTML = '';
            
            if (added.length === 0) {
                addedList.innerHTML = `
                    <div style="color: var(--text-dark); text-align: center; padding: 32px 0; font-size: 13px;">
                        与上期对比，未检测到大盘有新增载具上架
                    </div>`;
            } else {
                added.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'diff-item';
                    div.style.cursor = 'pointer';
                    div.addEventListener('click', () => {
                        switchTab('inventory');
                        document.getElementById('searchInput').value = item.name;
                        filterData();
                        highlightTableRow(item.name);
                    });
                    
                    div.innerHTML = `
                        <img src="${item.imageUrl}" style="width: 36px; height: 36px; border-radius: 4px; object-fit: cover; background: #111;" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2236%22 height=%2236%22 viewBox=%220 0 36 36%22><rect width=%2236%22 height=%2236%22 fill=%22%23222%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23666%22 font-size=%228%22>NoImg</text></svg>'">
                        <div class="diff-item-name" title="${item.name}">${item.name}</div>
                        <div style="text-align: right; flex-shrink: 0; min-width: 90px;">
                            <span class="badge badge-hold-strong" style="font-size: 9px; padding: 2px 6px; text-transform: none;">全新上架</span>
                            <div style="font-size: 10px; color: var(--gold); margin-top: 2px;">${item.sellPrice ? item.sellPrice.toFixed(2) + ' G' : '-'}</div>
                        </div>
                    `;
                    addedList.appendChild(div);
                });
            }
            
            if (removed.length === 0) {
                removedList.innerHTML = `
                    <div style="color: var(--text-dark); text-align: center; padding: 32px 0; font-size: 13px;">
                        与上期对比，未发现大盘有载具售罄下架
                    </div>`;
            } else {
                removed.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'diff-item';
                    
                    div.innerHTML = `
                        <img src="${item.imageUrl}" style="width: 36px; height: 36px; border-radius: 4px; object-fit: cover; background: #111;" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2236%22 height=%2236%22 viewBox=%220 0 36 36%22><rect width=%2236%22 height=%2236%22 fill=%22%23222%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23666%22 font-size=%228%22>NoImg</text></svg>'">
                        <div class="diff-item-name" title="${item.name}" style="text-decoration: line-through; color: var(--text-dark);">${item.name}</div>
                        <div style="text-align: right; flex-shrink: 0; min-width: 90px;">
                            <span class="badge badge-sell-quick" style="font-size: 9px; padding: 2px 6px; text-transform: none;">售罄下架</span>
                            <div style="font-size: 10px; color: var(--text-dark); margin-top: 2px;">${item.sellPrice ? item.sellPrice.toFixed(2) + ' G' : '-'}</div>
                        </div>
                    `;
                    removedList.appendChild(div);
                });
            }
        }

        // ==========================================
        // 初始化网页加载
        // ==========================================

        document.addEventListener('DOMContentLoaded', () => {
            if (!inventoryData || inventoryData.length === 0) {
                document.getElementById('emptyState').style.display = 'block';
                return;
            }

            initSnapshotDropdown();
            initParticleBackground();
            initCardEffects();

            calculateKPIs();
            initFilterCounts(inventoryData);
            renderTable(inventoryData);
            populateSelector();
            renderPieChart();
            initDiffPanel();
            initHistorySnapPanel();
            
            if (inventoryData.length > 0) {
                const firstRow = document.querySelector('#tableBody tr');
                if (firstRow) firstRow.classList.add('selected');
                
                const validItem = inventoryData.find(item => item.history && item.history.length > 0);
                if (validItem) {
                    document.getElementById('vehicleSelect').value = validItem.name;
                    currentVehicle = validItem;
                    renderTrendChart(validItem);
                } else {
                    currentVehicle = inventoryData[0];
                    renderTrendChart(inventoryData[0]);
                }
            }

            document.getElementById('searchInput').addEventListener('input', filterData);

            // 监听多维筛选组按钮点击
            ['categoryFilterGroup', 'actionFilterGroup', 'opportunityFilterGroup'].forEach(groupId => {
                const groupEl = document.getElementById(groupId);
                if (groupEl) {
                    groupEl.querySelectorAll('.filter-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const targetBtn = e.target.closest('.filter-btn');
                            if (!targetBtn) return;
                            groupEl.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                            targetBtn.classList.add('active');
                            filterData();
                        });
                    });
                }
            });

            document.getElementById('vehicleSelect').addEventListener('change', (e) => {
                const selectedItem = inventoryData.find(item => item.name === e.target.value);
                if (selectedItem) {
                    currentVehicle = selectedItem;
                    renderTrendChart(selectedItem);
                    highlightTableRow(selectedItem.name, false);
                }
            });

            document.getElementById('timeRangeSelect').addEventListener('change', () => {
                if (document.getElementById('chartTypeSelect').value === 'portfolio') {
                    renderPortfolioTrendChart();
                } else if (currentVehicle) {
                    renderTrendChart(currentVehicle);
                }
            });

            document.getElementById('chartTypeSelect').addEventListener('change', (e) => {
                if (e.target.value === 'portfolio') {
                    renderPortfolioTrendChart();
                } else {
                    document.getElementById('vehicleSelect').style.display = 'inline-block';
                    if (currentVehicle) {
                        renderTrendChart(currentVehicle);
                    }
                }
            });

            showToast("✨ <b>智能多大盘账本已成功载入！</b><br>已为您自动适配跨快照大盘变动比对与增值回溯算法。");
        });

        function calculateKPIs(sourceData = activeInventorySource) {
            let totalVehicles = sourceData.length;
            let totalSellVal = 0;
            let totalFairVal = 0;
            let opportunityCount = 0;
            let scarceCount = 0;
            let crashCount = 0;

            sourceData.forEach(item => {
                const p = item.sellPrice || 0;
                const fair = item.fairPrice || p;
                totalSellVal += p;
                totalFairVal += fair;

                if (item.action === 'STRONG_HOLD' || item.action === 'HOLD_DIP') {
                    opportunityCount++;
                }
                if (item.sellOrders !== undefined && item.sellOrders !== null && item.sellOrders >= 0 && item.sellOrders <= 10) {
                    scarceCount++;
                }
                if (item.lastCrashDrop !== undefined && item.lastCrashDrop !== null && item.lastCrashDrop >= 30) {
                    crashCount++;
                }
            });

            animateValue('total-vehicles', 0, totalVehicles, 1300, 0);
            animateValue('opportunity-count', 0, opportunityCount, 1300, 0);
            animateValue('scarce-count', 0, scarceCount, 1300, 0);
            animateValue('crash-count', 0, crashCount, 1300, 0);
            
            const elSell = document.getElementById('total-sell-val');
            if (elSell) elSell.innerText = totalSellVal.toFixed(1);
            const elFair = document.getElementById('total-fair-val');
            if (elFair) elFair.innerText = totalFairVal.toFixed(1);
        }

        function initFilterCounts(sourceData = activeInventorySource) {
            const catCounts = {
                all: sourceData.length,
                '载具': 0,
                '涂装': 0,
                '箱子': 0,
                '道具/挂饰': 0,
                '活动材料': 0,
                '其他': 0
            };
            const actCounts = {
                all: sourceData.length,
                STRONG_HOLD: 0,
                HOLD_NEUTRAL: 0,
                HOLD_DIP: 0,
                GRADUAL_SELL: 0,
                QUICK_SELL: 0
            };

            sourceData.forEach(item => {
                const cat = item.category || '其他';
                if (catCounts[cat] !== undefined) {
                    catCounts[cat]++;
                } else {
                    catCounts['其他']++;
                }

                const act = item.action || 'HOLD_NEUTRAL';
                if (actCounts[act] !== undefined) {
                    actCounts[act]++;
                }
            });

            const elCatAll = document.getElementById('count-cat-all');
            if (elCatAll) elCatAll.innerText = catCounts.all;
            const elCatVeh = document.getElementById('count-cat-vehicle');
            if (elCatVeh) elCatVeh.innerText = catCounts['载具'];
            const elCatCamo = document.getElementById('count-cat-camo');
            if (elCatCamo) elCatCamo.innerText = catCounts['涂装'];
            const elCatBox = document.getElementById('count-cat-box');
            if (elCatBox) elCatBox.innerText = catCounts['箱子'];
            const elCatItem = document.getElementById('count-cat-item');
            if (elCatItem) elCatItem.innerText = catCounts['道具/挂饰'];
            const elCatMat = document.getElementById('count-cat-mat');
            if (elCatMat) elCatMat.innerText = catCounts['活动材料'];
            const elCatOth = document.getElementById('count-cat-other');
            if (elCatOth) elCatOth.innerText = catCounts['其他'];

            const elActAll = document.getElementById('count-act-all');
            if (elActAll) elActAll.innerText = actCounts.all;
            const elActStr = document.getElementById('count-act-strong');
            if (elActStr) elActStr.innerText = actCounts.STRONG_HOLD;
            const elActNeu = document.getElementById('count-act-neutral');
            if (elActNeu) elActNeu.innerText = actCounts.HOLD_NEUTRAL;
            const elActDip = document.getElementById('count-act-dip');
            if (elActDip) elActDip.innerText = actCounts.HOLD_DIP;
            const elActGra = document.getElementById('count-act-gradual');
            if (elActGra) elActGra.innerText = actCounts.GRADUAL_SELL;
            const elActQui = document.getElementById('count-act-quick');
            if (elActQui) elActQui.innerText = actCounts.QUICK_SELL;
        }

        function filterData() {
            const q = document.getElementById('searchInput').value.trim().toLowerCase();

            const catActiveBtn = document.querySelector('#categoryFilterGroup .filter-btn.active');
            const catFilter = catActiveBtn ? catActiveBtn.getAttribute('data-val') : 'all';

            const actActiveBtn = document.querySelector('#actionFilterGroup .filter-btn.active');
            const actFilter = actActiveBtn ? actActiveBtn.getAttribute('data-val') : 'all';

            const oppActiveBtn = document.querySelector('#opportunityFilterGroup .filter-btn.active');
            const oppFilter = oppActiveBtn ? oppActiveBtn.getAttribute('data-val') : 'all';

            const filtered = activeInventorySource.filter(item => {
                let matchSearch = true;
                if (q) {
                    const name = (item.name || '').toLowerCase();
                    const category = (item.category || '').toLowerCase();
                    const actionName = (getActionText(item.action) || '').toLowerCase();
                    matchSearch = name.includes(q) || category.includes(q) || actionName.includes(q);
                }

                let matchCat = true;
                if (catFilter !== 'all') {
                    matchCat = (item.category === catFilter);
                }

                let matchAct = true;
                if (actFilter !== 'all') {
                    matchAct = (item.action === actFilter);
                }

                let matchOpp = true;
                if (oppFilter === 'dip') {
                    matchOpp = (item.action === 'STRONG_HOLD' || item.action === 'HOLD_DIP');
                } else if (oppFilter === 'scarce') {
                    matchOpp = (item.sellOrders !== undefined && item.sellOrders !== null && item.sellOrders <= 10);
                } else if (oppFilter === 'crash') {
                    matchOpp = (item.lastCrashDrop !== undefined && item.lastCrashDrop >= 30);
                }

                return matchSearch && matchCat && matchAct && matchOpp;
            });

            const tabCountEl = document.getElementById('tab-inventory-count');
            if (tabCountEl) {
                tabCountEl.innerText = filtered.length;
            }

            renderTable(filtered);
        }

        function renderTable(data) {
            const body = document.getElementById('tableBody');
            body.innerHTML = '';

            if (data.length === 0) {
                document.getElementById('emptyState').style.display = 'block';
                return;
            } else {
                document.getElementById('emptyState').style.display = 'none';
            }

            const refDate = activeSnapshotDate || (historyTrendData.length > 0 ? historyTrendData[historyTrendData.length - 1].date : null);

            data.forEach(item => {
                const tr = document.createElement('tr');
                tr.setAttribute('data-name', item.name);
                tr.addEventListener('click', () => {
                    document.querySelectorAll('#tableBody tr').forEach(r => r.classList.remove('selected'));
                    tr.classList.add('selected');
                    document.getElementById('vehicleSelect').value = item.name;
                    currentVehicle = item;
                    if (document.getElementById('chartTypeSelect').value === 'single') {
                        renderTrendChart(item);
                    }
                });

                const hasBuyData = item.buyPrice !== null && item.buyPrice !== undefined && item.buyPrice > 0;
                const spreadText = (hasBuyData && item.spread !== null && item.spread !== undefined) ? (item.spread * 100).toFixed(1) + '%' : '-';
                
                const sellText = item.sellPrice !== null ? item.sellPrice.toFixed(2) : '-';
                const buyText = hasBuyData ? item.buyPrice.toFixed(2) : '-';
                const buyOrdersText = (hasBuyData && item.buyOrders !== undefined && item.buyOrders !== null) ? item.buyOrders : '-';
                
                const score = item.growthScore !== undefined ? Math.round(item.growthScore) : 0;
                const scoreClass = getScoreClass(score);

                const ceilingBadge = item.isNearCeiling ? '<span class="badge badge-sell-gradual" style="font-size: 8px; padding: 1px 4px; margin-left: 4px; text-transform: none;" title="单价接近 2000 GJN 交易所硬顶">顶峰预警</span>' : '';

                let fairText = '';
                if (item.fairPrice && item.sellPrice && item.fairPrice < item.sellPrice * 0.96) {
                    fairText = `<div style="font-size: 9px; color: var(--gold-dark); text-align: right;" title="保守公允估值">公允: ${item.fairPrice.toFixed(1)} G</div>`;
                }

                let firstListedText = '<span style="color: var(--text-dark);">暂无数据</span>';
                if (item.firstListedDays !== undefined && item.firstListedDays >= 0) {
                    firstListedText = `
                        <span>${item.firstListedDate}</span>
                        <div style="font-size: 11px; color: var(--text-dark); margin-top: 2px;">${item.firstListedDays} 天前</div>
                    `;
                }

                let priceModText = '';
                if (item.snapshotGrowthPct !== undefined && item.snapshotPriceHistoryCount >= 2) {
                    const isGrowthPos = item.snapshotGrowthPct > 0;
                    const modCls = isGrowthPos ? 'color-high' : (item.snapshotGrowthPct < 0 ? 'color-poor' : 'color-medium');
                    const sym = isGrowthPos ? '+' : '';
                    priceModText = `
                        <div style="font-size: 10px; margin-top: 4px;">
                            大盘波动: <b class="${modCls}">${sym}${item.snapshotGrowthPct}%</b>
                            <span style="color:var(--text-dark);"> (${item.snapshotPriceHistoryCount}期)</span>
                        </div>
                    `;
                }

                tr.innerHTML = `
                    <td>
                        <div class="item-info">
                            <img class="item-image" src="${item.imageUrl || ''}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2244%22 height=%2244%22 viewBox=%220 0 44 44%22><rect width=%2244%22 height=%2244%22 fill=%22%23222%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23666%22 font-size=%2210%22>NoImg</text></svg>'">
                            <div class="item-details">
                                <span class="item-name">
                                    ${item.name}
                                    ${ceilingBadge}
                                    <a class="market-link" href="${item.url}" target="_blank" onclick="event.stopPropagation();" title="去Gaijin市场查看">
                                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/><path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/></svg>
                                    </a>
                                </span>
                            </div>
                        </div>
                    </td>
                    <td>${getCategoryBadge(item.category)}</td>
                    <td>${firstListedText}</td>
                    <td class="price-col">
                        <span class="price-gjn">${sellText}</span>
                        <div class="price-tax" style="display: flex; gap: 8px; justify-content: space-between; font-size: 10px;">
                            <span>在售: ${item.sellOrders !== undefined ? item.sellOrders : '-'}</span>
                            <span>税后: ${item.sellPrice !== null ? (item.sellPrice * 0.85).toFixed(2) : '-'}</span>
                        </div>
                        ${fairText}
                        ${priceModText}
                    </td>
                    <td class="price-col">
                        <span class="price-gjn" style="color: var(--gold-light);">${buyText}</span>
                        <div class="price-tax">求购: ${buyOrdersText}</div>
                    </td>
                    <td><span style="color: ${hasBuyData && item.spread !== null && item.spread < 0.15 ? 'var(--green)' : 'var(--text-muted)'}">${spreadText}</span></td>
                    <td>
                        <span class="score-value color-${scoreClass}">${score} 分</span>
                        <div class="score-bar-container">
                            <div class="score-bar bg-${scoreClass}" style="width: ${score}%"></div>
                        </div>
                    </td>
                    <td>${getActionBadge(item.action)}</td>
                    <td style="font-family: 'Inter', sans-serif; font-weight: 500;">
                        ${item.suggestedBuyDate === refDate ? '<span class="badge badge-hold-strong" style="font-size: 11px; padding: 2px 6px;">立即抄底</span>' : '<span style="color: var(--green); font-size: 13px;">' + item.suggestedBuyDate + '</span>'}
                    </td>
                    <td style="font-family: 'Inter', sans-serif; font-weight: 500;">
                        ${item.suggestedSellDate === refDate ? '<span class="badge badge-sell-quick" style="font-size: 11px; padding: 2px 6px;">建议现结</span>' : '<span style="color: var(--red); font-size: 13px;">' + item.suggestedSellDate + '</span>'}
                    </td>
                `;
                body.appendChild(tr);
            });
        }

        function populateSelector() {
            const select = document.getElementById('vehicleSelect');
            select.innerHTML = '';
            
            inventoryData.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.name;
                opt.innerText = item.name;
                select.appendChild(opt);
            });
        }

        function highlightTableRow(name, shouldScroll = true) {
            document.querySelectorAll('#tableBody tr').forEach(row => {
                if (row.getAttribute('data-name') === name) {
                    row.classList.add('selected');
                    if (shouldScroll) {
                        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                } else {
                    row.classList.remove('selected');
                }
            });
        }

        function renderPieChart(sourceData = activeInventorySource) {
            const container = document.getElementById('pieChartContainer');
            if (pieChartInstance) {
                pieChartInstance.destroy();
                pieChartInstance = null;
            }
            container.innerHTML = '<canvas id="pieChart"></canvas>';
            const ctx = document.getElementById('pieChart').getContext('2d');
            
            const actions = {
                'STRONG_HOLD': 0,
                'HOLD_NEUTRAL': 0,
                'HOLD_DIP': 0,
                'GRADUAL_SELL': 0,
                'QUICK_SELL': 0
            };
            
            sourceData.forEach(item => {
                if (actions[item.action] !== undefined) {
                    actions[item.action]++;
                }
            });
            
            pieChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['强力持有', '稳健持仓', '低位等待', '建议卖出', '快速套现'],
                    datasets: [{
                        data: [
                            actions['STRONG_HOLD'],
                            actions['HOLD_NEUTRAL'],
                            actions['HOLD_DIP'],
                            actions['GRADUAL_SELL'],
                            actions['QUICK_SELL']
                        ],
                        backgroundColor: [
                            '#4ade80',
                            '#60a5fa',
                            '#fb923c',
                            '#f87171',
                            '#f43f5e'
                        ],
                        borderWidth: 1,
                        borderColor: '#15171e'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#f3f4f6', font: { size: 11 }, boxWidth: 12 }
                        }
                    },
                    cutout: '65%'
                }
            });
        }

        function renderTrendChart(item) {
            const container = document.getElementById('trendChartContainer');
            if (trendChartInstance) {
                trendChartInstance.destroy();
                trendChartInstance = null;
            }
            container.innerHTML = '<canvas id="trendChart"></canvas>';
            const ctx = document.getElementById('trendChart').getContext('2d');
            
            const forecastPanel = document.getElementById('forecastPanel');
            if (forecastPanel) {
                if (!item.history || item.history.length === 0) {
                    forecastPanel.style.display = 'none';
                } else {
                    forecastPanel.style.display = 'grid';
                    
                    const crashDateEl = document.getElementById('crashDate');
                    const crashDropEl = document.getElementById('crashDrop');
                    if (item.lastCrashDate) {
                        crashDateEl.innerText = item.lastCrashDate;
                        if (item.lastCrashDrop > 0) {
                            crashDropEl.innerText = `(-${item.lastCrashDrop}%)`;
                            crashDropEl.style.display = 'inline';
                        } else {
                            crashDropEl.style.display = 'none';
                        }
                    } else {
                        crashDateEl.innerText = '未检测到大跌';
                        crashDropEl.style.display = 'none';
                    }
                    
                    const valleyEventEl = document.getElementById('valleyEvent');
                    const valleyDateEl = document.getElementById('valleyDate');
                    const valleyCountdownEl = document.getElementById('valleyCountdown');
                    
                    if (item.nextValleyEvent) {
                        valleyEventEl.innerText = item.nextValleyEvent;
                        valleyDateEl.innerText = `(${item.nextValleyDate})`;
                        valleyCountdownEl.innerText = `剩余 ${item.nextValleyDays} 天`;
                    } else {
                        valleyEventEl.innerText = '-';
                        valleyDateEl.innerText = '';
                        valleyCountdownEl.innerText = '剩余 - 天';
                    }
                }
            }

            if (!item.history || item.history.length === 0) {
                ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                trendChartInstance = new Chart(ctx, {
                    type: 'line',
                    data: { labels: [], datasets: [] },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: `"${item.name}" 暂无历史交易趋势数据`,
                                color: '#9ca3af',
                                font: { size: 14, weight: 'normal' }
                            }
                        }
                    }
                });
                return;
            }

            const sortedHistory = [...item.history].sort((a, b) => a[0] - b[0]);
            
            let activeHistory = sortedHistory;
            const rangeVal = document.getElementById('timeRangeSelect').value;
            if (rangeVal !== 'all' && sortedHistory.length > 0) {
                const latestTime = sortedHistory[sortedHistory.length - 1][0];
                const days = parseInt(rangeVal, 10);
                const cutoffTime = latestTime - days * 24 * 60 * 60 * 1000;
                let filtered = sortedHistory.filter(pt => pt[0] >= cutoffTime);
                if (filtered.length >= 2) {
                    activeHistory = filtered;
                } else {
                    activeHistory = sortedHistory.slice(-Math.min(2, sortedHistory.length));
                }
            }

            const labels = activeHistory.map(pt => {
                const date = new Date(pt[0]);
                return `${date.getMonth() + 1}/${date.getDate()}`;
            });
            const prices = activeHistory.map(pt => pt[1]);

            const chartGrad = ctx.createLinearGradient(0, 0, 0, 300);
            chartGrad.addColorStop(0, 'rgba(224, 169, 109, 0.26)');
            chartGrad.addColorStop(1, 'rgba(224, 169, 109, 0.00)');

            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '成交价 (GJN)',
                        data: prices,
                        borderColor: '#e0a96d',
                        backgroundColor: chartGrad,
                        borderWidth: 2,
                        tension: 0.15,
                        fill: true,
                        pointRadius: prices.length > 50 ? 0 : 2,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#e0a96d'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1f2937',
                            titleColor: '#e0a96d',
                            bodyColor: '#f3f4f6',
                            borderColor: '#374151',
                            borderWidth: 1,
                            callbacks: {
                                title: function(context) {
                                    const index = context[0].dataIndex;
                                    const date = new Date(activeHistory[index][0]);
                                    return date.toLocaleString();
                                },
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const pt = activeHistory[index];
                                    const volText = (pt && pt.length >= 3 && pt[2] > 0) ? ` | 成交: ${pt[2]} 辆` : '';
                                    return ` 均价: ${context.raw.toFixed(2)} GJN${volText}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255, 255, 255, 0.02)' }, ticks: { color: '#9ca3af', maxTicksLimit: 12 } },
                        y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, ticks: { color: '#9ca3af', callback: function(value) { return value.toFixed(1) + ' G'; } } }
                    }
                }
            });
        }

        function sortTable(colIndex) {
            const table = document.getElementById("inventoryTable");
            
            const headerIndexMap = {
                0: 0,
                9: 1,
                1: 2,
                2: 3,
                3: 4,
                4: 5,
                5: 6,
                6: 7,
                7: 8,
                8: 9
            };
            const headerIdx = headerIndexMap[colIndex];
            const header = table.querySelectorAll("thead th")[headerIdx];

            if (currentSortColumn === colIndex) {
                isSortAsc = !isSortAsc;
            } else {
                currentSortColumn = colIndex;
                isSortAsc = true;
            }

            table.querySelectorAll("thead th").forEach(th => {
                th.classList.remove("sort-asc", "sort-desc");
            });
            if (header) {
                header.classList.add(isSortAsc ? "sort-asc" : "sort-desc");
            }

            activeInventorySource.sort((a, b) => {
                let valA, valB;
                switch (colIndex) {
                    case 0:
                        valA = a.name;
                        valB = b.name;
                        return isSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                    case 9:
                        valA = a.category || '其他';
                        valB = b.category || '其他';
                        return isSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                    case 1:
                        valA = (a.firstListedDays !== undefined && a.firstListedDays >= 0) ? a.firstListedDays : (isSortAsc ? 999999 : -2.0);
                        valB = (b.firstListedDays !== undefined && b.firstListedDays >= 0) ? b.firstListedDays : (isSortAsc ? 999999 : -2.0);
                        break;
                    case 2:
                        valA = a.sellPrice !== null ? a.sellPrice : -1;
                        valB = b.sellPrice !== null ? b.sellPrice : -1;
                        break;
                    case 3:
                        valA = (a.buyPrice !== null && a.buyPrice !== undefined && a.buyPrice > 0) ? a.buyPrice : -1;
                        valB = (b.buyPrice !== null && b.buyPrice !== undefined && b.buyPrice > 0) ? b.buyPrice : -1;
                        break;
                    case 4:
                        valA = (a.buyPrice !== null && a.buyPrice !== undefined && a.buyPrice > 0 && a.spread !== null && a.spread !== undefined) ? a.spread : 999;
                        valB = (b.buyPrice !== null && b.buyPrice !== undefined && b.buyPrice > 0 && b.spread !== null && b.spread !== undefined) ? b.spread : 999;
                        break;
                    case 5:
                        valA = a.growthScore !== undefined ? a.growthScore : -1;
                        valB = b.growthScore !== undefined ? b.growthScore : -1;
                        break;
                    case 6:
                        valA = a.action || '';
                        valB = b.action || '';
                        return isSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                    case 7:
                        valA = a.suggestedBuyDate || "";
                        valB = b.suggestedBuyDate || "";
                        break;
                    case 8:
                        valA = a.suggestedSellDate || "";
                        valB = b.suggestedSellDate || "";
                        break;
                }

                if (valA < valB) return isSortAsc ? -1 : 1;
                if (valA > valB) return isSortAsc ? 1 : -1;
                return 0;
            });

            filterData();
        }
    </script>
</body>
</html>
'''

with open(template_path, "w", encoding="utf-8") as f:
    f.write(REPORT_TEMPLATE_HTML)
print("[成功] 已同步写入: wt-market-analyst/report_template.html")

print("\n==================================================")
print("  所有代码与算法已成功同步至全市场分析业务目录！")
print("==================================================")
