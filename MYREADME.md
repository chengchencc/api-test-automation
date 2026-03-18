# API测试使用文档

## 1. 运行API测试

### 基本命令

```bash
# 运行所有API测试 慎用！是所有的测试文件，包括子文件夹下的测试文件
python3 run.py --type api

# 运行指定Excel文件的API测试
python3 run.py --type api --fn api_test_cases.xlsx

# 运行指定文件夹下的API测试
python3 run.py --type api --fr test_folder

```

### 命令参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--type api` | 指定运行API测试 | 必选 |
| `--fn` | 指定Excel文件名 | `--fn api_test_cases.xlsx` |
| `--fr` | 指定测试数据文件夹 | `--fr aa` |

## 2. api_test_cases.xlsx 列说明

### 列详细解释和示例

| 列名 | 必选 | 类型 | 解释说明 | 示例 |
|------|------|------|----------|------|
| `case_id` | 是 | 字符串 | 测试用例唯一标识符，建议使用TCXXX格式 | `TC001` |
| `case_name` | 是 | 字符串 | 测试用例名称，描述测试的功能点 | `用户登录` |
| `description` | 否 | 字符串 | 测试用例的详细描述 | `测试用户使用正确用户名密码登录` |
| `tags` | 否 | 字符串 | 测试标签，用于分类和筛选测试用例，多个标签用逗号分隔 | `smoke,api,login` |
| `severity` | 否 | 字符串 | 测试用例的严重程度，可选值：blocker、critical、normal、minor、trivial | `critical` |
| `method` | 是 | 字符串 | HTTP请求方法，支持：GET、POST、PUT、DELETE、PATCH、HEAD、OPTIONS | `POST` |
| `url` | 是 | 字符串 | API接口的URL路径 | `/api/auth:signIn` |
| `headers` | 否 | JSON | 请求头信息，支持模板语法 | `{"Content-Type": "application/json", "Authorization": "Bearer {{token}}"}` |
| `params` | 否 | JSON | URL查询参数，JSON格式 | `{"page": 1, "pageSize": 20}` |
| `data` | 否 | JSON | 表单数据，用于application/x-www-form-urlencoded请求 | `{"username": "admin", "password": "123456"}` |
| `json` | 否 | JSON | JSON数据，用于application/json请求 | `{"username": "admin", "password": "123456"}` |
| `expected_status` | 是 | 数字 | 预期的HTTP状态码 | `200` |
| `expected_response` | 否 | JSON | 预期的响应数据，JSON格式 | `{"success": true, "data": {"token": "abc123"}}` |
| `expected_schema` | 否 | JSON | 预期的响应数据结构 | `{"success": "bool", "data": "object", "message": "string"}` |
| `expected_contains` | 否 | 字符串 | 预期响应中包含的文本 | `success` |
| `max_response_time` | 否 | 数字 | 最大响应时间（秒） | `1` |
| `setup_data` | 否 | JSON | 前置操作数据，支持API调用等 | `{"type": "api", "method": "POST", "url": "/api/setup", "json": {"key": "value"}}` |
| `teardown_data` | 否 | JSON | 后置操作数据，支持API调用等 | `{"type": "api", "method": "DELETE", "url": "/api/cleanup"}` |
| `extract` | 否 | JSON | 从响应中提取数据到缓存，键为缓存变量名，值为JSON路径 | `{"token": "data.token", "user_id": "data.user.id"}` |
| `assertions` | 否 | JSON | 自定义断言，JSON数组格式 | `[{"type": "status_code", "expected": 200}, {"type": "json_path", "jsonpath": "$.data.user.id", "expected": 1, "match_type": "equals"}]` |
| `sleep` | 否 | 数字 | 执行接口前的等待时间（秒） | `1` |

### 列使用示例

#### 1. case_id
- 用于唯一标识测试用例
- 建议使用统一的命名规范，如TC001、TC002
- 示例：`TC001`

#### 2. case_name
- 简洁描述测试用例的功能
- 示例：`用户登录`、`获取用户列表`

#### 3. description
- 详细描述测试用例的目的和测试场景
- 示例：`测试用户使用正确的用户名和密码进行登录`

#### 4. tags
- 用于分类测试用例，方便筛选
- 多个标签用逗号分隔
- 示例：`smoke,api,login`

#### 5. severity
- 标识测试用例的重要程度
- 可选值：blocker、critical、normal、minor、trivial
- 示例：`critical`

#### 6. method
- 指定HTTP请求方法
- 支持的方法：GET、POST、PUT、DELETE、PATCH、HEAD、OPTIONS
- 示例：`POST`

#### 7. url
- API接口的路径
- 示例：`/api/auth:signIn`、`/api/users`

#### 8. headers
- 请求头信息，JSON格式
- 支持使用模板语法引用缓存变量
- 示例：
  ```json
  {"Content-Type": "application/json", "Authorization": "Bearer {{token}}"}
  ```

#### 9. params
- URL查询参数，JSON格式
- 示例：
  ```json
  {"page": 1, "pageSize": 20}
  ```

#### 10. data
- 表单数据，用于application/x-www-form-urlencoded请求
- 示例：
  ```json
  {"username": "admin", "password": "123456"}
  ```

#### 11. json
- JSON数据，用于application/json请求
- 示例：
  ```json
  {"username": "admin", "password": "123456"}
  ```

#### 12. expected_status
- 预期的HTTP状态码
- 示例：`200`、`400`、`401`

#### 13. expected_response
- 预期的响应数据，JSON格式
- 示例：
  ```json
  {"success": true, "data": {"token": "abc123"}}
  ```

#### 14. expected_schema
- 预期的响应数据结构
- 示例：
  ```json
  {"success": "bool", "data": "object", "message": "string"}
  ```

#### 15. expected_contains
- 预期响应中包含的文本
- 示例：`success`、`token`

#### 16. max_response_time
- 最大响应时间（秒）
- 示例：`1`（1秒）

#### 17. setup_data
- 前置操作数据，JSON格式
- 支持API调用、SQL执行等操作
- 示例：
  ```json
  {"type": "api", "method": "POST", "url": "/api/setup", "json": {"key": "value"}}
  ```

#### 18. teardown_data
- 后置操作数据，JSON格式
- 示例：
  ```json
  {"type": "api", "method": "DELETE", "url": "/api/cleanup"}
  ```

#### 19. extract
- 从响应中提取数据到缓存
- 键为缓存变量名，值为JSON路径
- 示例：
  ```json
  {"token": "data.token", "user_id": "data.user.id"}
  ```

#### 20. assertions
- 自定义断言，JSON数组格式
- 支持多种断言类型
- 示例：
  ```json
  [
    {"type": "status_code", "expected": 200},
    {"type": "json_path", "jsonpath": "$.data.user.id", "expected": 1, "match_type": "equals"}
  ]
  ```

#### 21. sleep
- 执行接口前的等待时间（秒）
- 用于控制接口执行的间隔，避免接口调用过于频繁
- 支持小数形式的等待时间
- 示例：
  - `1`：等待1秒
  - `0.5`：等待0.5秒
  - `0`或空：不等待

## 3. 模板语法

测试数据支持Jinja2模板语法，可以使用变量和函数：

### 常用模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{ timestamp() }}` | 当前时间戳 | `{{ timestamp() }}` |
| `{{ random_string(10) }}` | 随机字符串 | `{{ random_string(8) }}` |
| `{{ random_int(1, 100) }}` | 随机整数 | `{{ random_int(1, 100) }}` |
| `{{ random_float(1.0, 10.0) }}` | 随机浮点数 | `{{ random_float(1.0, 10.0, 2) }}` |
| `{{ today() }}` | 今天日期 | `{{ today() }}` |
| `{{ sequence('order') }}` | 序列号 | `{{ sequence('user_id') }}` |
| `{{ cache.token }}` | 缓存中的token | `{{ cache.token }}` |
| `{{ token }}` | 直接使用缓存变量 | `{{ token }}` |

### 模板使用示例

#### 1. 使用随机数据
```json
{"username": "user{{ random_int(1000, 9999) }}", "email": "user{{ random_int(1000, 9999) }}@example.com"}
```

#### 2. 使用缓存中的token
```json
{"Authorization": "Bearer {{ token }}"}
```

#### 3. 使用时间戳
```json
{"timestamp": {{ timestamp() }}, "nonce": "{{ random_string(16) }}"}
```

## 4. 测试报告

### 报告生成

测试完成后，系统会自动生成两种报告：

1. **HTML报告**：存储在 `output/reports/` 目录，文件名格式为 `[测试文件夹_]年月日_时分秒.html`


## 5. 示例测试用例

### 登录测试

| 列名 | 值 |
|------|------|
| case_id | TC001 |
| case_name | 用户登录 |
| method | POST |
| url | /api/auth:signIn |
| headers | `{"Content-Type": "application/json"}` |
| json | `{"username": "admin", "password": "123456"}` |
| expected_status | 200 |
| extract | `{"token": "data.token"}` |

### 使用token访问接口

| 列名 | 值 |
|------|------|
| case_id | TC002 |
| case_name | 获取用户列表 |
| method | GET |
| url | /api/users |
| headers | `{"Authorization": "Bearer {{ token }}"}` |
| expected_status | 200 |
| expected_contains | users |

### 带断言的测试

| 列名 | 值 |
|------|------|
| case_id | TC003 |
| case_name | 验证用户信息 |
| method | GET |
| url | /api/users/1 |
| headers | `{"Authorization": "Bearer {{ token }}"}` |
| expected_status | 200 |
| assertions | `[{"type": "json_path", "jsonpath": "$.data.name", "expected": "zhangsan", "match_type": "equals"}]` |

### 带等待时间的测试

| 列名 | 值 |
|------|------|
| case_id | TC004 |
| case_name | 带等待时间的接口调用 |
| method | POST |
| url | /api/rate-limited |
| headers | `{"Content-Type": "application/json"}` |
| json | `{"action": "process"}` |
| expected_status | 200 |
| sleep | 1 |