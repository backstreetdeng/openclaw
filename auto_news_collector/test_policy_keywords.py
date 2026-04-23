"""测试政策的关键字过滤"""
import requests
from datetime import datetime

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

keywords = ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

print(f"政策总共 {len(data)} 条")

count = 0
for item in data[:50]:  # 检查前50条
    title = item.get('TITLE', '')
    date_str = item.get('DOC_REL_PUBTIME', '')
    
    # 检查日期
    pub_date = None
    if date_str:
        try:
            pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except:
            pass
    
    # 日期范围检查
    if pub_date and not (start_date <= pub_date <= end_date):
        continue
    
    # 关键字检查
    if any(k in title for k in keywords):
        count += 1
        if count <= 5:
            print(f"{count}. [{date_str}] {title[:50]}")

print(f"\n符合条件: {count} 条")
