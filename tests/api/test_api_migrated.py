"""
迁移后的API测试用例
从旧的test_api.py迁移而来，使用新的框架结构
"""
import pytest
import allure
import json
import time
from typing import Dict, Any, List
from src.core.base_test import BaseTest


@allure.epic("接口自动化测试")
@allure.feature("基础接口测试")
class TestAPIMigrated(BaseTest):
    """API测试类（迁移版）"""

    def _before_class(self):
        """测试类初始化"""
        self.logger.info("API测试类初始化")

        # 从Excel加载测试用例（兼容旧方式）
        try:
            from src.compat.legacy import excel_reader
            self.old_test_cases = excel_reader.get_test_cases("test_cases")
            self.logger.info(f"从Excel加载了 {len(self.old_test_cases)} 个测试用例")
        except Exception as e:
            self.logger.warning(f"加载Excel测试用例失败: {e}")
            self.old_test_cases = []

    @allure.story("Excel数据驱动测试")
    @pytest.mark.parametrize("test_case", [
        {"case_id": "TC001", "case_name": "示例测试", "method": "GET", "url": "/api/test"}
    ])
    def test_excel_driven_migrated(self, test_case: Dict[str, Any]):
        """
        执行Excel中的测试用例（迁移版）

        Args:
            test_case: 测试用例数据
        """
        # 获取测试用例信息
        case_id = test_case.get('case_id', 'unknown')
        case_name = test_case.get('case_name', '未知用例')
        description = test_case.get('description', '')
        method = test_case.get('method', 'GET').upper()
        url = test_case.get('url', '')
        headers = test_case.get('headers', {})
        params = test_case.get('params', {})
        data = test_case.get('data', {})
        json_data = test_case.get('json', {})
        expected_status = test_case.get('expected_status', 200)
        expected_response = test_case.get('expected_response', {})

        # 设置Allure报告信息
        allure.dynamic.title(f"{case_id}: {case_name}")
        allure.dynamic.description(description or f"测试用例: {case_name}")

        # 设置标签
        tags = test_case.get('tags', '').split(',') if test_case.get('tags') else []
        for tag in tags:
            if tag.strip():
                allure.dynamic.tag(tag.strip())

        # 设置严重级别
        severity = test_case.get('severity', 'normal').lower()
        if severity == 'blocker':
            allure.dynamic.severity(allure.severity_level.BLOCKER)
        elif severity == 'critical':
            allure.dynamic.severity(allure.severity_level.CRITICAL)
        elif severity == 'normal':
            allure.dynamic.severity(allure.severity_level.NORMAL)
        elif severity == 'minor':
            allure.dynamic.severity(allure.severity_level.MINOR)
        elif severity == 'trivial':
            allure.dynamic.severity(allure.severity_level.TRIVIAL)

        self.logger.info(f"执行测试用例: {case_id} - {case_name}")

        # 构建完整的URL
        base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
        full_url = f"{base_url}{url}" if url.startswith('/') else url

        # 准备请求数据
        request_data = {}
        if data:
            request_data['data'] = data
        if json_data:
            request_data['json'] = json_data
        if params:
            request_data['params'] = params

        # 添加请求头
        if headers:
            request_data['headers'] = headers

        try:
            # 发起请求
            with self.step(f"发送{method}请求"):
                response = self.make_request(
                    method=method,
                    url=full_url,
                    **request_data
                )

                # 附加请求和响应信息到报告
                self.attach_json("请求数据", {
                    "method": method,
                    "url": full_url,
                    "headers": headers,
                    "data": data,
                    "json": json_data,
                    "params": params
                })
                self.attach_json("响应数据", response.json())
                self.attach_text("响应状态码", str(response.status_code))
                self.attach_text("响应头", str(dict(response.headers)))

            # 验证响应状态码
            with self.step("验证状态码"):
                self.assert_equal(
                    response.status_code,
                    expected_status,
                    f"状态码验证失败: 期望 {expected_status}, 实际 {response.status_code}"
                )

            # 验证响应内容
            if expected_response:
                with self.step("验证响应内容"):
                    actual_response = response.json()

                    # 如果是字符串，尝试解析为JSON
                    if isinstance(expected_response, str):
                        try:
                            expected_response = json.loads(expected_response)
                        except json.JSONDecodeError:
                            # 如果是普通字符串，直接比较
                            self.assert_equal(
                                str(actual_response),
                                expected_response,
                                "响应内容不匹配"
                            )
                            return

                    # 如果是字典，进行深度比较
                    if isinstance(expected_response, dict):
                        self._assert_response_dict(actual_response, expected_response)

            self.logger.info(f"测试用例 {case_id} 执行成功")

        except Exception as e:
            self.logger.error(f"测试用例 {case_id} 执行失败: {e}")
            raise

    def _assert_response_dict(self, actual: Dict[str, Any], expected: Dict[str, Any]):
        """断言响应字典"""
        for key, expected_value in expected.items():
            self.assert_in(key, actual, f"响应中缺少字段: {key}")

            actual_value = actual[key]

            # 如果是字典，递归比较
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                self._assert_response_dict(actual_value, expected_value)
            # 如果是列表，比较每个元素
            elif isinstance(expected_value, list) and isinstance(actual_value, list):
                self.assert_equal(
                    len(actual_value),
                    len(expected_value),
                    f"列表长度不匹配: {key}"
                )
                for i, (actual_item, expected_item) in enumerate(zip(actual_value, expected_value)):
                    if isinstance(expected_item, dict) and isinstance(actual_item, dict):
                        self._assert_response_dict(actual_item, expected_item)
                    else:
                        self.assert_equal(
                            actual_item,
                            expected_item,
                            f"列表元素不匹配: {key}[{i}]"
                        )
            else:
                self.assert_equal(
                    actual_value,
                    expected_value,
                    f"字段值不匹配: {key}"
                )

    @allure.story("简单API测试")
    @allure.title("基础GET请求测试")
    def test_simple_get_request(self):
        """简单GET请求测试"""
        with self.step("准备测试数据"):
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            test_url = f"{base_url}/api/test"

        with self.step("发送GET请求"):
            response = self.make_request("GET", test_url)
            self.attach_json("响应数据", response.json())

        with self.step("验证响应"):
            self.assert_equal(response.status_code, 200)
            self.assert_in("code", response.json())
            self.assert_in("message", response.json())

    @allure.story("带参数的API测试")
    @allure.title("带查询参数的GET请求")
    def test_get_with_params(self):
        """带查询参数的GET请求测试"""
        with self.step("准备查询参数"):
            params = {
                "page": 1,
                "size": 10,
                "keyword": "test"
            }

        with self.step("发送带参数的GET请求"):
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            response = self.make_request(
                "GET",
                f"{base_url}/api/search",
                params=params
            )
            self.attach_json("响应数据", response.json())

        with self.step("验证响应"):
            self.assert_equal(response.status_code, 200)

    @allure.story("POST请求测试")
    @allure.title("JSON格式的POST请求")
    def test_post_json_request(self):
        """JSON格式的POST请求测试"""
        with self.step("准备请求数据"):
            request_data = {
                "username": self.render_template("{{ random_email() }}"),
                "password": "Test@123456",
                "timestamp": int(time.time())
            }

        with self.step("发送POST请求"):
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            response = self.make_request(
                "POST",
                f"{base_url}/api/login",
                json=request_data
            )
            self.attach_json("响应数据", response.json())

        with self.step("验证响应"):
            self.assert_equal(response.status_code, 200)

            response_data = response.json()
            self.assert_in("code", response_data)
            self.assert_in("message", response_data)

            # 如果登录成功，应该返回token
            if response_data.get("code") == 0:
                self.assert_in("data", response_data)
                self.assert_in("token", response_data["data"])

    @allure.story("错误处理测试")
    @allure.title("404 Not Found测试")
    def test_404_not_found(self):
        """测试404错误处理"""
        with self.step("发送不存在的URL请求"):
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            response = self.make_request(
                "GET",
                f"{base_url}/api/nonexistent"
            )

        with self.step("验证404响应"):
            self.assert_equal(response.status_code, 404)

            # 有些API可能返回JSON格式的错误信息
            if response.headers.get('Content-Type', '').startswith('application/json'):
                error_data = response.json()
                self.assert_in("error", error_data)
                self.assert_in("message", error_data)

    @allure.story("性能测试")
    @allure.title("请求响应时间测试")
    def test_response_time(self):
        """测试请求响应时间"""
        import time

        with self.step("测量响应时间"):
            start_time = time.time()

            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            response = self.make_request("GET", f"{base_url}/api/test")

            end_time = time.time()
            duration = end_time - start_time

            self.attach_text("响应时间", f"{duration:.3f}秒")

        with self.step("验证性能要求"):
            # 要求响应时间小于3秒
            max_duration = 3.0
            self.assert_true(
                duration < max_duration,
                f"响应时间 {duration:.3f}秒超过最大允许时间 {max_duration}秒"
            )

            self.logger.info(f"请求响应时间: {duration:.3f}秒")

    @allure.story("兼容性测试")
    @allure.title("使用旧框架的测试")
    def test_with_old_framework(self):
        """测试与旧框架的兼容性"""
        try:
            # 尝试使用兼容性模块
            from src.compat.legacy import excel_reader, request_client

            with self.step("使用旧Excel读取器"):
                config = excel_reader.get_config()
                self.logger.info(f"从旧配置读取BASE_URL: {config.get('BASE_URL')}")
                self.context.add_data('old_base_url', config.get('BASE_URL'))

            with self.step("使用旧HTTP客户端"):
                # 注意：旧客户端可能需要额外配置
                self.logger.info("旧HTTP客户端可用")

        except ImportError as e:
            self.logger.warning(f"兼容性模块不可用: {e}")
            pytest.skip("兼容性模块未安装")
        except Exception as e:
            self.logger.error(f"使用旧框架失败: {e}")
            raise