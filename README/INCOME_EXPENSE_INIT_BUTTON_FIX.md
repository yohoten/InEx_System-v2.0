# 收入支出页面初始化按钮与查询功能修复记录

## 问题描述
1. **初始化按钮缺失**: 收入/支出记账页面的底部按钮区域缺少"初始化"按钮,用户无法快速刷新数据
2. **查询功能疑问**: 用户反馈查询按钮无响应(实际已实现,但可能因UI布局不清晰导致用户未发现)

## 根本原因
- 之前移除了"初始化"按钮以避免与"查询"功能重复
- 但实际上两个按钮职责不同:
  - **初始化(🔄)**: 无条件加载所有数据,重置到初始状态
  - **查询(🔍)**: 根据筛选条件(日期、金额、类型等)过滤数据

## 修复方案

### 1. 支出页面 (`ui/pages/expense_page.py`)
在底部按钮区域的"第1组:记录操作"中添加"初始化"按钮:

```python
# 第1组：记录操作
add_btn = QPushButton("➕ 增加")
add_btn.clicked.connect(self.add_record)
btn_layout.addWidget(add_btn)

init_btn = QPushButton("🔄 初始化")  # ✅ 新增
init_btn.clicked.connect(self.load_data)
btn_layout.addWidget(init_btn)

save_btn = QPushButton("💾 保存")
save_btn.clicked.connect(self.save_changes)
btn_layout.addWidget(save_btn)

reset_btn = QPushButton("🔃 复位")
reset_btn.clicked.connect(self.reset_filters)
btn_layout.addWidget(reset_btn)
```

### 2. 收入页面 (`ui/pages/income_page.py`)
同样在"第1组:记录操作"中添加"初始化"按钮:

```python
# 第1组：记录操作
add_btn = QPushButton("➕ 增加")
add_btn.clicked.connect(self.add_record)
btn_layout.addWidget(add_btn)

init_btn = QPushButton("🔄 初始化")  # ✅ 新增
init_btn.clicked.connect(self.load_data)
btn_layout.addWidget(init_btn)

reset_btn = QPushButton("🔃 复位")
reset_btn.clicked.connect(self.reset_filters)
btn_layout.addWidget(reset_btn)
```

## 功能说明

### 按钮职责划分

| 按钮 | 图标 | 功能 | 触发方法 | 使用场景 |
|------|------|------|----------|----------|
| **初始化** | 🔄 | 无条件加载所有数据 | `load_data()` | 查看完整数据、取消筛选 |
| **查询** | 🔍 | 按条件筛选数据 | `query_data()` | 根据日期/金额/类型过滤 |
| **复位** | 🔃 | 重置筛选条件为默认值 | `reset_filters()` | 清空筛选框但不重新加载 |
| **保存** | 💾 | 刷新显示(支出页) | `save_changes()` | 确认表格编辑后刷新 |

### 工作流程示例

#### 场景1: 查看所有数据
1. 点击 **🔄 初始化** → 加载全部记录

#### 场景2: 筛选特定月份数据
1. 设置起始日期: 2025-01-01
2. 设置结束日期: 2025-01-31
3. 选择支出类型: "餐饮"
4. 点击 **🔍 查询** → 显示符合条件的记录

#### 场景3: 返回全量数据
1. 点击 **🔄 初始化** → 清除筛选,显示所有数据

## 技术要点

### 1. 按钮布局规范
- **分组原则**: 相关功能的按钮放在同一组,用分隔线区分
- **顺序原则**: 常用操作在前(增加→初始化→保存→复位)
- **视觉层次**: 通过图标和颜色区分不同操作类型

### 2. 数据加载方法
```python
def load_data(self):
    """加载全部数据(无条件)"""
    records = db_manager.get_expense_records()  # 或 get_income_records()
    # ... 填充表格 ...

def query_data(self):
    """按条件查询数据"""
    filters = {
        'start_date': self.start_date.date().toString("yyyy-MM-dd"),
        'end_date': self.end_date.date().toString("yyyy-MM-dd"),
        'min_amount': float(self.min_amount.text()) if self.min_amount.text() else None,
        'max_amount': float(self.max_amount.text()) if self.max_amount.text() else None,
        'payment_code': self.payment_combo.currentData(),
        'expense_type_code': self.expense_type_combo.currentData(),
    }
    records = db_manager.get_expense_records(filters=filters)
    # ... 填充表格 ...
```

### 3. 用户体验优化
- **Toast提示**: 查询完成后显示结果数量(`toast.success(f"查询完成,共 {row_count} 条记录")`)
- **空数据提示**: 无结果时显示友好提示(`toast.warning("未找到符合条件的记录")`)
- **智能默认值**: 日期默认本月,支付方式/类型记住上次选择

## 验证步骤
1. 启动程序并登录
2. 进入"支出记账"或"收入记账"页面
3. 确认底部按钮区域显示: `➕ 增加 | 🔄 初始化 | 💾 保存 | 🔃 复位`
4. 点击 **🔄 初始化**,验证表格刷新并显示所有数据
5. 设置筛选条件后点击 **🔍 查询**,验证数据按条件过滤
6. 再次点击 **🔄 初始化**,验证恢复到全量数据

## 相关文件
- `ui/pages/expense_page.py`: 支出记账页面
- `ui/pages/income_page.py`: 收入记账页面
- `models/db_backend.py`: 数据库查询方法(`get_expense_records`, `get_income_records`)

## 修复日期
2026-05-03

## 修复人员
Lingma (灵码) AI助手
