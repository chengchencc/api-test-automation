"""
模板引擎抽象基类
"""
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List, Tuple, Set
from src.config.logger import logger


class TemplateEngineBase(ABC):
    """模板引擎抽象基类"""

    def __init__(self, strict_mode: bool = False, auto_reload: bool = True):
        """
        初始化模板引擎

        Args:
            strict_mode: 严格模式，如果变量未定义则报错
            auto_reload: 自动重新加载模板
        """
        self.strict_mode = strict_mode
        self.auto_reload = auto_reload
        self.context: Dict[str, Any] = {}
        self.sequences: Dict[str, int] = {}
        self.template_cache: Dict[str, Any] = {}

    @abstractmethod
    def render(self, template: Any, extra_context: Dict = None, **kwargs) -> Any:
        """
        渲染模板

        Args:
            template: 模板数据（字符串、字典、列表等）
            extra_context: 额外的上下文变量
            **kwargs: 额外的关键字参数

        Returns:
            渲染后的结果
        """
        pass

    @abstractmethod
    def render_string(self, template_str: str, **kwargs) -> str:
        """渲染字符串模板"""
        pass

    @abstractmethod
    def render_file(self, filepath: str, **kwargs) -> str:
        """渲染文件模板"""
        pass

    @abstractmethod
    def eval_expression(self, expression: str, **kwargs) -> Any:
        """计算表达式（返回Python对象）"""
        pass

    def update_context(self, **kwargs):
        """更新上下文变量"""
        self.context.update(kwargs)
        logger.debug(f"更新上下文: {list(kwargs.keys())}")

    def clear_context(self):
        """清空上下文"""
        self.context.clear()
        self.sequences.clear()
        self.template_cache.clear()
        logger.debug("清空上下文")

    def register_filter(self, name: str, func):
        """注册自定义过滤器"""
        raise NotImplementedError("此模板引擎不支持过滤器注册")

    def register_function(self, name: str, func):
        """注册自定义函数"""
        raise NotImplementedError("此模板引擎不支持函数注册")

    def register_test(self, name: str, func):
        """注册自定义测试函数"""
        raise NotImplementedError("此模板引擎不支持测试函数注册")

    def _render_recursive(self, data: Any, context: Dict) -> Any:
        """递归渲染数据（通用实现）"""
        if isinstance(data, str):
            # 处理字符串模板
            return self.render_string(data, **context)

        elif isinstance(data, dict):
            # 处理字典
            result = {}
            for key, value in data.items():
                # 渲染键
                rendered_key = self._render_recursive(key, context)
                # 渲染值
                rendered_value = self._render_recursive(value, context)
                result[rendered_key] = rendered_value
            return result

        elif isinstance(data, (list, tuple, set)):
            # 处理序列
            result_type = type(data)
            rendered_items = [self._render_recursive(item, context) for item in data]
            return result_type(rendered_items)

        else:
            # 其他类型直接返回
            return data

    def _has_template_syntax(self, text: str, patterns: List[str] = None) -> bool:
        """检查字符串是否包含模板语法"""
        if patterns is None:
            # 默认检查是否包含 {{ }} 语法
            patterns = [r'\{\{.*?\}\}']

        for pattern in patterns:
            if re.search(pattern, text, re.DOTALL):
                return True

        return False