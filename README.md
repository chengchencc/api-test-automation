
# API自动化测试框架

基于Excel编写测试用例、使用pytest执行测试、生成Allure报告的接口自动化测试框架。

## 📖 目录

- [API自动化测试框架](#api自动化测试框架)
  - [📖 目录](#-目录)
  - [✨ 特性](#-特性)
  - [📁 项目结构](#-项目结构)
  - [🚀 快速开始](#-快速开始)
    - [1. 安装依赖](#1-安装依赖)
    - [2. 创建环境配置](#2-创建环境配置)
    - [3. 准备测试数据](#3-准备测试数据)
    - [4. 运行测试](#4-运行测试)
  - [📊 Excel测试用例编写指南](#-excel测试用例编写指南)
    - [Excel文件结构](#excel文件结构)
    - [基本列说明](#基本列说明)
    - [Jinja2模板语法](#jinja2模板语法)
    - [支持的模板函数](#支持的模板函数)
  - [🔧 高级功能](#-高级功能)
    - [1. 数据提取与链式调用](#1-数据提取与链式调用)
    - [2. 多种断言方式](#2-多种断言方式)
    - [3. 前后置操作](#3-前后置操作)
    - [4. OAuth 2.0认证](#4-oauth-20认证)
    - [5. 测试报告](#5-测试报告)
  - [🛠️ 命令行参数](#️-命令行参数)
  - [📝 示例](#-示例)
    - [示例1：简单的登录测试](#示例1简单的登录测试)
    - [示例2：链式调用测试](#示例2链式调用测试)
  - [🔍 调试与日志](#-调试与日志)
    - [日志级别](#日志级别)
    - [日志输出](#日志输出)
  - [🤝 贡献指南](#-贡献指南)
  - [📄 许可证](#-许可证)
  - [📞 联系方式](#-联系方式)
  - [🙏 致谢](#-致谢)

## ✨ 特性

- 📊 **Excel数据驱动**：使用Excel编写测试用例，支持多sheet、多场景
- 🎯 **Jinja2模板引擎**：支持动态参数生成、数据提取、链式调用
- 🔧 **参数化赋值**：支持多种参数化方式，包括随机数据、序列号、时间戳等
- 📈 **多种报告格式**：支持Allure报告、HTML报告、JSON日志
- ⚡ **并行执行**：支持pytest-xdist并行执行测试
- 🔄 **失败重试**：支持pytest-rerunfailures失败重试机制
- 🔐 **OAuth 2.0支持**：内置OAuth 2.0客户端，支持多种认证方式
- 🎨 **模板化断言**：支持JSON Schema、正则匹配、深度比较等多种断言方式

## 📁 项目结构（改进版）

```
api-test-demo/
├── src/                          # 源代码目录（重构）
│   ├── core/                     # 核心框架模块
│   │   ├── base_test.py          # 测试基类（统一生命周期管理）
│   │   ├── test_runner.py        # 测试运行器
│   │   └── test_suite.py         # 测试套件管理
│   ├── clients/                  # 客户端模块
│   │   ├── http_client.py        # HTTP客户端（支持异步）
│   │   ├── oauth_client.py       # OAuth客户端
│   │   └── database_client.py    # 数据库客户端
│   ├── data/                     # 数据管理模块
│   │   ├── data_loader.py        # 数据加载器（多格式支持）
│   │   ├── data_generator.py     # 数据生成器
│   │   ├── data_validator.py     # 数据验证器
│   │   └── data_extractor.py     # 数据提取器
│   ├── engine/                   # 引擎模块
│   │   ├── template_engine.py    # 模板引擎（Jinja2增强）
│   │   ├── assertion_engine.py   # 断言引擎
│   │   └── hook_engine.py        # 钩子引擎
│   ├── models/                   # 数据模型模块
│   │   ├── test_case.py          # 测试用例模型
│   │   ├── test_data.py          # 测试数据模型
│   │   └── test_result.py        # 测试结果模型
│   ├── utils/                    # 工具模块
│   │   ├── logger.py             # 日志工具（JSON格式）
│   │   ├── file_utils.py         # 文件工具
│   │   ├── time_utils.py         # 时间工具
│   │   └── security_utils.py     # 安全工具
│   ├── config/                   # 配置模块
│   │   ├── settings.py           # 配置设置（多环境支持）
│   │   ├── env_manager.py        # 环境管理器
│   │   └── config_validator.py   # 配置验证器
│   └── plugins/                  # 插件模块
│       ├── base_plugin.py        # 插件基类
│       ├── report_plugin.py      # 报告插件
│       └── auth_plugin.py        # 认证插件
├── tests/                        # 业务测试目录（用户测试用例）
│   ├── api/                      # API测试
│   │   ├── test_user_api.py      # 用户API测试示例
│   │   └── test_order_api.py     # 订单API测试
│   ├── smoke/                    # 冒烟测试
│   ├── regression/               # 回归测试
│   └── performance/              # 性能测试
├── data/                         # 测试数据目录（结构化）
│   ├── excel/                    # Excel数据
│   │   ├── test_cases.xlsx       # 测试用例
│   │   └── test_data.xlsx        # 测试数据
│   ├── json/                     # JSON数据
│   │   └── api_schemas.json      # API Schema定义
│   ├── yaml/                     # YAML数据
│   │   └── test_config.yaml      # 测试配置
│   └── sql/                      # SQL脚本
│       └── test_data.sql         # 测试数据SQL
├── config/                       # 配置文件目录
│   ├── settings.yaml             # 主配置文件
│   ├── env/                      # 环境配置
│   │   ├── development.yaml      # 开发环境
│   │   ├── testing.yaml          # 测试环境
│   │   └── production.yaml       # 生产环境
│   └── plugins/                  # 插件配置
├── reports/                      # 测试报告目录
│   ├── allure/                   # Allure报告
│   ├── html/                     # HTML报告
│   └── json/                     # JSON报告
├── logs/                         # 日志目录
│   ├── test/                     # 测试日志
│   └── framework/                # 框架日志
├── docs/                         # 文档目录
│   ├── api/                      # API文档
│   ├── examples/                 # 示例文档
│   └── guides/                   # 使用指南
├── scripts/                      # 脚本目录
│   ├── run.py                    # 主运行脚本（简化）
│   ├── generate_data.py          # 数据生成脚本
│   ├── validate_config.py        # 配置验证脚本
│   └── generate_report.py        # 报告生成脚本
├── conftest.py                   # pytest配置（优化）
├── pytest.ini                    # pytest配置（增强）
├── requirements.txt              # 依赖包列表
├── requirements-dev.txt          # 开发依赖
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git忽略文件
├── README.md                     # 项目说明
└── CHANGELOG.md                  # 变更日志
```

## 🚀 快速开始

### 1. 安装依赖

```shell
# 安装Python依赖包
pip install -r requirements.txt

# 安装Allure命令行工具（生成报告需要）
## macOS
brew install allure

## Windows (通过Scoop)
scoop install allure

## Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

### 2. 创建环境配置

```shell
# 复制环境配置文件
cp .env.example .env

# 编辑环境配置（根据实际情况修改）
vim .env  # 或使用其他编辑器
```

`.env`文件配置示例：
```env
# API基础配置
BASE_URL=https://api.example.com
API_VERSION=v1

# 数据库配置（可选）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=test_db
DB_USER=test_user
DB_PASSWORD=test_password

# OAuth 2.0配置（可选）
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_TOKEN_URL=https://api.example.com/oauth/token
OAUTH_SCOPE=read write

# 测试配置
TEST_TIMEOUT=30
MAX_RETRIES=3
LOG_LEVEL=INFO
```

### 3. 准备测试数据

```shell
# 生成Excel模板
python run.py --template

# 编辑测试数据
# 打开 output/test_data/api_test_cases.xlsx 文件进行编辑
```

### 4. 运行测试

```shell
# 使用新的脚本运行测试
cd scripts

# 运行所有测试
python run.py run tests/

# 运行API测试
python run.py run tests/api/ -t api

# 运行冒烟测试
python run.py run tests/ -t smoke

# 并行运行测试
python run.py run tests/ -p -w 4

# 失败重试
python run.py run tests/ -r 2

# 生成并打开报告
python run.py run tests/ -R -o

# 验证配置
python run.py validate

# 列出测试用例
python run.py list

# 生成Excel模板
python run.py template
```

### 5. 使用新的测试基类

```python
# tests/api/test_example.py
import allure
from src.core.base_test import BaseTest

@allure.epic("示例测试")
class TestExample(BaseTest):

    def test_example(self):
        """示例测试用例"""
        # 使用模板引擎
        username = self.render_template("{{ random_email() }}")

        # 发起HTTP请求
        response = self.make_request(
            method="POST",
            url="http://api.example.com/login",
            json={"username": username, "password": "Test@123456"}
        )

        # 使用断言方法
        self.assert_equal(response.status_code, 200)
        self.assert_in("token", response.json())

        # 附加数据到报告
        self.attach_json("响应数据", response.json())

        # 记录步骤
        with self.step("验证登录成功"):
            self.logger.info("登录测试通过")
```

## 📊 Excel测试用例编写指南

### Excel文件结构

测试用例Excel文件包含多个sheet，每个sheet代表一个测试场景或模块：

1. **测试用例表**：包含测试用例的基本信息
2. **测试数据表**：包含测试用的参数数据
3. **预期结果表**：包含预期结果的验证规则

### 基本列说明

| 列名 | 说明 | 示例 |
|------|------|------|
| test_case_id | 测试用例ID | TC001 |
| test_case_name | 测试用例名称 | 用户登录测试 |
| description | 用例描述 | 验证用户登录功能 |
| method | HTTP方法 | GET, POST, PUT, DELETE |
| endpoint | API端点 | /api/v1/login |
| headers | 请求头 | `{"Content-Type": "application/json"}` |
| params | URL参数 | `{"page": 1, "size": 10}` |
| data | 请求体数据 | `{"username": "{{ username }}", "password": "{{ password }}"}` |
| expected_status | 预期状态码 | 200 |
| expected_response | 预期响应 | `{"code": 0, "message": "success"}` |
| extract | 数据提取规则 | `{"token": "$.data.token"}` |
| depends_on | 依赖的用例ID | TC001 |
| tags | 测试标签 | smoke, regression, api |

### Jinja2模板语法

在Excel中可以使用以下Jinja2模板语法：

| 字段 | 示例 | 说明 |
|------|------|------|
| 随机用户名 | `{{ 'user_' ~ random_int(1000, 9999) }}` | 生成随机用户名 |
| 随机邮箱 | `{{ random_email() }}` | 生成随机邮箱 |
| 时间戳 | `{{ timestamp() }}` | 当前时间戳 |
| 订单号 | `ORDER_{{ now('%Y%m%d') }}_{{ sequence('order') }}` | 带序列的订单号 |
| MD5签名 | `{{ (user_id ~ timestamp()) \| md5 }}` | MD5签名 |
| 今天日期 | `{{ today() }}` | 今天日期 |
| 昨天日期 | `{{ today(days=-1) }}` | 昨天日期 |
| UUID | `{{ uuid() }}` | 生成UUID |
| 随机手机号 | `{{ random_phone() }}` | 生成随机手机号 |
| 提取变量 | `{{ extract('token') }}` | 从之前响应中提取变量 |

### 支持的模板函数

- **随机数据**：`random_int()`, `random_string()`, `random_email()`, `random_phone()`
- **时间日期**：`now()`, `today()`, `timestamp()`, `strftime()`
- **序列生成**：`sequence()`, `increment()`
- **加密哈希**：`md5()`, `sha1()`, `sha256()`
- **UUID生成**：`uuid()`, `uuid4()`
- **数据提取**：`extract()`, `get_context()`
- **字符串处理**：`upper()`, `lower()`, `replace()`, `join()`

## 🔧 高级功能

### 1. 数据提取与链式调用

支持从API响应中提取数据，并在后续测试用例中使用：

```json
{
  "extract": {
    "user_id": "$.data.user.id",
    "access_token": "$.data.token.access_token",
    "order_id": "$.data.order.id"
  }
}
```

### 2. 多种断言方式

- **状态码断言**：验证HTTP状态码
- **JSON Schema断言**：验证响应数据结构
- **正则匹配断言**：使用正则表达式验证响应内容
- **深度比较断言**：使用deepdiff进行深度比较
- **自定义断言**：支持自定义断言函数

### 3. 前后置操作

支持测试用例的前后置操作：
- **前置操作**：数据库清理、测试数据准备、API初始化
- **后置操作**：数据清理、资源释放、日志记录

### 4. OAuth 2.0认证

内置OAuth 2.0客户端，支持多种认证流程：
- 客户端凭证模式（Client Credentials）
- 密码模式（Resource Owner Password Credentials）
- 授权码模式（Authorization Code）

### 5. 测试报告

支持多种测试报告格式：
- **Allure报告**：美观的HTML报告，支持截图、日志附件
- **HTML报告**：简洁的HTML格式报告
- **JSON日志**：结构化的JSON日志，便于CI/CD集成
- **控制台输出**：详细的控制台输出，支持颜色高亮

## 🛠️ 命令行参数

`run.py`脚本支持以下命令行参数：

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--type` | `-t` | 测试类型 | `--type smoke` |
| `--parallel` | `-p` | 并行执行 | `--parallel` |
| `--workers` | `-w` | 工作进程数 | `--workers 4` |
| `--reruns` | `-r` | 失败重试次数 | `--reruns 2` |
| `--report` | `-R` | 生成报告 | `--report` |
| `--open` | `-o` | 打开报告 | `--open` |
| `--validate` | `-V` | 验证测试数据 | `--validate` |
| `--list` | `-l` | 列出测试用例 | `--list` |
| `--template` | `-T` | 生成Excel模板 | `--template` |
| `--help` | `-h` | 显示帮助信息 | `--help` |

## 📝 示例

### 示例1：简单的登录测试

```python
# Excel中的测试用例
test_case_id: TC001
test_case_name: 用户登录
method: POST
endpoint: /api/v1/login
data: |
  {
    "username": "{{ random_email() }}",
    "password": "Test@123456"
  }
expected_status: 200
expected_response: |
  {
    "code": 0,
    "message": "success",
    "data": {
      "token": "{{ regex('^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$') }}"
    }
  }
extract: |
  {
    "access_token": "$.data.token"
  }
```

### 示例2：链式调用测试

```python
# 第一个用例：创建订单
test_case_id: TC002
test_case_name: 创建订单
method: POST
endpoint: /api/v1/orders
data: |
  {
    "product_id": "P001",
    "quantity": 2,
    "price": 99.99
  }
extract: |
  {
    "order_id": "$.data.order_id"
  }

# 第二个用例：查询订单（依赖第一个用例）
test_case_id: TC003
test_case_name: 查询订单
method: GET
endpoint: /api/v1/orders/{{ extract('order_id') }}
depends_on: TC002
```

## 🔍 调试与日志

### 日志级别

支持多种日志级别：
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 日志输出

日志输出到多个位置：
- 控制台：彩色输出，便于调试
- 文件：`output/logs/test_{timestamp}.log`
- Allure报告：作为附件包含在报告中

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](https://github.com/yourusername/api-test-demo/issues)
- 发送邮件：your-email@example.com

## 🔄 迁移指南

### 从旧结构迁移到新结构

#### 1. 测试用例迁移

**旧结构：**
```python
# src/test_cases/test_api.py
from src.common.excel_reader import excel_reader
from src.common.request_client import request_client
from src.common.assert_utils import assert_utils

class BaseTest:
    def setup_class(self):
        self.test_logger = TestLogger(self.__class__.__name__)
```

**新结构：**
```python
# tests/api/test_user_api.py
from src.core.base_test import BaseTest

class TestUserAPI(BaseTest):
    def _before_class(self):
        self.logger.info("测试类初始化")

    def test_example(self):
        # 使用新的工具方法
        response = self.make_request(...)
        self.assert_equal(response.status_code, 200)
```

#### 2. 配置迁移

**旧结构：**
```python
from src.config.configuration import project_config
BASE_URL = project_config.BASE_URL
```

**新结构：**
```python
from src.config.settings import settings
BASE_URL = settings.API_BASE_URL
```

#### 3. 数据加载迁移

**旧结构：**
```python
from src.common.excel_reader import excel_reader
test_cases = excel_reader.get_test_cases("test_cases")
```

**新结构：**
```python
from src.data.data_loader import DataLoader
data_loader = DataLoader()
test_cases = data_loader.get_test_cases("test_cases")
```

#### 4. 主要变化总结

| 旧模块 | 新模块 | 说明 |
|--------|--------|------|
| `src/common/excel_reader.py` | `src/data/data_loader.py` | 支持多种数据格式 |
| `src/common/request_client.py` | `src/clients/http_client.py` | 支持异步请求 |
| `src/common/assert_utils.py` | `src/engine/assertion_engine.py` | 增强断言功能 |
| `src/common/template_engine.py` | `src/engine/template_engine.py` | 优化模板引擎 |
| `src/config/configuration.py` | `src/config/settings.py` | 多环境配置支持 |
| `src/config/logger.py` | `src/utils/logger.py` | JSON格式日志 |
| `src/test_cases/` | `tests/` | 测试用例目录重构 |

### 5. 向后兼容性

框架提供了向后兼容的适配器：

```python
# 兼容性导入（不建议长期使用）
from src.compat.legacy import (
    excel_reader,  # 指向新的DataLoader
    request_client,  # 指向新的HttpClient
    assert_utils,  # 指向新的AssertionEngine
    template_engine,  # 指向新的TemplateEngine
    project_config,  # 指向新的Settings
)
```

## 🙏 致谢

感谢以下开源项目的贡献：
- [pytest](https://docs.pytest.org/) - 测试框架
- [Allure](https://docs.qameta.io/allure/) - 测试报告
- [Jinja2](https://jinja.palletsprojects.com/) - 模板引擎
- [pandas](https://pandas.pydata.org/) - 数据处理
- [requests](https://docs.python-requests.org/) - HTTP客户端