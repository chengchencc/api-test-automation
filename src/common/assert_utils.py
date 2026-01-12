import json
import re
from typing import Dict, Any, List, Union
from deepdiff import DeepDiff
from ..config.logger import logger

import requests


class AssertUtils:
    """断言工具类"""

    @staticmethod
    def assert_status_code(actual: int, expected: Union[int, List[int]],
                           message: str = None) -> bool:
        """断言状态码"""
        if isinstance(expected, list):
            if actual not in expected:
                error_msg = message or f"状态码 {actual} 不在预期列表 {expected} 中"
                logger.error(error_msg)
                raise AssertionError(error_msg)
        else:
            if actual != expected:
                error_msg = message or f"状态码不匹配: 实际={actual}, 预期={expected}"
                logger.error(error_msg)
                raise AssertionError(error_msg)

        logger.debug(f"状态码断言成功: 实际={actual}, 预期={expected}")
        return True

    @staticmethod
    def assert_response_contains(response_text: str, expected_text: str,
                                 message: str = None) -> bool:
        """断言响应包含特定文本"""
        if expected_text not in response_text:
            error_msg = message or f"响应中不包含预期文本: {expected_text}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"响应包含断言成功: 包含 '{expected_text}'")
        return True

    @staticmethod
    def assert_response_not_contains(response_text: str, unexpected_text: str,
                                     message: str = None) -> bool:
        """断言响应不包含特定文本"""
        if unexpected_text in response_text:
            error_msg = message or f"响应中包含不应出现的文本: {unexpected_text}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"响应不包含断言成功: 不包含 '{unexpected_text}'")
        return True

    @staticmethod
    def assert_response_json(response_json: Dict, expected_json: Dict,
                             ignore_order: bool = True, exclude_paths: List[str] = None,
                             message: str = None) -> bool:
        """断言JSON响应"""
        diff = DeepDiff(
            response_json,
            expected_json,
            ignore_order=ignore_order,
            exclude_paths=exclude_paths
        )

        if diff:
            error_msg = message or f"JSON响应不匹配: {diff.to_json()}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug("JSON响应断言成功")
        return True

    @staticmethod
    def assert_response_schema(response_json: Dict, schema: Dict,
                               message: str = None) -> List[str]:
        """断言响应schema（简单版本）"""
        errors = []

        def check_schema(data: Any, schema_def: Dict, path: str = ""):
            if not isinstance(schema_def, dict):
                return

            for key, expected_type in schema_def.items():
                full_path = f"{path}.{key}" if path else key

                # 检查字段是否存在
                if key not in data:
                    errors.append(f"字段缺失: {full_path}")
                    continue

                # 检查字段类型
                actual_value = data[key]
                expected_type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(
                    expected_type)

                if expected_type is None:
                    # None表示字段可以为任意类型
                    continue
                elif isinstance(expected_type, type):
                    # 检查类型
                    if not isinstance(actual_value, expected_type):
                        errors.append(f"字段类型错误: {full_path}, "
                                      f"实际类型={type(actual_value).__name__}, 预期类型={expected_type_name}")
                elif isinstance(expected_type, dict):
                    # 嵌套schema
                    if isinstance(actual_value, dict):
                        check_schema(actual_value, expected_type, full_path)
                    else:
                        errors.append(f"字段应为对象: {full_path}")
                elif isinstance(expected_type, list) and len(expected_type) == 1:
                    # 数组类型
                    if isinstance(actual_value, list):
                        item_type = expected_type[0]
                        for i, item in enumerate(actual_value):
                            if isinstance(item_type, type) and not isinstance(item, item_type):
                                errors.append(f"数组元素类型错误: {full_path}[{i}], "
                                              f"实际类型={type(item).__name__}, 预期类型={item_type.__name__}")
                            elif isinstance(item_type, dict) and isinstance(item, dict):
                                check_schema(item, item_type, f"{full_path}[{i}]")
                    else:
                        errors.append(f"字段应为数组: {full_path}")

        check_schema(response_json, schema)

        if errors and message:
            raise AssertionError(f"{message}: {errors}")
        elif errors:
            raise AssertionError(f"Schema验证失败: {errors}")

        logger.debug("Schema断言成功")
        return []

    @staticmethod
    def assert_regex_match(text: str, pattern: str,
                           message: str = None) -> bool:
        """断言正则匹配"""
        match = re.search(pattern, text)
        if match is None:
            error_msg = message or f"文本不匹配正则模式: {pattern}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"正则匹配断言成功: 模式='{pattern}'")
        return True

    @staticmethod
    def assert_time(response_time: float, max_time: float,
                    message: str = None) -> bool:
        """断言响应时间"""
        if response_time > max_time:
            error_msg = message or f"响应时间过长: 实际={response_time:.2f}秒, 最大允许={max_time}秒"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"响应时间断言成功: 实际={response_time:.2f}秒, 最大={max_time}秒")
        return True

    @staticmethod
    def assert_equal(actual: Any, expected: Any,
                     message: str = None) -> bool:
        """断言相等"""
        if actual != expected:
            error_msg = message or f"值不相等: 实际={actual}, 预期={expected}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"相等断言成功: 实际={actual}, 预期={expected}")
        return True

    @staticmethod
    def assert_not_equal(actual: Any, expected: Any,
                         message: str = None) -> bool:
        """断言不相等"""
        if actual == expected:
            error_msg = message or f"值相等: 实际={actual}, 预期={expected}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"不相等断言成功: 实际={actual}, 预期={expected}")
        return True

    @staticmethod
    def assert_true(condition: bool, message: str = None) -> bool:
        """断言为True"""
        if not condition:
            error_msg = message or f"条件为False"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug("True断言成功")
        return True

    @staticmethod
    def assert_false(condition: bool, message: str = None) -> bool:
        """断言为False"""
        if condition:
            error_msg = message or f"条件为True"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug("False断言成功")
        return True

    @staticmethod
    def assert_is_none(value: Any, message: str = None) -> bool:
        """断言为None"""
        if value is not None:
            error_msg = message or f"值不为None: {value}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug("None断言成功")
        return True

    @staticmethod
    def assert_is_not_none(value: Any, message: str = None) -> bool:
        """断言不为None"""
        if value is None:
            error_msg = message or "值为None"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug("非None断言成功")
        return True

    @staticmethod
    def assert_in(item: Any, container: Any,
                  message: str = None) -> bool:
        """断言包含"""
        if item not in container:
            error_msg = message or f"{item} 不在 {container} 中"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"包含断言成功: {item} 在 {container} 中")
        return True

    @staticmethod
    def assert_not_in(item: Any, container: Any,
                      message: str = None) -> bool:
        """断言不包含"""
        if item in container:
            error_msg = message or f"{item} 在 {container} 中"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"不包含断言成功: {item} 不在 {container} 中")
        return True

    @staticmethod
    def assert_length(actual: Any, expected_length: int,
                      message: str = None) -> bool:
        """断言长度"""
        try:
            actual_length = len(actual)
        except TypeError:
            error_msg = message or f"无法获取长度: {actual}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        if actual_length != expected_length:
            error_msg = message or f"长度不匹配: 实际={actual_length}, 预期={expected_length}"
            logger.error(error_msg)
            raise AssertionError(error_msg)

        logger.debug(f"长度断言成功: 实际={actual_length}, 预期={expected_length}")
        return True

    @staticmethod
    def assert_response(response: requests.Response,
                        expected_status: Union[int, List[int]] = None,
                        expected_json: Dict = None,
                        expected_schema: Dict = None,
                        expected_contains: str = None,
                        expected_not_contains: str = None,
                        max_time: float = None,
                        message: str = None) -> Dict:
        """
        综合断言响应

        Args:
            response: 响应对象
            expected_status: 预期状态码
            expected_json: 预期JSON
            expected_schema: 预期Schema
            expected_contains: 预期包含文本
            expected_not_contains: 预期不包含文本
            max_time: 最大响应时间
            message: 自定义错误信息

        Returns:
            响应JSON（如果存在）
        """
        assertions = []

        try:
            # 尝试解析JSON响应
            response_json = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_json = None

        # 断言状态码
        if expected_status is not None:
            AssertUtils.assert_status_code(response.status_code, expected_status,
                                           f"{message} - 状态码断言失败")
            assertions.append(f"status_code={expected_status}")

        # 断言响应时间
        if max_time is not None:
            response_time = response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
            AssertUtils.assert_time(response_time, max_time,
                                    f"{message} - 响应时间断言失败")
            assertions.append(f"max_time={max_time}")

        # 断言包含文本
        if expected_contains is not None:
            AssertUtils.assert_response_contains(response.text, expected_contains,
                                                 f"{message} - 包含文本断言失败")
            assertions.append(f"contains='{expected_contains}'")

        # 断言不包含文本
        if expected_not_contains is not None:
            AssertUtils.assert_response_not_contains(response.text, expected_not_contains,
                                                     f"{message} - 不包含文本断言失败")
            assertions.append(f"not_contains='{expected_not_contains}'")

        # 断言JSON
        if expected_json is not None and response_json is not None:
            AssertUtils.assert_response_json(response_json, expected_json,
                                             message=f"{message} - JSON断言失败")
            assertions.append("json_matches")

        # 断言Schema
        if expected_schema is not None and response_json is not None:
            AssertUtils.assert_response_schema(response_json, expected_schema,
                                               message=f"{message} - Schema断言失败")
            assertions.append("schema_matches")

        logger.info(f"响应断言成功: {', '.join(assertions)}")
        return response_json


# 断言工具实例
assert_utils = AssertUtils()