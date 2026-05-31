# 🚀 数据字典导出平台

---

## 📋 项目简介

一个现代化的 Web 应用程序，用于连接数据库并导出表结构字典。支持 MySQL、PostgreSQL、Oracle 等多种数据库，提供炫酷的赛博朋克黑客风格界面！

---

## ✨ 功能特性

- 🌐 **Web 界面** - 无需命令行，通过浏览器操作
- 🎨 **赛博朋克风格** - 炫酷的黑客界面，数字雨背景
- 📊 **多数据库支持** - MySQL / PostgreSQL / Oracle
- 📋 **表选择器** - 可视化选择要导出的表
- 💾 **双格式导出** - CSV 格式 + Excel 格式（带目录页和超链接）
- 📱 **响应式设计** - 完美适配手机/平板/电脑
- 🔗 **Excel 超链接** - 点击表名可跳转，返回目录功能
- 📝 **配置保存** - 数据库连接信息本地持久化
- ⚡ **实时进度** - 导出进度条显示

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 启动服务

```bash
python app.py
```

### 3️⃣ 打开浏览器

访问地址：**http://127.0.0.1:5000**

---

## 📖 使用说明

### 第一步：连接数据库

1. 选择数据库类型
2. 输入连接参数：主机、端口、用户名、密码、数据库名
3. 点击「测试连接」验证（可选）
4. 点击「开始导出」进入

### 第二步：选择要导出的表

1. 在列表中勾选需要的表
2. 使用搜索框快速查找
3. 点击「全选」或「清除选择」快速操作
4. 查看右上角的「已选择 X 张表」

### 第三步：导出数据字典

1. 选择导出格式（CSV + Excel / 仅 CSV / 仅 Excel）
2. 点击「开始导出」
3. 在弹出的窗口中下载文件

---

## 📁 项目结构

```
├── app.py                      # Flask 后端主程序
├── config_gui.py               # 本地 GUI 配置工具
├── requirements.txt             # Python 依赖
├── db_config.json               # 数据库配置文件
├── db/                         # 核心模块
│   ├── factory.py              # 数据库连接工厂
│   ├── excel_exporter.py      # Excel 导出器（带超链接）
│   ├── csv_exporter.py        # CSV 导出器
│   ├── mysql.py               # MySQL 连接器
│   ├── postgresql.py          # PostgreSQL 连接器
│   ├── oracle.py              # Oracle 连接器
│   ├── interface.py           # 抽象接口
│   ├── schema_organizer.py    # 表结构组织器
│   ├── exceptions.py          # 异常定义
│   ├── logger.py              # 日志记录
│   └── config_manager.py      # 配置管理
├── templates/                   # HTML 模板
│   ├── index.html             # 数据库登录页
│   └── tables.html            # 表选择导出页
├── static/js/app.js           # 前端交互脚本
├── web_output/                # 导出文件目录
└── flask_session/             # Flask 会话存储
```

---

## 🎨 界面特色

- **矩阵数字雨** - 经典的赛博朋克背景
- **霓虹渐变边框** - 发光的科技感设计
- **故障文字效果** - 标题 Glitch 动画
- **扫描线滤镜** - CRT 显示器效果
- **多边形切角** - 未来感十足的卡片形状
- **实时状态条** - 系统状态、加密状态、时钟显示

---

## 📝 Excel 格式说明

生成的 Excel 文件包含：

1. **目录页** - 所有表的列表，点击表名跳转
2. **表详情页** - 每个表一个 Sheet，包含：
   - 表名、注释、添加时间、备注
   - 字段详情：字段名、数据类型、长度、可空、主键、默认值、注释
3. **返回目录** - 每个表 Sheet 都有返回目录按钮

---

## 💻 本地 GUI 配置工具（备用）

如果你更喜欢桌面应用，可以运行：

```bash
python config_gui.py
```

---

## 📋 常见问题

### Q: 连接数据库失败？
A: 检查连接参数是否正确，确保数据库服务正在运行，网络通畅。

### Q: 看不到进度条？
A: 确保浏览器没有禁用 JavaScript。

### Q: Excel 超链接无法跳转？
A: 确保使用 Excel 或 WPS 打开，格式已经优化为兼容 WPS 和 Excel。

---

## ⚙️ 依赖说明

主要依赖：
- Flask 2.3+ - Web 框架
- Flask-Session - 会话管理
- openpyxl - Excel 文件处理
- pymysql - MySQL 驱动（必需）
- psycopg2-binary - PostgreSQL 驱动（可选）
- cx-Oracle - Oracle 驱动（可选）

---

## 📄 许可证

本项目仅供内部使用。

---

## 🎉 开始使用吧！

现在就启动服务，享受炫酷的赛博朋克风格和便捷的数据字典导出！🚀
