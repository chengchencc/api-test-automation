"""
模板引擎工厂
"""
from typing import Dict, Type, Optional
from .base import TemplateEngineBase
from .jinja2_engine import Jinja2Engine
from .string_format_engine import StringFormatEngine
from src.config.logger import logger


class TemplateEngineFactory:
    """模板引擎工厂"""

    # 注册的模板引擎类型
    _engines: Dict[str, Type[TemplateEngineBase]] = {
        'jinja2': Jinja2Engine,
        'string_format': StringFormatEngine,
    }

    @classmethod
    def register_engine(cls, name: str, engine_class: Type[TemplateEngineBase]):
        """注册新的模板引擎类型"""
        if not issubclass(engine_class, TemplateEngineBase):
            raise TypeError(f"引擎类必须继承自 TemplateEngineBase: {engine_class}")
        cls._engines[name] = engine_class
        logger.info(f"注册模板引擎: {name} -> {engine_class.__name__}")

    @classmethod
    def unregister_engine(cls, name: str):
        """注销模板引擎类型"""
        if name in cls._engines:
            del cls._engines[name]
            logger.info(f"注销模板引擎: {name}")

    @classmethod
    def get_available_engines(cls) -> Dict[str, Type[TemplateEngineBase]]:
        """获取可用的模板引擎"""
        return cls._engines.copy()

    @classmethod
    def create_engine(cls, engine_type: str = 'jinja2', **kwargs) -> TemplateEngineBase:
        """
        创建模板引擎实例

        Args:
            engine_type: 引擎类型 ('jinja2', 'string_format')
            **kwargs: 传递给引擎构造函数的参数

        Returns:
            模板引擎实例
        """
        if engine_type not in cls._engines:
            available = ', '.join(cls._engines.keys())
            raise ValueError(f"不支持的模板引擎类型: {engine_type}. 可用类型: {available}")

        engine_class = cls._engines[engine_type]
        logger.info(f"创建模板引擎: {engine_type} -> {engine_class.__name__}")
        return engine_class(**kwargs)

    @classmethod
    def create_from_config(cls, config: Dict) -> TemplateEngineBase:
        """
        从配置创建模板引擎

        Args:
            config: 配置字典，包含 'type' 和 'options' 键

        Returns:
            模板引擎实例
        """
        engine_type = config.get('type', 'jinja2')
        options = config.get('options', {})
        return cls.create_engine(engine_type, **options)