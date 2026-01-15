"""
配置设置模块
提供统一的配置管理和环境变量支持
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class Settings:
    """
    配置设置类
    统一管理所有配置项，支持环境变量和配置文件
    """

    # 环境配置
    ENV: str = field(default_factory=lambda: os.getenv("ENV", "development"))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() == "true")

    # 项目路径
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    PROJECT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)

    # 数据目录
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    EXCEL_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "excel")
    JSON_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "json")
    YAML_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "yaml")
    SQL_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "sql")

    # 输出目录
    OUTPUT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "output")
    LOGS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    REPORTS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "reports")

    # 配置文件目录
    CONFIG_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "config")

    # 文档目录
    DOCS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "docs")

    # 脚本目录
    SCRIPTS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "scripts")

    # API配置
    API_BASE_URL: str = field(default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000"))
    API_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("API_TIMEOUT", "30")))
    API_MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv("API_MAX_RETRIES", "3")))
    API_VERIFY_SSL: bool = field(default_factory=lambda: os.getenv("API_VERIFY_SSL", "True").lower() == "true")

    # 测试配置
    TEST_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("TEST_TIMEOUT", "30")))
    TEST_MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv("TEST_MAX_RETRIES", "3")))
    TEST_PARALLEL: bool = field(default_factory=lambda: os.getenv("TEST_PARALLEL", "False").lower() == "true")
    TEST_WORKERS: int = field(default_factory=lambda: int(os.getenv("TEST_WORKERS", "4")))
    TEST_RERUNS: int = field(default_factory=lambda: int(os.getenv("TEST_RERUNS", "0")))

    # 日志配置
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FORMAT: str = field(default_factory=lambda: os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    ))
    LOG_FILE: str = field(default_factory=lambda: os.getenv("LOG_FILE", "test.log"))

    # 报告配置
    REPORT_FORMAT: str = field(default_factory=lambda: os.getenv("REPORT_FORMAT", "allure,html"))
    ALLURE_RESULTS_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "reports" / "allure-results")
    ALLURE_REPORT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "reports" / "allure-report")
    HTML_REPORT_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "reports" / "html")

    # 数据库配置
    DATABASE_URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    DATABASE_POOL_SIZE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "10")))
    DATABASE_MAX_OVERFLOW: int = field(default_factory=lambda: int(os.getenv("DATABASE_MAX_OVERFLOW", "20")))

    # OAuth 2.0配置
    OAUTH2_ENABLED: bool = field(default_factory=lambda: os.getenv("OAUTH2_ENABLED", "False").lower() == "true")
    OAUTH2_CLIENT_ID: str = field(default_factory=lambda: os.getenv("OAUTH2_CLIENT_ID", ""))
    OAUTH2_CLIENT_SECRET: str = field(default_factory=lambda: os.getenv("OAUTH2_CLIENT_SECRET", ""))
    OAUTH2_TOKEN_URL: str = field(default_factory=lambda: os.getenv("OAUTH2_TOKEN_URL", ""))
    OAUTH2_AUTH_URL: str = field(default_factory=lambda: os.getenv("OAUTH2_AUTH_URL", ""))
    OAUTH2_SCOPE: str = field(default_factory=lambda: os.getenv("OAUTH2_SCOPE", ""))

    # 模板配置
    TEMPLATE_AUTO_RELOAD: bool = field(default_factory=lambda: os.getenv("TEMPLATE_AUTO_RELOAD", "False").lower() == "true")
    TEMPLATE_STRICT_MODE: bool = field(default_factory=lambda: os.getenv("TEMPLATE_STRICT_MODE", "False").lower() == "true")
    TEMPLATE_CACHE_SIZE: int = field(default_factory=lambda: int(os.getenv("TEMPLATE_CACHE_SIZE", "100")))

    # 缓存配置
    CACHE_ENABLED: bool = field(default_factory=lambda: os.getenv("CACHE_ENABLED", "True").lower() == "true")
    CACHE_TTL: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "300")))
    CACHE_MAX_SIZE: int = field(default_factory=lambda: int(os.getenv("CACHE_MAX_SIZE", "1000")))

    # 邮件配置
    EMAIL_ENABLED: bool = field(default_factory=lambda: os.getenv("EMAIL_ENABLED", "False").lower() == "true")
    EMAIL_HOST: str = field(default_factory=lambda: os.getenv("EMAIL_HOST", ""))
    EMAIL_PORT: int = field(default_factory=lambda: int(os.getenv("EMAIL_PORT", "587")))
    EMAIL_USER: str = field(default_factory=lambda: os.getenv("EMAIL_USER", ""))
    EMAIL_PASSWORD: str = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))

    def __post_init__(self):
        """初始化后处理"""
        # 加载环境变量
        load_dotenv()

        # 加载配置文件
        self._load_config_files()

        # 创建必要的目录
        self._create_directories()

    def _load_config_files(self):
        """加载配置文件"""
        config_files = [
            self.CONFIG_DIR / "settings.yaml",
            self.CONFIG_DIR / "env" / f"{self.ENV}.yaml",
        ]

        for config_file in config_files:
            if config_file.exists():
                self._load_yaml_config(config_file)

    def _load_yaml_config(self, config_file: Path):
        """加载YAML配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    self._update_from_dict(config_data)
        except Exception as e:
            print(f"加载配置文件失败 {config_file}: {e}")

    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """从字典更新配置"""
        for key, value in config_dict.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.DATA_DIR,
            self.EXCEL_DIR,
            self.JSON_DIR,
            self.YAML_DIR,
            self.SQL_DIR,
            self.OUTPUT_DIR,
            self.LOGS_DIR,
            self.REPORTS_DIR,
            self.ALLURE_RESULTS_DIR,
            self.ALLURE_REPORT_DIR,
            self.HTML_REPORT_DIR,
            self.CONFIG_DIR / "env",
            self.CONFIG_DIR / "plugins",
            self.LOGS_DIR / "test",
            self.LOGS_DIR / "framework",
            self.REPORTS_DIR / "allure",
            self.REPORTS_DIR / "html",
            self.REPORTS_DIR / "json",
            self.DOCS_DIR / "api",
            self.DOCS_DIR / "examples",
            self.DOCS_DIR / "guides",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key in dir(self):
            if not key.startswith('_') and key.isupper():
                value = getattr(self, key)
                if isinstance(value, Path):
                    result[key] = str(value)
                else:
                    result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return getattr(self, key.upper(), default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        setattr(self, key.upper(), value)

    def update(self, config_dict: Dict[str, Any]):
        """批量更新配置"""
        for key, value in config_dict.items():
            self.set(key, value)

    def reload(self):
        """重新加载配置"""
        self.__post_init__()

    @property
    def allure_report_url(self) -> str:
        """获取Allure报告URL"""
        return f"file://{self.ALLURE_REPORT_DIR.absolute()}/index.html"

    @property
    def html_report_path(self) -> Path:
        """获取HTML报告路径"""
        return self.HTML_REPORT_DIR / "report.html"

    @property
    def excel_test_cases_path(self) -> Path:
        """获取Excel测试用例路径"""
        return self.EXCEL_DIR / "test_cases.xlsx"

    @property
    def excel_test_data_path(self) -> Path:
        """获取Excel测试数据路径"""
        return self.EXCEL_DIR / "test_data.xlsx"

    @property
    def json_schemas_path(self) -> Path:
        """获取JSON Schema路径"""
        return self.JSON_DIR / "api_schemas.json"

    @property
    def yaml_config_path(self) -> Path:
        """获取YAML配置路径"""
        return self.YAML_DIR / "test_config.yaml"

    @property
    def sql_data_path(self) -> Path:
        """获取SQL数据路径"""
        return self.SQL_DIR / "test_data.sql"

    def __str__(self) -> str:
        """字符串表示"""
        config_dict = self.to_dict()
        lines = ["Settings配置:"]
        for key, value in config_dict.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)