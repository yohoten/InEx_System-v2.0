# P0优化第三阶段：异常处理标准化方案

**开始时间**: 2026-04-28  
**当前状态**: 🔲 待执行

---

## 📋 问题分析

### 现状统计
通过代码扫描发现项目中有**25+处**裸`except Exception as e`的使用,分布在:
- `models/budget_manager.py`: 11处
- `models/config.py`: 4处 (已部分修复)
- `models/db_backend.py`: 7处 (已部分修复)
- `main.py`: 1处 (已修复)
- 其他文件: 2+处

### 主要问题
1. **缺少traceback记录**: 大部分except只记录错误消息,没有堆栈信息
2. **异常类型不明确**: 使用通用的Exception而非具体异常类型
3. **日志级别不统一**: 有些用print,有些用logger,有些用log_manager

---

## 🎯 标准化规范

### 规范1: 必须记录traceback(关键错误)

```python
# ❌ 错误做法 - 缺少traceback
try:
    db.connect()
except Exception as e:
    log_manager.error(f"数据库连接失败: {e}")

# ✅ 正确做法 - 包含完整traceback
try:
    db.connect()
except Exception as e:
    log_manager.error(f"数据库连接失败: {e}", exc_info=True)
```

**适用场景**:
- 数据库操作失败
- 文件IO错误
- 网络请求失败
- 配置加载失败
- 任何可能导致程序崩溃的错误

### 规范2: 使用具体异常类型

```python
# ❌ 错误做法 - 过于宽泛
try:
    with open(file_path, 'r') as f:
        content = f.read()
except Exception as e:
    log_manager.error(f"读取文件失败: {e}")

# ✅ 正确做法 - 精确捕获
try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    log_manager.warning(f"文件不存在: {file_path}")
except PermissionError:
    log_manager.error(f"文件权限不足: {file_path}")
except UnicodeDecodeError:
    log_manager.error(f"文件编码错误: {file_path}", exc_info=True)
```

**常见异常类型映射**:
| 场景 | 推荐异常类型 |
|------|-------------|
| 文件操作 | FileNotFoundError, PermissionError, IOError |
| 数据库操作 | sqlite3.Error, pymysql.Error |
| JSON解析 | json.JSONDecodeError |
| 网络请求 | requests.exceptions.RequestException |
| 类型转换 | ValueError, TypeError |
| 除零错误 | ZeroDivisionError |

### 规范3: 可恢复错误使用warning级别

```python
# 批量操作中单个失败不应中断整体流程
for i, item in enumerate(items):
    try:
        process_item(item)
    except Exception as e:
        log_manager.warning(f"处理第{i}项失败: {e}")
        continue  # 继续处理下一项
```

### 规范4: 用户输入验证使用info级别

```python
# 用户输入错误不需要记录traceback
try:
    amount = float(input_text)
except ValueError:
    log_manager.info(f"金额格式错误: {input_text}")
    show_error("请输入有效数字")
```

---

## 🔧 实施计划

### 阶段1: 关键模块优先(今天完成)

#### 1. models/budget_manager.py (11处)
**优先级**: ⭐⭐⭐ 高
**原因**: 预算管理是核心功能,错误会影响财务数据准确性

**修复策略**:
```python
# 添加log_manager导入
from utils.logger import log_manager

# 替换所有logger.error为log_manager.error并添加exc_info
except Exception as e:
    log_manager.error(f"[预算预警] 检查预算超支失败: {e}", exc_info=True)
```

**预计耗时**: 30分钟

#### 2. models/db_backend.py (剩余未修复的except)
**优先级**: ⭐⭐⭐ 高
**原因**: 数据库层是所有功能的基石

**修复策略**:
- 已有log_manager导入
- 补充缺失的exc_info参数
- 区分SQL语法错误和连接错误

**预计耗时**: 20分钟

#### 3. models/config.py (复查)
**优先级**: ⭐⭐ 中
**原因**: 已在日志迁移时部分修复

**修复策略**:
- 确认所有except都有exc_info=True
- 检查是否有遗漏的print语句

**预计耗时**: 10分钟

### 阶段2: UI层异常处理(明天完成)

#### 4. ui/pages/*.py (估计10+处)
**优先级**: ⭐⭐ 中
**原因**: UI层异常影响用户体验

**修复策略**:
- 数据加载失败 → warning + Toast提示
- 用户操作失败 → info + 友好提示
- 系统级错误 → error + exc_info

**预计耗时**: 1小时

#### 5. utils/*.py (估计5+处)
**优先级**: ⭐ 低
**原因**: 工具类异常通常会被上层捕获

**修复策略**:
- Excel/CSV处理 → 详细错误信息
- AI请求 → 网络异常分类处理
- 图表生成 → matplotlib异常捕获

**预计耗时**: 30分钟

---

## 📊 验收标准

### 代码质量指标
- [ ] 所有关键except都有exc_info=True
- [ ] 无裸except(Exception应改为具体类型)
- [ ] 日志级别使用合理(error/warning/info)
- [ ] 用户可见的错误有友好提示

### 测试验证
- [ ] 模拟数据库连接失败,日志包含traceback
- [ ] 模拟文件不存在,日志级别为warning
- [ ] 模拟用户输入错误,日志级别为info
- [ ] 模拟批量操作部分失败,不影响其他项

---

## 💡 最佳实践示例

### 示例1: 数据库操作
```python
def save_record(self, record_data):
    """保存记账记录"""
    try:
        self.db.execute("INSERT INTO ...", record_data)
        self.db.commit()
        log_manager.info("记录保存成功")
        return True
    except sqlite3.IntegrityError as e:
        log_manager.warning(f"记录重复: {e}")
        return False
    except sqlite3.OperationalError as e:
        log_manager.error(f"数据库操作失败: {e}", exc_info=True)
        raise  # 重新抛出,让上层处理
```

### 示例2: 文件导出
```python
def export_to_excel(self, data, file_path):
    """导出到Excel"""
    try:
        excel_handler.export(data, file_path)
        log_manager.info(f"导出成功: {file_path}")
    except PermissionError:
        log_manager.warning(f"文件被占用,无法写入: {file_path}")
        show_toast("文件正在使用中,请关闭后重试")
    except Exception as e:
        log_manager.error(f"导出失败: {e}", exc_info=True)
        show_toast("导出失败,请查看日志")
```

### 示例3: AI请求
```python
def get_ai_advice(self, financial_data):
    """获取AI理财建议"""
    try:
        response = requests.post(API_URL, json=financial_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        log_manager.warning("AI请求超时")
        return {"error": "请求超时,请稍后重试"}
    except requests.exceptions.ConnectionError:
        log_manager.error("AI服务连接失败", exc_info=True)
        return {"error": "网络连接失败"}
    except Exception as e:
        log_manager.error(f"AI请求异常: {e}", exc_info=True)
        return {"error": "服务暂时不可用"}
```

---

## 🎯 下一步行动

### 立即执行(今天)
1. 🔲 修复budget_manager.py的11处except
2. 🔲 复查db_backend.py的except处理
3. 🔲 验证config.py的异常处理完整性

### 明天任务
4. 🔲 处理UI层的异常
5. 🔲 处理utils层的异常
6. 🔲 运行全面测试验证

---

**预计总耗时**: 2-3小时  
**完成后P0进度**: 100% ✅
