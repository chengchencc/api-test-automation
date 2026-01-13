#!/usr/bin/env python3
"""
接口自动化测试框架运行脚本
支持Jinja2模板引擎和数据驱动测试
"""
import subprocess
import sys
import argparse
import webbrowser
import time
from src.config.configuration import project_config
from src.config.logger import logger

print("sys.path:")

print(sys.path)

class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def run_tests(self,
                  test_type: str = "all",
                  parallel: bool = False,
                  reruns: int = 0,
                  workers: int = None,
                  html_report: bool = True,
                  **kwargs) -> int:
        """
        运行测试

        Args:
            test_type: 测试类型 (all, smoke, api, regression)
            parallel: 是否并行执行
            reruns: 失败重试次数
            workers: 并行工作进程数
            html_report: 是否生成HTML报告
            **kwargs: 其他参数

        Returns:
            退出码
        """
        self.start_time = time.time()

        # 基本pytest命令
        cmd:list[str] = [
            "pytest",
            f"--alluredir={project_config.ALLURE_RESULTS}",
            "--clean-alluredir",
            "-v",
            "--disable-warnings",
        ]

        # 根据测试类型添加标记
        if test_type == "smoke":
            cmd.append("-m smoke")
            logger.info("运行冒烟测试")
        elif test_type == "api":
            cmd.append("-m api")
            logger.info("运行API测试")
        elif test_type == "regression":
            cmd.append("-m regression")
            logger.info("运行回归测试")
        elif test_type == "performance":
            cmd.append("-m performance")
            logger.info("运行性能测试")
        elif test_type != "all":
            # 自定义标记
            cmd.append(f"-m {test_type}")
            logger.info(f"运行 {test_type} 测试")

        # 并行执行
        if parallel:
            if workers:
                cmd.extend(["-n", str(workers)])
            else:
                cmd.extend(["-n", "auto"])
            logger.info("启用并行测试")

        # 失败重试
        if reruns > 0:
            cmd.extend(["--reruns", str(reruns), "--reruns-delay", "2"])
            logger.info(f"启用失败重试: {reruns}次")

        # HTML报告
        if html_report:
            html_report_path = project_config.get_html_report_path()
            cmd.extend([
                f"--html={html_report_path}",
                "--self-contained-html"
            ])

        # 添加额外的命令行参数
        for key, value in kwargs.items():
            if value is True:
                cmd.append(f"--{key.replace('_', '-')}")
            elif value is not False and value is not None:
                cmd.append(f"--{key.replace('_', '-')}={value}")

        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info("-" * 60)

        # 执行测试
        try:
            result = subprocess.run(cmd)
            exit_code = result.returncode
        except KeyboardInterrupt:
            logger.warning("测试被用户中断")
            exit_code = 130
        except Exception as e:
            logger.error(f"执行测试失败: {e}")
            exit_code = 1

        self.end_time = time.time()
        duration = self.end_time - self.start_time

        logger.info("-" * 60)
        if exit_code == 0:
            logger.info(f"测试执行成功，耗时: {duration:.2f}秒")
        else:
            logger.error(f"测试执行失败，退出码: {exit_code}，耗时: {duration:.2f}秒")

        return exit_code

    def generate_allure_report(self, open_browser: bool = False) -> int:
        """生成Allure报告"""
        logger.info("生成Allure报告...")

        if not project_config.ALLURE_RESULTS.exists() or not any(project_config.ALLURE_RESULTS.iterdir()):
            logger.warning("没有测试结果，跳过生成Allure报告")
            return 0

        # 生成Allure报告
        cmd = [
            "allure", "generate",
            str(project_config.ALLURE_RESULTS),
            "-o", str(project_config.ALLURE_REPORT),
            "--clean"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                report_url = project_config.get_allure_report_url()
                logger.info(f"Allure报告生成成功: {report_url}")

                # 在浏览器中打开报告
                if open_browser:
                    self.open_allure_report()

                return 0
            else:
                logger.error(f"Allure报告生成失败: {result.stderr}")
                return result.returncode

        except FileNotFoundError:
            logger.error("Allure未安装，请先安装Allure: https://docs.qameta.io/allure/")
            return 1
        except Exception as e:
            logger.error(f"生成Allure报告失败: {e}")
            return 1

    def open_allure_report(self):
        """打开Allure报告"""
        if (project_config.ALLURE_REPORT / "index.html").exists():
            report_url = project_config.get_allure_report_url()
            logger.info(f"在浏览器中打开报告: {report_url}")

            try:
                webbrowser.open(report_url)
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")
        else:
            logger.error("Allure报告不存在，请先运行测试并生成报告")

    def open_html_report(self):
        """打开HTML报告"""
        html_report_path = project_config.get_html_report_path()
        if html_report_path.exists():
            report_url = f"file://{html_report_path.absolute()}"
            logger.info(f"在浏览器中打开HTML报告: {report_url}")

            try:
                webbrowser.open(report_url)
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")
        else:
            logger.error("HTML报告不存在，请先运行测试")

    def list_test_cases(self):
        """列出所有测试用例"""
        from src.common.excel_reader import excel_reader

        logger.info("列出所有测试用例:")
        logger.info("=" * 60)

        suites = excel_reader.get_test_suites()
        total_cases = 0

        for sheet_name, test_cases in suites.items():
            logger.info(f"测试套件: {sheet_name} ({len(test_cases)} 个用例)")

            for case in test_cases:
                case_id = case.get('case_id', '未知')
                case_name = case.get('case_name', '未知')
                method = case.get('method', 'GET')
                url = case.get('url', '')
                logger.info(f"  {case_id}: {case_name} [{method} {url}]")

            total_cases += len(test_cases)

        logger.info("=" * 60)
        logger.info(f"总计: {len(suites)} 个测试套件, {total_cases} 个测试用例")

    def validate_test_data(self):
        """验证测试数据"""
        from src.common.excel_reader import excel_reader

        logger.info("验证测试数据...")

        try:
            # 验证Excel文件
            if not project_config.EXCEL_FILE.exists():
                logger.error(f"测试数据文件不存在: {project_config.EXCEL_FILE}")
                return 1

            # 读取测试用例
            test_cases = excel_reader.get_test_cases(render_templates=False)

            if not test_cases:
                logger.warning("没有找到测试用例")
                return 0

            # 验证每个用例
            valid_cases = 0
            invalid_cases = []

            for case in test_cases:
                case_id = case.get('case_id', '未知')
                case_name = case.get('case_name', '')

                # 基本验证
                errors = []

                if not case_name:
                    errors.append("缺少用例名称")

                if not case.get('method'):
                    errors.append("缺少请求方法")

                if not case.get('url'):
                    errors.append("缺少URL")

                if errors:
                    invalid_cases.append((case_id, case_name, errors))
                else:
                    valid_cases += 1

            # 输出验证结果
            logger.info(f"验证完成:")
            logger.info(f"  有效用例: {valid_cases}")
            logger.info(f"  无效用例: {len(invalid_cases)}")

            if invalid_cases:
                logger.warning("无效用例列表:")
                for case_id, case_name, errors in invalid_cases:
                    logger.warning(f"  {case_id}: {case_name}")
                    for error in errors:
                        logger.warning(f"    - {error}")
                return 1

            return 0

        except Exception as e:
            logger.error(f"验证测试数据失败: {e}")
            return 1

    def clear_reports(self):
        """清理测试报告"""
        import shutil

        logger.info("清理测试报告...")

        for report_dir in [project_config.ALLURE_RESULTS, project_config.ALLURE_REPORT, project_config.REPORT_DIR]:
            if report_dir.exists():
                try:
                    shutil.rmtree(report_dir)
                    logger.info(f"已删除: {report_dir}")
                except Exception as e:
                    logger.error(f"删除失败 {report_dir}: {e}")

        # 重新创建目录
        project_config.REPORT_DIR.mkdir(exist_ok=True)
        logger.info("清理完成")

    def generate_excel_template(self):
        """生成Excel模板文件"""
        import pandas as pd

        logger.info("生成Excel模板文件...")

        # 创建模板文件路径
        template_file = project_config.TEMPLATE_DIR / "api_test_cases_template.xlsx"

        # 定义测试用例模板
        test_cases_data = [
            {
                "case_id": "TC001",
                "case_name": "示例用例-健康检查",
                "description": "测试健康检查接口",
                "tags": "smoke,api",
                "severity": "critical",
                "method": "GET",
                "url": "/health",
                "headers": '{"Content-Type": "application/json"}',
                "params": "{}",
                "data": "",
                "json": "",
                "expected_status": 200,
                "expected_response": '{"status": "ok"}',
                "expected_schema": "",
                "expected_contains": "ok",
                "max_response_time": 1.0,
                "setup_data": "",
                "teardown_data": "",
                "extract": '{"token": "data.token"}',
                "assertions": '[{"type": "status_code", "expected": 200}]'
            },
            {
                "case_id": "TC002",
                "case_name": "示例用例-用户登录",
                "description": "测试用户登录接口，使用动态参数",
                "tags": "regression,api",
                "severity": "critical",
                "method": "POST",
                "url": "/api/login",
                "headers": '{"Content-Type": "application/json"}',
                "params": "",
                "data": "",
                "json": '{"username": "{{ random_string(8, \\"user_\\") }}", "password": "{{ random_string(12) }}", "timestamp": "{{ timestamp() }}"}',
                "expected_status": 200,
                "expected_response": '{"code": 0, "message": "success"}',
                "expected_schema": '{"code": "int", "message": "str", "data": {"token": "str", "user_id": "int"}}',
                "expected_contains": "",
                "max_response_time": 2.0,
                "setup_data": "",
                "teardown_data": "",
                "extract": '{"auth_token": "data.token", "user_id": "data.user_id"}',
                "assertions": '[{"type": "json_path", "jsonpath": "$.code", "expected": 0}]'
            }
        ]

        # 定义配置模板
        config_data = [
            {"key": "base_url", "value": "http://api.example.com"},
            {"key": "timeout", "value": "30"},
            {"key": "admin_user", "value": "admin"},
            {"key": "admin_password", "value": "admin123"},
        ]

        try:
            with pd.ExcelWriter(template_file, engine='openpyxl') as writer:
                # 写入测试用例
                df_cases = pd.DataFrame(test_cases_data)
                df_cases.to_excel(writer, sheet_name='test_cases', index=False)

                # 写入配置
                df_config = pd.DataFrame(config_data)
                df_config.to_excel(writer, sheet_name='config', index=False)

                # 写入说明
                wb = writer.book
                ws = wb.create_sheet("说明")

                instructions = [
                    ["Excel测试数据文件说明", "", "", ""],
                    ["", "", "", ""],
                    ["Sheet名称", "说明", "必填列", "示例"],
                    ["test_cases", "测试用例", "case_name, method, url", ""],
                    ["config", "配置文件", "key, value", ""],
                    ["", "", "", ""],
                    ["Jinja2模板语法示例:", "", "", ""],
                    ["变量替换", "{{ timestamp() }}", "当前时间戳", ""],
                    ["随机字符串", "{{ random_string(10) }}", "10位随机字符串", ""],
                    ["随机整数", "{{ random_int(1, 100) }}", "1-100随机整数", ""],
                    ["随机邮箱", "{{ random_email() }}", "随机邮箱地址", ""],
                    ["UUID", "{{ uuid() }}", "UUID字符串", ""],
                    ["今日日期", "{{ today() }}", "今天日期", ""],
                    ["日期计算", "{{ today(days=-1) }}", "昨天日期", ""],
                    ["序列号", "{{ sequence('order') }}", "订单序列号", ""],
                    ["", "", "", ""],
                    ["过滤器示例:", "", "", ""],
                    ["MD5", "{{ 'password' | md5 }}", "计算MD5", ""],
                    ["截断", "{{ 'long text' | truncate(5) }}", "截断文本", ""],
                    ["JSON", "{{ data | to_json }}", "转换为JSON", ""],
                ]

                for row in instructions:
                    ws.append(row)

            logger.info(f"Excel模板生成成功: {template_file}")
            return 0

        except Exception as e:
            logger.error(f"生成Excel模板失败: {e}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="接口自动化测试框架 - 基于Jinja2模板引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        使用示例:
          # 运行所有测试
          python run.py
        
          # 运行冒烟测试
          python run.py --type smoke
        
          # 并行运行测试
          python run.py --parallel --workers 4
        
          # 失败重试
          python run.py --reruns 2
        
          # 生成报告并在浏览器中打开
          python run.py --report --open
        
          # 验证测试数据
          python run.py --validate
        
          # 列出所有测试用例
          python run.py --list
                """
    )

    # 测试运行选项
    parser.add_argument("--type", "-t",
                        choices=["all", "smoke", "api", "regression", "performance","data_driven"],
                        default="all",
                        help="测试类型")
    parser.add_argument("--parallel", "-p",
                        action="store_true",
                        help="并行执行测试")
    parser.add_argument("--workers", "-w",
                        type=int,
                        help="并行工作进程数")
    parser.add_argument("--reruns", "-r",
                        type=int,
                        default=0,
                        help="失败重试次数")
    parser.add_argument("--html",
                        action="store_true",
                        default=True,
                        help="生成HTML报告")
    parser.add_argument("--no-html",
                        action="store_false",
                        dest="html",
                        help="不生成HTML报告")

    # 报告选项
    parser.add_argument("--report",
                        action="store_true",
                        help="生成Allure报告")
    parser.add_argument("--open",
                        action="store_true",
                        help="在浏览器中打开Allure报告")
    parser.add_argument("--open-html",
                        action="store_true",
                        help="在浏览器中打开HTML报告")

    # 工具选项
    parser.add_argument("--list", "-l",
                        action="store_true",
                        help="列出所有测试用例")
    parser.add_argument("--validate",
                        action="store_true",
                        help="验证测试数据")
    parser.add_argument("--clear",
                        action="store_true",
                        help="清理测试报告")
    parser.add_argument("--template",
                        action="store_true",
                        help="生成Excel模板文件")

    # 其他选项
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="详细输出")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logger.setLevel("DEBUG")
        logger.debug("启用详细日志")

    # 创建测试运行器
    runner = TestRunner()

    # 执行工具命令
    if args.list:
        runner.list_test_cases()
        return 0

    if args.validate:
        return runner.validate_test_data()

    if args.clear:
        runner.clear_reports()
        return 0

    if args.template:
        return runner.generate_excel_template()

    if args.open_html:
        runner.open_html_report()
        return 0

    # 生成报告
    if args.report:
        return runner.generate_allure_report(args.open)

    # 运行测试
    exit_code = runner.run_tests(
        test_type=args.type,
        parallel=args.parallel,
        reruns=args.reruns,
        workers=args.workers,
        html_report=args.html
    )

    # 生成报告
    if exit_code == 0 or exit_code == 1:  # 0: 成功, 1: 测试失败
        runner.generate_allure_report(args.open)

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)