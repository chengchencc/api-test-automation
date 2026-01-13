import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent.parent / "output"
    
    # 目录路径
    TEST_DATA_DIR = BASE_DIR / "test_data"
    REPORT_DIR = BASE_DIR / "reports"
    LOG_DIR = BASE_DIR / "logs"
    TEMPLATE_DIR = BASE_DIR / "templates"
    
    # 文件路径
    EXCEL_FILE = TEST_DATA_DIR / "api_test_cases.xlsx"
    
    # 基本配置
    BASE_URL = os.getenv("API_BASE_URL", "http://api.example.com")
    TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    VERIFY_SSL = os.getenv("VERIFY_SSL", "False").lower() == "true"
    MAX_RETRY = int(os.getenv("MAX_RETRY", "3"))
    
    # Allure配置
    ALLURE_RESULTS = REPORT_DIR / "allure-results"
    ALLURE_REPORT = REPORT_DIR / "allure-report"
    
    # 数据库配置（可选）
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # 邮件配置（可选）
    EMAIL_HOST = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    
    # 测试配置
    TEST_RUNNER = os.getenv("TEST_RUNNER", "pytest")
    TEST_PARALLEL = os.getenv("TEST_PARALLEL", "False").lower() == "true"
    TEST_RERUNS = int(os.getenv("TEST_RERUNS", "0"))
    
    # 模板配置
    TEMPLATE_AUTO_RELOAD = os.getenv("TEMPLATE_AUTO_RELOAD", "False").lower() == "true"
    TEMPLATE_STRICT_MODE = os.getenv("TEMPLATE_STRICT_MODE", "False").lower() == "true"
    
    # 创建必要的目录
    for directory in [TEST_DATA_DIR, REPORT_DIR, LOG_DIR, ALLURE_RESULTS, TEMPLATE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_allure_report_url(cls):
        """获取Allure报告URL"""
        return f"file://{cls.ALLURE_REPORT.absolute()}/index.html"
    
    @classmethod
    def get_html_report_path(cls):
        """获取HTML报告路径"""
        return cls.REPORT_DIR / "report.html"


project_config = Config()