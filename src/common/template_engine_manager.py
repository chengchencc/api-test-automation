"""
模板引擎模块 - 重构版本
支持多种模板引擎，保持向后兼容
"""
import sys
from typing import Any, Dict
from .template_engines.factory import TemplateEngineFactory
from .template_engines.base import TemplateEngineBase
from src.config.logger import logger


class TemplateEngineManager:
    """模板引擎管理器"""

    def __init__(self, engine_type: str = 'jinja2', **kwargs):
        """
        初始化模板引擎管理器

        Args:
            engine_type: 引擎类型 ('jinja2', 'string_format')
            **kwargs: 传递给引擎构造函数的参数
        """
        self.engine_type = engine_type
        self.engine = TemplateEngineFactory.create_engine(engine_type, **kwargs)
        logger.info(f"模板引擎管理器初始化完成，使用引擎: {engine_type}")

    def update_context(self, **kwargs):
        """更新上下文变量"""
        self.engine.update_context(**kwargs)

    def clear_context(self):
        """清空上下文"""
        self.engine.clear_context()

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
        return self.engine.render(template, extra_context, **kwargs)

    def render_string(self, template_str: str, **kwargs) -> str:
        """渲染字符串模板（快捷方法）"""
        return self.engine.render_string(template_str, **kwargs)

    def render_file(self, filepath: str, **kwargs) -> str:
        """渲染文件模板"""
        return self.engine.render_file(filepath, **kwargs)

    def eval_expression(self, expression: str, **kwargs) -> Any:
        """计算表达式（返回Python对象）"""
        return self.engine.eval_expression(expression, **kwargs)

    def register_filter(self, name: str, func):
        """注册自定义过滤器"""
        self.engine.register_filter(name, func)

    def register_function(self, name: str, func):
        """注册自定义函数"""
        self.engine.register_function(name, func)

    def register_test(self, name: str, func):
        """注册自定义测试函数"""
        self.engine.register_test(name, func)

    def switch_engine(self, engine_type: str, **kwargs):
        """
        切换模板引擎

        Args:
            engine_type: 新的引擎类型
            **kwargs: 传递给新引擎构造函数的参数
        """
        if engine_type == self.engine_type:
            logger.info(f"已经是 {engine_type} 引擎，无需切换")
            return

        # 保存当前上下文
        old_context = self.engine.context.copy()
        old_sequences = self.engine.sequences.copy()

        # 创建新引擎
        self.engine = TemplateEngineFactory.create_engine(engine_type, **kwargs)
        self.engine_type = engine_type

        # 恢复上下文
        self.engine.context.update(old_context)
        self.engine.sequences.update(old_sequences)

        logger.info(f"已切换到 {engine_type} 引擎")


# 创建全局模板引擎实例（保持向后兼容）
# 默认使用Jinja2引擎
template_engine = TemplateEngineManager('jinja2')


# 便捷函数
def create_engine(engine_type: str = 'jinja2', **kwargs) -> TemplateEngineManager:
    """创建新的模板引擎实例"""
    return TemplateEngineManager(engine_type, **kwargs)


def get_available_engines() -> Dict[str, str]:
    """获取可用的模板引擎类型"""
    engines = TemplateEngineFactory.get_available_engines()
    return {name: engine_class.__name__ for name, engine_class in engines.items()}


def register_custom_engine(name: str, engine_class):
    """注册自定义模板引擎"""
    TemplateEngineFactory.register_engine(name, engine_class)


# 导出常用类
__all__ = [
    'template_engine',
    'TemplateEngineManager',
    'TemplateEngineBase',
    'create_engine',
    'get_available_engines',
    'register_custom_engine',
]


if __name__ == "__main__":
    print(__file__)
    print(sys.path)

    # 测试基本功能
    context = {
        "a": "aa",
        "b": "bb",
    }

    template_engine.update_context(**context)
    print(template_engine.render("hello,{{ a }}"))
    print(template_engine.render("hello,{{ b }}"))
    print(template_engine.render("hello,{{ c }}"))

    # 测试字符串格式化引擎
    string_engine = create_engine('string_format')
    string_engine.update_context(**context)
    print(string_engine.render("hello,{a}"))
    print(string_engine.render("hello,{b}"))

    # 测试可用引擎
    print("可用引擎:", get_available_engines())