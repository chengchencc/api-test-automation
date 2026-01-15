"""
字符串格式化模板引擎
使用Python的字符串格式化语法：{variable}
"""
import json
import re
from typing import Any, Dict
from .base import TemplateEngineBase
from src.config.logger import logger


class StringFormatEngine(TemplateEngineBase):
    """基于Python字符串格式化的模板引擎"""

    def __init__(self, strict_mode: bool = False, auto_reload: bool = True):
        super().__init__(strict_mode, auto_reload)
        logger.info("字符串格式化模板引擎初始化完成")

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
        # 合并上下文
        context = {**self.context}
        if extra_context:
            context.update(extra_context)
        if kwargs:
            context.update(kwargs)

        # 渲染数据
        return self._render_recursive(template, context)

    def render_string(self, template_str: str, **kwargs) -> str:
        """渲染字符串模板"""
        if not isinstance(template_str, str):
            return template_str

        # 检查是否包含模板语法
        if not self._has_template_syntax(template_str):
            return template_str

        # 合并上下文
        context = {**self.context}
        if kwargs:
            context.update(kwargs)

        try:
            # 使用Python的字符串格式化
            return template_str.format(**context)
        except KeyError as e:
            if self.strict_mode:
                raise KeyError(f"变量未定义: {e}")
            logger.warning(f"变量未定义: {e}, 使用原字符串")
            return template_str
        except Exception as e:
            logger.warning(f"模板渲染失败: {e}, 模板: {template_str[:100]}...")
            return template_str

    def render_file(self, filepath: str, **kwargs) -> str:
        """渲染文件模板"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.render_string(content, **kwargs)
        except FileNotFoundError:
            logger.error(f"模板文件不存在: {filepath}")
            return ""

    def eval_expression(self, expression: str, **kwargs) -> Any:
        """计算表达式（返回Python对象）"""
        try:
            # 字符串格式化引擎不支持复杂表达式
            # 只能返回变量值
            context = {**self.context}
            if kwargs:
                context.update(kwargs)

            if expression in context:
                return context[expression]
            else:
                logger.warning(f"表达式变量未定义: {expression}")
                return None
        except Exception as e:
            logger.error(f"表达式计算失败: {expression}, 错误: {e}")
            return None

    def _has_template_syntax(self, text: str) -> bool:
        """检查字符串是否包含模板语法"""
        # 检查是否包含 {variable} 语法
        pattern = r'\{[^{}]*\}'
        return bool(re.search(pattern, text))