@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
title InEx System v2.0

:: ============================================================
::  InEx System v2.0 - Startup Script
::  Author : yohoten (S-ID: 12607320270457)
::  Usage  :
::    InEx_System_Launcher.bat             正常启动
::    InEx_System_Launcher.bat /fast       跳过检查, 直接启动
::    InEx_System_Launcher.bat /install    仅安装/更新依赖
:: ============================================================

:: ---- 命令行参数 ------------------------------------------
set "FAST_MODE="
set "INSTALL_ONLY="
for %%a in (%*) do (
    if /i "%%a"=="/fast"     set "FAST_MODE=1"
    if /i "%%a"=="/skip"     set "FAST_MODE=1"
    if /i "%%a"=="/install"  set "INSTALL_ONLY=1"
)

:: ---- 路径 ------------------------------------------------
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "DATA_DIR=%PROJECT_DIR%\data"
set "LOGS_DIR=%PROJECT_DIR%\logs"
set "REQUIREMENTS=%PROJECT_DIR%\requirements.txt"

cd /d "%PROJECT_DIR%"

:: ============================================================
:: 激活虚拟环境 (优先 .venv, 其次 venv, 最后系统 Python)
:: ============================================================
if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_ok
if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    set "VENV_DIR=%PROJECT_DIR%\venv"
    goto :venv_ok
)

:: 未找到虚拟环境
echo.
echo   [警告] 未找到虚拟环境 (.venv\)
echo   请先运行: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
echo.
pause
exit /b 1

:venv_ok
call "%VENV_DIR%\Scripts\activate.bat" >nul 2>&1
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

:: ---- 快速模式 ------------------------------------------
if defined FAST_MODE goto :launch

:: ---- 仅安装依赖 ------------------------------------------
if defined INSTALL_ONLY goto :install

:: ============================================================
echo.
echo   ================================================
echo         InEx System v2.0
echo         Python: %VENV_DIR%
echo   ================================================
echo.

:: ---- 确保必要目录存在 ----------------------------------
for %%d in ("%DATA_DIR%" "%LOGS_DIR%") do (
    if not exist %%d mkdir %%d >nul 2>&1
)

:: ---- 检查密钥文件 --------------------------------------
if not exist "%PROJECT_DIR%\secret.key" (
    echo   [提示] secret.key 未找到, 首次运行将自动生成
)
if not exist "%PROJECT_DIR%\connection.key" (
    echo   [提示] connection.key 未找到, 首次运行将自动生成
)

:: ---- 快速检查核心依赖 ----------------------------------
set "MISSING="
for %%p in (PyQt5 cryptography bcrypt) do (
    "%PYTHON_EXE%" -c "import %%p" >nul 2>&1
    if errorlevel 1 set "MISSING=!MISSING! %%p"
)

if defined MISSING (
    echo   [警告] 缺少依赖:%MISSING%
    echo.
    echo   正在自动安装...
    call :install
    if errorlevel 1 (
        echo   安装失败, 请手动执行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

goto :launch

:: ============================================================
::  安装依赖
:: ============================================================
:install
echo   [安装] 从 requirements.txt 安装依赖 (清华镜像)...
"%PIP_EXE%" install -r "%REQUIREMENTS%" -i https://pypi.tuna.tsinghua.edu.cn/simple --disable-pip-version-check
if errorlevel 1 (
    echo   [错误] 安装失败, 尝试默认源...
    "%PIP_EXE%" install -r "%REQUIREMENTS%" --disable-pip-version-check
)
echo   [完成]
if defined INSTALL_ONLY pause
goto :EOF

:: ============================================================
::  启动
:: ============================================================
:launch
echo   启动中...
"%PYTHON_EXE%" main.py
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% neq 0 (
    echo.
    echo   [错误] 程序异常退出 (错误码: %EXIT_CODE%)
    if %EXIT_CODE% equ -1073741510 (
        echo   缺少 Visual C++ Redistributable
        echo   下载: https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
    echo   详见 logs\ 目录中的日志文件
    pause
)

endlocal
exit /b %EXIT_CODE%