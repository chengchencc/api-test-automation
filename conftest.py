import pytest
import allure
import os
import json
from datetime import datetime
from src.config.settings import project_config
from src.config.logger import logger
from src.common.template_engine_manager import template_engine

import sys

print("syspath::")
print(sys.path)

def pytest_configure(config):
    """Pytest配置钩子"""
    # 设置环境变量
    os.environ['ALLURE_RESULTS'] = str(project_config.ALLURE_RESULTS)

    # 创建必要的目录
    project_config.ALLURE_RESULTS.mkdir(exist_ok=True)

    # 添加自定义标记说明
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "api: API接口测试"
    )
    config.addinivalue_line(
        "markers", "data_driven: 数据驱动测试"
    )

    logger.info("Pytest配置完成")


def pytest_unconfigure(config):
    """Pytest卸载钩子"""
    logger.info("Pytest测试完成")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """获取测试结果并添加附件"""
    outcome = yield
    rep = outcome.get_result()

    # 设置Allure报告属性
    if rep.when == "call":
        # 测试用例执行完成
        if rep.failed:
            # 测试失败
            item.allure_report = rep
            _attach_failure_details(item, rep)
        elif rep.passed:
            # 测试通过
            item.allure_report = rep
        else:
            # 测试跳过
            item.allure_report = rep


def _attach_failure_details(item, rep):
    """附加失败详情到Allure报告"""

    # 获取失败信息
    if rep.longrepr:
        failure_info = str(rep.longrepr)

        # 添加失败信息到Allure
        allure.attach(
            failure_info,
            name="失败详情",
            attachment_type=allure.attachment_type.TEXT
        )

    # 添加日志文件
    log_file = project_config.LOG_DIR / f"test_{datetime.now().strftime('%Y%m%d')}.log"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
                # 只取最后1000行日志
                log_lines = logs.split('\n')
                recent_logs = '\n'.join(log_lines[-1000:])

                allure.attach(
                    recent_logs,
                    name="测试日志",
                    attachment_type=allure.attachment_type.TEXT
                )
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """测试会话设置"""
    logger.info("=" * 60)
    logger.info("开始测试会话")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"项目目录: {project_config.BASE_DIR}")
    logger.info(f"测试数据: {project_config.EXCEL_FILE}")
    logger.info(f"基础URL: {project_config.BASE_URL}")
    logger.info(f"使用AccessToken: {project_config.TEST_AUTH_TOKEN}")
    logger.info("=" * 60)

    # request 增加 auth token

    from src.common.request_client import request_client
    request_client.set_auth("Bearer",**{"token":project_config.TEST_AUTH_TOKEN})

    # 创建测试环境
    yield

    logger.info("=" * 60)
    logger.info("测试会话结束")
    logger.info("=" * 60)


@pytest.fixture(scope="function", autouse=True)
def setup_test_function(request):
    """测试函数设置"""
    test_name = request.node.name
    logger.info(f"开始测试: {test_name}")

    # 记录测试开始时间
    request.start_time = datetime.now()

    yield

    # 记录测试结束时间
    end_time = datetime.now()
    duration = (end_time - request.start_time).total_seconds()
    logger.info(f"结束测试: {test_name}, 耗时: {duration:.2f}秒")


@pytest.fixture
def test_data():
    """测试数据fixture"""
    return {
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "test_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "random_string": template_engine.render_string("{{ random_string(10) }}"),
        "random_int": template_engine.render_string("{{ random_int(1, 1000) }}"),
    }


@pytest.fixture
def auth_token():
    """认证token fixture"""
    # 这里可以获取认证token
    token = os.environ.get("TEST_AUTH_TOKEN", "")
    if not token:
        # 如果没有配置token，尝试登录获取
        try:
            from src.common.request_client import request_client
            login_data = {
                "username": os.environ.get("TEST_USERNAME", "admin"),
                "password": os.environ.get("TEST_PASSWORD", "admin123")
            }
            response = request_client.post("/api/login", json_data=login_data)
            if response.status_code == 200:
                token = response.json().get("data", {}).get("token", "")
        except:
            pass

    return token


@pytest.fixture
def api_client(auth_token):
    """API客户端fixture"""
    from src.common.request_client import RequestClient

    client = RequestClient()

    # 添加认证头
    if auth_token:
        client.add_header("Authorization", f"Bearer {auth_token}")

    yield client

    # 清理
    client.clear_headers()


@pytest.fixture
def excel_test_cases():
    """Excel测试用例fixture"""
    from src.common.excel_reader import excel_reader
    return excel_reader.get_test_cases()


@pytest.fixture
def template_context():
    """模板上下文fixture"""
    context = {
        "timestamp": int(datetime.now().timestamp()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 更新模板引擎上下文
    template_engine.update_context(**context)

    return context


@pytest.fixture
def cleanup():
    """清理fixture"""
    cleanup_items = []

    def _add_cleanup(item):
        cleanup_items.append(item)

    yield _add_cleanup

    # 执行清理
    for item in cleanup_items:
        try:
            if callable(item):
                item()
            elif isinstance(item, dict) and 'type' in item:
                if item['type'] == 'api':
                    from src.common.request_client import request_client
                    request_client.send_request(**item['request'])
        except Exception as e:
            logger.warning(f"清理失败: {e}")


# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        help="测试环境: test, staging, production"
    )
    parser.addoption(
        "--browser",
        action="store_true",
        default=False,
        help="是否在浏览器中打开Allure报告"
    )
    parser.addoption(
        "--parallel",
        action="store_true",
        default=False,
        help="是否并行执行测试"
    )


@pytest.fixture(scope="session")
def test_env(request):
    """测试环境fixture"""
    return request.project_config.getoption("--env")


# Allure环境文件
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束钩子"""
    # 生成Allure环境文件
    allure_env = {
        "测试环境": os.environ.get("ENVIRONMENT", "test"),
        "基础URL": project_config.BASE_URL,
        "Python版本": os.environ.get("PYTHON_VERSION", "unknown"),
        "操作系统": os.name,
        "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "项目路径": str(project_config.BASE_DIR),
    }

    # 写入环境文件
    env_file = project_config.ALLURE_RESULTS / "environment.properties"
    with open(env_file, 'w', encoding='utf-8') as f:
        for key, value in allure_env.items():
            f.write(f"{key}={value}\n")

    # 生成测试结果汇总
    if hasattr(session, 'testscollected'):
        total = session.testscollected
        failed = session.testsfailed
        # skipped = session.testsskipped && 0
        skipped = 0 #TODO:无 testsskipped 参数
        passed = total - failed - skipped
        # passed = len(session.testscollected) - len(session.testsfailed) - len(session.testsskipped)

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%"
        }

        summary_file = project_config.ALLURE_RESULTS / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)