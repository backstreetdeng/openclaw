"""用requests测试eastmoney"""
import requests

url = "https://finance.eastmoney.com/a/cgnjj.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"状态: {resp.status_code}")
    print(f"长度: {len(resp.text)}")
    if "工信部" in resp.text:
        print("✅ 找到'工信部'")
    if "七部门" in resp.text:
        print("✅ 找到'七部门'")
except Exception as e:
    print(f"错误: {e}")
