import requests
import re

def duckduckgo_search(query: str) -> tuple:
    """用DuckDuckGo搜索获取新闻摘要（不需要API key）"""
    try:
        url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}+上市+官方"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应长度: {len(resp.text)}")
        
        # 用正则提取第一个结果的摘要和链接
        snippet_match = re.search(r'class="result__snippet">([^<]+)', resp.text)
        link_match = re.search(r'class="result__a" href="([^"]+)"', resp.text)
        
        if snippet_match:
            text = snippet_match.group(1).strip()
            text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
            href = link_match.group(1) if link_match else ""
            print(f"\n摘要: {text[:200]}")
            print(f"链接: {href}")
            return text, href
        else:
            print("未找到结果")
            print(f"页面前500字符: {resp.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    return "", ""

# 测试
print("=== 测试 DuckDuckGo 搜索 ===")
content, link = duckduckgo_search("小米SU7 上市")
