# 💰 FinTrace · 财迹

> 基于 **PyQt5** 的桌面端个人财务管理应用 —— 记账 · 流水 · 报表 · 分析 · 建议，一体化闭环。

`Python 3.9+` · `PyQt5 ≥ 5.15` · `SQLite / MySQL 8.0 / Sybase SQL Anywhere 9` · `DeepSeek AI`

「数智经管·创见未来」创意作品设计大赛参赛作品

---

## ✨ 功能特性

| 模块 | 能力 |
| :--- | :--- |
| 📊 **首页看板** | 余额 / 收入 / 支出指标卡；日 · 月 · 年收支趋势；预算使用率实时显示，**80%** 预警、**100%** 超支提醒 |
| 💰 **收支记账** | 收入 5 类、支出 7 大类、支付方式三级资料维护；按日期 / 金额 / 类型 / 支付方式组合筛选；批量删除与改类；录入即联动预算校验 |
| 📝 **收支流水** | 按日自动生成流水并实时结算余额，单据号全局唯一；Excel / CSV / JSON 双向导入导出 |
| 📈 **收支月报** | 期初余额自动结转，期末结余一目了然；柱状 · 饼图 · 趋势 · 双轴组合四类图表，支持按月导航与账套过滤 |
| 📉 **账单分析** | 时段消费热力图、年度日历热力图、资金流向桑基图、财务健康雷达图 |
| 🤖 **AI 助手** | DeepSeek 读取真实账本生成理财建议；近 3 月趋势、Top 消费类别、异常消费检测；API Key 经 Fernet 加密落盘 |
| 🔐 **安全认证** | bcrypt（12 轮 salt）密码哈希；账套登录信息加密存储；内置 41 个班级账套，人手一册 |
| 🗄️ **数据管理** | 三后端一键切换；MySQL 连接池 + 自动重连 + 慢查询监控；SQL 导入后自动重建流水与月报；自动 / 手动备份、数据质量体检 |
| 📤 **导出能力** | ReportLab 中文 PDF 财务报告（含图表、AI 分析与改进建议）；Excel / CSV / JSON 导出；账套清单导出 |

## 🛠️ 技术栈

| 层级 | 技术 |
| :--- | :--- |
| GUI | PyQt5 ≥ 5.15（HighDPI 适配、启动画面） |
| 数据库 | SQLite 3 / MySQL 8.0（pymysql + DBUtils）/ Sybase SA 9（pyodbc + sqlanydb） |
| 可视化 | matplotlib 3.5+、seaborn 0.12+ |
| AI | DeepSeek API（异步线程调用） |
| 安全 | cryptography（Fernet 对称加密）、bcrypt（密码哈希） |
| 报表 | reportlab 3.6.13（PDF）、openpyxl（Excel） |
| 分析 | pandas、numpy、scipy |
| 交付 | PyInstaller ≥ 5.0 + Inno Setup |

## 🏗️ 系统架构

MVC 分层，界面与数据后端解耦：

| 层 | 位置 | 核心组件 |
| :--- | :--- | :--- |
| **View** | `ui/` | 主窗口、登录、9 大功能页面、对话框、主题引擎 |
| **Controller** | `models/` · `utils/` | 三后端抽象、连接池、预算预警、AI 助手、数据分析与报表导出 |
| **Model** | 数据库 | SQLite ↔ MySQL 8.0 ↔ Sybase SQL Anywhere 9 |

数据表统一 `sz_` 前缀，仿财务账务系统风格：

| 表名 | 说明 |
| :--- | :--- |
| `sz_c_sr` / `sz_c_zc` / `sz_c_zf` | 收入类型 / 支出类型 / 支付方式码表 |
| `sz_d_zt` | 账套档案（账套号 · 学号 · 姓名 · 班级 · 密码） |
| `sz_sheet_sr` / `sz_sheet_zc` | 收入 / 支出单据 |
| `sz_table_lsz` | 流水账（自动生成，含余额 `ye`） |
| `sz_report_srzc` | 月报表（期初 / 收入 / 支出 / 期末） |
| `sz_budget` / `sz_budget_history` | 预算 / 预算变更历史 |
| `sys_users` / `sys_audit_log` | 用户 / 审计日志 |

## 🚀 快速开始

**环境**：Windows 7 / 10 / 11（推荐 10+）· Python 3.9+ · 任一数据库（SQLite 免安装）

```bash
git clone https://github.com/yohoten/FinTrace-v2.1.0.git
cd FinTrace-v2.1.0

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

也可双击 `launcher.bat` 一键启动：

| 命令 | 说明 |
| :--- | :--- |
| `launcher.bat` | 检测依赖后启动 |
| `launcher.bat /fast` | 跳过检测直接启动 |
| `launcher.bat /install` | 仅安装依赖 |

**默认账套**：`2501033401` / `admin0457`。内置班级账套 `25010331xx` ~ `25010336xx`，可在登录页切换，密码规则见 `sz_d_zt` 表。

**打包发布**：

```bash
python build.py              # onedir 目录版
python build.py --installer  # 追加 Inno Setup 安装包
python build.py --clean      # 清理构建产物
```

产物位于 `dist/FinTrace_v2.1.0/FinTrace_v2.1.0.exe`。

## 📁 目录结构

```
FinTrace/
├── main.py                  # 入口：HighDPI、启动画面、登录流程
├── config.json              # 数据库 / UI / 日志 / AI 配置
├── launcher.bat             # 一键启动（依赖检测与安装）
├── build.py                 # PyInstaller 打包 · 安装包生成
├── FinTrace_v2.1.0.spec     # PyInstaller 配置
├── models/                  # M：db_backend（三后端）· db_pool · budget_manager · config
├── ui/                      # V：main_window · login_dialog
│   ├── pages/               #   首页 / 分类 / 收入 / 支出 / 流水 / 月报 / 分析 / 个人 / 设置
│   ├── dialogs/             #   数据库连接 · 数据库管理 · 全局搜索
│   ├── theme.py             #   浅色 / 深色主题引擎
│   └── styles.py            #   样式常量与工厂方法
├── utils/                   # C：认证 · AI · 数据分析 · PDF 报告 · 导入导出 · 建库 · 日志
├── data/                    # inex.db · backup/ · export/
├── tools/                   # 维护脚本
└── dist/ · build/ · .venv/  # 构建产物与虚拟环境（忽略）
```

## 📦 作品提交包

| 文件 | 内容 |
| :--- | :--- |
| `1.作品文件/README.txt` | 源码路径与 GitHub 仓库 |
| `2.FinTrace_作品说明书.pdf` | 作品说明书 |
| `3.作品展示视频/` | 展示视频（MP4） |
| `4.“数智经管·创见未来”创意作品设计大赛-诚信书.pdf` | 大赛诚信书 |
| `index.html` | 串讲演示页面 |

## ❓ 常见问题

| 问题 | 解决 |
| :--- | :--- |
| 启动提示缺少依赖 | 双击 `launcher.bat` 自动安装，或手动执行 `pip install -r requirements.txt` |
| 如何切换数据库 | 「系统设置 → 数据库配置」选择 SQLite / MySQL / Sybase；Sybase 支持 DSN、DSN-less、文件直连三种方式 |
| AI 助手不可用 | 「系统设置 → AI 助手」填入 DeepSeek API Key（自动加密），默认模型 `deepseek-chat` |
| 打包后缺少模块 | 使用 `build.py` 打包（已内置 hiddenimports 与 collect_all），避免手动 PyInstaller 遗漏依赖 |
| 数据文件在哪里 | 数据库 `data/inex.db`，备份 `data/backup/`，导出报告 `data/export/` |

## 🔧 工程优化（2026-11）

功能不变的前提下完成工程化收口：

- **路径可移植**：数据库与构建路径改为相对路径（`__file__` / `sys.executable`），默认库 `data/inex.db`。
- **主题系统**：新增 `ui/theme.py`，浅色 / 深色一键切换（视图 → 主题），选择持久化至 `config.json` 的 `ui.theme`。
- **目录规范**：一次性脚本归入 `tools/`；`secret.key`、`connection.key` 与数据库文件移出版本库（`.gitignore` 已配置）。
- **打包瘦身**：裁去未使用的 Qt 模块、PIL AVIF 与测试模块，打包后移除 `opengl32sw.dll`（约 5 MB），体积由约 84 MB 降至 55–65 MB。
- **安全与整洁**：清空 `config.json` 中明文数据库密码；日志默认 `INFO`；移除启动空转与 BOM；未落地功能改为诚实的“解析预览”提示。

> 回滚基线：Git 标签 `pre-optimization-baseline`（改造分支 `refactor/optimization`）。

## 📜 许可

本项目为课程设计 / 创意作品大赛参赛作品，代码仅供学习交流使用。
