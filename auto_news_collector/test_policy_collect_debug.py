"""调试政策采集"""
import requests
from datetime import datetime

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

keywords = ["消费", "投资", "外贸", "出口", "进口", "民生", "就业", "大市场"]
start_date = datetime(2026, 4, 18)
end_date = datetime(2026, 4, 24)

results = []
for item in data[:100]:  # 只检查前100条
    title = item.get('TITLE', '')
    date_str = item.get('DOCRELPUBTIME', '') or item.get('DOC_REL_PUBTIME', '')
    
    # 解析日期
    pub_date = None
    if date_str:
        try:
            pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except:
            pass
    
    # 关键字匹配
    keyword_match = any(k in title for k in keywords)
    
    # 日期匹配
    date_match = pub_date and (start_date <= pub_date <= end_date)
    
    if keyword_match:
        print(f"关键字匹配: [{date_str}] {pub_date} 日期匹配:{date_match}")
        print(f"  标题: {title[:40]}")
        print()
    
    if len(results) >= 10:
        break

print(f"\n结果数: {len(results)}")
