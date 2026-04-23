"""研究政策页面的JSON API可能格式"""
import requests

base_url = "https://www.gov.cn/zhengce/zuixin/"

# 根据要闻的模式推测政策可能的JSON格式
# 要闻: /yaowen/liebiao/ -> /yaowen/liebiao/YAOWENLIEBIAO.json
# 政策: /zhengce/zuixin/ -> ?

test_urls = [
    base_url + "ZHENGCEZUIXIN.json",      # 全大写
    base_url + "zhengcezuixin.json",      # 全小写
    base_url + "Zhengcezuixin.json",     # 首字母大写
    base_url + "ZUIXIN.json",            # 只大写最后部分
    "https://www.gov.cn/zhengce/zuixin/ZHENGCEZUIXIN.json",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://www.gov.cn/',
    'X-Requested-With': 'XMLHttpRequest',
}

for url in test_urls:
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"{url}")
        print(f"  状态: {resp.status_code}, 类型: {resp.headers.get('content-type', 'unknown')[:50]}")
        if resp.status_code == 200 and 'json' in resp.headers.get('content-type', '').lower():
            print(f"  ✅ 找到JSON!")
            print(f"  前100字符: {resp.text[:100]}")
            break
    except Exception as e:
        print(f"  错误: {str(e)[:50]}")
