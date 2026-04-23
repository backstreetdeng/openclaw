from config import DOMAINS
for name, cfg in DOMAINS.items():
    print(f'领域: {name}')
    print(f'  urls: {len(cfg.get("urls", []))}')
    print(f'  sub_domains: {list(cfg.get("sub_domains", {}).keys())}')
    print()