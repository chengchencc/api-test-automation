import json
import re
import sys
from typing import Any, Dict
from jinja2 import Environment, BaseLoader, StrictUndefined, TemplateError, Undefined
from jinja2 import select_autoescape
import time
import random
import string
import uuid
import hashlib
import os
import inspect
from datetime import datetime, timedelta
from faker import Faker
from src.config.logger import logger


class TemplateEngine:
    """
    基于Jinja2的模板引擎
    支持复杂的动态变量渲染
    """

    def __init__(self, strict_mode: bool = False, auto_reload: bool = True):
        """
        初始化模板引擎

        Args:
            strict_mode: 严格模式，如果变量未定义则报错
            auto_reload: 自动重新加载模板
        """
        # 创建Jinja2环境
        self.env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined if strict_mode else Undefined,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            auto_reload=auto_reload,
            extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols']
        )

        # 上下文数据
        self.context = {}

        # 序列计数器
        self.sequences: Dict[str, int] = {}

        # 缓存已编译的模板
        self.template_cache: Dict[str, Any] = {}

        # 注册功能
        self._register_filters()
        self._register_functions()
        self._register_tests()

        logger.info("模板引擎初始化完成")

    def _register_filters(self):
        """注册Jinja2过滤器"""

        # JSON过滤器
        def to_json(value, indent=2, ensure_ascii=False):
            """转换为JSON字符串"""
            try:
                return json.dumps(value, indent=indent, ensure_ascii=ensure_ascii)
            except (TypeError, ValueError):
                return str(value)

        def from_json(value):
            """从JSON字符串解析"""
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        # 字符串过滤器
        def truncate(value, length=100, end='...'):
            """截断字符串"""
            if not isinstance(value, str):
                value = str(value)
            if len(value) <= length:
                return value
            return value[:length - len(end)] + end

        def strip(value, chars=None):
            """去除空格"""
            if isinstance(value, str):
                return value.strip(chars) if chars else value.strip()
            return value

        def md5_filter(value):
            """计算MD5哈希"""
            return hashlib.md5(str(value).encode()).hexdigest()

        def sha256_filter(value):
            """计算SHA256哈希"""
            return hashlib.sha256(str(value).encode()).hexdigest()

        def base64_encode(value):
            """Base64编码"""
            import base64
            return base64.b64encode(str(value).encode()).decode()

        def base64_decode(value):
            """Base64解码"""
            import base64
            try:
                return base64.b64decode(value).decode()
            except:
                return value

        # 数字过滤器
        def round_filter(value, digits=2):
            """四舍五入"""
            try:
                return round(float(value), digits)
            except (ValueError, TypeError):
                return value

        def int_filter(value, default=0):
            """转换为整数"""
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        def float_filter(value, default=0.0):
            """转换为浮点数"""
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        # 日期时间过滤器
        def strftime(value, format="%Y-%m-%d %H:%M:%S"):
            """格式化时间"""
            if isinstance(value, (int, float)):
                value = datetime.fromtimestamp(value)
            if isinstance(value, datetime):
                return value.strftime(format)
            return value

        def timestamp_filter(value):
            """转换为时间戳"""
            if isinstance(value, datetime):
                return int(value.timestamp())
            return value

        # 注册过滤器
        self.env.filters.update({
            # JSON
            'to_json': to_json,
            'from_json': from_json,
            'json': to_json,

            # 字符串
            'truncate': truncate,
            'strip': strip,
            'lower': lambda x: x.lower() if isinstance(x, str) else x,
            'upper': lambda x: x.upper() if isinstance(x, str) else x,
            'capitalize': lambda x: x.capitalize() if isinstance(x, str) else x,
            'title': lambda x: x.title() if isinstance(x, str) else x,
            'replace': lambda x, old, new: x.replace(old, new) if isinstance(x, str) else x,
            'split': lambda x, sep=',': x.split(sep) if isinstance(x, str) else [x],
            'join': lambda x, sep=',': sep.join(str(i) for i in x) if isinstance(x, (list, tuple)) else x,
            'md5': md5_filter,
            'sha256': sha256_filter,
            'base64': base64_encode,
            'base64_decode': base64_decode,
            'length': len,

            # 数字
            'round': round_filter,
            'int': int_filter,
            'float': float_filter,
            'abs': abs,

            # 日期时间
            'strftime': strftime,
            'timestamp': timestamp_filter,

            # 类型转换
            'str': str,
            'list': lambda x: list(x) if isinstance(x, (tuple, set)) else [x],
            'dict': dict,
            'bool': bool,
        })

        logger.debug("Jinja2过滤器注册完成")

    def _register_functions(self):
        """注册全局函数"""

        # 时间函数
        def timestamp(offset_seconds=0):
            """获取时间戳"""
            return int(time.time()) + offset_seconds

        def now(format_str="%Y-%m-%d %H:%M:%S", days=0, hours=0, minutes=0, seconds=0):
            """获取当前时间"""
            dt = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            if format_str:
                return dt.strftime(format_str)
            return dt

        def today(days=0, format_str="%Y-%m-%d"):
            """获取日期"""
            dt = datetime.now() + timedelta(days=days)
            return dt.strftime(format_str)

        def time_millis():
            """获取毫秒时间戳"""
            return int(time.time() * 1000)

        def date_add(date_str, days=0, format_str="%Y-%m-%d"):
            """日期加减"""
            dt = datetime.strptime(date_str, format_str) if isinstance(date_str, str) else date_str
            dt = dt + timedelta(days=days)
            return dt.strftime(format_str)

        # 随机函数
        def random_string(length=10, chars=None):
            """生成随机字符串"""
            if chars is None:
                chars = string.ascii_letters + string.digits
            return ''.join(random.choice(chars) for _ in range(length))

        def random_int(min_val=1, max_val=1000):
            """生成随机整数"""
            return random.randint(min_val, max_val)

        def random_float(min_val=0.0, max_val=1.0, precision=2):
            """生成随机浮点数"""
            value = random.uniform(min_val, max_val)
            return round(value, precision)

        def random_choice(items):
            """随机选择"""
            if isinstance(items, str):
                items = [item.strip() for item in items.split(',')]
            return random.choice(items) if items else None

        def random_bool(true_probability=0.5):
            """随机布尔值"""
            return random.random() < true_probability

        def random_uuid():
            """生成UUID"""
            return str(uuid.uuid4())

        # 序列函数
        def sequence(name="default", start=1, step=1, reset=False):
            """生成序列号"""
            if reset or name not in self.sequences:
                self.sequences[name] = start
            else:
                self.sequences[name] += step
            return self.sequences[name]

        # 数学函数
        def add(*args):
            """求和"""
            return sum(float(arg) for arg in args)

        def multiply(*args):
            """求积"""
            result = 1
            for arg in args:
                result *= float(arg)
            return result

        def divide(a, b, default=0):
            """除法"""
            try:
                return float(a) / float(b)
            except ZeroDivisionError:
                return default

        # 环境变量函数
        def get_env(key, default=None):
            """获取环境变量"""
            return os.environ.get(key, default)

        def get_env_int(key, default=0):
            """获取整数环境变量"""
            try:
                return int(os.environ.get(key, default))
            except (ValueError, TypeError):
                return default

        def get_env_bool(key, default=False):
            """获取布尔环境变量"""
            value = os.environ.get(key, str(default))
            return value.lower() in ('true', '1', 'yes', 'y', 't')

        # 加密函数
        def md5(value):
            """计算MD5"""
            return hashlib.md5(str(value).encode()).hexdigest()

        def sha256(value):
            """计算SHA256"""
            return hashlib.sha256(str(value).encode()).hexdigest()

        # 文件函数
        def read_file(filepath):
            """读取文件"""
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                logger.error(f"文件不存在: {filepath}")
                return ""

        # 注册函数
        self.env.globals.update({
            # 时间
            'timestamp': timestamp,
            'now': now,
            'today': today,
            'time_millis': time_millis,
            'date_add': date_add,
            'datetime': datetime,
            'timedelta': timedelta,

            # 随机
            'random': random,
            'random_string': random_string,
            'random_int': random_int,
            'random_float': random_float,
            'random_choice': random_choice,
            'random_bool': random_bool,
            'random_uuid': random_uuid,
            'uuid': random_uuid,

            # 序列
            'sequence': sequence,

            # 数学
            'add': add,
            'sum': add,
            'multiply': multiply,
            'sub': lambda a, b: float(a) - float(b),
            'div': divide,
            'divide': divide,
            'mod': lambda a, b: float(a) % float(b) if float(b) != 0 else 0,
            'max': max,
            'min': min,
            'avg': lambda *args: sum(float(arg) for arg in args) / len(args) if args else 0,
            'abs': abs,
            'round': round,

            # 环境变量
            'env': get_env,
            'getenv': get_env,
            'env_int': get_env_int,
            'env_bool': get_env_bool,

            # 类型转换
            'int': int,
            'float': float,
            'str': str,
            'bool': lambda x: bool(x),
            'list': lambda x: list(x) if x else [],
            'dict': lambda x: dict(x) if x else {},

            # 加密
            'md5': md5,
            'sha256': sha256,
            'hash': md5,

            # 文件
            'read_file': read_file,

            # 其他
            'len': len,
            'range': range,
            'zip': zip,
            'enumerate': enumerate,
        })

        # 注册Faker函数
        try:
            faker = Faker()
            for attr_name in dir(faker):
                if not attr_name.startswith('_') and callable(getattr(faker, attr_name)):
                    func = getattr(faker, attr_name)
                    if not inspect.isclass(func):
                        self.env.globals[f'fake_{attr_name}'] = func
        except Exception as e:
            logger.warning(f"注册Faker函数失败: {e}")

        logger.debug("Jinja2全局函数注册完成")

    def _register_tests(self):
        """注册测试函数"""

        def is_number(value):
            """检查是否为数字"""
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False

        def is_int(value):
            """检查是否为整数"""
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False

        def is_float(value):
            """检查是否为浮点数"""
            try:
                float(value)
                return not is_int(value)
            except (ValueError, TypeError):
                return False

        def is_list(value):
            """检查是否为列表"""
            return isinstance(value, (list, tuple))

        def is_dict(value):
            """检查是否为字典"""
            return isinstance(value, dict)

        def is_str(value):
            """检查是否为字符串"""
            return isinstance(value, str)

        def is_bool(value):
            """检查是否为布尔值"""
            return isinstance(value, bool)

        def is_none(value):
            """检查是否为None"""
            return value is None

        def is_not_none(value):
            """检查是否不为None"""
            return value is not None

        def is_empty(value):
            """检查是否为空"""
            if value is None:
                return True
            if isinstance(value, (str, list, dict, tuple, set)):
                return len(value) == 0
            return False

        def is_not_empty(value):
            """检查是否不为空"""
            return not is_empty(value)

        # 注册测试函数
        self.env.tests.update({
            'number': is_number,
            'integer': is_int,
            'float': is_float,
            'list': is_list,
            'tuple': is_list,
            'dict': is_dict,
            'string': is_str,
            'bool': is_bool,
            'none': is_none,
            'not_none': is_not_none,
            'empty': is_empty,
            'not_empty': is_not_empty,
        })

        logger.debug("Jinja2测试函数注册完成")

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

    def _render_recursive(self, data: Any, context: Dict) -> Any:
        """递归渲染数据"""

        if isinstance(data, str):
            # 处理字符串模板
            return self._render_string(data, context)

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

    def _render_string(self, template_str: str, context: Dict) -> str:
        """渲染字符串模板"""
        if not isinstance(template_str, str):
            return template_str

        # 检查是否包含模板语法
        if not self._has_template_syntax(template_str):
            return template_str

        # 编译和缓存模板
        if template_str in self.template_cache:
            compiled_template = self.template_cache[template_str]
        else:
            try:
                compiled_template = self.env.from_string(template_str)
                self.template_cache[template_str] = compiled_template
            except TemplateError as e:
                logger.warning(f"模板编译失败: {e}, 模板: {template_str[:100]}...")
                return template_str

        # 渲染模板
        try:
            return compiled_template.render(**context)
        except TemplateError as e:
            logger.warning(f"模板渲染失败: {e}, 模板: {template_str[:100]}...")
            return template_str

    def _has_template_syntax(self, text: str) -> bool:
        """检查字符串是否包含模板语法"""
        # 检查是否包含Jinja2模板语法
        patterns = [
            r'\{\{.*?\}\}',  # 变量 {{ var }}
            r'\{\%.*?\%\}',  # 语句 {% statement %}
            r'\{\#.*?\#\}',  # 注释 {# comment #}
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.DOTALL):
                return True

        return False

    def render_string(self, template_str: str, **kwargs) -> str:
        """渲染字符串模板（快捷方法）"""
        return self.render(template_str, **kwargs)

    def render_file(self, filepath: str, **kwargs) -> str:
        """渲染文件模板"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.render(content, **kwargs)
        except FileNotFoundError:
            logger.error(f"模板文件不存在: {filepath}")
            return ""

    def eval_expression(self, expression: str, **kwargs) -> Any:
        """计算表达式（返回Python对象）"""
        try:
            # 将表达式包装在模板中
            template_str = f"{{{{ {expression} }}}}"
            result = self.render_string(template_str, **kwargs)

            # 尝试解析为Python对象
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return result
        except Exception as e:
            logger.error(f"表达式计算失败: {expression}, 错误: {e}")
            return None

    def register_filter(self, name: str, func):
        """注册自定义过滤器"""
        self.env.filters[name] = func
        logger.debug(f"注册过滤器: {name}")

    def register_function(self, name: str, func):
        """注册自定义函数"""
        self.env.globals[name] = func
        logger.debug(f"注册函数: {name}")

    def register_test(self, name: str, func):
        """注册自定义测试函数"""
        self.env.tests[name] = func
        logger.debug(f"注册测试函数: {name}")


# 创建全局模板引擎实例
template_engine = TemplateEngine()


if __name__ == "__main__":
    print(__file__)
    print(sys.path)
    context = {
        "a": "aa",
        "b": "bb",
    }
    template_engine.register_function("test", lambda x, y: x + y)
    template_engine.update_context(**context)
    print(template_engine.render("hello,{{ a }}"))
    print(template_engine.render("hello,{{ b }}"))
    print(template_engine.render("hello,{{ c }}"))
    print(template_engine.render("now(),{{ now() | }}"))
    print(template_engine.render("md5,{{ 'aaaa'|md5 }}"))
    print(template_engine.render("json,{{ '{name:1;ba:2}' | to_json }}"))
