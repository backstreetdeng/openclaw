"""
汽车产业资讯采集工具 - 主入口
用于PyInstaller打包

打包命令:
pyinstaller --onefile --windowed --name "汽车资讯采集工具" --add-data "config.py;." --add-data "exporter.py;." --add-data "collector;collector" main.py
"""
import sys
import os

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from gui import main
    main()
