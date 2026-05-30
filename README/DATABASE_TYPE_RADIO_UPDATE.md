# 数据库类型选择UI改进说明

## 📋 修改概述

将系统设置页面中的数据库类型选择从**下拉框（QComboBox）**改为**单选按钮组（QRadioButton）**，提供更直观的视觉反馈和更便捷的操作体验。

## ✅ 已完成的修改

### 1. 导入必要的组件
在文件顶部添加了 `QRadioButton` 和 `QButtonGroup` 的导入：
```python
from PyQt5.QtWidgets import (..., QRadioButton, QButtonGroup)
```

### 2. UI初始化修改 (`initUI` 方法)

#### 修改前（下拉框）：
```python
type_layout = QHBoxLayout()
type_layout.addWidget(QLabel("数据库类型:"))
self.db_type_combo = QComboBox()
self.db_type_combo.addItems(["SQLite", "MySQL", "Sybase Anywhere 9"])
self.db_type_combo.currentTextChanged.connect(self.on_db_type_changed)
type_layout.addWidget(self.db_type_combo)
type_layout.addStretch()
db_layout.addLayout(type_layout)
```

#### 修改后（单选按钮）：
```python
# 数据库类型 - 使用单选按钮（圆点样式）
type_label = QLabel("数据库类型:")
db_layout.addWidget(type_label)

# 创建单选按钮组
self.db_type_group = QButtonGroup(self)
self.db_type_group.setExclusive(True)

radio_layout = QHBoxLayout()
radio_layout.setSpacing(20)

# SQLite 单选按钮
self.sqlite_radio = QRadioButton("SQLite")
self.sqlite_radio.setFont(QFont("微软雅黑", 10))
self.sqlite_radio.setChecked(True)
self.sqlite_radio.toggled.connect(lambda: self.on_db_type_changed("SQLite"))
radio_layout.addWidget(self.sqlite_radio)
self.db_type_group.addButton(self.sqlite_radio, 0)

# MySQL 单选按钮
self.mysql_radio = QRadioButton("MySQL")
self.mysql_radio.setFont(QFont("微软雅黑", 10))
self.mysql_radio.toggled.connect(lambda: self.on_db_type_changed("MySQL"))
radio_layout.addWidget(self.mysql_radio)
self.db_type_group.addButton(self.mysql_radio, 1)

# Sybase 单选按钮
self.sybase_radio = QRadioButton("Sybase Anywhere 9")
self.sybase_radio.setFont(QFont("微软雅黑", 10))
self.sybase_radio.toggled.connect(lambda: self.on_db_type_changed("Sybase Anywhere 9"))
radio_layout.addWidget(self.sybase_radio)
self.db_type_group.addButton(self.sybase_radio, 2)

radio_layout.addStretch()
db_layout.addLayout(radio_layout)
```

### 3. 加载配置修改 (`load_settings` 方法)

#### 修改前：
```python
db_type = db_config.get('type', 'sqlite')
if db_type == 'sqlite':
    self.db_type_combo.setCurrentText("SQLite")
elif db_type == 'mysql':
    self.db_type_combo.setCurrentText("MySQL")
elif db_type == 'sybase':
    self.db_type_combo.setCurrentText("Sybase Anywhere 9")
```

#### 修改后：
```python
db_type = db_config.get('type', 'sqlite')
if db_type == 'sqlite':
    self.sqlite_radio.setChecked(True)
elif db_type == 'mysql':
    self.mysql_radio.setChecked(True)
elif db_type == 'sybase':
    self.sybase_radio.setChecked(True)
```

### 4. 保存配置修改 (`save_all_settings` 方法)

#### 修改前：
```python
db_type = self.db_type_combo.currentText().lower()
```

#### 修改后：
```python
# 从单选按钮组获取数据库类型
if self.sqlite_radio.isChecked():
    db_type = 'sqlite'
elif self.mysql_radio.isChecked():
    db_type = 'mysql'
elif self.sybase_radio.isChecked():
    db_type = 'sybase'
```

## 🎨 UI改进效果

### 优势对比

| 特性 | 下拉框 (QComboBox) | 单选按钮 (QRadioButton) |
|------|-------------------|------------------------|
| **可见性** | ❌ 需要点击才能看到所有选项 | ✅ 所有选项一目了然 |
| **操作步骤** | ⚠️ 需要2步（点击+选择） | ✅ 只需1步（直接点击） |
| **空间占用** | ✅ 较小 | ⚠️ 稍大但可接受 |
| **视觉反馈** | ⚠️ 较弱 | ✅ 清晰明确 |
| **适用场景** | 选项较多时 | 选项较少（2-5个）时 |

### 视觉效果
- **圆点样式**：标准的单选按钮圆形图标
- **字体统一**：微软雅黑 10pt，与整体UI风格一致
- **间距合理**：按钮之间20px间距，不会过于拥挤
- **默认选中**：SQLite作为默认选项，符合大多数用户使用习惯

## 🔧 技术实现要点

### 1. 互斥选择
使用 `QButtonGroup` 管理三个单选按钮，确保同一时间只能选择一个：
```python
self.db_type_group = QButtonGroup(self)
self.db_type_group.setExclusive(True)  # 启用互斥
```

### 2. 信号连接
每个单选按钮的 `toggled` 信号都连接到同一个处理函数，通过lambda传递参数：
```python
self.sqlite_radio.toggled.connect(lambda: self.on_db_type_changed("SQLite"))
```

### 3. ID分配
为每个按钮分配唯一的ID，便于后续可能的扩展：
- SQLite: ID = 0
- MySQL: ID = 1
- Sybase: ID = 2

## ✨ 用户体验提升

1. **更直观**：用户一眼就能看到所有可用的数据库类型
2. **更快速**：减少了一次点击操作
3. **更明确**：当前选中的数据库类型更加醒目
4. **更符合规范**：对于少量固定选项，单选按钮是更好的UI选择

## 📝 注意事项

1. **向后兼容**：配置文件格式未改变，不影响已有用户的配置
2. **功能完整**：所有原有功能保持不变，只是UI展示方式改变
3. **测试验证**：已通过测试脚本验证功能正常

## 🚀 后续优化建议

1. **添加图标**：可以在单选按钮前添加数据库图标，增强视觉识别
2. **添加提示**：鼠标悬停时显示各数据库类型的简要说明
3. **响应式布局**：在小屏幕下可以调整为垂直排列

---

**修改日期**: 2026-04-18  
**修改人**: AI助手  
**影响范围**: `ui/pages/settings_page.py`  
**测试状态**: ✅ 已通过基本功能测试
