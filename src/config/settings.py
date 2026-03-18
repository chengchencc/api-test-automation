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
    TOKEN_CACHE_DIR = BASE_DIR / ".token_cache"

    # 文件路径   # TEST_DATA_DIR / "api_test_cases.xlsx"
    EXCEL_FILE = ""
    
    # 基本配置
    BASE_URL = os.getenv("API_BASE_URL", "https://www.metersphere.com")
    TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    VERIFY_SSL = os.getenv("VERIFY_SSL", "False").lower() == "true"
    MAX_RETRY = int(os.getenv("MAX_RETRY", "3"))

    # 测试认证信息
    TEST_AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN")

    # OAuth 2.0 配置
    OAUTH2_ENABLED = os.getenv("OAUTH2_ENABLED", "True").lower() == "true"
    OAUTH2_AUTH_URL = os.getenv("OAUTH2_AUTH_URL", f"{BASE_URL}/oauth/authorize")
    OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL", f"{BASE_URL}/oauth/token")
    OAUTH2_REFRESH_URL = os.getenv("OAUTH2_REFRESH_URL", f"{BASE_URL}/oauth/token")
    OAUTH2_REVOKE_URL = os.getenv("OAUTH2_REVOKE_URL", f"{BASE_URL}/oauth/revoke")
    OAUTH2_INTROSPECT_URL = os.getenv("OAUTH2_INTROSPECT_URL", f"{BASE_URL}/oauth/introspect")

    # 客户端凭证
    OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "test_client")
    OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "test_secret")
    OAUTH2_SCOPE = os.getenv("OAUTH2_SCOPE", "read write").split(" ")

    # 资源所有者凭证（密码模式）
    OAUTH2_USERNAME = os.getenv("OAUTH2_USERNAME", "test_user")
    OAUTH2_PASSWORD = os.getenv("OAUTH2_PASSWORD", "test_password")

    # 授权类型
    OAUTH2_GRANT_TYPE = os.getenv("OAUTH2_GRANT_TYPE", "password")  # password, client_credentials, authorization_code

    # 令牌配置
    OAUTH2_TOKEN_EXPIRY_THRESHOLD = int(os.getenv("OAUTH2_TOKEN_EXPIRY_THRESHOLD", "300"))  # 5分钟
    OAUTH2_AUTO_REFRESH = os.getenv("OAUTH2_AUTO_REFRESH", "True").lower() == "true"
    OAUTH2_TOKEN_CACHE_FILE = TOKEN_CACHE_DIR / "oauth2_tokens.json"

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