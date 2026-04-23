"""检查政策日期字段类型"""
import requests

url = "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json"
resp = requests.get(url, timeout=30)
data = resp.json()

item = data[0]
print("第一条数据:")
for k, v in item.items():
    print(f"  {k}: type={type(v).__name__}, value={str(v)[:50]}")
