"""
用户API测试用例
展示如何使用新的框架结构
"""
import pytest
import allure
from src.core.base_test import BaseTest


@allure.epic("用户管理")
@allure.feature("用户API")
class TestUserAPI(BaseTest):
    """用户API测试类"""

    def _before_class(self):
        """测试类前置操作"""
        self.logger.info("用户API测试类初始化")
        # 可以在这里进行一些初始化操作，比如创建测试用户

    def _after_class(self):
        """测试类后置操作"""
        self.logger.info("用户API测试类清理")
        # 可以在这里进行清理操作，比如删除测试用户

    def _before_test(self, method):
        """测试方法前置操作"""
        self.logger.info(f"准备执行测试: {method.__name__}")
        # 可以在这里重置测试数据

    @allure.story("用户登录")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "api")
    def test_user_login(self):
        """测试用户登录"""
        with self.step("准备登录数据"):
            # 使用模板引擎生成测试数据
            username = self.render_template("{{ random_email() }}")
            password = "Test@123456"

            login_data = {
                "username": username,
                "password": password
            }

            self.attach_json("登录请求数据", login_data)

        with self.step("发送登录请求"):
            response = self.make_request(
                method="POST",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/login",
                json=login_data
            )

            self.attach_json("登录响应", response.json())
            self.attach_text("响应状态码", str(response.status_code))

        with self.step("验证登录结果"):
            self.assert_equal(response.status_code, 200, "状态码应为200")
            self.assert_in("token", response.json(), "响应应包含token")

            # 提取token供后续测试使用
            token = response.json()["token"]
            self.context.add_data("auth_token", token)

            self.logger.info(f"登录成功，获取到token: {token[:20]}...")

    @allure.story("获取用户信息")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api", "regression")
    def test_get_user_info(self):
        """测试获取用户信息"""
        # 从上下文获取登录token
        token = self.context.get_data("auth_token")
        if not token:
            pytest.skip("需要先登录获取token")

        with self.step("发送获取用户信息请求"):
            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = self.make_request(
                method="GET",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/user/info",
                headers=headers
            )

            self.attach_json("用户信息响应", response.json())

        with self.step("验证用户信息"):
            self.assert_equal(response.status_code, 200, "状态码应为200")

            user_info = response.json()
            self.assert_in("id", user_info, "用户信息应包含id")
            self.assert_in("username", user_info, "用户信息应包含username")
            self.assert_in("email", user_info, "用户信息应包含email")

            # 验证邮箱格式
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            self.assert_true(
                re.match(email_pattern, user_info["email"]),
                f"邮箱格式不正确: {user_info['email']}"
            )

    @allure.story("更新用户信息")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api")
    def test_update_user_info(self):
        """测试更新用户信息"""
        token = self.context.get_data("auth_token")
        if not token:
            pytest.skip("需要先登录获取token")

        with self.step("准备更新数据"):
            update_data = {
                "nickname": self.render_template("用户_{{ random_int(1000, 9999) }}"),
                "avatar": "https://example.com/avatar.jpg",
                "bio": "这是一个测试用户"
            }

            self.attach_json("更新数据", update_data)

        with self.step("发送更新请求"):
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = self.make_request(
                method="PUT",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/user/info",
                headers=headers,
                json=update_data
            )

            self.attach_json("更新响应", response.json())

        with self.step("验证更新结果"):
            self.assert_equal(response.status_code, 200, "状态码应为200")

            result = response.json()
            self.assert_equal(result["code"], 0, "返回码应为0")
            self.assert_equal(result["message"], "success", "返回消息应为success")

            # 验证更新后的数据
            if "data" in result:
                updated_user = result["data"]
                self.assert_equal(updated_user["nickname"], update_data["nickname"], "昵称应更新成功")

    @allure.story("用户注销")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api", "cleanup")
    def test_user_logout(self):
        """测试用户注销"""
        token = self.context.get_data("auth_token")
        if not token:
            pytest.skip("需要先登录获取token")

        with self.step("发送注销请求"):
            headers = {
                "Authorization": f"Bearer {token}"
            }

            response = self.make_request(
                method="POST",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/logout",
                headers=headers
            )

            self.attach_json("注销响应", response.json())

        with self.step("验证注销结果"):
            self.assert_equal(response.status_code, 200, "状态码应为200")

            result = response.json()
            self.assert_equal(result["code"], 0, "返回码应为0")
            self.assert_equal(result["message"], "success", "返回消息应为success")

            # 清理上下文中的token
            self.context.add_data("auth_token", None)
            self.logger.info("用户注销成功")

    @allure.story("用户注册")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("api", "smoke")
    @pytest.mark.parametrize("user_data", [
        {
            "username": "test_user_1@example.com",
            "password": "Test@123456",
            "nickname": "测试用户1"
        },
        {
            "username": "test_user_2@example.com",
            "password": "Test@123456",
            "nickname": "测试用户2"
        }
    ])
    def test_user_registration(self, user_data):
        """测试用户注册（参数化测试）"""
        with self.step("准备注册数据"):
            # 使用模板渲染用户名
            if "{{" in user_data["username"]:
                user_data["username"] = self.render_template(user_data["username"])

            self.attach_json("注册数据", user_data)

        with self.step("发送注册请求"):
            response = self.make_request(
                method="POST",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/register",
                json=user_data
            )

            self.attach_json("注册响应", response.json())

        with self.step("验证注册结果"):
            self.assert_equal(response.status_code, 201, "状态码应为201")

            result = response.json()
            self.assert_in("id", result, "响应应包含用户ID")
            self.assert_in("username", result, "响应应包含用户名")
            self.assert_equal(result["username"], user_data["username"], "用户名应一致")

            # 验证密码不包含在响应中
            self.assert_not_in("password", result, "响应不应包含密码")

    @allure.story("错误处理")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("api", "error")
    def test_login_with_invalid_credentials(self):
        """测试使用无效凭证登录"""
        with self.step("准备无效的登录数据"):
            invalid_data = {
                "username": "invalid_user@example.com",
                "password": "WrongPassword123"
            }

            self.attach_json("无效登录数据", invalid_data)

        with self.step("发送登录请求"):
            response = self.make_request(
                method="POST",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/login",
                json=invalid_data
            )

            self.attach_json("错误响应", response.json())

        with self.step("验证错误处理"):
            self.assert_equal(response.status_code, 401, "状态码应为401")

            error_response = response.json()
            self.assert_in("error", error_response, "错误响应应包含error字段")
            self.assert_in("message", error_response, "错误响应应包含message字段")

            self.logger.info(f"错误处理正常: {error_response['message']}")

    @allure.story("性能测试")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("performance", "slow")
    def test_login_performance(self):
        """测试登录性能"""
        import time

        with self.step("准备测试数据"):
            username = self.render_template("{{ random_email() }}")
            password = "Test@123456"

            login_data = {
                "username": username,
                "password": password
            }

        with self.step("执行性能测试"):
            start_time = time.time()

            response = self.make_request(
                method="POST",
                url=f"{self.context.get_data('base_url', 'http://localhost:8000')}/api/v1/login",
                json=login_data
            )

            end_time = time.time()
            duration = end_time - start_time

            self.attach_text("请求耗时", f"{duration:.3f}秒")

            # 验证性能要求
            max_duration = 2.0  # 最大允许2秒
            self.assert_true(
                duration < max_duration,
                f"登录请求耗时 {duration:.3f}秒，超过最大允许时间 {max_duration}秒"
            )

            self.logger.info(f"登录请求耗时: {duration:.3f}秒")

        with self.step("验证响应"):
            self.assert_equal(response.status_code, 200, "状态码应为200")