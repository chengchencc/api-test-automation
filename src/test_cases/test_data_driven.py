import pytest
import allure
import json
import time
from typing import Dict, Any, List
from src.common.excel_reader import excel_reader
from src.common.request_client import request_client
from src.common.assert_utils import assert_utils
from src.common.template_engine_manager import template_engine
from src.config.logger import logger, TestLogger

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
    print(__file__)
    # 直接运行测试
    pytest.main([__file__, "-v", "--tb=short"])