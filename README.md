
# 安装依赖

```shell

## 安装基础依赖
pip install -r requirements.txt

## 安装Allure命令行工具（生成报告需要）
## macOS
brew install allure

## Windows (通过Scoop)
scoop install allure

## Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure


```

# 创建环境配置

```shell

# 复制环境配置文件
cp .env.example .env

# 编辑环境配置
vim .env

```

# 准备测试数据

```shell
## 生成Excel模板
python run.py --template

## 编辑测试数据
vim test_data/api_test_cases.xlsx

```

# 运行测试

```shell

# 运行所有测试
python run.py

# 运行冒烟测试
python run.py --type smoke

# 并行运行测试
python run.py --parallel --workers 4

# 失败重试
python run.py --reruns 2

# 生成报告
python run.py --report --open

# 验证测试数据
python run.py --validate

# 列出测试用例
python run.py --list

```

# Excel模板说明
在Excel中可以使用以下Jinja2模板语法：


| 字段 | 示例 | 说明 |
|------|------|------|
| username | `{{ 'user_' ~ random_int(1000, 9999) }}` | 生成随机用户名 |
| email | `{{ random_email() }}` | 生成随机邮箱 |
| timestamp | `{{ timestamp() }}` | 当前时间戳 |
| order_no | `ORDER_{{ now('%Y%m%d') }}_{{ sequence('order') }}` | 带序列的订单号 |
| signature | `{{ (user_id ~ timestamp()) \| md5 }}` | MD5签名 |
| today | `{{ today() }}` | 今天日期 |
| yesterday | `{{ today(days=-1) }}` | 昨天日期 |


# 后续高级功能
1. **数据提取**：从响应中提取数据供后续用例使用
2. **链式测试**：一个用例的响应作为另一个用例的输入
3. **自定义断言**：支持JSON Schema、正则匹配等
4. **前后置操作**：支持测试前后的API调用、SQL执行等
5. **动态参数**：使用Jinja2模板生成动态测试数据
6. **多种报告**：Allure报告、HTML报告、JSON日志