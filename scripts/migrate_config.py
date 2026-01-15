#!/usr/bin/env python3
"""
配置文件迁移脚本
将旧的.env配置迁移到新的YAML配置结构
"""
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv


def load_old_env_config(env_file: Path) -> dict:
    """加载旧的.env配置文件"""
    if not env_file.exists():
        print(f"错误: .env文件不存在: {env_file}")
        sys.exit(1)

    # 加载环境变量
    load_dotenv(env_file)

    # 收集所有环境变量
    config = {}
    for key, value in os.environ.items():
        # 跳过系统环境变量
        if key.startswith(('PATH', 'PYTHON', 'HOME', 'USER', 'SHELL', 'TERM')):
            continue
        config[key] = value

    return config


def convert_to_yaml_config(old_config: dict) -> dict:
    """将旧的配置转换为新的YAML结构"""
    yaml_config = {
        'env': 'testing',
        'debug': False,
        'api': {},
        'database': {},
        'test_account': {},
        'email': {},
        'logging': {},
        'test': {},
        'template': {},
        'oauth2': {},
        'cache': {},
        'report': {},
        'data': {},
        'monitoring': {}
    }

    # API配置映射
    api_mapping = {
        'API_BASE_URL': 'base_url',
        'REQUEST_TIMEOUT': 'timeout',
        'MAX_RETRY': 'max_retries',
        'VERIFY_SSL': 'verify_ssl'
    }

    for old_key, new_key in api_mapping.items():
        if old_key in old_config:
            value = old_config[old_key]
            # 类型转换
            if new_key == 'timeout' or new_key == 'max_retries':
                yaml_config['api'][new_key] = int(value)
            elif new_key == 'verify_ssl':
                yaml_config['api'][new_key] = value.lower() == 'true'
            else:
                yaml_config['api'][new_key] = value

    # 数据库配置
    if 'DATABASE_URL' in old_config:
        yaml_config['database']['url'] = old_config['DATABASE_URL']

    # Redis配置
    if 'REDIS_URL' in old_config:
        yaml_config['redis'] = {'url': old_config['REDIS_URL']}

    # 测试账号
    account_mapping = {
        'TEST_USERNAME': 'username',
        'TEST_PASSWORD': 'password',
        'TEST_AUTH_TOKEN': 'auth_token'
    }

    for old_key, new_key in account_mapping.items():
        if old_key in old_config:
            yaml_config['test_account'][new_key] = old_config[old_key]

    # 邮件配置
    email_mapping = {
        'EMAIL_HOST': 'host',
        'EMAIL_PORT': 'port',
        'EMAIL_USER': 'user',
        'EMAIL_PASSWORD': 'password'
    }

    for old_key, new_key in email_mapping.items():
        if old_key in old_config:
            value = old_config[old_key]
            if new_key == 'port':
                yaml_config['email'][new_key] = int(value)
            else:
                yaml_config['email'][new_key] = value

    # 日志配置
    if 'LOG_LEVEL' in old_config:
        yaml_config['logging']['level'] = old_config['LOG_LEVEL']
    if 'LOG_FORMAT' in old_config:
        yaml_config['logging']['format'] = old_config['LOG_FORMAT']

    # 测试配置
    test_mapping = {
        'TEST_RUNNER': 'runner',
        'TEST_PARALLEL': 'parallel',
        'TEST_RERUNS': 'reruns'
    }

    for old_key, new_key in test_mapping.items():
        if old_key in old_config:
            value = old_config[old_key]
            if new_key == 'reruns':
                yaml_config['test'][new_key] = int(value)
            elif new_key == 'parallel':
                yaml_config['test'][new_key] = value.lower() == 'true'
            else:
                yaml_config['test'][new_key] = value

    # 模板配置
    if 'TEMPLATE_AUTO_RELOAD' in old_config:
        yaml_config['template']['auto_reload'] = old_config['TEMPLATE_AUTO_RELOAD'].lower() == 'true'
    if 'TEMPLATE_STRICT_MODE' in old_config:
        yaml_config['template']['strict_mode'] = old_config['TEMPLATE_STRICT_MODE'].lower() == 'true'

    # 环境标识
    if 'ENVIRONMENT' in old_config:
        env_value = old_config['ENVIRONMENT'].lower()
        if env_value in ['development', 'testing', 'production']:
            yaml_config['env'] = env_value
        if env_value == 'development':
            yaml_config['debug'] = True

    return yaml_config


def save_yaml_config(config: dict, output_file: Path):
    """保存YAML配置到文件"""
    # 确保目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"YAML配置已保存到: {output_file}")


def create_env_example(old_config: dict):
    """创建新的.env.example文件"""
    env_example_content = """# 新的环境变量配置
# 注意：新的框架建议使用YAML配置文件
# 环境变量主要用于覆盖YAML配置中的特定值

# 环境标识
ENV=testing

# API配置覆盖
# API_BASE_URL=https://api.example.com
# API_TIMEOUT=30
# API_MAX_RETRIES=3
# API_VERIFY_SSL=true

# 日志配置覆盖
# LOG_LEVEL=INFO

# 数据库配置覆盖
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# 测试配置覆盖
# TEST_PARALLEL=false
# TEST_WORKERS=4
# TEST_RERUNS=0

# 敏感信息（建议使用环境变量而不是配置文件）
# OAUTH2_CLIENT_ID=your_client_id
# OAUTH2_CLIENT_SECRET=your_client_secret
# EMAIL_PASSWORD=your_email_password
"""

    # 添加旧的敏感信息作为注释
    sensitive_keys = ['TEST_PASSWORD', 'TEST_AUTH_TOKEN', 'EMAIL_PASSWORD', 'DATABASE_URL']
    env_example_content += "\n# 从旧配置迁移的敏感信息（请更新为实际值）\n"
    for key in sensitive_keys:
        if key in old_config:
            masked_value = '*' * 8 if old_config[key] else '未设置'
            env_example_content += f"# {key}={masked_value}\n"

    output_file = Path('.env.new.example')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(env_example_content)

    print(f"新的.env.example已创建: {output_file}")


def generate_migration_report(old_config: dict, new_config: dict):
    """生成迁移报告"""
    report = """# 配置迁移报告

## 迁移摘要

已将旧的.env配置迁移到新的YAML配置结构。

## 主要变化

### 1. 配置格式变化
- **旧格式**: .env文件（键值对）
- **新格式**: YAML文件（结构化配置）

### 2. 配置项重命名

| 旧配置项 | 新配置项 | 说明 |
|----------|----------|------|
"""

    # 添加重命名映射
    mappings = [
        ('API_BASE_URL', 'api.base_url', 'API基础URL'),
        ('REQUEST_TIMEOUT', 'api.timeout', '请求超时时间'),
        ('MAX_RETRY', 'api.max_retries', '最大重试次数'),
        ('VERIFY_SSL', 'api.verify_ssl', 'SSL验证'),
        ('DATABASE_URL', 'database.url', '数据库URL'),
        ('TEST_USERNAME', 'test_account.username', '测试用户名'),
        ('TEST_PASSWORD', 'test_account.password', '测试密码'),
        ('TEST_AUTH_TOKEN', 'test_account.auth_token', '测试认证令牌'),
        ('EMAIL_HOST', 'email.host', '邮件服务器'),
        ('EMAIL_PORT', 'email.port', '邮件端口'),
        ('EMAIL_USER', 'email.user', '邮件用户'),
        ('EMAIL_PASSWORD', 'email.password', '邮件密码'),
        ('LOG_LEVEL', 'logging.level', '日志级别'),
        ('LOG_FORMAT', 'logging.format', '日志格式'),
        ('TEST_RUNNER', 'test.runner', '测试运行器'),
        ('TEST_PARALLEL', 'test.parallel', '并行测试'),
        ('TEST_RERUNS', 'test.reruns', '失败重试'),
        ('TEMPLATE_AUTO_RELOAD', 'template.auto_reload', '模板自动重载'),
        ('TEMPLATE_STRICT_MODE', 'template.strict_mode', '模板严格模式'),
        ('ENVIRONMENT', 'env', '环境标识'),
    ]

    for old_key, new_key, description in mappings:
        if old_key in old_config:
            report += f"| `{old_key}` | `{new_key}` | {description} |\n"

    report += """
### 3. 新增配置项

新的配置结构添加了以下配置项：
- `oauth2`: OAuth 2.0认证配置
- `cache`: 缓存配置
- `report`: 报告配置
- `data`: 数据目录配置
- `monitoring`: 监控配置

### 4. 配置访问方式变化

**旧方式**:
```python
from src.config.configuration import project_config
BASE_URL = project_config.BASE_URL
```

**新方式**:
```python
from src.config.settings import settings
BASE_URL = settings.API_BASE_URL
```

### 5. 多环境支持

新的配置系统支持多环境：
- `config/env/development.yaml` - 开发环境
- `config/env/testing.yaml` - 测试环境
- `config/env/production.yaml` - 生产环境

## 迁移步骤

1. **备份旧的配置**
   ```bash
   cp .env .env.backup
   ```

2. **使用新的配置**
   - 主配置: `config/settings.yaml`
   - 环境配置: `config/env/testing.yaml`
   - 环境变量: `.env`（仅用于覆盖）

3. **更新代码**
   - 将 `from src.config.configuration import project_config` 替换为 `from src.config.settings import settings`
   - 更新配置访问方式（如 `project_config.BASE_URL` -> `settings.API_BASE_URL`）

4. **测试验证**
   ```bash
   python scripts/migrate_config.py --test
   ```

## 注意事项

1. **敏感信息**: 密码、令牌等敏感信息建议使用环境变量而不是配置文件
2. **向后兼容**: 旧的代码可以通过兼容性模块继续工作
3. **逐步迁移**: 可以逐步迁移，不需要一次性完成

## 帮助和支持

如有问题，请参考：
- 新框架文档: `docs/guides/framework-improvement.md`
- 示例代码: `tests/api/test_api_migrated.py`
- 兼容性模块: `src/compat/__init__.py`
"""

    output_file = Path('config_migration_report.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"迁移报告已生成: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='配置文件迁移工具')
    parser.add_argument('--env-file', default='.env', help='旧的.env文件路径')
    parser.add_argument('--output', default='config/env/testing.yaml', help='输出YAML文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式，不实际写入文件')
    parser.add_argument('--report', action='store_true', help='生成迁移报告')

    args = parser.parse_args()

    print("开始配置文件迁移...")
    print(f"源文件: {args.env_file}")
    print(f"目标文件: {args.output}")

    # 加载旧配置
    old_config = load_old_env_config(Path(args.env_file))
    print(f"加载了 {len(old_config)} 个配置项")

    # 转换为新配置
    new_config = convert_to_yaml_config(old_config)
    print("配置转换完成")

    if args.test:
        # 测试模式，只显示配置
        print("\n转换后的YAML配置:")
        print(yaml.dump(new_config, default_flow_style=False, allow_unicode=True))
        return

    # 保存新配置
    save_yaml_config(new_config, Path(args.output))

    # 创建新的.env.example
    create_env_example(old_config)

    if args.report:
        # 生成迁移报告
        generate_migration_report(old_config, new_config)

    print("\n迁移完成！")
    print("下一步:")
    print("1. 检查生成的YAML配置文件")
    print("2. 更新代码中的配置访问方式")
    print("3. 运行测试验证迁移结果")
    print("4. 删除或备份旧的.env文件")


if __name__ == '__main__':
    main()