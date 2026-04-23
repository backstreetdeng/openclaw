"""
微信公众号文章解析器
使用 Agent Browser 渲染 + BeautifulSoup 解析微信文章
依赖: pip install beautifulsoup4 lxml
"""
import subprocess
import json
import re
import sys
from pathlib import Path

def run_agent_cmd(cmd):
    """执行 agent-browser 命令"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        encoding='utf-8', errors='replace'
    )
    return result.stdout.strip(), result.stderr.strip()

def extract_article_info(snapshot_text):
    """从 agent-browser snapshot 文本中提取文章信息"""
    lines = snapshot_text.split('\n')
    info = {
        'title': '',
        'source': '',
        'datetime': '',
        'content': []
    }

    current_paragraph = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_paragraph:
                text = ' '.join(current_paragraph)
                if text and not text.startswith('来源：') and not text.startswith('http'):
                    info['content'].append(text)
                current_paragraph = []
            continue

        # 标题行
        if line.startswith('heading') or (line.startswith('「') and '」' in line):
            if not info['title']:
                title_match = re.search(r'「([^」]+)」', line)
                if title_match:
                    info['title'] = title_match.group(1)
                else:
                    title_match = re.search(r'[\"\'](.*?)[\"\']', line)
                    if title_match:
                        info['title'] = title_match.group(1)

        # 来源
        if 'link' in line and ('盛景' in line or '汽车' in line or '日报' in line):
            source_match = re.search(r'link "([^"]+)"', line)
            if source_match and not info['source']:
                info['source'] = source_match.group(1)

        # 日期时间
        if 'emphasis' in line:
            date_match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', line)
            if date_match and not info['datetime']:
                info['datetime'] = date_match.group(0)

        # 正文段落
        if line.startswith('paragraph') or line.startswith('- text'):
            text = re.sub(r'^\S+\s*', '', line)
            if text and len(text) > 5:
                current_paragraph.append(text)

    if current_paragraph:
        text = ' '.join(current_paragraph)
        if text:
            info['content'].append(text)

    return info

def fetch_wechat_article(url):
    """使用 Agent Browser 获取并解析微信文章"""
    print(f"正在打开: {url}")

    stdout, stderr = run_agent_cmd(f'agent-browser open "{url}"')
    if 'error' in stderr.lower() and '✓' not in stdout:
        return {'error': f'打开页面失败: {stderr}'}

    run_agent_cmd('agent-browser wait 2000')
    snapshot_out, _ = run_agent_cmd('agent-browser snapshot -c')

    if not snapshot_out or 'Empty page' in snapshot_out:
        return {'error': '页面为空，可能需要登录或URL失效'}

    article_info = extract_article_info(snapshot_out)

    if not article_info['title']:
        title_match = re.search(r'heading "([^"]+)"', snapshot_out)
        if title_match:
            article_info['title'] = title_match.group(1)

    return article_info

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python wechat_article_parser.py <微信文章URL>")
        sys.exit(1)

    url = sys.argv[1]
    result = fetch_wechat_article(url)

    print("\n=== 解析结果 ===")
    print(f"标题: {result.get('title', 'N/A')}")
    print(f"来源: {result.get('source', 'N/A')}")
    print(f"时间: {result.get('datetime', 'N/A')}")
    print(f"正文段落数: {len(result.get('content', []))}")
    for i, p in enumerate(result['content'][:5], 1):
        print(f"  [{i}] {p[:80]}...")
