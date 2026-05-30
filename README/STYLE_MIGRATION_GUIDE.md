# UI样式迁移指南

**目标**: 将所有硬编码QSS样式迁移到`ui/styles.py`统一管理

---

## 📋 迁移清单

### ✅ 已完成
- [x] 创建`ui/styles.py`模块
- [x] 定义主题色常量
- [x] 定义字体和尺寸规范
- [x] 实现样式模板和工厂方法

### 🔲 待迁移文件

#### 1. ui/main_window.py (3处)
```python
# Line 120: 内容区背景色
content_frame.setStyleSheet("background-color: #ecf0f1;")
# ✅ 改为:
content_frame.setStyleSheet(UIStyles.gray_background())

# Line 127: 堆叠窗口背景色
self.stacked_widget.setStyleSheet("background-color: #ecf0f1;")
# ✅ 改为:
self.stacked_widget.setStyleSheet(UIStyles.gray_background())

# Line 988: 分隔线
line.setStyleSheet("background-color: #e0e0e0;")
# ✅ 改为:
line.setStyleSheet(f"background-color: {UIStyles.BORDER_MEDIUM};")

# Line 1027: 信息标签
info_label.setStyleSheet("font-family: 'Microsoft YaHei'; font-size: 13px; color: #34495e; padding: 10px; background-color: #f8f9fa; border-radius: 8px;")
# ✅ 改为:
info_label.setStyleSheet(f"""
    QLabel {{
        font-family: '{UIStyles.FONT_FAMILY}';
        font-size: {UIStyles.FONT_SIZE_LARGE}px;
        color: {UIStyles.SIDEBAR_BG};
        padding: {UIStyles.PADDING_MEDIUM}px;
        background-color: {UIStyles.BG_GRAY_50};
        border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
    }}
""")
```

#### 2. ui/login_dialog.py (1处)
```python
# Line 260: 底部框架
bottom_frame.setStyleSheet("background-color: #F5F7FA;")
# ✅ 改为:
bottom_frame.setStyleSheet(f"background-color: {UIStyles.BG_GRAY_100};")
```

#### 3. ui/pages/base_record_page.py (2处)
```python
# Line 46: 筛选框
filter_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
# ✅ 改为:
filter_frame.setStyleSheet(f"""
    QFrame {{
        background-color: {UIStyles.BG_GRAY_50};
        border-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
        padding: {UIStyles.PADDING_MEDIUM}px;
    }}
""")

# Line 206: 批量操作框
batch_frame.setStyleSheet("background-color: #fef3c7; border-radius: 5px; padding: 8px;")
# ✅ 改为:
batch_frame.setStyleSheet(UIStyles.warning_box())
```

#### 4. ui/pages/cash_flow_page.py (1处)
```python
# Line 40: 查询框
query_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
# ✅ 改为:
query_frame.setStyleSheet(UIStyles.gray_background())
```

#### 5. ui/pages/expense_page.py (4处)
```python
# Line 46: 筛选框
filter_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
# ✅ 改为:
filter_frame.setStyleSheet(UIStyles.gray_background())

# Line 656 & 764: 取消按钮
cancel_btn.setStyleSheet("background-color: #6c757d;")
# ✅ 改为:
cancel_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {UIStyles.TEXT_TERTIARY};
        color: white;
        border: none;
        border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
        padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
    }}
""")

# Line 850: 确认对话框按钮
ok_btn.setStyleSheet("background-color: #ef4444; color: white; border: none; border-radius: 4px; padding: 8px 16px;")
# ✅ 改为:
ok_btn.setStyleSheet(UIStyles.danger_button())
```

#### 6. ui/pages/income_page.py (3处)
```python
# Line 45: 筛选框
filter_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
# ✅ 改为:
filter_frame.setStyleSheet(UIStyles.gray_background())

# Line 327 & 434: 取消按钮
cancel_btn.setStyleSheet("background-color: #6c757d;")
# ✅ 改为: (同expense_page)

# Line 847: 确认对话框按钮
ok_btn.setStyleSheet("background-color: #10b981; color: white; border: none; border-radius: 4px; padding: 8px 16px;")
# ✅ 改为:
ok_btn.setStyleSheet(UIStyles.success_button())
```

#### 7. ui/pages/home_page.py (4处)
```python
# Line 834: 预算金额框
budget_amount_frame.setStyleSheet("background-color: #f0f9ff; border-radius: 8px; padding: 10px;")
# ✅ 改为:
budget_amount_frame.setStyleSheet(UIStyles.info_box())

# Line 852: 已花费框
spent_amount_frame.setStyleSheet("background-color: #fef3c7; border-radius: 8px; padding: 10px;")
# ✅ 改为:
spent_amount_frame.setStyleSheet(UIStyles.warning_box())

# Line 870: 剩余金额框
remaining_amount_frame.setStyleSheet("background-color: #ecfdf5; border-radius: 8px; padding: 10px;")
# ✅ 改为:
remaining_amount_frame.setStyleSheet(UIStyles.success_box())

# Line 890: 进度条框
progress_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 10px;")
# ✅ 改为:
progress_frame.setStyleSheet(UIStyles.gray_background())
```

#### 8. ui/pages/settings_sections/*.py (多处)
```python
# ai_assistant_section.py Line 69, 121, 173, 223
# backup_section.py Line 70
# database_section.py
# log_section.py

# 统一改为:
frame.setStyleSheet(UIStyles.gray_background())
```

---

## 🔧 迁移步骤

### 步骤1: 添加导入语句
在每个需要修改的文件顶部添加:
```python
from ui.styles import UIStyles
```

### 步骤2: 逐个文件迁移
按照上述清单,逐个文件替换硬编码样式

### 步骤3: 测试验证
每迁移一个文件后立即运行程序,确保:
- UI显示正常
- 无控制台错误
- 交互功能正常

### 步骤4: 代码审查
完成所有迁移后,检查:
- 是否还有遗漏的硬编码样式
- 样式是否一致
- 代码可读性是否提升

---

## 📊 迁移效果对比

### 迁移前
```python
# 硬编码样式 - 难以维护
card.setStyleSheet("""
    QFrame {
        background-color: #f0f3ff;
        border-radius: 12px;
        border-left: 4px solid #667eea;
    }
""")
```

### 迁移后
```python
# 使用工厂方法 - 简洁统一
card.setStyleSheet(UIStyles.card_style(UIStyles.PRIMARY, UIStyles.PRIMARY_LIGHT))
```

**优势**:
- ✅ 代码行数减少60%
- ✅ 主题切换只需修改UIStyles常量
- ✅ 样式一致性自动保证
- ✅ 易于维护和扩展

---

## ⚠️ 注意事项

1. **保持向后兼容**: 迁移过程中确保不破坏现有功能
2. **逐步迁移**: 不要一次性修改所有文件,避免引入大量bug
3. **充分测试**: 每迁移一个文件都要全面测试
4. **记录变更**: 在git提交时详细说明修改内容
5. **团队协作**: 通知团队成员新的样式规范

---

## 🎯 验收标准

- [ ] 所有硬编码QSS已迁移
- [ ] 项目中仅`ui/styles.py`包含样式定义
- [ ] 所有页面UI显示正常
- [ ] 无任何样式相关控制台错误
- [ ] 代码审查通过

---

**开始时间**: 2026-04-28  
**预计完成**: 2026-04-29  
**负责人**: 开发团队
