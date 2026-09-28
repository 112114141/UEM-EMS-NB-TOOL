@echo off
chcp 65001 >nul
echo ========================================
echo   教务抢课工具 - 打包脚本
echo ========================================
echo.
echo 正在安装 PyInstaller...
pip install pyinstaller -q
echo.
echo 正在打包...
pyinstaller --onefile --windowed --name 教务抢课 main.py
echo.
if exist "dist\教务抢课.exe" (
    echo ========================================
    echo   打包成功！
    echo   exe 文件位于: dist\教务抢课.exe
    echo ========================================
) else (
    echo 打包失败，请检查错误信息
)
echo.
pause