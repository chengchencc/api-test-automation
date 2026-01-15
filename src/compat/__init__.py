"""
兼容性模块
提供从旧结构到新结构的向后兼容支持
"""
import warnings
from typing import Any

warnings.warn(
    "兼容性模块仅用于过渡期，请尽快迁移到新的模块结构",
    DeprecationWarning,
    stacklevel=2
)


class LegacyAdapter:
    """旧模块适配器"""

    def __init__(self, new_module: Any, adapter_func=None):
        self._new_module = new_module
        self._adapter_func = adapter_func

    def __getattr__(self, name: str) -> Any:
        """获取属性"""
        if hasattr(self._new_module, name):
            return getattr(self._new_module, name)
        elif self._adapter_func:
            return self._adapter_func(name)
        else:
            raise AttributeError(f"属性不存在: {name}")


# 创建兼容性实例
try:
    from src.data.data_loader import DataLoader
    from src.clients.http_client import HttpClient
    from src.engine.assertion_engine import AssertionEngine
    from src.engine.template_engine import TemplateEngine
    from src.config.settings import settings

    # 数据加载器兼容
    excel_reader = LegacyAdapter(DataLoader())

    # HTTP客户端兼容
    request_client = LegacyAdapter(HttpClient())

    # 断言工具兼容
    assert_utils = LegacyAdapter(AssertionEngine())

    # 模板引擎兼容
    template_engine = LegacyAdapter(TemplateEngine())

    # 配置兼容
    class ConfigCompat:
        """配置兼容类"""

        def __getattr__(self, name: str) -> Any:
            # 将旧配置名映射到新配置名
            mapping = {
                'BASE_URL': 'API_BASE_URL',
                'TIMEOUT': 'API_TIMEOUT',
                'VERIFY_SSL': 'API_VERIFY_SSL',
                'MAX_RETRY': 'API_MAX_RETRIES',
                'LOG_LEVEL': 'LOG_LEVEL',
                'TEST_DATA_DIR': 'EXCEL_DIR',
                'REPORT_DIR': 'REPORTS_DIR',
                'LOG_DIR': 'LOGS_DIR',
                'ALLURE_RESULTS': 'ALLURE_RESULTS_DIR',
                'ALLURE_REPORT': 'ALLURE_REPORT_DIR',
            }

            new_name = mapping.get(name, name)
            if hasattr(settings, new_name):
                return getattr(settings, new_name)
            else:
                raise AttributeError(f"配置项不存在: {name}")

        @property
        def BASE_DIR(self):
            """项目根目录"""
            return settings.PROJECT_DIR

        @property
        def EXCEL_FILE(self):
            """Excel文件路径"""
            return settings.excel_test_cases_path

        def get_allure_report_url(self):
            """获取Allure报告URL"""
            return settings.allure_report_url

        def get_html_report_path(self):
            """获取HTML报告路径"""
            return settings.html_report_path

    project_config = ConfigCompat()

except ImportError as e:
    warnings.warn(f"无法导入新模块: {e}", ImportWarning)

    # 创建空对象，避免导入错误
    class EmptyModule:
        def __getattr__(self, name):
            raise ImportError("新模块未正确安装，请检查依赖")

    excel_reader = EmptyModule()
    request_client = EmptyModule()
    assert_utils = EmptyModule()
    template_engine = EmptyModule()
    project_config = EmptyModule()


__all__ = [
    'excel_reader',
    'request_client',
    'assert_utils',
    'template_engine',
    'project_config',
]