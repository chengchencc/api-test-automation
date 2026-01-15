import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from .settings import project_config


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "extra_data"):
            log_record["extra_data"] = record.extra_data
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record, ensure_ascii=False)


def setup_logger(name: str = "api_test"):
    """设置日志"""
    
    logger = logging.getLogger(name)
    
    # 避免重复设置
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, project_config.LOG_LEVEL))
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(project_config.LOG_LEVEL)
    
    if project_config.LOG_LEVEL == "DEBUG":
        console_format = logging.Formatter(project_config.LOG_FORMAT)
    else:
        console_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    
    console_handler.setFormatter(console_format)
    
    # 文件handler
    log_file = project_config.LOG_DIR / f"test_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 使用JSON格式记录到文件
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    
    # 错误日志文件handler
    error_file = project_config.LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # 添加handler
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


logger = setup_logger()


class TestLogger:
    """测试专用的日志记录器"""
    
    def __init__(self, test_name: str = None):
        self.test_name = test_name
        self.logger = logger
        
    def log_request(self, method: str, url: str, data: dict = None, headers: dict = None):
        """记录请求日志"""
        request_info = {
            "method": method,
            "url": url,
            "data": data,
            "headers": headers
        }
        # self.logger.info(f"请求信息: {method} {url} {headers}", extra={"extra_data": request_info})
        self.logger.info(f"请求信息: {method} {url} {headers}", extra=request_info)

    def log_response(self, response):
        """记录响应日志"""
        try:
            response_data = response.json() if response.content else None
        except:
            response_data = response.text[:500]  # 截断过长的响应
        
        response_info = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response_data,
            "elapsed": response.elapsed.total_seconds()
        }
        
        level = logging.ERROR if response.status_code >= 400 else logging.INFO
        self.logger.log(level, f"响应: {response.status_code}，data:{response_data}", extra={"extra_data": response_info})
    
    def log_step(self, step_name: str, details: dict = None):
        """记录测试步骤"""
        step_info = {
            "step": step_name,
            "details": details
        }
        if self.test_name:
            self.logger.info(f"{self.test_name} - {step_name}", extra={"extra_data": step_info})
        else:
            self.logger.info(step_name, extra={"extra_data": details})


test_logger = TestLogger()