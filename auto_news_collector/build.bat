@echo off
chcp 65001 >nul
echo ========================================
echo   汽车资讯采集工具 - 打包程序
echo ========================================
echo.

REM 检查PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [错误] PyInstaller未安装，正在安装...
    pip install pyinstaller
)

REM 清理旧文件
echo [1/3] 清理旧文件...
if exist "dist\汽车资讯采集工具" rmdir /s /q "dist\汽车资讯采集工具"
if exist "build" rmdir /s /q "build"
if exist "汽车资讯采集工具.spec" del /q "汽车资讯采集工具.spec"

REM 打包
echo [2/3] 正在打包（请耐心等待，首次可能需要3-5分钟）...
pyinstaller --onefile --windowed --name "汽车资讯采集工具" --add-data="config.py;." --add-data="collector;collector" --add-data="exporter.py;." gui.py

REM 完成
echo [3/3] 打包完成！
echo.
echo ========================================
if exist "dist\汽车资讯采集工具.exe" (
    echo   打包成功！
    echo   文件位置: dist\汽车资讯采集工具.exe
    echo ========================================
    echo.
    echo   正在打开文件夹...
    start explorer dist
) else (
    echo   打包失败，请检查错误信息
    echo ========================================
)
pause
