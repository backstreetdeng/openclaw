import os
from tavily import TavilyClient

# 读取.env
env_path = os.path.join('.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key] = val

api_key = os.environ.get('TAVILY_API_KEY')
print(f'API Key: {api_key[:20]}...')

# 尝试获取账户信息
try:
    client = TavilyClient(api_key=api_key)
    result = client.search('test', max_results=1)
    print(f'搜索成功，返回{len(result.get("results", []))}条结果')
    print(f'API额度应该充足')
except Exception as e:
    print(f'错误: {e}')
