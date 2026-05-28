import json
import os
import shutil

def main():
    print("=" * 50)
    print("        Gaijin 市场仓库测试数据生成器 (v3.2)")
    print("=" * 50)
    
    src_file = "gaijin_inventory_2026-05-22.json"
    dest_file = "gaijin_inventory_2026-05-25.json"
    earliest_file = "gaijin_inventory_2026-05-20.json"
    
    if not os.path.exists(src_file):
        print(f"[错误] 未找到源文件: {src_file}")
        return
        
    print(f"[信息] 正在读取原始 5-22 数据: {src_file}")
    with open(src_file, 'r', encoding='utf-8') as f:
        prev_data = json.load(f)
        
    # ====================================================
    # A. 模拟生成最早期 5-20 数据（总市值较小，持仓数量较少）
    # ====================================================
    print(f"[最早期模拟] 正在构建 5-20 早期资产快照...")
    earliest_data = json.loads(json.dumps(prev_data))
    
    # 过滤掉约三分之一的物品以模拟极早期仓位规模
    earliest_data = earliest_data[:25] # 只保留前25个物品
    for idx, item in enumerate(earliest_data):
        item['quantity'] = 1 # 统一缩减为 1 个
        # 市值也稍微缩水一点点以模拟上升通道
        if item.get('sellPrice'):
            item['sellPrice'] = round(item['sellPrice'] * 0.85, 2)
            
    print(f"[最早期模拟] 5-20 模拟仓位品种数: {len(earliest_data)} 种")
    
    # ====================================================
    # B. 模拟生成最新 5-25 数据（加仓/减仓/新增）
    # ====================================================
    latest_data = json.loads(json.dumps(prev_data))
    
    # 1. 模拟减仓变动：
    item_to_reduce = None
    for item in prev_data:
        if item['name'] != "279 工程（苏联）":
            item_to_reduce = item
            break
            
    if item_to_reduce:
        name_reduce = item_to_reduce['name']
        # 强制让次新版本(5-22)里的持有数量为 3 个
        for item in prev_data:
            if item['name'] == name_reduce:
                item['quantity'] = 3
        # 强制让最新版本(5-25)里的持有数量为 1 个（相当于卖出了 2 个，触发减仓）
        for item in latest_data:
            if item['name'] == name_reduce:
                item['quantity'] = 1
        print(f"[数量模拟] 减仓模拟载具: {name_reduce} (5-22 持有 3 个 -> 5-25 持有 1 个)")
        
    # 2. 模拟加仓变动：
    item_to_add = None
    for item in prev_data:
        if item['name'] != "279 工程（苏联）" and item['name'] != name_reduce:
            item_to_add = item
            break
            
    if item_to_add:
        name_add = item_to_add['name']
        # 强制让次新版本(5-22)里的持有数量为 1 个
        for item in prev_data:
            if item['name'] == name_add:
                item['quantity'] = 1
        # 强制让最新版本(5-25)里的持有数量为 4 个（相当于加仓买入了 3 个，触发加仓）
        for item in latest_data:
            if item['name'] == name_add:
                item['quantity'] = 4
        print(f"[数量模拟] 加仓模拟载具: {name_add} (5-22 持有 1 个 -> 5-25 持有 4 个)")
        
    # 3. 模拟纯卖空 (清仓)：
    latest_data = [item for item in latest_data if item['name'] != "279 工程（苏联）"]
    print("[数量模拟] 清仓模拟载具: 279 工程（苏联） (最新 5-25 完全清仓)")
    
    # 4. 模拟纯新增：
    new_item = {
        "name": "IS-7 重型坦克 (测试纯新增)",
        "url": "https://trade.gaijin.net/market/1067/IS-7%20(USSR)",
        "imageUrl": "https://static-ggc.gaijin.net/units/ussr_is_7.png",
        "quantity": 1,
        "sellPrice": 2000.0,
        "sellOrders": 2,
        "buyPrice": 1850.0,
        "buyOrders": 120,
        "history": [
            [1716300000000, 1600.0],
            [1716386400000, 1650.0]
        ],
        "scrapedAt": "2026-05-25T13:00:00Z"
    }
    latest_data.append(new_item)
    print(f"[数量模拟] 纯新增模拟载具: {new_item['name']} (纯新收录 1 个)")
    
    # 保存覆盖 dest_file (5-25)
    print(f"[信息] 正在保存最新 5-25 数据: {dest_file}")
    with open(dest_file, 'w', encoding='utf-8') as f:
        json.dump(latest_data, f, ensure_ascii=False, indent=4)
        
    # 保存重写的 src_file (5-22) 模拟多持仓
    print(f"[信息] 正在重写 5-22 历史数据: {src_file}")
    with open(src_file, 'w', encoding='utf-8') as f:
        json.dump(prev_data, f, ensure_ascii=False, indent=4)
        
    # 保存最早期 file (5-20)
    print(f"[信息] 正在保存早期 5-20 数据: {earliest_file}")
    with open(earliest_file, 'w', encoding='utf-8') as f:
        json.dump(earliest_data, f, ensure_ascii=False, indent=4)
        
    print("=" * 50)
    print("[成功] v3.2 长期历史快照 (5-20、5-22、5-25) 测试用例全部生成完毕！")
    print("现在可执行 python analyze.py 重新比对分析历史趋势。")
    print("=" * 50)

if __name__ == "__main__":
    main()
