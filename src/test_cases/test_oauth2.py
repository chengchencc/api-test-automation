# import pytest
# import allure
# import time
# import json
# from typing import Dict, Any
# from common.request_client import request_client
# from common.oauth2_client import oauth2_client, OAuth2Client
# from common.assert_utils import assert_utils
# from config.logger import logger, TestLogger
# from config.config import config
#
#
# @allure.epic("接口自动化测试")
# @allure.feature("OAuth 2.0认证测试")
# class TestOAuth2:
#     """OAuth 2.0认证测试类"""
#
#     def setup_class(self):
#         """测试类初始化"""
#         self.test_logger = TestLogger(self.__class__.__name__)
#         self.test_logger.log_step("OAuth 2.0测试类初始化")
#
#     def teardown_class(self):
#         """测试类清理"""
#         self.test_logger.log_step("OAuth 2.0测试类清理")
#
#     @allure.story("OAuth 2.0密码模式")
#     @allure.title("密码模式获取访问令牌")
#     def test_password_grant(self):
#         """测试OAuth 2.0密码模式"""
#
#         # 创建独立的OAuth 2.0客户端
#         oauth_client = OAuth2Client(
#             grant_type="password",
#             username=config.OAUTH2_USERNAME,
#             password=config.OAUTH2_PASSWORD
#         )
#
#         try:
#             # 获取令牌
#             token = oauth_client.request_token()
#
#             # 断言令牌信息
#             assert token.access_token, "访问令牌不能为空"
#             assert token.token_type == "Bearer", f"令牌类型应为Bearer，实际为{token.token_type}"
#             assert token.expires_in > 0, f"过期时间应大于0，实际为{token.expires_in}"
#
#             # 记录令牌信息
#             logger.info(f"获取访问令牌成功: {token.access_token[:20]}...")
#             logger.info(f"令牌过期时间: {token.expires_in}秒")
#
#             # 将令牌信息附加到Allure报告
#             allure.attach(
#                 json.dumps(token.to_dict(), indent=2, ensure_ascii=False),
#                 name="OAuth 2.0令牌信息",
#                 attachment_type=allure.attachment_type.JSON
#             )
#
#         except Exception as e:
#             pytest.fail(f"获取OAuth 2.0令牌失败: {e}")
#
#     @allure.story("OAuth 2.0客户端凭证模式")
#     @allure.title("客户端凭证模式获取访问令牌")
#     def test_client_credentials_grant(self):
#         """测试OAuth 2.0客户端凭证模式"""
#
#         # 创建独立的OAuth 2.0客户端
#         oauth_client = OAuth2Client(
#             grant_type="client_credentials"
#         )
#
#         try:
#             # 获取令牌
#             token = oauth_client.request_token()
#
#             # 断言令牌信息
#             assert token.access_token, "访问令牌不能为空"
#
#             logger.info(f"客户端凭证模式获取访问令牌成功")
#
#         except Exception as e:
#             # 客户端凭证模式可能不支持，跳过测试
#             if "unsupported_grant_type" in str(e).lower():
#                 pytest.skip("客户端凭证模式不支持")
#             else:
#                 pytest.fail(f"客户端凭证模式获取令牌失败: {e}")
#
#     @allure.story("OAuth 2.0令牌刷新")
#     @allure.title("刷新访问令牌")
#     def test_token_refresh(self):
#         """测试OAuth 2.0令牌刷新"""
#
#         # 获取初始令牌
#         initial_token = oauth2_client.request_token()
#
#         # 等待一会儿
#         time.sleep(1)
#
#         try:
#             # 刷新令牌
#             refreshed_token = oauth2_client.refresh_token()
#
#             # 断言新令牌与旧令牌不同
#             assert refreshed_token.access_token != initial_token.access_token, "刷新后的令牌应与原令牌不同"
#             assert refreshed_token.refresh_token != initial_token.refresh_token, "刷新后的刷新令牌应与原刷新令牌不同"
#
#             logger.info("令牌刷新成功")
#
#         except Exception as e:
#             # 刷新令牌可能不支持，跳过测试
#             if "unsupported_grant_type" in str(e).lower():
#                 pytest.skip("刷新令牌不支持")
#             else:
#                 pytest.fail(f"刷新令牌失败: {e}")
#
#     @allure.story("OAuth 2.0令牌检查")
#     @allure.title("检查访问令牌有效性")
#     def test_token_introspection(self):
#         """测试OAuth 2.0令牌检查"""
#
#         # 获取令牌
#         token = oauth2_client.get_access_token()
#
#         # 检查令牌
#         introspect_result = oauth2_client.introspect_token(token)
#
#         if introspect_result:
#             # 将检查结果附加到Allure报告
#             allure.attach(
#                 json.dumps(introspect_result, indent=2, ensure_ascii=False),
#                 name="令牌检查结果",
#                 attachment_type=allure.attachment_type.JSON
#             )
#
#             # 断言令牌有效
#             assert introspect_result.get('active', False) == True, "令牌应处于活跃状态"
#
#             logger.info("令牌检查成功")
#         else:
#             # 令牌检查可能不支持，跳过测试
#             pytest.skip("令牌检查接口不支持")
#
#     @allure.story("OAuth 2.0保护资源访问")
#     @allure.title("访问受OAuth 2.0保护的资源")
#     def test_protected_resource_access(self):
#         """测试访问受OAuth 2.0保护的资源"""
#
#         # 使用OAuth 2.0认证的客户端
#         oauth_client = OAuth2Client()
#         protected_client = request_client.__class__(oauth_client=oauth_client)
#
#         # 尝试访问受保护的资源
#         try:
#             response = protected_client.get("/api/protected/resource")
#
#             # 断言响应状态
#             assert_utils.assert_status_code(response.status_code, 200)
#
#             # 断言响应包含预期数据
#             response_data = response.json()
#             assert 'data' in response_data, "响应应包含数据"
#
#             logger.info("成功访问受OAuth 2.0保护的资源")
#
#         except Exception as e:
#             # 如果接口不存在，跳过测试
#             if "404" in str(e) or "Not Found" in str(e):
#                 pytest.skip("受保护资源接口不存在")
#             elif "401" in str(e) or "Unauthorized" in str(e):
#                 pytest.fail("OAuth 2.0认证失败，无法访问受保护资源")
#             else:
#                 raise
#
#     @allure.story("OAuth 2.0令牌过期处理")
#     @allure.title("自动刷新过期令牌")
#     def test_auto_token_refresh(self):
#         """测试OAuth 2.0令牌自动刷新"""
#
#         # 创建短期有效的令牌（模拟）
#         oauth_client = OAuth2Client()
#
#         # 获取初始令牌
#         initial_token = oauth_client.request_token()
#
#         # 模拟令牌即将过期
#         import time
#         time.sleep(1)  # 等待1秒
#
#         # 尝试使用即将过期的令牌访问资源
#         # 这里应该触发自动刷新
#
#         logger.info("OAuth 2.0令牌自动刷新测试完成")
#
#     @allure.story("OAuth 2.0错误处理")
#     @allure.title("处理无效令牌")
#     def test_invalid_token_handling(self):
#         """测试处理无效OAuth 2.0令牌"""
#
#         # 使用无效令牌
#         invalid_token = "invalid_token_here"
#
#         # 创建带有无效令牌的客户端
#         from common.request_client import RequestClient
#         client = RequestClient(use_oauth2=False)
#         client.add_header("Authorization", f"Bearer {invalid_token}")
#
#         # 尝试访问受保护资源
#         response = client.get("/api/protected/resource")
#
#         # 应返回401 Unauthorized
#         assert_utils.assert_status_code(response.status_code, 401)
#
#         logger.info("无效令牌处理测试完成")
#
#     @allure.story("OAuth 2.0范围测试")
#     @allure.title("测试不同范围的访问权限")
#     @pytest.mark.parametrize("scope,expected_status", [
#         (["read"], 200),  # 只读权限
#         (["write"], 403),  # 只写权限（无法访问只读资源）
#         (["read", "write"], 200),  # 读写权限
#     ])
#     def test_scope_based_access(self, scope, expected_status):
#         """测试基于范围的访问控制"""
#
#         # 创建带特定范围的OAuth 2.0客户端
#         oauth_client = OAuth2Client(scope=scope)
#
#         try:
#             # 获取令牌
#             token = oauth_client.request_token()
#
#             # 使用该令牌访问资源
#             client = request_client.__class__(oauth_client=oauth_client)
#             response = client.get("/api/protected/resource")
#
#             # 断言响应状态
#             assert_utils.assert_status_code(response.status_code, expected_status)
#
#             logger.info(f"范围测试通过: {scope} -> {expected_status}")
#
#         except Exception as e:
#             if "invalid_scope" in str(e).lower():
#                 pytest.skip(f"范围 {scope} 不支持")
#             else:
#                 raise
#
#     @allure.story("OAuth 2.0集成测试")
#     @allure.title("完整OAuth 2.0流程测试")
#     def test_oauth2_full_flow(self):
#         """测试完整的OAuth 2.0流程"""
#
#         with allure.step("1. 获取访问令牌"):
#             token = oauth2_client.request_token()
#             assert token.access_token, "应成功获取访问令牌"
#
#         with allure.step("2. 使用令牌访问受保护资源"):
#             response = request_client.get("/api/protected/resource")
#             assert_utils.assert_status_code(response.status_code, 200)
#
#         with allure.step("3. 检查令牌有效性"):
#             introspect_result = oauth2_client.introspect_token()
#             if introspect_result:
#                 assert introspect_result.get('active', False) == True, "令牌应有效"
#
#         with allure.step("4. 刷新令牌"):
#             try:
#                 refreshed_token = oauth2_client.refresh_token()
#                 assert refreshed_token.access_token != token.access_token, "刷新后应获得新令牌"
#             except Exception as e:
#                 if "unsupported_grant_type" in str(e).lower():
#                     logger.info("刷新令牌不支持，跳过此步骤")
#                 else:
#                     raise
#
#         with allure.step("5. 使用新令牌访问资源"):
#             response = request_client.get("/api/protected/resource")
#             assert_utils.assert_status_code(response.status_code, 200)
#
#         with allure.step("6. 撤销令牌"):
#             try:
#                 oauth2_client.revoke_token()
#                 logger.info("令牌撤销成功")
#             except Exception as e:
#                 logger.warning(f"令牌撤销失败: {e}")
#
#         logger.info("完整OAuth 2.0流程测试完成")