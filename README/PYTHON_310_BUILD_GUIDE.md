# Python 3.10 打包配置说明

## 修改概述
已将打包脚本 `build.py` 优化以支持 Python 3.10 环境。

## 主要修改内容

### 1. UPX 压缩配置更新
**文件**: `build.py`  
**位置**: 第 268-279 行

**修改前**:
```python
'--upx-exclude=python313.dll',  # Python 3.13 核心DLL
```

**修改后**:
```python
'--upx-exclude=python310.dll',  # Python 3.10 核心DLL
```

**原因**: Python 3.10 使用的核心 DLL 文件名为 `python310.dll`，而非 `python313.dll`。排除此文件可避免 UPX 压缩导致的运行时错误。

### 2. Python 版本检测功能
**文件**: `build.py`  
**位置**: 新增 `check_python_version()` 函数（第 402-415 行）

**功能**:
- 自动检测当前 Python 版本
- 如果版本为 3.10.x，显示确认信息并继续
- 如果版本不匹配，发出警告并要求用户确认是否继续
- 确保打包环境与目标环境一致

**示例输出**:
```
当前Python版本: 3.10.11
✓ Python版本符合要求 (3.10.x)
```

或

```
当前Python版本: 3.11.5
⚠ 警告: 当前Python版本为 3.11，建议使用Python 3.10
  虽然可以继续打包，但可能遇到兼容性问题
是否继续? (y/n):
```

## 使用方法

### 前置条件
1. 安装 Python 3.10.x
2. 安装依赖包: `pip install -r requirements.txt`
3. 确保 UPX 已安装（可选，但推荐）

### 执行打包
```bash
python build.py
```

打包脚本会自动：
1. 检测 Python 版本
2. 检查 PyInstaller 是否安装
3. 清理旧的构建文件
4. 执行打包操作
5. （可选）使用 UPX 压缩可执行文件

### 生成的文件
- **位置**: `dist/InExSystem_v2.0/`
- **主程序**: `InEx_System_v2.0.exe`
- **启动脚本**: `启动程序.bat`

## 注意事项

### ⚠️ 重要提醒
1. **必须使用 Python 3.10**  
   虽然其他版本的 Python 3.x 可能也能工作，但为了确保最佳兼容性，强烈建议使用 Python 3.10。

2. **UPX 路径配置**  
   如果需要启用 UPX 压缩，请确保 `build.py` 中的 `UPX_PATH` 指向正确的 UPX 可执行文件：
   ```python
   UPX_PATH = r"H:\UPX\upx.exe"  # 修改为你的实际路径
   ```

3. **首次运行前的准备**  
   打包后的应用程序在首次运行前，需要确保数据库已初始化：
   ```bash
   python utils/db_initializer.py
   ```

### 💡 优化建议
- **清理缓存**: 如果修改代码后打包结果未更新，请删除 `__pycache__` 目录
- **测试打包**: 建议在分发前先在本地测试打包后的程序
- **压缩分发**: 可将整个 `dist/InExSystem_v2.0/` 文件夹压缩为 ZIP，减小 50-70% 体积

## 故障排查

### 问题 1: 提示 "PyInstaller 未安装"
**解决方案**:
```bash
pip install pyinstaller>=5.0
```

### 问题 2: UPX 压缩失败
**解决方案**:
- 检查 UPX_PATH 是否正确
- 确认 UPX 可执行文件存在且可执行
- 如果不需要 UPX，可以忽略此警告（打包仍会成功）

### 问题 3: 打包后的程序无法启动
**可能原因**:
- 缺少必要的 DLL 文件
- Python 版本不匹配
- 数据库未初始化

**解决方案**:
1. 确认使用 Python 3.10 进行打包
2. 检查 `dist/InExSystem_v2.0/` 目录下是否包含所有必要文件
3. 运行 `python utils/db_initializer.py` 初始化数据库

## 版本历史

### v2.0 (2026-05-01)
- ✅ 适配 Python 3.10
- ✅ 添加 Python 版本检测功能
- ✅ 更新 UPX 排除配置
- ✅ 优化打包流程和错误提示

---

**最后更新**: 2026-05-01  
**维护者**: InEx System 开发团队