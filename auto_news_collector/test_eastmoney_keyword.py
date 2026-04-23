"""检查eastmoney是否包含目标新闻"""
import requests

url = "https://finance.eastmoney.com/a/cgnjj.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

resp = requests.get(url, headers=headers, timeout=30)
print(f"状态: {resp.status_code}, 长度: {len(resp.text)}")

# 检查关键字
if "工信部" in resp.text:
    print("✅ 包含'工信部'")
    # 找到包含的上下文
    idx = resp.text.find("工信部")
    print(f"上下文: {resp.text[max(0,idx-50):idx+100]}")
else:
    print("❌ 不包含'工信部'")

if "七部门" in resp.text:
    print("✅ 包含'七部门'")
else:
    print("❌ 不包含'七部门'")
