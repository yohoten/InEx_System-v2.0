# UPX 压缩工具安装与配置指南

## 什么是 UPX?

**UPX (Ultimate Packer for eXecutables)** 是一个开源的可执行文件压缩工具,可以将PyInstaller打包后的exe文件体积减少 **50-70%**,同时保持完全兼容性。

### 压缩效果对比

| 项目 | 未压缩 | UPX压缩 | 减少比例 |
|------|--------|---------|----------|
| InEx System v2.0 | ~180 MB | ~60-90 MB | **50-70%** |
| 启动速度 | 正常 | 略慢(首次解压) | - |
| 内存占用 | 正常 | 略高(运行时解压) | - |

## 安装步骤

### 方法1: 官方下载(推荐)

1. **访问官网**: https://github.com/upx/upx/releases
2. **下载最新版本**: 选择 `upx-X.X.X-win64.zip` (Windows 64位)
3. **解压到固定路径**: 
   ```
   推荐路径: C:\upx\upx.exe
   或: D:\upx\upx.exe
   ```
4. **验证安装**:
   ```bash
   C:\upx\upx.exe --version
   ```

### 方法2: 使用 Chocolatey (Windows包管理器)

```bash
choco install upx
```

### 方法3: 使用 Scoop (Windows包管理器)

```bash
scoop install upx
```

## 配置 build.py

### 自动检测(已实现)

当前 `build.py` 已支持自动检测以下路径:
- ✅ `C:\Program Files\upx\upx.exe`
- ✅ `C:\upx\upx.exe`
- ✅ `D:\upx\upx.exe`
- ✅ `E:\upx\upx.exe`
- ✅ `%USERPROFILE%\upx\upx.exe`
- ✅ PATH环境变量中的upx

### 手动配置

如果UPX安装在其他位置,修改 `build.py` 第14行:

```python
# 修改前
UPX_PATH = find_upx() or r"H:/UPX/upx.exe"

# 修改为你的实际路径
UPX_PATH = find_upx() or r"D:\Tools\upx\upx.exe"
```

## 使用 UPX 打包

### 启用UPX压缩

```bash
py -3.9 build.py
```

脚本会自动:
1. 检测UPX是否可用
2. 如果可用,使用 `--upx-dir` 参数传递给PyInstaller
3. 应用最佳压缩参数: `--best --lzma`

### 禁用UPX(临时)

如果不想使用UPX,可以:
1. 重命名UPX可执行文件
2. 或修改 `build.py` 设置 `UPX_PATH = None`

## 常见问题

### Q1: UPX压缩后程序无法运行?

**原因**: 某些Python扩展模块与UPX不兼容。

**解决方案**:
```python
# 在 build.py 的 PyInstaller 命令中添加排除
--exclude-module=some_problematic_module
```

### Q2: 压缩率不高?

**原因**: Python打包后的文件包含大量已压缩的资源(如图片、字体)。

**优化建议**:
1. 移除不必要的依赖库
2. 使用 `--exclude-module` 排除未使用的模块
3. 清理 `__pycache__` 和 `.pyc` 文件

### Q3: 启动速度变慢?

**说明**: UPX压缩的程序首次启动时需要解压,会略慢1-2秒。

**权衡**: 
- ✅ 优点: 磁盘空间节省50-70%
- ⚠️ 缺点: 首次启动略慢,内存占用略高

对于桌面应用,这个权衡通常是值得的。

## 替代方案: 不使用UPX的体积优化

如果无法使用UPX,可以通过以下方式减小体积:

### 1. 排除不必要的模块

在 `build.py` 的 `get_excludes()` 函数中添加:

```python
def get_excludes():
    """获取需要排除的模块列表"""
    return [
        'tkinter',      # GUI框架(已用PyQt5)
        'test',         # 测试模块
        'unittest',     # 单元测试
        'doctest',      # 文档测试
        'distutils',    # 分发工具
        'setuptools',   # 包管理
        'pip',          # 包安装器
        # ... 更多未使用的模块
    ]
```

### 2. 使用 --onefile 模式(单文件)

⚠️ **注意**: 单文件模式启动更慢,但只有一个exe文件。

```python
# 修改 build.py
cmd.extend([
    '--onefile',  # 改为单文件模式
    # '--onedir', # 注释掉文件夹模式
])
```

### 3. 清理缓存和临时文件

```bash
# 打包前清理
rmdir /s /q build dist
del *.spec
py -3.9 -B build.py  # -B 禁用字节码缓存
```

## 推荐配置

对于 InEx System v2.0,推荐使用:

✅ **文件夹模式 + UPX压缩**
- 体积: ~60-90 MB
- 启动速度: 快
- 易于调试和维护

❌ **不推荐单文件模式**
- 体积: ~150-200 MB(解压后)
- 启动速度: 慢(需解压到临时目录)
- 每次启动都解压,效率低

## 验证UPX是否生效

打包完成后,检查输出:

```
✓ UPX 压缩完成
  原始大小: 185.3 MB
  压缩后大小: 72.1 MB
  压缩率: 61.1%
```

如果没有看到此信息,说明UPX未启用。

## 相关链接

- UPX 官网: https://upx.github.io/
- UPX GitHub: https://github.com/upx/upx
- PyInstaller 文档: https://pyinstaller.org/

## 更新日期
2026-05-03
