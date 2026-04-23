"""直接访问eastmoney"""
import requests

# 直接访问主页
url = "https://finance.eastmoney.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.eastmoney.com/'
}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"主页状态: {resp.status_code}, 长度: {len(resp.text)}")
except Exception as e:
    print(f"主页访问失败: {e}")

# 访问国内经济页面
url2 = "https://finance.eastmoney.com/a/cgnjj.html"
try:
    resp = requests.get(url2, headers=headers, timeout=30)
    print(f"国内经济页面状态: {resp.status_code}, 长度: {len(resp.text)}")
    if "工信部" in resp.text:
        print("✅ 包含'工信部'")
except Exception as e:
    print(f"国内经济页面访问失败: {e}")
