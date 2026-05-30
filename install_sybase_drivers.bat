@echo off
chcp 936 >nul
echo ============================================================
echo        Sybase SQL Anywhere 9 数据库驱动安装向导
echo ============================================================
echo.
echo 请选择要安装的驱动：
echo.
echo 1. 安装 sqlanydb (推荐 - Sybase 官方驱动)
echo 2. 安装 pyodbc (备用 - ODBC 通用驱动)
echo 3. 安装两者
echo 4. 退出
echo.
set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo [1/1] 正在安装 sqlanydb...
    pip install sqlanydb
    echo.
    echo [OK] sqlanydb 安装完成！
    pause
) else if "%choice%"=="2" (
    echo.
    echo [1/1] 正在安装 pyodbc...
    pip install pyodbc
    echo.
    echo [OK] pyodbc 安装完成！
    echo.
    echo [!] 注意：还需要安装 SQL Anywhere 9 ODBC 驱动
    echo    请确保已安装 SQL Anywhere 9 客户端
    pause
) else if "%choice%"=="3" (
    echo.
    echo [1/2] 正在安装 sqlanydb...
    pip install sqlanydb
    echo.
    echo [2/2] 正在安装 pyodbc...
    pip install pyodbc
    echo.
    echo [OK] 所有驱动安装完成！
    pause
) else if "%choice%"=="4" (
    echo.
    echo 退出安装向导
    pause
) else (
    echo.
    echo [ERROR] 无效选项
    pause
)
