"""
测试基类模块
提供所有测试类的基类，包含通用的测试生命周期管理
"""
import time
import inspect
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import allure
import pytest
from src.utils.logger import get_test_logger
from src.config.settings import settings
from src.engine.template_engine import TemplateEngine
from src.data.data_loader import DataLoader
from src.clients.http_client import HttpClient


@dataclass
class TestContext:
    """测试上下文，存储测试执行过程中的共享数据"""
    test_id: str = ""
    test_name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)

    @property
    def duration(self) -> float:
        """获取测试持续时间"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def add_data(self, key: str, value: Any):
        """添加数据到上下文"""
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """从上下文获取数据"""
        return self.data.get(key, default)

    def add_result(self, key: str, value: Any):
        """添加测试结果"""
        self.results[key] = value

    def add_error(self, error: Exception):
        """添加错误信息"""
        self.errors.append({
            'time': time.time(),
            'error': str(error),
            'type': type(error).__name__
        })


class BaseTest(ABC):
    """
    测试基类
    所有测试类都应该继承此类，提供统一的测试生命周期管理
    """

    def __init__(self):
        """初始化测试类"""
        self._context = TestContext()
        self._logger = get_test_logger(self.__class__.__name__)
        self._template_engine = TemplateEngine()
        self._data_loader = DataLoader()
        self._http_client = HttpClient()

        # 初始化模板引擎上下文
        self._init_template_context()

    def _init_template_context(self):
        """初始化模板引擎上下文"""
        self._template_engine.update_context(
            config=settings.to_dict(),
            timestamp=int(time.time()),
            test_class=self.__class__.__name__
        )

    @property
    def context(self) -> TestContext:
        """获取测试上下文"""
        return self._context

    @property
    def logger(self):
        """获取测试日志器"""
        return self._logger

    @property
    def template_engine(self) -> TemplateEngine:
        """获取模板引擎"""
        return self._template_engine

    @property
    def data_loader(self) -> DataLoader:
        """获取数据加载器"""
        return self._data_loader

    @property
    def http_client(self) -> HttpClient:
        """获取HTTP客户端"""
        return self._http_client

    # 测试生命周期钩子
    def setup_class(self):
        """测试类初始化钩子"""
        self.context.test_id = f"{self.__class__.__name__}_{int(time.time())}"
        self.logger.info(f"开始测试类: {self.__class__.__name__}")
        self._before_class()

    def teardown_class(self):
        """测试类清理钩子"""
        self.logger.info(f"结束测试类: {self.__class__.__name__}")
        self._after_class()

    def setup_method(self, method):
        """测试方法初始化钩子"""
        self.context.test_name = method.__name__
        self.context.start_time = time.time()
        self.logger.info(f"开始测试方法: {method.__name__}")
        self._before_test(method)

    def teardown_method(self, method):
        """测试方法清理钩子"""
        self.context.end_time = time.time()
        self.logger.info(f"结束测试方法: {method.__name__}, 耗时: {self.context.duration:.2f}s")
        self._after_test(method)

    # 可重写的钩子方法
    def _before_class(self):
        """测试类前置操作，子类可重写"""
        pass

    def _after_class(self):
        """测试类后置操作，子类可重写"""
        pass

    def _before_test(self, method):
        """测试方法前置操作，子类可重写"""
        pass

    def _after_test(self, method):
        """测试方法后置操作，子类可重写"""
        pass

    # 通用工具方法
    def render_template(self, template: str, **kwargs) -> Any:
        """
        渲染模板

        Args:
            template: 模板字符串
            **kwargs: 模板变量

        Returns:
            渲染后的结果
        """
        return self.template_engine.render(template, **kwargs)

    def load_test_data(self, data_source: str, **kwargs) -> Any:
        """
        加载测试数据

        Args:
            data_source: 数据源标识
            **kwargs: 加载参数

        Returns:
            加载的数据
        """
        return self.data_loader.load(data_source, **kwargs)

    def make_request(self, method: str, url: str, **kwargs):
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 请求参数

        Returns:
            响应对象
        """
        return self.http_client.request(method, url, **kwargs)

    def assert_equal(self, actual, expected, message: str = ""):
        """断言相等"""
        assert actual == expected, f"{message} 期望: {expected}, 实际: {actual}"

    def assert_not_equal(self, actual, expected, message: str = ""):
        """断言不相等"""
        assert actual != expected, f"{message} 期望不等于: {expected}, 实际: {actual}"

    def assert_true(self, condition, message: str = ""):
        """断言为真"""
        assert condition, f"{message} 期望为真"

    def assert_false(self, condition, message: str = ""):
        """断言为假"""
        assert not condition, f"{message} 期望为假"

    def assert_in(self, item, container, message: str = ""):
        """断言包含"""
        assert item in container, f"{message} 期望包含: {item}"

    def assert_not_in(self, item, container, message: str = ""):
        """断言不包含"""
        assert item not in container, f"{message} 期望不包含: {item}"

    def assert_is_none(self, value, message: str = ""):
        """断言为None"""
        assert value is None, f"{message} 期望为None"

    def assert_is_not_none(self, value, message: str = ""):
        """断言不为None"""
        assert value is not None, f"{message} 期望不为None"

    def assert_raises(self, exception, func, *args, **kwargs):
        """断言抛出异常"""
        try:
            func(*args, **kwargs)
            assert False, f"期望抛出异常: {exception.__name__}"
        except exception:
            pass
        except Exception as e:
            assert False, f"期望抛出异常 {exception.__name__}, 实际抛出: {type(e).__name__}: {str(e)}"

    # Allure报告集成
    def attach_text(self, name: str, content: str, attachment_type: str = allure.attachment_type.TEXT):
        """附加文本到Allure报告"""
        allure.attach(content, name, attachment_type)

    def attach_json(self, name: str, data: Any):
        """附加JSON到Allure报告"""
        import json
        content = json.dumps(data, ensure_ascii=False, indent=2)
        allure.attach(content, name, allure.attachment_type.JSON)

    def attach_html(self, name: str, content: str):
        """附加HTML到Allure报告"""
        allure.attach(content, name, allure.attachment_type.HTML)

    def step(self, name: str):
        """创建Allure步骤"""
        return allure.step(name)

    def feature(self, name: str):
        """设置Allure特性"""
        return allure.feature(name)

    def story(self, name: str):
        """设置Allure故事"""
        return allure.story(name)

    def severity(self, level: str):
        """设置Allure严重级别"""
        return allure.severity(level)

    def tag(self, *tags: str):
        """设置Allure标签"""
        for tag in tags:
            allure.tag(tag)