"""测试gov.cn JSON API"""
import requests

def get_gov_news():
    """获取中国政府网要闻列表"""
    url = 'https://www.gov.cn/yaowen/liebiao/YAOWENLIEBIAO.json'
    resp = requests.get(url, timeout=30)
    data = resp.json()
    return data

# 使用
news = get_gov_news()
print(f"总共 {len(news)} 条\n")

# 打印前30条
for i, n in enumerate(news[:30], 1):
    print(f"{i}. {n.get('TITLE', '')}")
    print(f"   {n.get('URL', '')}")
