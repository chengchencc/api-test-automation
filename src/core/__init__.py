"""
核心框架模块
提供测试框架的基础组件和核心功能
"""

from .base_test import BaseTest
from .test_runner import TestRunner
from .test_suite import TestSuite

__all__ = [
    'BaseTest',
    'TestRunner',
    'TestSuite',
]