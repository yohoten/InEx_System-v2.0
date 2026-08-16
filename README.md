# 💰 InEx System v2.0 — 个人收支管理系统

一款基于 **PyQt5** 构建的现代化桌面端个人财务管理应用，支持 **SQLite / MySQL 8.0 / Sybase SQL Anywhere 9** 三种数据库灵活切换，覆盖"记账 → 流水 → 报表 → 分析 → 建议"完整财务管理闭环，并集成 **DeepSeek AI 智能理财助手**。

> **大赛背景**：「数智经管·创见未来」创意作品设计大赛参赛作品

---

## ✨ 功能特性

### 📊 首页看板
- 总余额、总收入、总支出等核心指标卡片
- 收支趋势图（支持按 **日 / 月 / 年** 维度切换）
- 预算状态卡片：实时展示当月预算使用率与结余
- 预算预警：支出达预算 **80%** 触发警告，**100%** 触发超支提醒

### 💰 收入 / 支出记账
- 分类化管理：收入类型、支出类型、支付方式三级基础资料维护
- 收入支持 5 种来源分类（工资、兼职工资、奖学金等）、支出支持 7 大类（餐饮、通讯、学习用品、交通、水电等）
- 支付方式：现金、银行存款、微信、支付宝等
- 支持多条件组合筛选（日期范围、金额区间、类型、支付方式）
- 批量删除、批量修改支付方式/类型
- 预算联动：支出录入时自动检查预算并弹出预警确认

### 📝 收支流水账
- 自动按日期生成流水账，**实时计算并更新余额**
- 单据号（djh）自动生成，全局唯一
- 支持 Excel 导入/导出、CSV 导入/导出、JSON 导入/导出

### 📈 收支月报表
- 按月查看收入、支出、期初/期末余额（含期初余额自动结转）
- 四种图表：柱状图、饼图、趋势图、双轴组合图
- 支持按月导航（上/下月切换）与按账套过滤

### 📉 账单分析（高级可视化）
- **消费热力图**：一周内不同时间段的消费分布
- **日历热力图**：一年内各日期的消费分布
- **资金流向桑基图**：收入来源 → 支出去向的完整资金链路
- **财务健康雷达图**：收入稳定性、支出控制、储蓄率等多维评分

### 🤖 DeepSeek AI 助手
- 基于真实数据库记录生成个性化理财建议
- 支出习惯分析（近 3 个月趋势、Top 消费类别、异常消费检测）
- API Key 使用 `cryptography`（Fernet）加密存储，`secret.key` 本地管理
- 模型默认 `deepseek-chat`，可在系统设置中配置

### 🔐 安全与认证
- 登录密码使用 **bcrypt**（12 轮 salt）哈希存储
- 账套登录信息（账号）加密存储于 `config.json`
- 多账套支持：内置班级 41 个账套，每人独立账本

### 🗄️ 数据管理
- 三种数据库后端一键切换：SQLite（单文件）、MySQL 8.0（连接池 + 自动重连 + 慢查询监控）、Sybase SQL Anywhere 9（智能多方式连接）
- MySQL 连接池：DBUtils PooledDB，支持连接回收、空闲重连、性能统计
- SQL 文件导入器：自动检测编码、事务化执行、导入后自动重建流水账与月报表
- 自动备份（可按日/周配置）、手动备份/恢复
- 数据质量检测与图表可用性建议

### 📤 导出能力
- **PDF 财务分析报告**：ReportLab 生成专业中文报告（CID 字体 + TTF 后备），含图表、AI 分析、改进建议
- Excel（openpyxl）、CSV、JSON 多格式导出
- 账套列表导出 Excel

---

## 🛠️ 技术栈

| 层级 | 技术 |
| --- | --- |
| GUI 框架 | PyQt5 ≥ 5.15（HighDPI 适配、QSplashScreen 启动画面） |
| 数据库 | SQLite 3 / MySQL 8.0（pymysql + DBUtils 连接池）/ Sybase SQL Anywhere 9（pyodbc + sqlanydb） |
| 可视化 | matplotlib 3.5+、seaborn 0.12+（热力图/桑基图/雷达图） |
| AI | DeepSeek API（requests 异步线程调用） |
| 安全 | cryptography（Fernet 对称加密）、bcrypt（密码哈希） |
| 报表 | reportlab 3.6.13（PDF）、openpyxl（Excel） |
| 数据分析 | pandas、numpy、scipy（统计与趋势分析） |
| 打包 | PyInstaller ≥ 5.0 + Inno Setup（可选安装包） |

## 🏗️ 系统架构

采用 **MVC 架构**，分层清晰：

```
┌─────────────────────────────────────────────┐
│  View 层（ui/）                              │
│   main_window · login_dialog · pages/        │
│   dialogs/ · styles                          │
├─────────────────────────────────────────────┤
│  Controller 层（models/ + utils/）           │
│   db_backend（三后端抽象）· db_pool          │
│   budget_manager（预算预警）· config         │
│   auth_manager · ai_assistant · data_analyzer│
│   pdf_report_generator · excel/csv 工具       │
├─────────────────────────────────────────────┤
│  Model 层（数据库）                           │
│   SQLite ↔ MySQL 8.0 ↔ Sybase SA 9           │
└─────────────────────────────────────────────┘
```

**数据库设计**（`sz_` 前缀表，仿财务账务系统风格）：

| 表名 | 说明 |
| --- | --- |
| `sz_c_sr` | 收入类型码表 |
| `sz_c_zc` | 支出类型码表 |
| `sz_c_zf` | 支付方式码表 |
| `sz_d_zt` | 账套档案（账套号/学号/姓名/班级/密码） |
| `sz_sheet_sr` | 收入单据表 |
| `sz_sheet_zc` | 支出单据表 |
| `sz_table_lsz` | 流水账（自动生成，含余额 `ye`） |
| `sz_report_srzc` | 月报表（期初/收入/支出/期末） |
| `sz_budget` / `sz_budget_history` | 预算表 / 预算变更历史 |
| `sys_users` / `sys_audit_log` | 用户表 / 审计日志 |

---

## 🚀 快速开始

### 环境要求
- Windows 7 / 10 / 11（推荐 10+）
- Python 3.9+（开发/源码运行）
- 数据库（任一）：SQLite（默认，免安装）/ MySQL 8.0 / Sybase SQL Anywhere 9

### 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/yohoten/InEx_System-v2.0.git
cd InEx_System-v2.0

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动
python main.py
```

或直接双击 **`InEx_System_Launcher.bat`**（自动检测/安装依赖并启动）：

```
InEx_System_Launcher.bat            # 正常启动（含依赖检测）
InEx_System_Launcher.bat /fast      # 跳过检测直接启动
InEx_System_Launcher.bat /install   # 仅安装依赖
```

### 默认账套

| 项目 | 值 |
| --- | --- |
| 默认账套号 | `2501033401` |
| 默认密码 | `admin0457` |

> 💡 内置班级多个账套（`25010331xx` ~ `25010336xx`），可在登录页下拉切换，密码规则见数据库 `sz_d_zt` 表。

### 打包发布

```bash
python build.py                 # 打包为文件夹（onedir EXE）
python build.py --installer     # 打包 + 生成 Inno Setup 安装脚本
python build.py --clean         # 清理构建产物
```

产物输出至 `dist/InEx_System_v2.0/InEx_System_v2.0.exe`。

---

## 📁 目录结构

```
InEx_System v2.0_26041800/
├── main.py                      # 程序入口（HighDPI、启动画面、登录流程）
├── config.json                  # 系统配置（数据库/UI/日志/AI 加密存储）
├── requirements.txt             # 依赖清单
├── build.py                     # PyInstaller 打包脚本
├── InEx_System_Launcher.bat     # 一键启动脚本
├── InEx_System_v2.0.spec        # PyInstaller 配置
├── InEx_System_v2.0_installer.iss  # Inno Setup 安装脚本
├── InEx_System.ico              # 应用图标
├── index.html                   # 串讲演示页面（网页版项目介绍）
├── models/                      # 数据层（MVC 的 M）
│   ├── db_backend.py            #   三数据库后端（SQLite/MySQL/Sybase）
│   ├── db_pool.py               #   SQLite 连接池
│   ├── budget_manager.py        #   预算管理与预警
│   └── config.py                #   配置管理器（线程安全单例）
├── ui/                          # 界面层（MVC 的 V）
│   ├── main_window.py           #   主窗口（侧边栏+菜单栏+状态栏）
│   ├── login_dialog.py          #   登录对话框
│   ├── pages/                   #   9 大功能页面
│   │   ├── home_page.py         #     首页看板
│   │   ├── category_page.py     #     分类管理
│   │   ├── income_page.py       #     收入记账
│   │   ├── expense_page.py      #     支出记账
│   │   ├── cash_flow_page.py    #     收支流水账
│   │   ├── monthly_report_page.py #   收支月报表
│   │   ├── statistics_page.py   #     账单分析
│   │   ├── profile_page.py      #     个人中心
│   │   └── settings_page.py     #     系统设置
│   ├── dialogs/                 #   对话框（数据库连接/管理/全局搜索）
│   └── styles.py                #   样式常量
├── utils/                       # 工具层（MVC 的 C）
│   ├── auth_manager.py          #   认证（bcrypt + Fernet）
│   ├── ai_assistant.py          #   DeepSeek AI 助手
│   ├── ai_analyzer.py           #   支出分析引擎
│   ├── data_analyzer.py         #   数据质量与建议
│   ├── pdf_report_generator.py  #   PDF 报告
│   ├── excel_utils.py           #   Excel 读写
│   ├── csv_utils.py             #   CSV 读写
│   ├── db_initializer.py        #   建表与初始化数据
│   ├── sql_dialect.py           #   SQL 方言适配
│   └── logger.py                #   统一日志
├── data/                        # 数据目录（SQLite 数据库/备份/导出）
│   ├── inex.db                  #   默认数据库
│   ├── backup/                  #   自动备份
│   └── export/                  #   导出文件（PDF 报告等）
├── dist/                        # 打包输出（忽略）
├── build/                       # 构建中间产物（忽略）
└── .venv/                       # 虚拟环境（忽略）
```

---

## 📄 作品提交包

| 文件 | 说明 |
| --- | --- |
| `1.作品文件/README.txt` | 源码路径与 GitHub 仓库链接 |
| `2.InEx_System_作品说明书.pdf` | 作品说明书 |
| `3.作品展示视频/` | 作品展示视频（MP4） |
| `4."数智经管·创见未来"创意作品设计大赛-诚信书.pdf` | 大赛诚信书 |
| `index.html` | 串讲演示页面 |

---

## ❓ 常见问题

**Q1：启动提示缺少依赖？**
双击 `InEx_System_Launcher.bat` 会自动安装；或手动执行 `pip install -r requirements.txt`。

**Q2：如何切换数据库？**
进入「系统设置 → 数据库配置」，选择 SQLite / MySQL / Sybase 并填写连接参数；Sybase 支持 DSN、DSN-less、文件直连三种方式，首次使用可参考应用内驱动安装指南。

**Q3：AI 助手无法使用？**
在「系统设置 → AI 助手」中配置 DeepSeek API Key（自动加密存储），默认模型 `deepseek-chat`。

**Q4：打包后运行时缺模块？**
使用项目内 `build.py` 打包（已内置 hiddenimports 与 collect_all 配置），避免手动 PyInstaller 遗漏依赖。

**Q5：数据库文件在哪里？**
默认 `data/inex.db`；自动备份在 `data/backup/`，导出报告在 `data/export/`。

---

## 📜 许可

本项目为课程设计 / 创意作品大赛参赛作品，代码仅供学习交流使用。
