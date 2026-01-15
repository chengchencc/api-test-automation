"""
环境管理器模块
提供环境变量管理和多环境配置支持
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv, find_dotenv


class EnvironmentManager:
    """
    环境管理器
    管理环境变量和多环境配置
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化环境管理器

        Args:
            env_file: 环境变量文件路径，如果为None则自动查找
        """
        self.env_file = env_file
        self._loaded = False
        self._environments = {}

    def load(self, override: bool = False) -> bool:
        """
        加载环境变量

        Args:
            override: 是否覆盖已存在的环境变量

        Returns:
            是否成功加载
        """
        try:
            if self.env_file:
                # 加载指定的环境变量文件
                result = load_dotenv(self.env_file, override=override)
            else:
                # 自动查找环境变量文件
                result = load_dotenv(override=override)

            self._loaded = result
            return result
        except Exception as e:
            print(f"加载环境变量失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取环境变量

        Args:
            key: 环境变量键
            default: 默认值

        Returns:
            环境变量值
        """
        return os.getenv(key, default)

    def set(self, key: str, value: Any):
        """
        设置环境变量

        Args:
            key: 环境变量键
            value: 环境变量值
        """
        os.environ[key] = str(value)

    def delete(self, key: str):
        """
        删除环境变量

        Args:
            key: 环境变量键
        """
        if key in os.environ:
            del os.environ[key]

    def get_all(self) -> Dict[str, str]:
        """
        获取所有环境变量

        Returns:
            环境变量字典
        """
        return dict(os.environ)

    def load_environment(self, env_name: str, env_dir: Optional[Path] = None) -> bool:
        """
        加载指定环境的配置

        Args:
            env_name: 环境名称（development, testing, production等）
            env_dir: 环境配置目录

        Returns:
            是否成功加载
        """
        if env_dir is None:
            env_dir = Path(__file__).parent.parent.parent / "config" / "env"

        env_file = env_dir / f"{env_name}.yaml"
        if not env_file.exists():
            print(f"环境配置文件不存在: {env_file}")
            return False

        try:
            import yaml
            with open(env_file, 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f)

            if env_config:
                # 将配置设置到环境变量中
                for key, value in env_config.items():
                    if isinstance(value, (dict, list)):
                        # 复杂类型转换为JSON字符串
                        import json
                        self.set(key, json.dumps(value))
                    else:
                        self.set(key, str(value))

                self._environments[env_name] = env_config
                return True

        except Exception as e:
            print(f"加载环境配置失败 {env_file}: {e}")

        return False

    def get_environment_config(self, env_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定环境的配置

        Args:
            env_name: 环境名称

        Returns:
            环境配置字典
        """
        return self._environments.get(env_name)

    def switch_environment(self, env_name: str) -> bool:
        """
        切换环境

        Args:
            env_name: 环境名称

        Returns:
            是否成功切换
        """
        # 清除当前环境变量（除了系统变量）
        for key in list(os.environ.keys()):
            if not key.startswith(('PATH', 'PYTHON', 'HOME', 'USER', 'SHELL')):
                self.delete(key)

        # 加载新环境
        return self.load_environment(env_name)

    def validate_required_vars(self, required_vars: list) -> list:
        """
        验证必需的环境变量

        Args:
            required_vars: 必需的环境变量列表

        Returns:
            缺失的环境变量列表
        """
        missing_vars = []
        for var in required_vars:
            if not self.get(var):
                missing_vars.append(var)
        return missing_vars

    def export_to_file(self, file_path: Path, include_system: bool = False):
        """
        导出环境变量到文件

        Args:
            file_path: 导出文件路径
            include_system: 是否包含系统环境变量
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.get_all().items():
                    if include_system or not key.startswith(('PATH', 'PYTHON', 'HOME', 'USER', 'SHELL')):
                        # 对值进行转义处理
                        escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                        f.write(f'{key}="{escaped_value}"\n')
        except Exception as e:
            print(f"导出环境变量失败: {e}")

    def print_summary(self):
        """打印环境变量摘要"""
        print("=" * 50)
        print("环境变量摘要:")
        print("=" * 50)

        # 打印加载的环境
        if self._environments:
            print(f"已加载环境: {', '.join(self._environments.keys())}")

        # 打印重要的环境变量
        important_vars = [
            'ENV', 'DEBUG', 'API_BASE_URL', 'LOG_LEVEL',
            'DATABASE_URL', 'OAUTH2_ENABLED', 'EMAIL_ENABLED'
        ]

        print("\n重要环境变量:")
        for var in important_vars:
            value = self.get(var)
            if value:
                # 敏感信息脱敏
                if 'SECRET' in var or 'PASSWORD' in var or 'TOKEN' in var:
                    masked_value = '*' * 8 if value else '未设置'
                    print(f"  {var}: {masked_value}")
                else:
                    print(f"  {var}: {value}")
            else:
                print(f"  {var}: 未设置")

        # 验证必需的环境变量
        required_vars = ['API_BASE_URL']
        missing_vars = self.validate_required_vars(required_vars)
        if missing_vars:
            print(f"\n警告: 缺失必需的环境变量: {missing_vars}")

        print("=" * 50)

    @property
    def is_loaded(self) -> bool:
        """是否已加载环境变量"""
        return self._loaded

    @property
    def current_environment(self) -> Optional[str]:
        """获取当前环境"""
        return self.get('ENV')

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.current_environment == 'development'

    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.current_environment == 'testing'

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.current_environment == 'production'


# 全局环境管理器实例
env_manager = EnvironmentManager()

# 自动加载环境变量
env_manager.load()