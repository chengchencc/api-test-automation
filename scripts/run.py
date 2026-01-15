#!/usr/bin/env python3
"""
API自动化测试框架运行脚本
简化版，专注于核心功能
"""
import sys
import os
import argparse
import subprocess
import webbrowser
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.utils.logger import logger, setup_logging


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.logger = logger

    def run_tests(self, args):
        """
        运行测试

        Args:
            args: 命令行参数
        """
        self.logger.info("开始运行测试")

        # 构建pytest命令
        pytest_cmd = self._build_pytest_command(args)

        # 执行测试
        exit_code = self._execute_command(pytest_cmd)

        # 生成报告
        if args.report:
            self.generate_report()

        # 打开报告
        if args.open:
            self.open_report()

        return exit_code

    def _build_pytest_command(self, args):
        """构建pytest命令"""
        cmd = ["pytest"]

        # 添加测试路径
        if args.test_path:
            cmd.append(args.test_path)
        else:
            cmd.append("tests/")

        # 添加标记过滤
        if args.markers:
            cmd.extend(["-m", args.markers])

        # 添加测试类型
        if args.type:
            cmd.extend(["-m", args.type])

        # 并行执行
        if args.parallel:
            cmd.extend(["-n", str(args.workers)])

        # 失败重试
        if args.reruns > 0:
            cmd.extend(["--reruns", str(args.reruns)])

        # 详细输出
        if args.verbose:
            cmd.append("-v")

        # 输出Allure结果
        cmd.extend(["--alluredir", str(settings.ALLURE_RESULTS_DIR)])

        # 添加配置文件
        cmd.extend(["-c", "pytest.ini"])

        return cmd

    def _execute_command(self, cmd):
        """执行命令"""
        self.logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return 1

    def generate_report(self):
        """生成测试报告"""
        self.logger.info("生成测试报告")

        # 生成Allure报告
        if settings.ALLURE_RESULTS_DIR.exists():
            allure_cmd = [
                "allure", "generate",
                str(settings.ALLURE_RESULTS_DIR),
                "-o", str(settings.ALLURE_REPORT_DIR),
                "--clean"
            ]

            try:
                subprocess.run(allure_cmd, check=True)
                self.logger.info(f"Allure报告已生成: {settings.allure_report_url}")
            except Exception as e:
                self.logger.error(f"生成Allure报告失败: {e}")

    def open_report(self):
        """打开测试报告"""
        if settings.ALLURE_REPORT_DIR.exists():
            report_url = settings.allure_report_url
            self.logger.info(f"打开报告: {report_url}")
            webbrowser.open(report_url)
        else:
            self.logger.warning("报告不存在，请先生成报告")

    def validate_config(self):
        """验证配置"""
        self.logger.info("验证配置")

        # 检查必要的目录
        required_dirs = [
            settings.DATA_DIR,
            settings.EXCEL_DIR,
            settings.JSON_DIR,
            settings.LOGS_DIR,
            settings.REPORTS_DIR,
        ]

        for directory in required_dirs:
            if not directory.exists():
                self.logger.warning(f"目录不存在: {directory}")
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"已创建目录: {directory}")

        # 检查必要的文件
        required_files = [
            settings.excel_test_cases_path,
            Path("requirements.txt"),
            Path("pytest.ini"),
        ]

        for file_path in required_files:
            if not file_path.exists():
                self.logger.warning(f"文件不存在: {file_path}")

        self.logger.info("配置验证完成")

    def list_tests(self):
        """列出测试用例"""
        self.logger.info("列出测试用例")

        cmd = ["pytest", "--collect-only", "-q"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            tests = [line for line in result.stdout.split('\n') if line.strip()]
            for test in tests:
                print(test)
        except Exception as e:
            self.logger.error(f"列出测试用例失败: {e}")

    def generate_template(self):
        """生成Excel模板"""
        self.logger.info("生成Excel模板")

        try:
            import pandas as pd
            from openpyxl import Workbook

            # 创建测试用例模板
            test_cases_df = pd.DataFrame(columns=[
                'test_case_id', 'test_case_name', 'description',
                'method', 'endpoint', 'headers', 'params', 'data',
                'expected_status', 'expected_response', 'extract',
                'depends_on', 'tags', 'severity', 'setup', 'teardown'
            ])

            # 创建测试数据模板
            test_data_df = pd.DataFrame(columns=[
                'data_id', 'data_name', 'description',
                'data_type', 'data_value', 'is_template'
            ])

            # 保存到Excel文件
            with pd.ExcelWriter(settings.excel_test_cases_path, engine='openpyxl') as writer:
                test_cases_df.to_excel(writer, sheet_name='test_cases', index=False)
                test_data_df.to_excel(writer, sheet_name='test_data', index=False)

            self.logger.info(f"Excel模板已生成: {settings.excel_test_cases_path}")

        except Exception as e:
            self.logger.error(f"生成Excel模板失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="API自动化测试框架")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # run命令
    run_parser = subparsers.add_parser('run', help='运行测试')
    run_parser.add_argument('test_path', nargs='?', help='测试路径')
    run_parser.add_argument('-t', '--type', help='测试类型 (smoke, regression, api)')
    run_parser.add_argument('-m', '--markers', help='测试标记')
    run_parser.add_argument('-p', '--parallel', action='store_true', help='并行执行')
    run_parser.add_argument('-w', '--workers', type=int, default=4, help='工作进程数')
    run_parser.add_argument('-r', '--reruns', type=int, default=0, help='失败重试次数')
    run_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    run_parser.add_argument('-R', '--report', action='store_true', help='生成报告')
    run_parser.add_argument('-o', '--open', action='store_true', help='打开报告')

    # validate命令
    subparsers.add_parser('validate', help='验证配置')

    # list命令
    subparsers.add_parser('list', help='列出测试用例')

    # template命令
    subparsers.add_parser('template', help='生成Excel模板')

    # 解析参数
    args = parser.parse_args()

    # 设置日志
    setup_logging()

    # 创建运行器
    runner = TestRunner()

    # 执行命令
    if args.command == 'run':
        return runner.run_tests(args)
    elif args.command == 'validate':
        runner.validate_config()
    elif args.command == 'list':
        runner.list_tests()
    elif args.command == 'template':
        runner.generate_template()
    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    sys.exit(main())