"""
迁移后的数据驱动测试用例
从旧的test_data_driven.py迁移而来，使用新的框架结构
"""
import pytest
import allure
from typing import Dict, Any
from src.core.base_test import BaseTest


@allure.epic("数据驱动测试")
@allure.feature("Excel数据驱动")
class TestDataDrivenMigrated(BaseTest):
    """数据驱动测试类（迁移版）"""

    def _before_class(self):
        """测试类初始化"""
        self.logger.info("数据驱动测试类初始化")

        # 尝试从Excel加载测试用例
        try:
            from src.data.data_loader import DataLoader
            data_loader = DataLoader()
            self.test_cases = data_loader.get_test_cases("test_cases")
            self.logger.info(f"从数据加载器加载了 {len(self.test_cases)} 个测试用例")
        except Exception as e:
            self.logger.warning(f"使用新数据加载器失败: {e}")

            # 回退到兼容性模块
            try:
                from src.compat.legacy import excel_reader
                self.test_cases = excel_reader.get_test_cases("data_driven")
                self.logger.info(f"从兼容性模块加载了 {len(self.test_cases)} 个测试用例")
            except Exception as e2:
                self.logger.error(f"加载测试用例失败: {e2}")
                self.test_cases = []

    @pytest.fixture(params=[
        {"case_name": "测试用例1", "method": "GET", "url": "/api/test1", "expected_status": 200},
        {"case_name": "测试用例2", "method": "POST", "url": "/api/test2", "expected_status": 201},
        {"case_name": "测试用例3", "method": "PUT", "url": "/api/test3", "expected_status": 200},
    ])
    def data_driven_case(self, request):
        """数据驱动测试用例fixture"""
        return request.param

    @allure.story("Fixture数据驱动测试")
    def test_data_driven_with_fixture(self, data_driven_case: Dict[str, Any]):
        """使用fixture的数据驱动测试"""
        case_name = data_driven_case.get('case_name', '未知用例')
        allure.dynamic.title(case_name)

        self.logger.info(f"执行数据驱动测试: {case_name}")

        with self.step("准备请求参数"):
            method = data_driven_case.get('method', 'GET')
            url_path = data_driven_case.get('url', '')
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            full_url = f"{base_url}{url_path}" if url_path.startswith('/') else url_path

            json_data = data_driven_case.get('json', {})
            expected_status = data_driven_case.get('expected_status', 200)

        with self.step(f"发送{method}请求"):
            response = self.make_request(
                method=method,
                url=full_url,
                json=json_data if json_data else None
            )

            self.attach_json("请求数据", {
                "method": method,
                "url": full_url,
                "json": json_data
            })
            self.attach_json("响应数据", response.json())

        with self.step("验证响应"):
            self.assert_equal(
                response.status_code,
                expected_status,
                f"状态码验证失败: 期望 {expected_status}, 实际 {response.status_code}"
            )

        self.logger.info(f"数据驱动测试 {case_name} 执行成功")

    @allure.story("参数化数据驱动测试")
    @pytest.mark.parametrize("method,url_path,expected_status", [
        ("GET", "/api/users", 200),
        ("POST", "/api/users", 201),
        ("PUT", "/api/users/1", 200),
        ("DELETE", "/api/users/1", 204),
    ])
    def test_parametrized_data_driven(self, method: str, url_path: str, expected_status: int):
        """参数化数据驱动测试"""
        test_name = f"{method} {url_path}"
        allure.dynamic.title(test_name)

        self.logger.info(f"执行参数化测试: {test_name}")

        with self.step("构建请求URL"):
            base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
            full_url = f"{base_url}{url_path}"

        with self.step(f"发送{method}请求"):
            # 根据方法准备不同的请求数据
            request_data = {}
            if method in ["POST", "PUT"]:
                request_data['json'] = {
                    "name": self.render_template("用户_{{ random_int(1000, 9999) }}"),
                    "email": self.render_template("{{ random_email() }}"),
                    "timestamp": int(pytest.__import__('time').time())
                }

            response = self.make_request(method, full_url, **request_data)

            if request_data.get('json'):
                self.attach_json("请求数据", request_data['json'])
            self.attach_json("响应数据", response.json())

        with self.step("验证响应"):
            self.assert_equal(
                response.status_code,
                expected_status,
                f"状态码验证失败: 期望 {expected_status}, 实际 {response.status_code}"
            )

        self.logger.info(f"参数化测试 {test_name} 执行成功")

    @allure.story("从Excel加载的数据驱动测试")
    def test_excel_data_driven(self):
        """从Excel加载数据的数据驱动测试"""
        if not self.test_cases:
            pytest.skip("没有可用的测试用例数据")

        self.logger.info(f"执行Excel数据驱动测试，共 {len(self.test_cases)} 个用例")

        for i, test_case in enumerate(self.test_cases[:5]):  # 限制前5个用例
            case_id = test_case.get('case_id', f'CASE_{i+1}')
            case_name = test_case.get('case_name', f'测试用例 {i+1}')

            with self.step(f"执行用例 {case_id}: {case_name}"):
                self._execute_excel_test_case(test_case)

        self.logger.info("Excel数据驱动测试完成")

    def _execute_excel_test_case(self, test_case: Dict[str, Any]):
        """执行单个Excel测试用例"""
        case_id = test_case.get('case_id', 'unknown')
        case_name = test_case.get('case_name', '未知用例')
        method = test_case.get('method', 'GET').upper()
        url_path = test_case.get('url', '')
        expected_status = test_case.get('expected_status', 200)

        # 构建完整URL
        base_url = self.context.get_data('base_url', 'https://yw.gjrdjj.com')
        full_url = f"{base_url}{url_path}" if url_path.startswith('/') else url_path

        # 准备请求数据
        request_data = {}
        if test_case.get('json'):
            request_data['json'] = test_case['json']
        if test_case.get('data'):
            request_data['data'] = test_case['data']
        if test_case.get('params'):
            request_data['params'] = test_case['params']
        if test_case.get('headers'):
            request_data['headers'] = test_case['headers']

        try:
            # 发送请求
            response = self.make_request(method, full_url, **request_data)

            # 验证响应
            self.assert_equal(
                response.status_code,
                expected_status,
                f"用例 {case_id} 状态码验证失败"
            )

            # 验证响应内容（如果有预期响应）
            if test_case.get('expected_response'):
                self._validate_expected_response(
                    response.json(),
                    test_case['expected_response'],
                    case_id
                )

            self.logger.info(f"用例 {case_id} 执行成功")

        except Exception as e:
            self.logger.error(f"用例 {case_id} 执行失败: {e}")
            # 记录错误但不中断整个测试
            self.context.add_error(e)
            pytest.fail(f"用例 {case_id} 执行失败: {e}")

    def _validate_expected_response(self, actual_response, expected_response, case_id: str):
        """验证预期响应"""
        import json

        # 如果expected_response是字符串，尝试解析为JSON
        if isinstance(expected_response, str):
            try:
                expected_response = json.loads(expected_response)
            except json.JSONDecodeError:
                # 如果是普通字符串，直接比较
                self.assert_equal(
                    str(actual_response),
                    expected_response,
                    f"用例 {case_id} 响应内容不匹配"
                )
                return

        # 如果是字典，验证关键字段
        if isinstance(expected_response, dict):
            for key, expected_value in expected_response.items():
                self.assert_in(
                    key,
                    actual_response,
                    f"用例 {case_id} 响应缺少字段: {key}"
                )

                actual_value = actual_response[key]

                # 如果是嵌套字典，递归验证
                if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                    self._validate_expected_response(actual_value, expected_value, case_id)
                else:
                    self.assert_equal(
                        actual_value,
                        expected_value,
                        f"用例 {case_id} 字段 {key} 值不匹配"
                    )

    @allure.story("动态数据生成测试")
    @allure.title("使用模板引擎生成测试数据")
    def test_template_data_generation(self):
        """测试使用模板引擎生成动态测试数据"""
        with self.step("生成各种测试数据"):
            # 生成随机邮箱
            random_email = self.render_template("{{ random_email() }}")
            self.logger.info(f"生成随机邮箱: {random_email}")

            # 生成随机用户名
            random_username = self.render_template("user_{{ random_int(1000, 9999) }}")
            self.logger.info(f"生成随机用户名: {random_username}")

            # 生成当前时间戳
            timestamp = self.render_template("{{ timestamp() }}")
            self.logger.info(f"生成时间戳: {timestamp}")

            # 生成订单号
            order_no = self.render_template("ORDER_{{ now('%Y%m%d') }}_{{ sequence('order') }}")
            self.logger.info(f"生成订单号: {order_no}")

            # 生成MD5签名
            signature = self.render_template("{{ (random_username ~ timestamp) | md5 }}")
            self.logger.info(f"生成MD5签名: {signature[:16]}...")

        with self.step("使用动态数据发起请求"):
            request_data = {
                "username": random_username,
                "email": random_email,
                "order_no": order_no,
                "signature": signature,
                "timestamp": int(timestamp)
            }

            self.attach_json("动态生成的请求数据", request_data)

            # 这里可以实际发起请求
            self.logger.info("动态数据生成测试完成")

    @allure.story("数据提取测试")
    @allure.title("从响应中提取数据")
    def test_data_extraction(self):
        """测试从API响应中提取数据"""
        # 模拟一个API响应
        mock_response = {
            "code": 0,
            "message": "success",
            "data": {
                "user": {
                    "id": 12345,
                    "username": "test_user",
                    "email": "test@example.com",
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                },
                "profile": {
                    "nickname": "测试用户",
                    "avatar": "https://example.com/avatar.jpg"
                }
            }
        }

        with self.step("从响应中提取数据"):
            # 提取用户ID
            user_id = mock_response["data"]["user"]["id"]
            self.context.add_data("extracted_user_id", user_id)

            # 提取token
            token = mock_response["data"]["user"]["token"]
            self.context.add_data("extracted_token", token)

            # 提取用户信息
            user_info = {
                "username": mock_response["data"]["user"]["username"],
                "email": mock_response["data"]["user"]["email"]
            }
            self.context.add_data("extracted_user_info", user_info)

        with self.step("验证提取的数据"):
            extracted_user_id = self.context.get_data("extracted_user_id")
            extracted_token = self.context.get_data("extracted_token")
            extracted_user_info = self.context.get_data("extracted_user_info")

            self.assert_equal(extracted_user_id, 12345, "用户ID提取错误")
            self.assert_true(extracted_token.startswith("eyJ"), "Token格式错误")
            self.assert_in("username", extracted_user_info, "用户信息缺少username")
            self.assert_in("email", extracted_user_info, "用户信息缺少email")

            self.logger.info(f"提取的用户ID: {extracted_user_id}")
            self.logger.info(f"提取的Token: {extracted_token[:20]}...")
            self.logger.info(f"提取的用户信息: {extracted_user_info}")

    @allure.story("链式测试")
    @allure.title("多个测试用例的链式执行")
    def test_chained_test_cases(self):
        """测试多个测试用例的链式执行"""
        # 第一个测试：获取token
        with self.step("第一步：获取访问令牌"):
            mock_token_response = {
                "code": 0,
                "message": "success",
                "data": {
                    "access_token": "mock_access_token_123",
                    "refresh_token": "mock_refresh_token_456",
                    "expires_in": 3600
                }
            }

            access_token = mock_token_response["data"]["access_token"]
            self.context.add_data("access_token", access_token)
            self.logger.info(f"获取到访问令牌: {access_token[:20]}...")

        # 第二个测试：使用token访问受保护接口
        with self.step("第二步：使用令牌访问用户信息"):
            access_token = self.context.get_data("access_token")
            self.assert_is_not_none(access_token, "访问令牌不能为空")

            # 模拟使用token访问用户信息
            headers = {"Authorization": f"Bearer {access_token}"}
            mock_user_response = {
                "code": 0,
                "message": "success",
                "data": {
                    "id": 12345,
                    "username": "test_user",
                    "email": "test@example.com"
                }
            }

            user_id = mock_user_response["data"]["id"]
            self.context.add_data("user_id", user_id)
            self.logger.info(f"获取到用户ID: {user_id}")

        # 第三个测试：使用用户ID执行操作
        with self.step("第三步：使用用户ID更新信息"):
            user_id = self.context.get_data("user_id")
            self.assert_is_not_none(user_id, "用户ID不能为空")

            # 模拟更新用户信息
            update_data = {
                "nickname": self.render_template("更新用户_{{ random_int(1000, 9999) }}"),
                "bio": "这是通过链式测试更新的用户信息"
            }

            self.attach_json("更新数据", update_data)
            self.logger.info(f"使用用户ID {user_id} 更新信息")

        self.logger.info("链式测试执行完成")