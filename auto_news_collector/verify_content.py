"""
校验9条新闻正文完整性
"""
import requests
import re

def clean_content(content):
    """清理正文"""
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'\s+', ' ', content)
    return content.strip()

def fetch_full_content(url):
    """获取完整正文"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        # 提取ArticleContent
        match = re.search(r'<div[^>]*id=["\']ArticleContent["\'][^>]*>(.*?)</div>', html, re.DOTALL)
        if match:
            return clean_content(match.group(1))
    except:
        pass
    return ""

news_list = [
    ("北斗智联与地平线达成战略合作", "https://auto.gasgoo.com/news/202604/22I70454728C103.shtml"),
    ("麦迪克智行完成数千万元Pre-A轮融资", "https://auto.gasgoo.com/news/202604/22I70454727C103.shtml"),
    ("地平线与北斗智联、博泰车联合作", "https://auto.gasgoo.com/news/202604/22I70454721C601.shtml"),
    ("港股HUD第一股的向上之路", "https://auto.gasgoo.com/news/202604/22I70454572C601.shtml"),
    ("这款国产芯片要做800V时代安全基石", "https://auto.gasgoo.com/news/202604/22I70454706C601.shtml"),
    ("纳芯微推出ASIL D等级隔离栅极驱动", "https://auto.gasgoo.com/news/202604/22I70454705C103.shtml"),
    # 第7条跳过（纯图片）
    ("芯擎科技青岛子公司建成运营", "https://auto.gasgoo.com/news/202604/22I70454703C601.shtml"),
    ("中科创达2025年业绩亮眼", "https://auto.gasgoo.com/news/202604/22I70454698C601.shtml"),
    ("德赛西威与长安汽车签署全球战略协同伙伴协议", "https://auto.gasgoo.com/news/202604/22I70454697C601.shtml"),
]

print("="*70)
print("校验新闻正文完整性")
print("="*70)

for i, (title, url) in enumerate(news_list, 1):
    print(f"\n{i}. {title}")
    print("-"*60)
    
    content = fetch_full_content(url)
    length = len(content)
    
    # 判断完整性
    if length < 100:
        status = "❌ 太短，可能失败"
    elif content.endswith('...') or '...' in content[-50:]:
        status = "⚠️ 可能被截断"
    elif length > 5000:
        status = "✅ 完整（较长）"
    else:
        status = "✅ 完整"
    
    print(f"字符数: {length}")
    print(f"状态: {status}")
    print(f"结尾: ...{content[-80:] if len(content) > 80 else content}...")
    
    # 简单检查是否有版权声明（正常文章的标志）
    if '版权' in content or '盖世汽车' in content or '原创' in content:
        print("✓ 包含正常结尾标记")
