# -*- coding: utf-8 -*-
"""
InEx System v2.0 — 打包脚本
支持三种模式:
    python build.py                 打包为文件夹 (onedir EXE)
    python build.py --installer     打包为文件夹 + 生成 Inno Setup 安装脚本 (.iss)
    python build.py --clean         仅清理构建产物

依赖:
    - PyInstaller >= 5.0 (pip install pyinstaller)
    - UPX (可选，自动检测 H:/UPX/upx.exe)
    - Inno Setup 6+ (可选，仅 --installer 模式需要)
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ── 项目元数据 ──────────────────────────────────────────
PROJECT_NAME = "InEx System"
PROJECT_NAME_SAFE = "InEx_System_v2.0"
VERSION = "2.0"
AUTHOR = "yohoten"
PUBLISHER = "InEx System Team"
APP_ID = "InExSystem.InEx_System.v2.0"
DESCRIPTION = "个人收支管理系统"
COPYRIGHT = f"Copyright (C) 2026 {AUTHOR}"
DEFAULT_ACCOUNT = "2501033401"
DEFAULT_PASSWORD = "admin0457"

# ── 路径常量 ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ICO_PATH = PROJECT_ROOT / "InEx_System.ico"
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
OUTPUT_EXE_DIR = DIST_DIR / PROJECT_NAME_SAFE
OUTPUT_EXE = OUTPUT_EXE_DIR / f"{PROJECT_NAME_SAFE}.exe"
ISS_OUTPUT = PROJECT_ROOT / f"{PROJECT_NAME_SAFE}_installer.iss"

# ── UPX ─────────────────────────────────────────────────
UPX_PATHS = [
    Path("H:/UPX/upx.exe"),
    Path("D:/upx/upx.exe"),
    Path("C:/upx/upx.exe"),
]


def find_upx():
    for p in UPX_PATHS:
        if p.is_file():
            return str(p)
    return shutil.which("upx") or ""


UPX = find_upx()

# ── Python 解释器 ────────────────────────────────────────
PYTHON = str(VENV_DIR / "Scripts" / "python.exe")
if not os.path.exists(PYTHON):
    PYTHON = sys.executable


# ═══════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════

def run(cmd, desc="", check=True):
    """运行命令 — cmd 可传 list 或 str"""
    if desc:
        print(f"  {desc}...")
    if isinstance(cmd, list):
        result = subprocess.run(cmd, capture_output=False, text=True)
    else:
        result = subprocess.run(cmd, capture_output=False, text=True, shell=True)
    if check and result.returncode != 0:
        print(f"  [失败] 返回码: {result.returncode}")
        sys.exit(1)
    return result


def secho(text, level="info"):
    """带图标打印"""
    prefixes = {"info": "  →", "ok": "  ✓", "warn": "  ⚠", "err": "  ✗", "h1": "\n═══"}
    print(f"{prefixes.get(level, '')} {text}")


def get_size_mb(directory):
    """计算目录总大小 (MB)"""
    total = 0
    for f in Path(directory).rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total / (1024 * 1024)


# ═══════════════════════════════════════════════════════════
#  清理
# ═══════════════════════════════════════════════════════════

def clean():
    """清理旧的构建产物"""
    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)
            secho(f"清理目录: {d}", "ok")
    for spec in PROJECT_ROOT.glob("*.spec"):
        spec.unlink()
        secho(f"删除 spec: {spec.name}", "ok")


# ═══════════════════════════════════════════════════════════
#  依赖检查
# ═══════════════════════════════════════════════════════════

def ensure_pyinstaller():
    try:
        import PyInstaller
        secho(f"PyInstaller {PyInstaller.__version__}", "ok")
    except ImportError:
        secho("安装 PyInstaller...", "info")
        run(f'"{PYTHON}" -m pip install pyinstaller>=5.0', "pip install pyinstaller")


def show_upx_status():
    if UPX and Path(UPX).is_file():
        r = subprocess.run([UPX, "--version"], capture_output=True, text=True)
        secho(f"UPX: {r.stdout.strip().split(chr(10))[0]}", "ok")
        return True
    else:
        secho("UPX 未找到 (跳过压缩)", "warn")
        return False


# ═══════════════════════════════════════════════════════════
#  隐藏导入 & 排除模块
# ═══════════════════════════════════════════════════════════

HIDDEN_IMPORTS = [
    # PyQt5
    "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
    # 数据库
    "pymysql", "pymysql.constants", "pymysql.connections", "pymysql.cursors",
    "pyodbc", "sqlanydb", "DBUtils", "DBUtils.pooled_db",
    # 数据处理
    "openpyxl", "pandas", "numpy", "scipy",
    # 可视化
    "matplotlib", "seaborn", "matplotlib.backends.backend_qt5agg",
    # 网络 & 加密
    "requests", "cryptography", "cryptography.fernet", "bcrypt",
    # 其他
    "reportlab", "dateutil", "dateutil.parser",
    "lxml", "lxml.etree",
    # 项目模块
    "ui", "ui.pages", "ui.dialogs", "ui.widgets", "ui.utils", "models", "utils",
]

EXCLUDES = [
    "tkinter", "wx", "test", "tests", "pytest",
    "IPython", "jupyter", "notebook",
    "matplotlib.backends.backend_gtk3agg", "matplotlib.backends.backend_tkagg",
    "numpy.core.tests", "numpy.lib.tests", "numpy.f2py",
    "scipy.tests",
]

DATA_FILES = [
    ("config.json", "."),
    ("InEx_System.ico", "."),
    ("data", "data"),
]
for kf in ["secret.key", "connection.key"]:
    if (PROJECT_ROOT / kf).exists():
        DATA_FILES.append((kf, "."))


# ═══════════════════════════════════════════════════════════
#  PyInstaller 打包 (onedir)
# ═══════════════════════════════════════════════════════════

def build_exe():
    """PyInstaller onedir 打包"""
    print("\n" + "=" * 56)
    print("  InEx System v2.0 — EXE 打包 (onedir)")
    print("=" * 56)

    ensure_pyinstaller()
    upx_ok = show_upx_status()
    clean()

    secho("构建 PyInstaller 命令...", "info")

    cmd = [
        PYTHON, "-m", "PyInstaller",
        f"--name={PROJECT_NAME_SAFE}",
        "--onedir",
        "--windowed",
        f"--icon={ICO_PATH}",
        # 收集
        "--collect-all=pymysql",
        "--collect-all=DBUtils",
        "--collect-all=bcrypt",
    ]

    if upx_ok:
        cmd += [f"--upx-dir={str(Path(UPX).parent)}"]

    for src, dst in DATA_FILES:
        cmd.append(f'--add-data={src};{dst}')
    for imp in HIDDEN_IMPORTS:
        cmd.append(f"--hidden-import={imp}")
    for exc in EXCLUDES:
        cmd.append(f"--exclude-module={exc}")

    cmd.append(str(MAIN_SCRIPT))

    secho("执行 PyInstaller (需 2-4 分钟)...", "info")
    run(cmd, "PyInstaller")

    # 创建启动脚本
    bat = OUTPUT_EXE_DIR / "启动应用.bat"
    bat.write_text(
        '@echo off\r\nchcp 936 >nul\r\n'
        f'title {PROJECT_NAME} v{VERSION}\r\n'
        f'echo 正在启动 {PROJECT_NAME}...\r\n'
        f'start "" "{PROJECT_NAME_SAFE}.exe"\r\n'
        'exit\r\n',
        encoding="gbk"
    )

    return True


# ═══════════════════════════════════════════════════════════
#  Inno Setup 安装包生成
# ═══════════════════════════════════════════════════════════

def generate_iss():
    """生成 Inno Setup .iss 安装脚本"""
    print("\n" + "=" * 56)
    print("  InEx System v2.0 — Inno Setup 安装包")
    print("=" * 56)

    # 先确保 EXE 已打包
    if not OUTPUT_EXE.is_file():
        secho("未找到打包产物，先执行 PyInstaller 打包...", "warn")
        if not build_exe():
            return False

    total_mb = get_size_mb(OUTPUT_EXE_DIR)
    secho(f"打包产物: {total_mb:.1f} MB", "info")

    iss_content = f'''; ── Inno Setup 安装脚本 ─────────────────────────────────
; 由 build.py --installer 自动生成
; 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
; 需要 Inno Setup 6+: https://jrsoftware.org/isinfo.php
; ─────────────────────────────────────────────────────────

#define MyAppName "{PROJECT_NAME}"
#define MyAppVersion "{VERSION}"
#define MyAppPublisher "{PUBLISHER}"
#define MyAppURL "https://github.com/yohoten/InEx_System"
#define MyAppExeName "{PROJECT_NAME_SAFE}.exe"
#define MyAppId "{APP_ID}"
#define MyAppDescription "{DESCRIPTION}"

[Setup]
AppId={{{{{{#MyAppId}}}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
DefaultDirName={{pf}}\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=InEx_System_v{VERSION}_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=InEx_System.ico
UninstallDisplayIcon={{app}}\{PROJECT_NAME_SAFE}.exe
PrivilegesRequiredOverridesAllowed=commandline dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 注意: 请将下方 Source 路径改为实际的打包输出目录
Source: "dist\\{PROJECT_NAME_SAFE}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{PROJECT_NAME}"; Filename: "{{app}}\\{PROJECT_NAME_SAFE}.exe"; WorkingDir: "{{app}}"
Name: "{{group}}\\卸载 {PROJECT_NAME}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{PROJECT_NAME}"; Filename: "{{app}}\\{PROJECT_NAME_SAFE}.exe"; Tasks: desktopicon; WorkingDir: "{{app}}"
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{PROJECT_NAME}"; Filename: "{{app}}\\{PROJECT_NAME_SAFE}.exe"; Tasks: quicklaunchicon; WorkingDir: "{{app}}"

[Run]
Filename: "{{app}}\\{PROJECT_NAME_SAFE}.exe"; Description: "启动 {PROJECT_NAME}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 首次安装提示
  end;
end;
'''

    iss_content = iss_content.replace("{{#{", "{{#{")
    ISS_OUTPUT.write_text(iss_content, encoding="utf-8")
    secho(f"安装脚本已生成: {ISS_OUTPUT.name}", "ok")
    secho(f"安装包体积估计: {total_mb + 15:.0f} MB (含运行时)", "info")

    print(f"""
  ── 下一步操作 ─────────────────────────────────
  1. 下载安装 Inno Setup 6:
     https://jrsoftware.org/isinfo.php

  2. 用 Inno Setup 打开:
     {ISS_OUTPUT}

  3. 点击 Build → Compile (Ctrl+F9)
     生成的安装包位于: dist\\InEx_System_v{VERSION}_Setup.exe

  4. 双击安装包即可安装到 Program Files,
     自动创建桌面快捷方式和开始菜单项.
  ────────────────────────────────────────────────
""")
    return True


# ═══════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════

def main():
    os.chdir(PROJECT_ROOT)

    print(f"Python:  {PYTHON}")
    print(f"项目:    {PROJECT_ROOT}")
    print(f"虚拟环境: {'是' if '.venv' in PYTHON else '否 (系统 Python)'}")

    args = sys.argv[1:]

    if "--clean" in args:
        clean()
        secho("清理完成", "ok")
        return

    if "--installer" in args:
        generate_iss()
        return

    # 默认: EXE 打包
    ok = build_exe()
    if ok:
        total_mb = get_size_mb(OUTPUT_EXE_DIR)
        file_count = sum(1 for _ in OUTPUT_EXE_DIR.rglob("*") if _.is_file())
        print(f"\n{'=' * 56}")
        print(f"  打包完成!")
        print(f"  输出: {OUTPUT_EXE_DIR}")
        print(f"  体积: {total_mb:.1f} MB ({file_count} 个文件)")
        print(f"  启动: {OUTPUT_EXE_DIR / '启动应用.bat'}")
        if UPX and Path(UPX).is_file():
            print(f"  压缩: UPX 已启用")
        print(f"  安装包: python build.py --installer")
        print(f"{'=' * 56}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
