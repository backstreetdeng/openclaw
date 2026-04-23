"""检查eastmoney国内经济页面"""
import requests

url = "https://finance.eastmoney.com/a/cgnjj.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

resp = requests.get(url, headers=headers, timeout=30)
print(f"长度: {len(resp.text)}")

# 搜索关键字
text = resp.text
print(f"包含'工信部': {'工信部' in text}")
print(f"包含'七部门': {'七部门' in text}")
print(f"包含'两新': {'两新' in text}")
print(f"包含'石化化工': {'石化化工' in text}")
