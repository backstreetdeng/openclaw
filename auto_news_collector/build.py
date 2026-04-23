"""
打包脚本 - 生成exe文件
运行方式: python build.py
"""
import os
import sys
import subprocess


def build_exe():
    """构建exe文件"""

    print("=" * 60)
    print("汽车产业资讯采集工具 - 打包程序")
    print("=" * 60)

    # 检查依赖
    print("\n[1/4] 检查依赖...")
    try:
        import PyQt5
        import docx
        import requests
        import bs4
        print("  ✅ Python依赖检查通过")
    except ImportError as e:
        print(f"  ❌ 缺少依赖: {e}")
        print("  请先运行: pip install -r requirements.txt")
        return False

    # 安装依赖
    print("\n[2/4] 安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])

    # 安装Playwright浏览器
    print("\n[3/4] 安装Playwright浏览器...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("  ✅ Chromium安装成功")
    except Exception as e:
        print(f"  ⚠️ Playwright浏览器安装失败: {e}")
        print("  将使用requests备用采集方式")

    # 打包exe
    print("\n[4/4] 打包exe文件...")
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                    # 单文件
        "--windowed",                   # 无控制台窗口
        "--name", "汽车资讯采集工具",    # 输出文件名
        "--icon=NONE",                  # 无图标（可替换为.ico文件）
        "--add-data", "config.py;.",    # 添加配置文件
        "--add-data", "exporter.py;.",  # 添加导出模块
        "--add-data", "collector;collector",  # 添加采集器模块
        "--hidden-import", "PyQt5",
        "--hidden-import", "docx",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "--hidden-import", "lxml",
        "--hidden-import", "playwright",
        "--hidden-import", "APScheduler",
        "main.py"
    ]

    try:
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ 打包成功!")
            print(f"\n输出目录: {os.path.join(os.getcwd(), 'dist')}")
            return True
        else:
            print(f"  ❌ 打包失败: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ❌ PyInstaller未安装")
        print("  请先运行: pip install pyinstaller")
        return False


if __name__ == "__main__":
    success = build_exe()
    if success:
        print("\n" + "=" * 60)
        print("🎉 打包完成！请在dist目录中找到 【汽车资讯采集工具.exe】")
        print("=" * 60)
    else:
        print("\n打包失败，请检查错误信息")
