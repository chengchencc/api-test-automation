"""
日志工具模块
提供统一的日志管理和格式化功能
"""
import logging
import sys
import json
import inspect
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON字符串"""
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.threadName,
            "process": record.processName,
        }

        # 添加额外数据
        if hasattr(record, "extra_data"):
            log_record["extra_data"] = record.extra_data

        # 添加异常信息
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # 添加堆栈信息（仅DEBUG级别）
        if record.levelno == logging.DEBUG:
            log_record["stack"] = self._get_stack_info()

        return json.dumps(log_record, ensure_ascii=False, separators=(',', ':'))

    def _get_stack_info(self) -> str:
        """获取堆栈信息"""
        stack = inspect.stack()
        # 跳过logger.py本身的调用
        stack_info = []
        for frame_info in stack[3:10]:  # 限制深度
            filename = frame_info.filename
            lineno = frame_info.lineno
            function = frame_info.function
            stack_info.append(f"{filename}:{lineno} in {function}")
        return " -> ".join(stack_info)


class ColorFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""

    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m',       # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS['RESET'])

        if settings.DEBUG:
            # 调试模式显示详细信息
            message = f"{color}{levelname:8s}{self.COLORS['RESET']} " \
                     f"{record.name} - {record.filename}:{record.lineno} - {record.getMessage()}"
        else:
            # 非调试模式显示简洁信息
            message = f"{color}{levelname:8s}{self.COLORS['RESET']} {record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class TestLogger:
    """测试专用的日志器"""

    def __init__(self, test_name: str):
        """
        初始化测试日志器

        Args:
            test_name: 测试名称
        """
        self.test_name = test_name
        self.logger = get_logger(f"test.{test_name}")
        self.steps = []
        self.start_time = datetime.now()

    def log_step(self, step: str, data: Optional[Dict[str, Any]] = None):
        """
        记录测试步骤

        Args:
            step: 步骤描述
            data: 步骤数据
        """
        timestamp = datetime.now()
        step_info = {
            "step": step,
            "timestamp": timestamp.isoformat(),
            "data": data or {}
        }
        self.steps.append(step_info)

        # 记录到日志
        log_data = {"step": step, "test": self.test_name}
        if data:
            log_data.update(data)

        self.logger.info(f"测试步骤: {step}", extra={"extra_data": log_data})

    def log_result(self, result: str, details: Optional[Dict[str, Any]] = None):
        """
        记录测试结果

        Args:
            result: 测试结果（PASS, FAIL, SKIP等）
            details: 结果详情
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        result_info = {
            "result": result,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "steps": self.steps,
            "details": details or {}
        }

        self.logger.info(f"测试结果: {result}", extra={"extra_data": result_info})

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        记录测试错误

        Args:
            error: 异常对象
            context: 错误上下文
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "test": self.test_name,
            "context": context or {}
        }

        self.logger.error(f"测试错误: {error}", extra={"extra_data": error_info}, exc_info=True)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取测试摘要

        Returns:
            测试摘要字典
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "total_steps": len(self.steps),
            "steps": self.steps,
        }


def setup_logging():
    """设置日志系统"""
    # 获取日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper())

    # 创建日志目录
    log_dir = settings.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColorFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（JSON格式）
    json_log_file = log_dir / "framework" / "framework.json.log"
    json_log_file.parent.mkdir(parents=True, exist_ok=True)

    json_handler = RotatingFileHandler(
        json_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    json_handler.setLevel(log_level)
    json_formatter = JSONFormatter()
    json_handler.setFormatter(json_formatter)
    root_logger.addHandler(json_handler)

    # 测试日志文件（文本格式）
    test_log_file = log_dir / "test" / "test.log"
    test_log_file.parent.mkdir(parents=True, exist_ok=True)

    test_handler = RotatingFileHandler(
        test_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    test_handler.setLevel(log_level)
    test_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    test_handler.setFormatter(test_formatter)
    root_logger.addHandler(test_handler)

    # 设置特定模块的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('pytest').setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


def get_test_logger(test_name: str) -> TestLogger:
    """
    获取测试日志器

    Args:
        test_name: 测试名称

    Returns:
        测试日志器实例
    """
    return TestLogger(test_name)


def log_function_call(func):
    """记录函数调用的装饰器"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = func.__name__

        # 记录函数调用开始
        logger.debug(f"调用函数: {func_name}", extra={
            "extra_data": {
                "args": str(args),
                "kwargs": str(kwargs)
            }
        })

        try:
            result = func(*args, **kwargs)
            # 记录函数调用成功
            logger.debug(f"函数调用成功: {func_name}", extra={
                "extra_data": {
                    "result": str(result)[:100]  # 限制结果长度
                }
            })
            return result
        except Exception as e:
            # 记录函数调用失败
            logger.error(f"函数调用失败: {func_name}", extra={
                "extra_data": {
                    "error": str(e),
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            }, exc_info=True)
            raise

    return wrapper


# 自动设置日志系统
setup_logging()

# 创建全局日志器
logger = get_logger("api_test_framework")