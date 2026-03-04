import pytest
import allure
import json
import time
import glob
from pathlib import Path
from typing import Dict, Any, List
from src.common.excel_reader import excel_reader, ExcelReader
from src.common.request_client import request_client
from src.common.assert_utils import assert_utils
from src.common.template_engine_manager import template_engine
from src.config.logger import logger, TestLogger
from src.config.settings import project_config


def get_all_excel_files():
    """获取test_data目录下所有Excel文件"""
    import os
    test_data_dir = project_config.TEST_DATA_DIR
    excel_files = list(test_data_dir.glob("*.xlsx")) + list(test_data_dir.glob("*.xls"))
    
    # 读取环境变量 API_TEST_EXCEL_FILE
    fn = os.environ.get('API_TEST_EXCEL_FILE')
    if fn:
        # 过滤指定的Excel文件
        filtered_files = []
        for file in excel_files:
            if file.name == fn:
                filtered_files.append(file)
        if filtered_files:
            return filtered_files
        else:
            # 如果没有找到指定文件，返回空列表
            return []
    
    return sorted(excel_files)  # 按文件名排序

class BaseTest:
    """测试基类"""

    def setup_class(self):

        print(f"test logger name:: {self.__class__.__name__} ")

        """测试类初始化"""
        self.test_logger = TestLogger(self.__class__.__name__)
        self.test_logger.log_step("测试类初始化")

        # 读取配置文件
        self.config = excel_reader.get_config()

        # 更新模板引擎上下文
        template_engine.update_context(
            config=self.config,
            timestamp=int(time.time()),
        )

    def teardown_class(self):
        """测试类清理"""
        self.test_logger.log_step("测试类清理")

    def setup_method(self, method):
        """测试方法初始化"""
        test_name = method.__name__
        self.test_logger.test_name = test_name
        self.test_logger.log_step(f"开始测试: {test_name}")

    def teardown_method(self, method):
        """测试方法清理"""
        self.test_logger.log_step(f"结束测试: {method.__name__}")


@allure.epic("接口自动化测试")
@allure.feature("基础接口测试")
@pytest.mark.api
class TestAPI(BaseTest):
    """API测试类"""

    def setup_class(self):
        """测试类级别的初始化"""
        # 先调用父类的setup_class方法
        BaseTest.setup_class(self)
        self.cache = {}  # 用于存储测试间共享的数据

    def teardown_class(self):
        """测试类清理"""
        # 调用父类的teardown_class方法
        BaseTest.teardown_class(self)

    @allure.story("Excel数据驱动测试")
    @pytest.mark.parametrize(
        "excel_file, sheet_name, case_index",
        [(str(excel_file), sheet, idx) 
         for excel_file in get_all_excel_files() 
         for sheet, cases in ExcelReader(excel_file).get_test_suites().items() 
         for idx in range(len(cases))]
    )
    def test_excel_driven(self, excel_file: str, sheet_name: str, case_index: int):
        """
        执行Excel中的测试用例

        Args:
            excel_file: Excel文件路径
            sheet_name: 工作表名称
            case_index: 测试用例索引
        """
        # 实时读取并渲染测试用例，确保使用最新的缓存
        reader = ExcelReader(excel_file)
        test_cases = reader.get_test_cases(sheet_name, render_templates=False)
        test_case = test_cases[case_index]
        
        # 准备上下文
        context = {
            'case_id': test_case.get('case_id', 'unknown'),
            'case_name': test_case.get('case_name', '未知用例'),
            'cache': self.cache,
            'timestamp': int(time.time()),
            **self.cache
        }
        
        # 渲染测试用例数据
        from src.common.template_engine_manager import template_engine
        
        # 先处理JSON字段，解析后再渲染
        json_fields = ['headers', 'params', 'data', 'json', 'expected', 'setup_data', 'teardown_data', 'assertions']
        processed_data = test_case.copy()
        
        for field in json_fields:
            if field in processed_data and processed_data[field] and isinstance(processed_data[field], str):
                try:
                    # 先尝试解析为JSON
                    import json
                    processed_data[field] = json.loads(processed_data[field])
                except json.JSONDecodeError:
                    try:
                        # 再尝试解析为YAML
                        import yaml
                        processed_data[field] = yaml.safe_load(processed_data[field])
                    except (yaml.YAMLError, AttributeError):
                        # 如果都失败，保持原样
                        pass
        
        # 渲染处理后的数据
        test_case = template_engine.render(processed_data, context)
        
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
        files = test_case.get('files', None)
        # 把test_case.get('expected_status', 200)类型转换为int
        expected_status = int(test_case.get('expected_status', 200))
        expected_response = test_case.get('expected_response', {})
        expected_schema = test_case.get('expected_schema', {})
        expected_contains = test_case.get('expected_contains')
        max_response_time = int(test_case.get('max_response_time'))
        setup_data = test_case.get('setup_data', {})
        teardown_data = test_case.get('teardown_data', {})

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

        self.test_logger.log_step(f"执行测试用例: {case_id} - {case_name}")

        try:
            # 前置操作
            if setup_data:
                self._execute_setup(setup_data, case_id)

            # 准备上下文
            context = {
                'case_id': case_id,
                'case_name': case_name,
                'cache': self.cache,
                'timestamp': int(time.time()),
                **self.cache
            }
            # 确保headers中的动态参数能够正确获取到cache中的值
            if headers:
                # 输出原始headers
                self.test_logger.log_step(f"原始headers === : - {headers}")
                # 重新渲染headers中的动态参数
                rendered_headers = {}
                for k, v in headers.items():
                    if isinstance(v, str):
                        rendered_value = template_engine.render_string(v, **context)
                        self.test_logger.log_step(f"渲染headers[{k}] === : {v} -> {rendered_value}")
                        rendered_headers[k] = rendered_value
                    else:
                        rendered_headers[k] = v
                headers = rendered_headers
                # 输出渲染后的headers
                self.test_logger.log_step(f"渲染后headers === : - {headers}")
            # 发送请求
            response = request_client.send_request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json_data=json_data,
                data=data,
                files=files,
                context=context
            )

            # 将响应数据保存到缓存，供后续用例使用
            # self.test_logger.log_step(f"获取数据 --- extract === : - {test_case.get('extract', {})}")
            response_data = self._extract_response_data(response, test_case.get('extract', {}))
            # self.test_logger.log_step(f"获取数据 --- response_data === : - {response_data}")
            self.cache.update(response_data)

            # 更新模板引擎上下文
            template_engine.update_context(
                response=response_data,
                last_response=response_data,
                cache=self.cache
            )

            # 输出获取缓存中的数据
            self.test_logger.log_step(f"获取缓存中的数据 === : - {self.cache}")


            # 记录请求响应详情到Allure
            self._attach_request_response_to_allure(response, test_case)

            # 综合断言
            assert_utils.assert_response(
                response=response,
                expected_status=expected_status,
                expected_json=expected_response,
                expected_schema=expected_schema,
                expected_contains=expected_contains,
                max_time=max_response_time,
                message=f"用例 {case_id} 断言失败"
            )

            # 自定义断言
            custom_assertions = test_case.get('assertions', [])
            if custom_assertions and isinstance(custom_assertions, list):
                self.test_logger.log_step(f"自定义断言开始执行：")
                self._execute_custom_assertions(response, custom_assertions)

            self.test_logger.log_step(f"测试用例 {case_id} 执行成功")

        except Exception as e:
            self.test_logger.log_step(f"测试用例 {case_id} 执行失败: {e}")
            pytest.fail(f"测试用例执行失败: {e}")

        finally:
            # 后置操作
            if teardown_data:
                self._execute_teardown(teardown_data, case_id)

    def _execute_setup(self, setup_data: Dict, case_id: str):
        """执行前置操作"""
        self.test_logger.log_step(f"执行前置操作: {case_id}")

        # 这里可以执行各种前置操作，如：
        # 1. 数据库准备
        # 2. 文件准备
        # 3. 环境准备
        # 4. 调用其他接口等

        if setup_data.get('type') == 'api':
            # 执行API前置操作
            setup_response = request_client.send_request(
                method=setup_data.get('method', 'GET'),
                url=setup_data.get('url', ''),
                headers=setup_data.get('headers', {}),
                json_data=setup_data.get('json', {}),
                data=setup_data.get('data', {})
            )

            # 提取数据到缓存
            extract = setup_data.get('extract', {})
            if extract:
                extracted = self._extract_from_response(setup_response, extract)
                self.cache.update(extracted)

        elif setup_data.get('type') == 'sql':
            # 执行SQL前置操作
            # 这里可以连接数据库执行SQL
            pass

        elif setup_data.get('type') == 'command':
            # 执行命令前置操作
            import subprocess
            command = setup_data.get('command', '')
            if command:
                subprocess.run(command, shell=True, check=True)

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

    def _extract_response_data(self, response, extract_rules) -> Dict:
        """从响应中提取数据"""
        extracted = {}

        if not extract_rules or not response.content:
            return extracted

        # 尝试将extract_rules从字符串解析为字典
        if isinstance(extract_rules, str):
            try:
                extract_rules = json.loads(extract_rules)
            except json.JSONDecodeError:
                logger.warning(f"extract_rules不是有效的JSON格式: {extract_rules}")
                return extracted

        # 确保extract_rules是字典
        if not isinstance(extract_rules, dict):
            logger.warning(f"extract_rules不是字典类型: {type(extract_rules)}")
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
                message = assertion.get('message', f'自定义断言 {idx + 1} 失败')

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
                        self.test_logger.log_step("jsonpath-ng未安装，跳过JSON路径断言")

                elif assertion_type == 'schema':
                    response_json = response.json() if response.content else {}
                    assert_utils.assert_response_schema(response_json, expected, message)

                self.test_logger.log_step(f"自定义断言结果： {idx + 1} 成功: {assertion_type}")

            except Exception as e:
                self.test_logger.log_step(f"自定义断言结果： {idx + 1} 失败: {e}")
                raise

    def _ensure_serializable(self, data):
        """确保数据可以被JSON序列化"""
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return str(data)
        elif isinstance(data, dict):
            return {k: self._ensure_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._ensure_serializable(item) for item in data]
        return data

    def _attach_request_response_to_allure(self, response, test_case: Dict):
        """将请求响应详情附加到Allure报告"""

        # 请求信息
        request_info = {
            'method': response.request.method,
            'url': response.request.url,
            'headers': dict(response.request.headers),
            'body': self._ensure_serializable(response.request.body)
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
            json.dumps(self._ensure_serializable(case_info), indent=2, ensure_ascii=False),
            name="用例信息",
            attachment_type=allure.attachment_type.JSON
        )

        allure.attach(
            json.dumps(self._ensure_serializable(request_info), indent=2, ensure_ascii=False),
            name="请求详情",
            attachment_type=allure.attachment_type.JSON
        )

        # 如果响应是JSON，以JSON格式附加
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                allure.attach(
                    json.dumps(self._ensure_serializable(json.loads(response.text)), indent=2, ensure_ascii=False),
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

if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "--tb=short"])