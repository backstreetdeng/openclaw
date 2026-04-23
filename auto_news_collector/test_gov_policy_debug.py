"""调试政策JSON解析"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

print(f"政策JSON返回 {len(data)} 条")
print(f"第一条数据:")
for k, v in data[0].items():
    print(f"  {k}: {str(v)[:80]}")
