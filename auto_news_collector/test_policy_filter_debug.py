"""调试政策过滤"""
import requests
from datetime import datetime

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

keywords = ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

print(f"日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
print(f"关键字: {keywords}\n")

count_total = 0
count_date_ok = 0
count_keyword_ok = 0

for item in data:
    title = item.get('TITLE', '')
    date_str = item.get('DOC_REL_PUBTIME', '')
    
    count_total += 1
    
    # 解析日期
    pub_date = None
    if date_str:
        try:
            pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except:
            pass
    
    # 检查日期
    if pub_date and (start_date <= pub_date <= end_date):
        count_date_ok += 1
    
    # 检查关键字
    if any(k in title for k in keywords):
        count_keyword_ok += 1
        print(f"匹配关键字: [{date_str}] {title[:50]}")

print(f"\n总条数: {count_total}")
print(f"日期符合: {count_date_ok}")
print(f"关键字符合: {count_keyword_ok}")
