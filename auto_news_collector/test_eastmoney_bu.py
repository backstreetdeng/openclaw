"""检查eastmoney页面中包含'部'的内容"""
import requests

url = "https://finance.eastmoney.com/a/cgnjj.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

resp = requests.get(url, headers=headers, timeout=30)

# 查找包含"部"的中文文本
import re
# 匹配中文文本中包含"部"的
pattern = r'[\u4e00-\u9fa5]{2,20}部[\u4e00-\u9fa5]{0,20}'
matches = re.findall(pattern, resp.text)

print(f"包含'部'的词组 ({len(matches)} 个):")
for m in matches[:30]:
    print(f"  {m}")
