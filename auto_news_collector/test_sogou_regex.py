import requests
import re

def test_both():
    queries = ["小米SU7", "探境者01"]
    
    for query in queries:
        print(f"\n=== 测试: {query} ===")
        url = f"https://www.sogou.com/web?query={requests.utils.quote(query)}+上市+官方"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.sogou.com/",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        
        # 检查是否有"摘要开始"
        if "<!--摘要开始-->" in resp.text:
            print("有 <!--摘要开始--> 标记")
            snippet_match = re.search(r'<!--摘要开始-->([^<]+)<!--摘要结束-->', resp.text)
            if snippet_match:
                print(f"摘要: {snippet_match.group(1)[:100]}")
        else:
            print("没有 <!--摘要开始--> 标记")
        
        # 检查是否有vr-title
        h3_count = len(re.findall(r'class="vr-title', resp.text))
        print(f"vr-title数量: {h3_count}")
        
        # 检查有多少个链接
        all_links = re.findall(r'href="(https?://[^"]+)"', resp.text)
        print(f"完整https链接数: {len([l for l in all_links if l.startswith('http')])}")
        
        # 看看有没有.baidu.com或.qq.com等常见域名
        for domain in ['baidu.com', 'qq.com', 'sina.com', 'sohu.com', 'ifeng.com']:
            count = len([l for l in all_links if domain in l])
            if count > 0:
                print(f"  {domain}链接: {count}")

test_both()
