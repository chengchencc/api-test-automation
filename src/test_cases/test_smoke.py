# import pytest
# import allure
#
# from ..config.logger import logger
# from test_api import TestAPI
#
#
# @allure.epic("接口自动化测试")
# @allure.feature("冒烟测试")
# class TestSmoke(TestAPI):
#     """冒烟测试类"""
#
#     @pytest.fixture(scope="class", autouse=True)
#     def setup_smoke_class(self):
#         """冒烟测试类初始化"""
#         logger.info("=" * 50)
#         logger.info("开始冒烟测试")
#         logger.info("=" * 50)
#         yield
#         logger.info("=" * 50)
#         logger.info("冒烟测试结束")
#         logger.info("=" * 50)
#
#     @allure.story("核心功能冒烟测试")
#     @allure.title("核心接口健康检查")
#     @allure.severity(allure.severity_level.BLOCKER)
#     @pytest.mark.smoke
#     def test_smoke_core_apis(self):
#         """核心接口冒烟测试"""
#
#         # 定义核心接口列表
#         core_apis = [
#             {"name": "健康检查", "method": "GET", "url": "/health", "expected_status": 200},
#             {"name": "服务状态", "method": "GET", "url": "/api/status", "expected_status": 200},
#             {"name": "版本信息", "method": "GET", "url": "/api/version", "expected_status": 200},
#         ]
#
#         for api in core_apis:
#             with allure.step(f"测试 {api['name']} 接口"):
#                 response = request_client.send_request(
#                     method=api['method'],
#                     url=api['url']
#                 )
#                 assert_utils.assert_status_code(response.status_code, api['expected_status'])
#
#     @allure.story("关键业务流程冒烟测试")
#     @allure.title("用户注册登录流程")
#     @allure.severity(allure.severity_level.CRITICAL)
#     @pytest.mark.smoke
#     def test_user_registration_login_flow(self):
#         """用户注册登录流程冒烟测试"""
#
#         # 生成测试用户数据
#         test_user = {
#             "username": f"smoketest_{int(time.time())}",
#             "password": "SmokeTest@123",
#             "email": f"smoke_{int(time.time())}@test.com"
#         }
#
#         # 步骤1: 用户注册
#         with allure.step("用户注册"):
#             register_response = request_client.post(
#                 "/api/register",
#                 json_data=test_user
#             )
#             assert_utils.assert_status_code(register_response.status_code, 201)
#
#         # 步骤2: 用户登录
#         with allure.step("用户登录"):
#             login_response = request_client.post(
#                 "/api/login",
#                 json_data={
#                     "username": test_user["username"],
#                     "password": test_user["password"]
#                 }
#             )
#             assert_utils.assert_status_code(login_response.status_code, 200)
#
#             # 提取token
#             login_data = login_response.json()
#             token = login_data.get("data", {}).get("token")
#             assert token, "登录响应中未找到token"
#
#         # 步骤3: 获取用户信息
#         with allure.step("获取用户信息"):
#             request_client.add_header("Authorization", f"Bearer {token}")
#             profile_response = request_client.get("/api/user/profile")
#             assert_utils.assert_status_code(profile_response.status_code, 200)
#             request_client.remove_header("Authorization")
#
#     @allure.story("Excel数据冒烟测试")
#     @allure.title("冒烟测试用例集")
#     @pytest.mark.smoke
#     @pytest.mark.parametrize("test_case", excel_reader.get_test_cases("smoke_cases"))
#     def test_smoke_excel_cases(self, test_case):
#         """执行Excel中的冒烟测试用例"""
#
#         # 只执行标记为冒烟的用例
#         tags = test_case.get('tags', '')
#         if 'smoke' not in tags.lower():
#             pytest.skip("非冒烟测试用例")
#
#         # 调用父类的测试方法
#         self.test_excel_driven(test_case)
#
#     @allure.story("性能冒烟测试")
#     @allure.title("接口响应时间冒烟测试")
#     @pytest.mark.smoke
#     @pytest.mark.performance
#     def test_smoke_performance(self):
#         """性能冒烟测试"""
#
#         # 测试关键接口的响应时间
#         performance_limits = [
#             {"name": "健康检查", "url": "/health", "max_time": 0.5},
#             {"name": "首页接口", "url": "/api/home", "max_time": 1.0},
#             {"name": "配置接口", "url": "/api/config", "max_time": 1.0},
#         ]
#
#         for api in performance_limits:
#             with allure.step(f"测试 {api['name']} 响应时间"):
#                 import time
#                 start_time = time.time()
#                 response = request_client.get(api['url'])
#                 elapsed = time.time() - start_time
#
#                 # 断言响应状态
#                 assert_utils.assert_status_code(response.status_code, 200)
#
#                 # 断言响应时间
#                 assert_utils.assert_time(elapsed, api['max_time'])
#
#                 allure.attach(
#                     f"接口: {api['name']}\n"
#                     f"URL: {api['url']}\n"
#                     f"响应时间: {elapsed:.3f}秒\n"
#                     f"限制时间: {api['max_time']}秒\n"
#                     f"结果: {'通过' if elapsed <= api['max_time'] else '失败'}",
#                     name=f"{api['name']}性能测试",
#                     attachment_type=allure.attachment_type.TEXT
#                 )
#
#     @allure.story("错误处理冒烟测试")
#     @allure.title("异常场景处理测试")
#     @pytest.mark.smoke
#     def test_smoke_error_handling(self):
#         """错误处理冒烟测试"""
#
#         error_scenarios = [
#             {
#                 "name": "不存在的接口",
#                 "method": "GET",
#                 "url": "/api/nonexistent",
#                 "expected_status": 404
#             },
#             {
#                 "name": "无效的请求方法",
#                 "method": "POST",
#                 "url": "/health",  # 假设健康检查只支持GET
#                 "expected_status": 405
#             },
#             {
#                 "name": "缺少必要参数",
#                 "method": "POST",
#                 "url": "/api/login",
#                 "json_data": {},  # 不传用户名密码
#                 "expected_status": 400
#             },
#         ]
#
#         for scenario in error_scenarios:
#             with allure.step(f"测试 {scenario['name']}"):
#                 response = request_client.send_request(
#                     method=scenario['method'],
#                     url=scenario['url'],
#                     json_data=scenario.get('json_data', {})
#                 )
#                 assert_utils.assert_status_code(response.status_code, scenario['expected_status'])
#
#     @allure.story("配置验证冒烟测试")
#     @allure.title("环境配置验证")
#     @pytest.mark.smoke
#     def test_smoke_configuration(self):
#         """环境配置冒烟测试"""
#
#         # 验证必要的环境配置
#         required_configs = [
#             ("API_BASE_URL", "基础URL"),
#             ("DATABASE_URL", "数据库连接"),
#             ("REDIS_URL", "Redis连接"),
#         ]
#
#         missing_configs = []
#
#         for config_key, config_name in required_configs:
#             config_value = os.environ.get(config_key)
#             if not config_value:
#                 missing_configs.append(config_key)
#                 logger.warning(f"缺少环境配置: {config_key} ({config_name})")
#
#         if missing_configs:
#             allure.attach(
#                 f"缺少的环境配置: {', '.join(missing_configs)}\n"
#                 f"请检查 .env 文件或环境变量设置",
#                 name="环境配置检查",
#                 attachment_type=allure.attachment_type.TEXT
#             )
#
#         # 验证API可访问性
#         try:
#             response = request_client.get("/health", timeout=5)
#             if response.status_code != 200:
#                 logger.warning(f"API健康检查失败: {response.status_code}")
#         except Exception as e:
#             logger.error(f"API不可访问: {e}")
#             pytest.fail(f"API服务不可访问: {e}")
#
#     @allure.story("依赖服务冒烟测试")
#     @allure.title("外部依赖服务检查")
#     @pytest.mark.smoke
#     def test_smoke_dependencies(self):
#         """依赖服务冒烟测试"""
#
#         # 这里可以添加对外部服务的检查
#         # 例如：数据库连接、缓存服务、消息队列等
#
#         dependencies = [
#             {
#                 "name": "数据库",
#                 "check": self._check_database,
#                 "required": True
#             },
#             {
#                 "name": "Redis缓存",
#                 "check": self._check_redis,
#                 "required": False
#             },
#             {
#                 "name": "文件存储",
#                 "check": self._check_file_storage,
#                 "required": False
#             },
#         ]
#
#         for dependency in dependencies:
#             with allure.step(f"检查 {dependency['name']}"):
#                 try:
#                     result = dependency["check"]()
#                     if result:
#                         logger.info(f"{dependency['name']} 检查通过")
#                         allure.attach(
#                             f"{dependency['name']}: 正常",
#                             name=f"{dependency['name']}状态",
#                             attachment_type=allure.attachment_type.TEXT
#                         )
#                     else:
#                         if dependency["required"]:
#                             pytest.fail(f"{dependency['name']} 检查失败")
#                         else:
#                             logger.warning(f"{dependency['name']} 检查失败（非必需）")
#                 except Exception as e:
#                     if dependency["required"]:
#                         pytest.fail(f"{dependency['name']} 检查异常: {e}")
#                     else:
#                         logger.warning(f"{dependency['name']} 检查异常（非必需）: {e}")
#
#     def _check_database(self):
#         """检查数据库连接"""
#         # 这里可以添加数据库连接检查
#         # 例如：执行一个简单的SQL查询
#         try:
#             # 如果有数据库配置，尝试连接
#             if config.DATABASE_URL:
#                 import sqlalchemy
#                 engine = sqlalchemy.create_engine(config.DATABASE_URL)
#                 connection = engine.connect()
#                 connection.close()
#                 return True
#             else:
#                 logger.warning("未配置数据库连接")
#                 return False
#         except Exception as e:
#             logger.error(f"数据库连接失败: {e}")
#             return False
#
#     def _check_redis(self):
#         """检查Redis连接"""
#         # 这里可以添加Redis连接检查
#         try:
#             redis_url = os.environ.get("REDIS_URL")
#             if redis_url:
#                 import redis
#                 r = redis.from_url(redis_url)
#                 r.ping()
#                 return True
#             else:
#                 logger.warning("未配置Redis连接")
#                 return False
#         except Exception as e:
#             logger.error(f"Redis连接失败: {e}")
#             return False
#
#     def _check_file_storage(self):
#         """检查文件存储"""
#         # 这里可以添加文件存储检查
#         # 例如：检查文件目录是否可写
#         try:
#             test_dir = Path("/tmp/test_file_storage")
#             test_dir.mkdir(exist_ok=True)
#             test_file = test_dir / "test.txt"
#             test_file.write_text("test")
#             test_file.unlink()
#             test_dir.rmdir()
#             return True
#         except Exception as e:
#             logger.error(f"文件存储检查失败: {e}")
#             return False
#
#
# @allure.epic("接口自动化测试")
# @allure.feature("快速冒烟测试")
# @pytest.mark.smoke
# class TestQuickSmoke:
#     """快速冒烟测试类"""
#
#     @allure.story("快速健康检查")
#     @allure.title("5分钟快速冒烟测试")
#     @pytest.mark.timeout(300)  # 5分钟超时
#     def test_quick_smoke(self):
#         """5分钟快速冒烟测试"""
#
#         # 只运行最核心的测试
#         test_cases = [
#             self._test_health,
#             self._test_main_apis,
#             self._test_error_handling
#         ]
#
#         results = []
#         for test_func in test_cases:
#             try:
#                 test_func()
#                 results.append(True)
#             except Exception as e:
#                 logger.error(f"快速冒烟测试失败: {e}")
#                 results.append(False)
#
#         # 所有核心测试必须通过
#         assert all(results), "快速冒烟测试失败"
#
#     def _test_health(self):
#         """测试健康检查"""
#         response = request_client.get("/health", timeout=5)
#         assert_utils.assert_status_code(response.status_code, 200)
#
#     def _test_main_apis(self):
#         """测试主要API"""
#         main_apis = ["/api/status", "/api/version", "/api/config"]
#         for api in main_apis:
#             response = request_client.get(api, timeout=5)
#             assert_utils.assert_status_code(response.status_code, 200)
#
#     def _test_error_handling(self):
#         """测试错误处理"""
#         response = request_client.get("/api/nonexistent", timeout=5)
#         assert_utils.assert_status_code(response.status_code, 404)