"""检查eastmoney页面内容"""
import requests
import re

url = "https://finance.eastmoney.com/a/cgnjj.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

resp = requests.get(url, headers=headers, timeout=30)

# 查找所有链接和标题
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', resp.text)

print(f"找到 {len(links)} 个链接\n")
for href, text in links[:20]:
    text = text.strip()
    if text and len(text) > 5:
        print(f"{text[:60]}")
        print(f"  -> {href[:60]}")
