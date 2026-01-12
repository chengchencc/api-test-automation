继续生成剩余代码：

## 7. 测试用例文件（续）

**test_cases/test_api.py**（续）：
```python
    def _execute_teardown(self, teardown_data: Dict, case_id: str):
        """执行后置操作"""
        self.test_logger.log_step(f"执行后置操作: {case_id}")
        
        # 这里可以执行各种后置操作，如：
        # 1. 数据清理
        # 2. 文件清理
        # 3. 环境恢复
        
        if teardown_data.get('type') == 'api':
            # 执行API后置操作
            teardown_response = request_client.send_request(
                method=teardown_data.get('method', 'DELETE'),
                url=teardown_data.get('url', ''),
                headers=teardown_data.get('headers', {}),
                json_data=teardown_data.get('json', {}),
                data=teardown_data.get('data', {})
            )
            
            # 验证后置操作结果
            expected_status = teardown_data.get('expected_status', 200)
            if teardown_response.status_code != expected_status:
                logger.warning(f"后置操作返回异常状态码: {teardown_response.status_code}")
        
        elif teardown_data.get('type') == 'sql':
            # 执行SQL后置操作
            pass
        
        elif teardown_data.get('type') == 'command':
            # 执行命令后置操作
            import subprocess
            command = teardown_data.get('command', '')
            if command:
                subprocess.run(command, shell=True, check=False)  # 不检查返回码
    
    def _extract_response_data(self, response, extract_rules: Dict) -> Dict:
        """从响应中提取数据"""
        extracted = {}
        
        if not extract_rules or not response.content:
            return extracted
        
        try:
            # 尝试解析JSON响应
            if response.headers.get('Content-Type', '').startswith('application/json'):
                response_data = response.json()
                
                for key, jsonpath in extract_rules.items():
                    try:
                        # 简单的JSON路径提取（支持点表示法）
                        value = self._extract_by_jsonpath(response_data, jsonpath)
                        if value is not None:
                            extracted[key] = value
                            logger.debug(f"提取数据: {key} = {value}")
                    except Exception as e:
                        logger.warning(f"提取字段失败: {key} -> {jsonpath}, 错误: {e}")
            else:
                # 非JSON响应，可以提取文本或使用正则
                response_text = response.text
                for key, pattern in extract_rules.items():
                    if isinstance(pattern, str) and pattern.startswith('regex:'):
                        import re
                        regex = pattern[6:]  # 去掉'regex:'前缀
                        match = re.search(regex, response_text)
                        if match:
                            extracted[key] = match.group(1) if match.groups() else match.group(0)
        
        except json.JSONDecodeError:
            logger.warning("响应不是有效的JSON格式，无法提取数据")
        
        return extracted
    
    def _extract_by_jsonpath(self, data: Any, jsonpath: str) -> Any:
        """使用简单JSON路径提取数据"""
        if not jsonpath or jsonpath == '.':
            return data
        
        # 简单的点表示法实现
        parts = jsonpath.split('.')
        current = data
        
        for part in parts:
            if part == '':
                continue
            
            # 处理数组索引，如items[0]
            if '[' in part and part.endswith(']'):
                # 分割字段名和索引
                import re
                match = re.match(r'(\w+)\[(\d+)\]$', part)
                if match:
                    field_name, index_str = match.groups()
                    index = int(index_str)
                    
                    if isinstance(current, dict) and field_name in current:
                        if isinstance(current[field_name], list) and 0 <= index < len(current[field_name]):
                            current = current[field_name][index]
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                # 普通字段
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit() and 0 <= int(part) < len(current):
                    current = current[int(part)]
                else:
                    return None
        
        return current
    
    def _execute_custom_assertions(self, response, assertions: List[Dict]):
        """执行自定义断言"""
        for idx, assertion in enumerate(assertions):
            try:
                assertion_type = assertion.get('type', '')
                expected = assertion.get('expected')
                actual = assertion.get('actual')
                message = assertion.get('message', f'自定义断言 {idx+1} 失败')
                
                if assertion_type == 'status_code':
                    assert_utils.assert_status_code(response.status_code, expected, message)
                
                elif assertion_type == 'contains':
                    assert_utils.assert_response_contains(response.text, expected, message)
                
                elif assertion_type == 'json_path':
                    # 需要安装jsonpath-ng库
                    try:
                        from jsonpath_ng import parse
                        jsonpath_expr = parse(assertion.get('jsonpath', ''))
                        matches = [match.value for match in jsonpath_expr.find(response.json())]
                        
                        if assertion.get('expect_exists', True):
                            assert matches, f"JSON路径未找到匹配: {assertion.get('jsonpath')}"
                        
                        if expected is not None:
                            if assertion.get('match_type') == 'equals':
                                assert matches[0] == expected, f"JSON路径值不匹配: {matches[0]} != {expected}"
                            elif assertion.get('match_type') == 'contains':
                                assert expected in str(matches[0]), f"JSON路径值不包含: {expected}"
                    except ImportError:
                        logger.warning("jsonpath-ng未安装，跳过JSON路径断言")
                
                elif assertion_type == 'schema':
                    response_json = response.json() if response.content else {}
                    assert_utils.assert_response_schema(response_json, expected, message)
                
                logger.debug(f"自定义断言 {idx+1} 成功: {assertion_type}")
            
            except Exception as e:
                logger.error(f"自定义断言 {idx+1} 失败: {e}")
                raise
    
    def _attach_request_response_to_allure(self, response, test_case: Dict):
        """将请求响应详情附加到Allure报告"""
        
        # 请求信息
        request_info = {
            'method': response.request.method,
            'url': response.request.url,
            'headers': dict(response.request.headers),
            'body': response.request.body
        }
        
        # 响应信息
        response_info = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.text,
            'elapsed': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
        }
        
        # 用例信息
        case_info = {
            'case_id': test_case.get('case_id'),
            'case_name': test_case.get('case_name'),
            'description': test_case.get('description'),
            'severity': test_case.get('severity', 'normal')
        }
        
        # 附加到Allure报告
        allure.attach(
            json.dumps(case_info, indent=2, ensure_ascii=False),
            name="用例信息",
            attachment_type=allure.attachment_type.JSON
        )
        
        allure.attach(
            json.dumps(request_info, indent=2, ensure_ascii=False),
            name="请求详情",
            attachment_type=allure.attachment_type.JSON
        )
        
        # 如果响应是JSON，以JSON格式附加
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                allure.attach(
                    json.dumps(json.loads(response.text), indent=2, ensure_ascii=False),
                    name="响应详情(JSON)",
                    attachment_type=allure.attachment_type.JSON
                )
            except:
                allure.attach(
                    response.text,
                    name="响应详情(Text)",
                    attachment_type=allure.attachment_type.TEXT
                )
        else:
            allure.attach(
                response.text,
                name="响应详情",
                attachment_type=allure.attachment_type.TEXT
            )
    
    @allure.story("基本接口测试")
    @allure.title("健康检查接口")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_health_check(self):
        """健康检查接口测试"""
        response = request_client.get("/health")
        
        assert_utils.assert_status_code(response.status_code, 200)
        assert_utils.assert_response_contains(response.text, "ok")
    
    @allure.story("认证接口测试")
    @allure.title("用户登录接口")
    def test_login(self):
        """用户登录接口测试"""
        login_data = {
            "username": "{{ random_string(8, 'user_') }}",
            "password": "{{ random_string(12) }}",
            "timestamp": "{{ timestamp() }}"
        }
        
        # 渲染模板
        rendered_data = template_engine.render(login_data)
        
        response = request_client.post("/api/login", json_data=rendered_data)
        
        # 综合断言
        assert_utils.assert_response(
            response=response,
            expected_status=200,
            expected_schema={
                "code": int,
                "message": str,
                "data": {
                    "token": str,
                    "user_id": int
                }
            }
        )
    
    @allure.story("参数化测试")
    @pytest.mark.parametrize("username,password,expected_status", [
        ("admin", "admin123", 200),
        ("user", "wrongpass", 401),
        ("", "password", 400),
        ("user", "", 400),
    ])
    def test_login_parameterized(self, username, password, expected_status):
        """参数化登录测试"""
        login_data = {
            "username": username,
            "password": password
        }
        
        response = request_client.post("/api/login", json_data=login_data)
        assert_utils.assert_status_code(response.status_code, expected_status)
    
    @allure.story("文件上传测试")
    def test_file_upload(self):
        """文件上传接口测试"""
        import io
        
        # 创建测试文件
        test_file = io.BytesIO(b"This is a test file content")
        test_file.name = "test.txt"
        
        files = {
            "file": test_file
        }
        
        response = request_client.post("/api/upload", files=files)
        
        assert_utils.assert_status_code(response.status_code, 200)
        assert_utils.assert_response_json(
            response.json(),
            {"code": 0, "message": "success"}
        )
    
    @allure.story("链式接口测试")
    def test_chained_requests(self):
        """链式接口测试（一个接口的响应作为另一个接口的输入）"""
        
        # 1. 先登录获取token
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        login_response = request_client.post("/api/login", json_data=login_data)
        assert_utils.assert_status_code(login_response.status_code, 200)
        
        # 提取token
        login_data = login_response.json()
        token = login_data.get("data", {}).get("token")
        assert token, "登录响应中未找到token"
        
        # 2. 使用token获取用户信息
        request_client.add_header("Authorization", f"Bearer {token}")
        
        user_response = request_client.get("/api/user/profile")
        assert_utils.assert_status_code(user_response.status_code, 200)
        
        # 清理请求头
        request_client.remove_header("Authorization")
    
    @allure.story("性能测试")
    def test_response_time(self):
        """响应时间测试"""
        import time
        
        start_time = time.time()
        response = request_client.get("/api/health")
        elapsed = time.time() - start_time
        
        # 断言响应时间小于1秒
        assert_utils.assert_time(elapsed, 1.0)
        
        # 记录响应时间
        logger.info(f"接口响应时间: {elapsed:.3f}秒")
    
    @allure.story("异常测试")
    def test_invalid_endpoint(self):
        """测试不存在的接口"""
        response = request_client.get("/invalid-endpoint")
        assert_utils.assert_status_code(response.status_code, 404)
    
    @allure.story("动态参数测试")
    def test_dynamic_parameters(self):
        """测试Jinja2动态参数功能"""
        
        # 使用模板引擎生成测试数据
        test_context = {
            "user_id": 12345,
            "order_prefix": "ORD"
        }
        
        # 渲染各种动态参数
        test_cases = [
            ("随机用户名", "{{ 'user_' ~ random_int(1000, 9999) }}"),
            ("带时间戳的订单号", "{{ order_prefix }}_{{ timestamp() }}"),
            ("MD5签名", "{{ (user_id|string ~ timestamp()|string) | md5 }}"),
            ("随机邮箱", "{{ random_string(8) }}@test.com"),
            ("今日日期", "{{ today() }}"),
        ]
        
        for name, template in test_cases:
            result = template_engine.render_string(template, **test_context)
            logger.info(f"{name}: {template} -> {result}")
            assert result, f"模板渲染失败: {template}"
    
    @allure.story("数据驱动测试-多Sheet")
    @pytest.mark.parametrize("sheet_name", ["login_cases", "user_cases", "order_cases"])
    def test_multiple_sheets(self, sheet_name):
        """测试多个Excel Sheet"""
        try:
            test_cases = excel_reader.get_test_cases(sheet_name)
            
            if not test_cases:
                pytest.skip(f"Sheet {sheet_name} 中没有测试用例")
            
            for test_case in test_cases:
                # 简化执行，不记录详细的Allure步骤
                response = request_client.send_request(
                    method=test_case.get('method', 'GET'),
                    url=test_case.get('url', ''),
                    json_data=test_case.get('json', {})
                )
                
                expected_status = test_case.get('expected_status', 200)
                assert_utils.assert_status_code(response.status_code, expected_status)
        
        except Exception as e:
            if "No sheet named" in str(e):
                pytest.skip(f"Sheet {sheet_name} 不存在")
            else:
                raise


class TestDataDriven:
    """数据驱动测试类"""
    
    @pytest.fixture(params=excel_reader.get_test_cases("data_driven"))
    def data_driven_case(self, request):
        """数据驱动测试用例fixture"""
        return request.param
    
    @allure.story("数据驱动测试")
    def test_data_driven(self, data_driven_case):
        """使用fixture的数据驱动测试"""
        case_name = data_driven_case.get('case_name', '未知用例')
        allure.dynamic.title(case_name)
        
        response = request_client.send_request(
            method=data_driven_case.get('method', 'GET'),
            url=data_driven_case.get('url', ''),
            json_data=data_driven_case.get('json', {})
        )
        
        expected_status = data_driven_case.get('expected_status', 200)
        assert_utils.assert_status_code(response.status_code, expected_status)


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "--tb=short"])
```

## 8. 冒烟测试

**test_cases/test_smoke.py:**

```python
import pytest
import allure
from src.test_cases.test_api import TestAPI


@allure.epic("接口自动化测试")
@allure.feature("冒烟测试")
class TestSmoke(TestAPI):
    """冒烟测试类"""

    @pytest.fixture(scope="class", autouse=True)
    def setup_smoke_class(self):
        """冒烟测试类初始化"""
        logger.info("=" * 50)
        logger.info("开始冒烟测试")
        logger.info("=" * 50)
        yield
        logger.info("=" * 50)
        logger.info("冒烟测试结束")
        logger.info("=" * 50)

    @allure.story("核心功能冒烟测试")
    @allure.title("核心接口健康检查")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_smoke_core_apis(self):
        """核心接口冒烟测试"""

        # 定义核心接口列表
        core_apis = [
            {"name": "健康检查", "method": "GET", "url": "/health", "expected_status": 200},
            {"name": "服务状态", "method": "GET", "url": "/api/status", "expected_status": 200},
            {"name": "版本信息", "method": "GET", "url": "/api/version", "expected_status": 200},
        ]

        for api in core_apis:
            with allure.step(f"测试 {api['name']} 接口"):
                response = request_client.send_request(
                    method=api['method'],
                    url=api['url']
                )
                assert_utils.assert_status_code(response.status_code, api['expected_status'])

    @allure.story("关键业务流程冒烟测试")
    @allure.title("用户注册登录流程")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_user_registration_login_flow(self):
        """用户注册登录流程冒烟测试"""

        # 生成测试用户数据
        test_user = {
            "username": f"smoketest_{int(time.time())}",
            "password": "SmokeTest@123",
            "email": f"smoke_{int(time.time())}@test.com"
        }

        # 步骤1: 用户注册
        with allure.step("用户注册"):
            register_response = request_client.post(
                "/api/register",
                json_data=test_user
            )
            assert_utils.assert_status_code(register_response.status_code, 201)

        # 步骤2: 用户登录
        with allure.step("用户登录"):
            login_response = request_client.post(
                "/api/login",
                json_data={
                    "username": test_user["username"],
                    "password": test_user["password"]
                }
            )
            assert_utils.assert_status_code(login_response.status_code, 200)

            # 提取token
            login_data = login_response.json()
            token = login_data.get("data", {}).get("token")
            assert token, "登录响应中未找到token"

        # 步骤3: 获取用户信息
        with allure.step("获取用户信息"):
            request_client.add_header("Authorization", f"Bearer {token}")
            profile_response = request_client.get("/api/user/profile")
            assert_utils.assert_status_code(profile_response.status_code, 200)
            request_client.remove_header("Authorization")

    @allure.story("Excel数据冒烟测试")
    @allure.title("冒烟测试用例集")
    @pytest.mark.smoke
    @pytest.mark.parametrize("test_case", excel_reader.get_test_cases("smoke_cases"))
    def test_smoke_excel_cases(self, test_case):
        """执行Excel中的冒烟测试用例"""

        # 只执行标记为冒烟的用例
        tags = test_case.get('tags', '')
        if 'smoke' not in tags.lower():
            pytest.skip("非冒烟测试用例")

        # 调用父类的测试方法
        self.test_excel_driven(test_case)

    @allure.story("性能冒烟测试")
    @allure.title("接口响应时间冒烟测试")
    @pytest.mark.smoke
    @pytest.mark.performance
    def test_smoke_performance(self):
        """性能冒烟测试"""

        # 测试关键接口的响应时间
        performance_limits = [
            {"name": "健康检查", "url": "/health", "max_time": 0.5},
            {"name": "首页接口", "url": "/api/home", "max_time": 1.0},
            {"name": "配置接口", "url": "/api/config", "max_time": 1.0},
        ]

        for api in performance_limits:
            with allure.step(f"测试 {api['name']} 响应时间"):
                import time
                start_time = time.time()
                response = request_client.get(api['url'])
                elapsed = time.time() - start_time

                # 断言响应状态
                assert_utils.assert_status_code(response.status_code, 200)

                # 断言响应时间
                assert_utils.assert_time(elapsed, api['max_time'])

                allure.attach(
                    f"接口: {api['name']}\n"
                    f"URL: {api['url']}\n"
                    f"响应时间: {elapsed:.3f}秒\n"
                    f"限制时间: {api['max_time']}秒\n"
                    f"结果: {'通过' if elapsed <= api['max_time'] else '失败'}",
                    name=f"{api['name']}性能测试",
                    attachment_type=allure.attachment_type.TEXT
                )

    @allure.story("错误处理冒烟测试")
    @allure.title("异常场景处理测试")
    @pytest.mark.smoke
    def test_smoke_error_handling(self):
        """错误处理冒烟测试"""

        error_scenarios = [
            {
                "name": "不存在的接口",
                "method": "GET",
                "url": "/api/nonexistent",
                "expected_status": 404
            },
            {
                "name": "无效的请求方法",
                "method": "POST",
                "url": "/health",  # 假设健康检查只支持GET
                "expected_status": 405
            },
            {
                "name": "缺少必要参数",
                "method": "POST",
                "url": "/api/login",
                "json_data": {},  # 不传用户名密码
                "expected_status": 400
            },
        ]

        for scenario in error_scenarios:
            with allure.step(f"测试 {scenario['name']}"):
                response = request_client.send_request(
                    method=scenario['method'],
                    url=scenario['url'],
                    json_data=scenario.get('json_data', {})
                )
                assert_utils.assert_status_code(response.status_code, scenario['expected_status'])

    @allure.story("配置验证冒烟测试")
    @allure.title("环境配置验证")
    @pytest.mark.smoke
    def test_smoke_configuration(self):
        """环境配置冒烟测试"""

        # 验证必要的环境配置
        required_configs = [
            ("API_BASE_URL", "基础URL"),
            ("DATABASE_URL", "数据库连接"),
            ("REDIS_URL", "Redis连接"),
        ]

        missing_configs = []

        for config_key, config_name in required_configs:
            config_value = os.environ.get(config_key)
            if not config_value:
                missing_configs.append(config_key)
                logger.warning(f"缺少环境配置: {config_key} ({config_name})")

        if missing_configs:
            allure.attach(
                f"缺少的环境配置: {', '.join(missing_configs)}\n"
                f"请检查 .env 文件或环境变量设置",
                name="环境配置检查",
                attachment_type=allure.attachment_type.TEXT
            )

        # 验证API可访问性
        try:
            response = request_client.get("/health", timeout=5)
            if response.status_code != 200:
                logger.warning(f"API健康检查失败: {response.status_code}")
        except Exception as e:
            logger.error(f"API不可访问: {e}")
            pytest.fail(f"API服务不可访问: {e}")

    @allure.story("依赖服务冒烟测试")
    @allure.title("外部依赖服务检查")
    @pytest.mark.smoke
    def test_smoke_dependencies(self):
        """依赖服务冒烟测试"""

        # 这里可以添加对外部服务的检查
        # 例如：数据库连接、缓存服务、消息队列等

        dependencies = [
            {
                "name": "数据库",
                "check": self._check_database,
                "required": True
            },
            {
                "name": "Redis缓存",
                "check": self._check_redis,
                "required": False
            },
            {
                "name": "文件存储",
                "check": self._check_file_storage,
                "required": False
            },
        ]

        for dependency in dependencies:
            with allure.step(f"检查 {dependency['name']}"):
                try:
                    result = dependency
                    if result:
                        logger.info(f"{dependency['name']} 检查通过")
                        allure.attach(
                            f"{dependency['name']}: 正常",
                            name=f"{dependency['name']}状态",
                            attachment_type=allure.attachment_type.TEXT
                        )
                    else:
                        if dependency["required"]:
                            pytest.fail(f"{dependency['name']} 检查失败")
                        else:
                            logger.warning(f"{dependency['name']} 检查失败（非必需）")
                except Exception as e:
                    if dependency["required"]:
                        pytest.fail(f"{dependency['name']} 检查异常: {e}")
                    else:
                        logger.warning(f"{dependency['name']} 检查异常（非必需）: {e}")

    def _check_database(self):
        """检查数据库连接"""
        # 这里可以添加数据库连接检查
        # 例如：执行一个简单的SQL查询
        try:
            # 如果有数据库配置，尝试连接
            if config.DATABASE_URL:
                import sqlalchemy
                engine = sqlalchemy.create_engine(config.DATABASE_URL)
                connection = engine.connect()
                connection.close()
                return True
            else:
                logger.warning("未配置数据库连接")
                return False
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def _check_redis(self):
        """检查Redis连接"""
        # 这里可以添加Redis连接检查
        try:
            redis_url = os.environ.get("REDIS_URL")
            if redis_url:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                return True
            else:
                logger.warning("未配置Redis连接")
                return False
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False

    def _check_file_storage(self):
        """检查文件存储"""
        # 这里可以添加文件存储检查
        # 例如：检查文件目录是否可写
        try:
            test_dir = Path("/tmp/test_file_storage")
            test_dir.mkdir(exist_ok=True)
            test_file = test_dir / "test.txt"
            test_file.write_text("test")
            test_file.unlink()
            test_dir.rmdir()
            return True
        except Exception as e:
            logger.error(f"文件存储检查失败: {e}")
            return False


@allure.epic("接口自动化测试")
@allure.feature("快速冒烟测试")
@pytest.mark.smoke
class TestQuickSmoke:
    """快速冒烟测试类"""

    @allure.story("快速健康检查")
    @allure.title("5分钟快速冒烟测试")
    @pytest.mark.timeout(300)  # 5分钟超时
    def test_quick_smoke(self):
        """5分钟快速冒烟测试"""

        # 只运行最核心的测试
        test_cases = [
            self._test_health,
            self._test_main_apis,
            self._test_error_handling
        ]

        results = []
        for test_func in test_cases:
            try:
                test_func()
                results.append(True)
            except Exception as e:
                logger.error(f"快速冒烟测试失败: {e}")
                results.append(False)

        # 所有核心测试必须通过
        assert all(results), "快速冒烟测试失败"

    def _test_health(self):
        """测试健康检查"""
        response = request_client.get("/health", timeout=5)
        assert_utils.assert_status_code(response.status_code, 200)

    def _test_main_apis(self):
        """测试主要API"""
        main_apis = ["/api/status", "/api/version", "/api/config"]
        for api in main_apis:
            response = request_client.get(api, timeout=5)
            assert_utils.assert_status_code(response.status_code, 200)

    def _test_error_handling(self):
        """测试错误处理"""
        response = request_client.get("/api/nonexistent", timeout=5)
        assert_utils.assert_status_code(response.status_code, 404)
```

## 9. Pytest配置

**conftest.py:**

```python
import pytest
import allure
import os
import json
from datetime import datetime
from pathlib import Path
from src.config import config
from src.config.logger import logger
from src.common.template_engine import template_engine


def pytest_configure(config):
    """Pytest配置钩子"""
    # 设置环境变量
    os.environ['ALLURE_RESULTS'] = str(config.ALLURE_RESULTS)

    # 创建必要的目录
    config.ALLURE_RESULTS.mkdir(exist_ok=True)

    # 添加自定义标记说明
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "api: API接口测试"
    )
    config.addinivalue_line(
        "markers", "data_driven: 数据驱动测试"
    )

    logger.info("Pytest配置完成")


def pytest_unconfigure(config):
    """Pytest卸载钩子"""
    logger.info("Pytest测试完成")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """获取测试结果并添加附件"""
    outcome = yield
    rep = outcome.get_result()

    # 设置Allure报告属性
    if rep.when == "call":
        # 测试用例执行完成
        if rep.failed:
            # 测试失败
            item.allure_report = rep
            _attach_failure_details(item, rep)
        elif rep.passed:
            # 测试通过
            item.allure_report = rep
        else:
            # 测试跳过
            item.allure_report = rep


def _attach_failure_details(item, rep):
    """附加失败详情到Allure报告"""

    # 获取失败信息
    if rep.longrepr:
        failure_info = str(rep.longrepr)

        # 添加失败信息到Allure
        allure.attach(
            failure_info,
            name="失败详情",
            attachment_type=allure.attachment_type.TEXT
        )

    # 添加日志文件
    log_file = config.LOG_DIR / f"test_{datetime.now().strftime('%Y%m%d')}.log"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
                # 只取最后1000行日志
                log_lines = logs.split('\n')
                recent_logs = '\n'.join(log_lines[-1000:])

                allure.attach(
                    recent_logs,
                    name="测试日志",
                    attachment_type=allure.attachment_type.TEXT
                )
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """测试会话设置"""
    logger.info("=" * 60)
    logger.info("开始测试会话")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"项目目录: {config.BASE_DIR}")
    logger.info(f"测试数据: {config.EXCEL_FILE}")
    logger.info(f"基础URL: {config.BASE_URL}")
    logger.info("=" * 60)

    # 创建测试环境
    yield

    logger.info("=" * 60)
    logger.info("测试会话结束")
    logger.info("=" * 60)


@pytest.fixture(scope="function", autouse=True)
def setup_test_function(request):
    """测试函数设置"""
    test_name = request.node.name
    logger.info(f"开始测试: {test_name}")

    # 记录测试开始时间
    request.start_time = datetime.now()

    yield

    # 记录测试结束时间
    end_time = datetime.now()
    duration = (end_time - request.start_time).total_seconds()
    logger.info(f"结束测试: {test_name}, 耗时: {duration:.2f}秒")


@pytest.fixture
def test_data():
    """测试数据fixture"""
    return {
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "test_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "random_string": template_engine.render_string("{{ random_string(10) }}"),
        "random_int": template_engine.render_string("{{ random_int(1, 1000) }}"),
    }


@pytest.fixture
def auth_token():
    """认证token fixture"""
    # 这里可以获取认证token
    token = os.environ.get("TEST_AUTH_TOKEN", "")
    if not token:
        # 如果没有配置token，尝试登录获取
        try:
            from src.common.request_client import request_client
            login_data = {
                "username": os.environ.get("TEST_USERNAME", "admin"),
                "password": os.environ.get("TEST_PASSWORD", "admin123")
            }
            response = request_client.post("/api/login", json_data=login_data)
            if response.status_code == 200:
                token = response.json().get("data", {}).get("token", "")
        except:
            pass

    return token


@pytest.fixture
def api_client(auth_token):
    """API客户端fixture"""
    from src.common.request_client import RequestClient

    client = RequestClient()

    # 添加认证头
    if auth_token:
        client.add_header("Authorization", f"Bearer {auth_token}")

    yield client

    # 清理
    client.clear_headers()


@pytest.fixture
def excel_test_cases():
    """Excel测试用例fixture"""
    from src.common.excel_reader import excel_reader
    return excel_reader.get_test_cases()


@pytest.fixture
def template_context():
    """模板上下文fixture"""
    context = {
        "timestamp": int(datetime.now().timestamp()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 更新模板引擎上下文
    template_engine.update_context(**context)

    return context


@pytest.fixture
def cleanup():
    """清理fixture"""
    cleanup_items = []

    def _add_cleanup(item):
        cleanup_items.append(item)

    yield _add_cleanup

    # 执行清理
    for item in cleanup_items:
        try:
            if callable(item):
                item()
            elif isinstance(item, dict) and 'type' in item:
                if item['type'] == 'api':
                    from src.common.request_client import request_client
                    request_client.send_request(**item['request'])
        except Exception as e:
            logger.warning(f"清理失败: {e}")


# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        help="测试环境: test, staging, production"
    )
    parser.addoption(
        "--browser",
        action="store_true",
        default=False,
        help="是否在浏览器中打开Allure报告"
    )
    parser.addoption(
        "--parallel",
        action="store_true",
        default=False,
        help="是否并行执行测试"
    )


@pytest.fixture(scope="session")
def test_env(request):
    """测试环境fixture"""
    return request.config.getoption("--env")


# Allure环境文件
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束钩子"""
    # 生成Allure环境文件
    allure_env = {
        "测试环境": os.environ.get("ENVIRONMENT", "test"),
        "基础URL": config.BASE_URL,
        "Python版本": os.environ.get("PYTHON_VERSION", "unknown"),
        "操作系统": os.name,
        "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "项目路径": str(config.BASE_DIR),
    }

    # 写入环境文件
    env_file = config.ALLURE_RESULTS / "environment.properties"
    with open(env_file, 'w', encoding='utf-8') as f:
        for key, value in allure_env.items():
            f.write(f"{key}={value}\n")

    # 生成测试结果汇总
    if hasattr(session, 'testscollected'):
        total = session.testscollected
        passed = len(session.testscollected) - len(session.testsfailed) - len(session.testsskipped)
        failed = len(session.testsfailed)
        skipped = len(session.testsskipped)

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%"
        }

        summary_file = config.ALLURE_RESULTS / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
```

**pytest.ini:**
```ini
[pytest]
# 测试文件匹配模式
testpaths = test_cases
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 命令行参数
addopts = 
    -v
    --strict-markers
    --alluredir=reports/allure-results
    --clean-alluredir
    --tb=short
    --show-capture=log
    --disable-warnings
    -p no:warnings

# 标记定义
markers =
    smoke: 冒烟测试
    regression: 回归测试
    performance: 性能测试
    api: API接口测试
    data_driven: 数据驱动测试
    slow: 慢速测试（执行时间超过30秒）
    db: 需要数据库的测试
    external: 依赖外部服务的测试

# 日志配置
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# 测试超时设置（默认5分钟）
timeout = 300
timeout_method = thread

# 缓存配置
cache_dir = .pytest_cache

# 测试执行配置
xfail_strict = true
# 失败重试
# reruns = 2
# reruns_delay = 1

# 忽略的目录
norecursedirs = .git .idea __pycache__ *.egg-info build dist

# 测试发现配置
consider_namespace_packages = false
consider_testmodule_pattern = test_*.py
consider_testdirectory_pattern = test_*

# 插件配置
junit_family = xunit2
```

## 10. 运行脚本

**run_tests.py:**

```python
#!/usr/bin/env python3
"""
接口自动化测试框架运行脚本
支持Jinja2模板引擎和数据驱动测试
"""
import subprocess
import sys
import os
import argparse
import webbrowser
import time
from datetime import datetime
from pathlib import Path
from src.config import config
from src.config.logger import logger


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def run_tests(self,
                  test_type: str = "all",
                  parallel: bool = False,
                  reruns: int = 0,
                  workers: int = None,
                  html_report: bool = True,
                  **kwargs) -> int:
        """
        运行测试
        
        Args:
            test_type: 测试类型 (all, smoke, api, regression)
            parallel: 是否并行执行
            reruns: 失败重试次数
            workers: 并行工作进程数
            html_report: 是否生成HTML报告
            **kwargs: 其他参数
            
        Returns:
            退出码
        """
        self.start_time = time.time()

        # 基本pytest命令
        cmd = [
            "pytest",
            f"--alluredir={config.ALLURE_RESULTS}",
            "--clean-alluredir",
            "-v",
            "--disable-warnings",
        ]

        # 根据测试类型添加标记
        if test_type == "smoke":
            cmd.append("-m smoke")
            logger.info("运行冒烟测试")
        elif test_type == "api":
            cmd.append("-m api")
            logger.info("运行API测试")
        elif test_type == "regression":
            cmd.append("-m regression")
            logger.info("运行回归测试")
        elif test_type == "performance":
            cmd.append("-m performance")
            logger.info("运行性能测试")
        elif test_type != "all":
            # 自定义标记
            cmd.append(f"-m {test_type}")
            logger.info(f"运行 {test_type} 测试")

        # 并行执行
        if parallel:
            if workers:
                cmd.extend(["-n", str(workers)])
            else:
                cmd.extend(["-n", "auto"])
            logger.info("启用并行测试")

        # 失败重试
        if reruns > 0:
            cmd.extend(["--reruns", str(reruns), "--reruns-delay", "2"])
            logger.info(f"启用失败重试: {reruns}次")

        # HTML报告
        if html_report:
            html_report_path = config.get_html_report_path()
            cmd.extend([
                f"--html={html_report_path}",
                "--self-contained-html"
            ])

        # 添加额外的命令行参数
        for key, value in kwargs.items():
            if value is True:
                cmd.append(f"--{key.replace('_', '-')}")
            elif value is not False and value is not None:
                cmd.append(f"--{key.replace('_', '-')}={value}")

        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info("-" * 60)

        # 执行测试
        try:
            result = subprocess.run(cmd)
            exit_code = result.returncode
        except KeyboardInterrupt:
            logger.warning("测试被用户中断")
            exit_code = 130
        except Exception as e:
            logger.error(f"执行测试失败: {e}")
            exit_code = 1

        self.end_time = time.time()
        duration = self.end_time - self.start_time

        logger.info("-" * 60)
        if exit_code == 0:
            logger.info(f"测试执行成功，耗时: {duration:.2f}秒")
        else:
            logger.error(f"测试执行失败，退出码: {exit_code}，耗时: {duration:.2f}秒")

        return exit_code

    def generate_allure_report(self, open_browser: bool = False) -> int:
        """生成Allure报告"""
        logger.info("生成Allure报告...")

        if not config.ALLURE_RESULTS.exists() or not any(config.ALLURE_RESULTS.iterdir()):
            logger.warning("没有测试结果，跳过生成Allure报告")
            return 0

        # 生成Allure报告
        cmd = [
            "allure", "generate",
            str(config.ALLURE_RESULTS),
            "-o", str(config.ALLURE_REPORT),
            "--clean"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                report_url = config.get_allure_report_url()
                logger.info(f"Allure报告生成成功: {report_url}")

                # 在浏览器中打开报告
                if open_browser:
                    self.open_allure_report()

                return 0
            else:
                logger.error(f"Allure报告生成失败: {result.stderr}")
                return result.returncode

        except FileNotFoundError:
            logger.error("Allure未安装，请先安装Allure: https://docs.qameta.io/allure/")
            return 1
        except Exception as e:
            logger.error(f"生成Allure报告失败: {e}")
            return 1

    def open_allure_report(self):
        """打开Allure报告"""
        if (config.ALLURE_REPORT / "index.html").exists():
            report_url = config.get_allure_report_url()
            logger.info(f"在浏览器中打开报告: {report_url}")

            try:
                webbrowser.open(report_url)
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")
        else:
            logger.error("Allure报告不存在，请先运行测试并生成报告")

    def open_html_report(self):
        """打开HTML报告"""
        html_report_path = config.get_html_report_path()
        if html_report_path.exists():
            report_url = f"file://{html_report_path.absolute()}"
            logger.info(f"在浏览器中打开HTML报告: {report_url}")

            try:
                webbrowser.open(report_url)
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")
        else:
            logger.error("HTML报告不存在，请先运行测试")

    def list_test_cases(self):
        """列出所有测试用例"""
        from src.common.excel_reader import excel_reader

        logger.info("列出所有测试用例:")
        logger.info("=" * 60)

        suites = excel_reader.get_test_suites()
        total_cases = 0

        for sheet_name, test_cases in suites.items():
            logger.info(f"测试套件: {sheet_name} ({len(test_cases)} 个用例)")

            for case in test_cases:
                case_id = case.get('case_id', '未知')
                case_name = case.get('case_name', '未知')
                method = case.get('method', 'GET')
                url = case.get('url', '')
                logger.info(f"  {case_id}: {case_name} [{method} {url}]")

            total_cases += len(test_cases)

        logger.info("=" * 60)
        logger.info(f"总计: {len(suites)} 个测试套件, {total_cases} 个测试用例")

    def validate_test_data(self):
        """验证测试数据"""
        from src.common.excel_reader import excel_reader

        logger.info("验证测试数据...")

        try:
            # 验证Excel文件
            if not config.EXCEL_FILE.exists():
                logger.error(f"测试数据文件不存在: {config.EXCEL_FILE}")
                return 1

            # 读取测试用例
            test_cases = excel_reader.get_test_cases(render_templates=False)

            if not test_cases:
                logger.warning("没有找到测试用例")
                return 0

            # 验证每个用例
            valid_cases = 0
            invalid_cases = []

            for case in test_cases:
                case_id = case.get('case_id', '未知')
                case_name = case.get('case_name', '')

                # 基本验证
                errors = []

                if not case_name:
                    errors.append("缺少用例名称")

                if not case.get('method'):
                    errors.append("缺少请求方法")

                if not case.get('url'):
                    errors.append("缺少URL")

                if errors:
                    invalid_cases.append((case_id, case_name, errors))
                else:
                    valid_cases += 1

            # 输出验证结果
            logger.info(f"验证完成:")
            logger.info(f"  有效用例: {valid_cases}")
            logger.info(f"  无效用例: {len(invalid_cases)}")

            if invalid_cases:
                logger.warning("无效用例列表:")
                for case_id, case_name, errors in invalid_cases:
                    logger.warning(f"  {case_id}: {case_name}")
                    for error in errors:
                        logger.warning(f"    - {error}")
                return 1

            return 0

        except Exception as e:
            logger.error(f"验证测试数据失败: {e}")
            return 1

    def clear_reports(self):
        """清理测试报告"""
        import shutil

        logger.info("清理测试报告...")

        for report_dir in [config.ALLURE_RESULTS, config.ALLURE_REPORT, config.REPORT_DIR]:
            if report_dir.exists():
                try:
                    shutil.rmtree(report_dir)
                    logger.info(f"已删除: {report_dir}")
                except Exception as e:
                    logger.error(f"删除失败 {report_dir}: {e}")

        # 重新创建目录
        config.REPORT_DIR.mkdir(exist_ok=True)
        logger.info("清理完成")

    def generate_excel_template(self):
        """生成Excel模板文件"""
        import pandas as pd
        from openpyxl import Workbook

        logger.info("生成Excel模板文件...")

        # 创建模板文件路径
        template_file = config.TEST_DATA_DIR / "api_test_cases_template.xlsx"

        # 定义测试用例模板
        test_cases_data = [
            {
                "case_id": "TC001",
                "case_name": "示例用例-健康检查",
                "description": "测试健康检查接口",
                "tags": "smoke,api",
                "severity": "critical",
                "method": "GET",
                "url": "/health",
                "headers": '{"Content-Type": "application/json"}',
                "params": "{}",
                "data": "",
                "json": "",
                "expected_status": 200,
                "expected_response": '{"status": "ok"}',
                "expected_schema": "",
                "expected_contains": "ok",
                "max_response_time": 1.0,
                "setup_data": "",
                "teardown_data": "",
                "extract": '{"token": "data.token"}',
                "assertions": '[{"type": "status_code", "expected": 200}]'
            },
            {
                "case_id": "TC002",
                "case_name": "示例用例-用户登录",
                "description": "测试用户登录接口，使用动态参数",
                "tags": "regression,api",
                "severity": "critical",
                "method": "POST",
                "url": "/api/login",
                "headers": '{"Content-Type": "application/json"}',
                "params": "",
                "data": "",
                "json": '{"username": "{{ random_string(8, \\"user_\\") }}", "password": "{{ random_string(12) }}", "timestamp": "{{ timestamp() }}"}',
                "expected_status": 200,
                "expected_response": '{"code": 0, "message": "success"}',
                "expected_schema": '{"code": "int", "message": "str", "data": {"token": "str", "user_id": "int"}}',
                "expected_contains": "",
                "max_response_time": 2.0,
                "setup_data": "",
                "teardown_data": "",
                "extract": '{"auth_token": "data.token", "user_id": "data.user_id"}',
                "assertions": '[{"type": "json_path", "jsonpath": "$.code", "expected": 0}]'
            }
        ]

        # 定义配置模板
        config_data = [
            {"key": "base_url", "value": "http://api.example.com"},
            {"key": "timeout", "value": "30"},
            {"key": "admin_user", "value": "admin"},
            {"key": "admin_password", "value": "admin123"},
        ]

        try:
            with pd.ExcelWriter(template_file, engine='openpyxl') as writer:
                # 写入测试用例
                df_cases = pd.DataFrame(test_cases_data)
                df_cases.to_excel(writer, sheet_name='test_cases', index=False)

                # 写入配置
                df_config = pd.DataFrame(config_data)
                df_config.to_excel(writer, sheet_name='config', index=False)

                # 写入说明
                wb = writer.book
                ws = wb.create_sheet("说明")

                instructions = [
                    ["Excel测试数据文件说明", "", "", ""],
                    ["", "", "", ""],
                    ["Sheet名称", "说明", "必填列", "示例"],
                    ["test_cases", "测试用例", "case_name, method, url", ""],
                    ["config", "配置文件", "key, value", ""],
                    ["", "", "", ""],
                    ["Jinja2模板语法示例:", "", "", ""],
                    ["变量替换", "{{ timestamp() }}", "当前时间戳", ""],
                    ["随机字符串", "{{ random_string(10) }}", "10位随机字符串", ""],
                    ["随机整数", "{{ random_int(1, 100) }}", "1-100随机整数", ""],
                    ["随机邮箱", "{{ random_email() }}", "随机邮箱地址", ""],
                    ["UUID", "{{ uuid() }}", "UUID字符串", ""],
                    ["今日日期", "{{ today() }}", "今天日期", ""],
                    ["日期计算", "{{ today(days=-1) }}", "昨天日期", ""],
                    ["序列号", "{{ sequence('order') }}", "订单序列号", ""],
                    ["", "", "", ""],
                    ["过滤器示例:", "", "", ""],
                    ["MD5", "{{ 'password' | md5 }}", "计算MD5", ""],
                    ["截断", "{{ 'long text' | truncate(5) }}", "截断文本", ""],
                    ["JSON", "{{ data | to_json }}", "转换为JSON", ""],
                ]

                for row in instructions:
                    ws.append(row)

            logger.info(f"Excel模板生成成功: {template_file}")
            return 0

        except Exception as e:
            logger.error(f"生成Excel模板失败: {e}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="接口自动化测试框架 - 基于Jinja2模板引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 运行所有测试
  python run.py
  
  # 运行冒烟测试
  python run.py --type smoke
  
  # 并行运行测试
  python run.py --parallel --workers 4
  
  # 失败重试
  python run.py --reruns 2
  
  # 生成报告并在浏览器中打开
  python run.py --report --open
  
  # 验证测试数据
  python run.py --validate
  
  # 列出所有测试用例
  python run.py --list
        """
    )

    # 测试运行选项
    parser.add_argument("--type", "-t",
                        choices=["all", "smoke", "api", "regression", "performance"],
                        default="all",
                        help="测试类型")
    parser.add_argument("--parallel", "-p",
                        action="store_true",
                        help="并行执行测试")
    parser.add_argument("--workers", "-w",
                        type=int,
                        help="并行工作进程数")
    parser.add_argument("--reruns", "-r",
                        type=int,
                        default=0,
                        help="失败重试次数")
    parser.add_argument("--html",
                        action="store_true",
                        default=True,
                        help="生成HTML报告")
    parser.add_argument("--no-html",
                        action="store_false",
                        dest="html",
                        help="不生成HTML报告")

    # 报告选项
    parser.add_argument("--report",
                        action="store_true",
                        help="生成Allure报告")
    parser.add_argument("--open",
                        action="store_true",
                        help="在浏览器中打开Allure报告")
    parser.add_argument("--open-html",
                        action="store_true",
                        help="在浏览器中打开HTML报告")

    # 工具选项
    parser.add_argument("--list", "-l",
                        action="store_true",
                        help="列出所有测试用例")
    parser.add_argument("--validate",
                        action="store_true",
                        help="验证测试数据")
    parser.add_argument("--clear",
                        action="store_true",
                        help="清理测试报告")
    parser.add_argument("--template",
                        action="store_true",
                        help="生成Excel模板文件")

    # 其他选项
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="详细输出")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logger.setLevel("DEBUG")
        logger.debug("启用详细日志")

    # 创建测试运行器
    runner = TestRunner()

    # 执行工具命令
    if args.list:
        runner.list_test_cases()
        return 0

    if args.validate:
        return runner.validate_test_data()

    if args.clear:
        runner.clear_reports()
        return 0

    if args.template:
        return runner.generate_excel_template()

    if args.open_html:
        runner.open_html_report()
        return 0

    # 生成报告
    if args.report:
        return runner.generate_allure_report(args.open)

    # 运行测试
    exit_code = runner.run_tests(
        test_type=args.type,
        parallel=args.parallel,
        reruns=args.reruns,
        workers=args.workers,
        html_report=args.html
    )

    # 生成报告
    if exit_code == 0 or exit_code == 1:  # 0: 成功, 1: 测试失败
        runner.generate_allure_report(args.open)

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)
```

## 11. 环境配置示例

**.env.example:**
```env
# 环境配置
ENVIRONMENT=test

# API配置
API_BASE_URL=http://api.example.com
REQUEST_TIMEOUT=30
VERIFY_SSL=False
MAX_RETRY=3

# 数据库配置（可选）
DATABASE_URL=postgresql://user:password@localhost:5432/testdb
REDIS_URL=redis://localhost:6379/0

# 测试账号
TEST_USERNAME=admin
TEST_PASSWORD=admin123
TEST_AUTH_TOKEN=

# 邮件配置（可选）
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=user@example.com
EMAIL_PASSWORD=password

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s

# 测试配置
TEST_RUNNER=pytest
TEST_PARALLEL=False
TEST_RERUNS=0

# 模板配置
TEMPLATE_AUTO_RELOAD=True
TEMPLATE_STRICT_MODE=False
```

## 12. 使用说明

### 安装依赖
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装Allure命令行工具（生成报告需要）
# macOS
brew install allure

# Windows (通过Scoop)
scoop install allure

# Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure
```

### 创建环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑环境配置
vim .env
```

### 准备测试数据
```bash
# 生成Excel模板
python run.py --template

# 编辑测试数据
vim test_data/api_test_cases.xlsx
```

### 运行测试
```bash
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

### Excel模板说明
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

### 高级功能
1. **数据提取**：从响应中提取数据供后续用例使用
2. **链式测试**：一个用例的响应作为另一个用例的输入
3. **自定义断言**：支持JSON Schema、正则匹配等
4. **前后置操作**：支持测试前后的API调用、SQL执行等
5. **动态参数**：使用Jinja2模板生成动态测试数据
6. **多种报告**：Allure报告、HTML报告、JSON日志

这个完整的框架提供了强大的接口自动化测试能力，支持复杂的数据驱动和模板化测试，能够满足大多数接口测试场景的需求。