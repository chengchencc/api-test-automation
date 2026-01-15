import pandas as pd
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from src.config.logger import logger
from src.config.settings import project_config
from .template_engine_manager import template_engine

# from .template_engines.factory import TemplateEngineFactory
#
# factory = TemplateEngineFactory()
#
# template_engine = factory.create_engine()

class ExcelReader:
    """Excel数据读取器（支持Jinja2模板）"""

    def __init__(self, excel_file: Optional[Union[str, Path]] = None):
        """
        初始化Excel读取器

        Args:
            excel_file: Excel文件路径
        """
        self.excel_file = Path(excel_file) if excel_file else project_config.EXCEL_FILE
        self._data_cache = {}
        self._sheet_cache = {}

        if not self.excel_file.exists():
            logger.error(f"Excel文件不存在: {self.excel_file}")
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_file}")

        logger.info(f"初始化Excel读取器，文件: {self.excel_file}")

    def read_sheet(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        读取Excel工作表

        Args:
            sheet_name: 工作表名称，如果为None则读取第一个工作表

        Returns:
            pandas DataFrame
        """
        cache_key = sheet_name or "first_sheet"

        if cache_key in self._sheet_cache:
            logger.debug(f"从缓存读取工作表: {sheet_name or '第一个工作表'}")
            return self._sheet_cache[cache_key]

        try:
            if sheet_name:
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name, dtype=str)
            else:
                # 读取第一个sheet
                df = pd.read_excel(self.excel_file, dtype=str, sheet_name=0)

            # 清理列名
            df.columns = df.columns.str.strip()

            # 填充NaN值为空字符串
            df = df.fillna('')

            # 缓存数据
            self._sheet_cache[cache_key] = df

            logger.info(f"成功读取Excel工作表: {sheet_name or '第一个工作表'}, 行数: {len(df)}")
            return df

        except Exception as e:
            logger.error(f"读取Excel工作表失败: {e}")
            raise

    def get_sheet_names(self) -> List[str]:
        """获取所有工作表名称"""
        try:
            excel_file = pd.ExcelFile(self.excel_file)
            sheet_names = excel_file.sheet_names
            logger.info(f"获取工作表名称: {sheet_names}")
            return sheet_names
        except Exception as e:
            logger.error(f"获取工作表名称失败: {e}")
            return []

    def get_test_cases(self,
                       sheet_name: str = "test_cases",
                       render_templates: bool = True,
                       context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        获取测试用例列表

        Args:
            sheet_name: 工作表名称
            render_templates: 是否渲染模板
            context: 额外的上下文变量

        Returns:
            测试用例列表
        """
        cache_key = f"{sheet_name}_{render_templates}_{str(context)}"

        if cache_key in self._data_cache:
            logger.debug(f"从缓存读取测试用例: {sheet_name}")
            return self._data_cache[cache_key]

        try:
            df = self.read_sheet(sheet_name)

            if df.empty:
                logger.warning(f"工作表 {sheet_name} 为空")
                return []

            # 确保必要的列存在
            required_columns = ['case_name', 'method', 'url']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                logger.warning(f"工作表[{sheet_name}]缺少列: {missing_columns}")

            test_cases = []

            for idx, row in df.iterrows():
                try:
                    # 转换为字典
                    case_data = row.to_dict()

                    # 清理数据
                    case_data = self._clean_case_data(case_data)

                    # 添加行号
                    case_data['_row'] = idx + 1

                    # 处理模板渲染
                    if render_templates:
                        case_data = self._render_case_data(case_data, context, idx)

                    # 验证用例数据
                    if self._validate_case_data(case_data):
                        test_cases.append(case_data)
                    else:
                        logger.warning(f"第{idx + 1}行测试用例验证失败，已跳过")

                except Exception as e:
                    logger.error(f"处理第{idx + 1}行数据失败: {e}")
                    continue

            # 缓存结果
            self._data_cache[cache_key] = test_cases

            logger.info(f"从工作表 {sheet_name} 加载了 {len(test_cases)} 个测试用例")
            return test_cases

        except Exception as e:
            logger.error(f"获取测试用例失败: {e}")
            raise

    def _clean_case_data(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理用例数据"""
        cleaned_data = {}

        for key, value in case_data.items():
            if isinstance(value, str):
                # 去除字符串两端的空格
                value = value.strip()

                # 处理空值
                if value.lower() in ('null', 'none', 'nil'):
                    value = None
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value == '':
                    value = None

            cleaned_data[key.strip()] = value

        return cleaned_data

    def _render_case_data(self,
                          case_data: Dict[str, Any],
                          context: Optional[Dict],
                          row_index: int) -> Dict[str, Any]:
        """渲染用例数据中的模板"""

        # 准备上下文
        render_context = {
            'row': row_index + 1,
            'case': case_data,
            'env': {k: v for k, v in case_data.items() if v is not None},
        }

        if context:
            render_context.update(context)

        # 更新模板引擎上下文
        template_engine.update_context(**render_context)

        # 渲染整个用例数据
        rendered_data = template_engine.render(case_data, render_context)

        # 特殊处理JSON字段
        json_fields = ['headers', 'params', 'data', 'json', 'expected', 'setup_data', 'teardown_data']

        for field in json_fields:
            if field in rendered_data and rendered_data[field] and isinstance(rendered_data[field], str):
                try:
                    # 先尝试解析为JSON
                    rendered_data[field] = json.loads(rendered_data[field])
                except json.JSONDecodeError:
                    try:
                        # 再尝试解析为YAML
                        rendered_data[field] = yaml.safe_load(rendered_data[field])
                    except (yaml.YAMLError, AttributeError):
                        # 如果都失败，保持原样
                        pass

        return rendered_data

    def _validate_case_data(self, case_data: Dict[str, Any]) -> bool:
        """验证用例数据"""

        # 必须有用例名称
        if 'case_name' not in case_data or not case_data['case_name']:
            logger.error(f"用例缺少名称: {case_data.get('_row', '未知')}")
            return False

        # 必须有请求方法和URL
        if 'method' not in case_data or not case_data['method']:
            logger.error(f"用例缺少请求方法: {case_data.get('case_name')}")
            return False

        if 'url' not in case_data or not case_data['url']:
            logger.error(f"用例缺少URL: {case_data.get('case_name')}")
            return False

        # 方法必须是大写
        case_data['method'] = str(case_data['method']).upper()

        # 验证方法是否有效
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if case_data['method'] not in valid_methods:
            logger.error(f"无效的请求方法: {case_data['method']}")
            return False

        return True

    def get_test_suites(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有测试套件"""
        sheet_names = self.get_sheet_names()
        suites = {}

        for sheet_name in sheet_names:
            if sheet_name.lower() not in ['config', 'setup', 'teardown','说明']:
                try:
                    test_cases = self.get_test_cases(sheet_name, render_templates=False)
                    if test_cases:
                        suites[sheet_name] = test_cases
                except Exception as e:
                    logger.warning(f"读取测试套件 {sheet_name} 失败: {e}")

        logger.info(f"获取了 {len(suites)} 个测试套件")
        return suites

    def get_config(self, sheet_name: str = "config") -> Dict[str, Any]:
        """获取配置信息"""
        try:
            df = self.read_sheet(sheet_name)
            config_data = {}

            for _, row in df.iterrows():
                key = str(row.get('key', '')).strip()
                value = str(row.get('value', '')).strip()

                if key:
                    # 尝试解析JSON/YAML
                    if value:
                        try:
                            config_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            try:
                                config_data[key] = yaml.safe_load(value)
                            except (yaml.YAMLError, AttributeError):
                                config_data[key] = value
                    else:
                        config_data[key] = None

            # 渲染模板
            config_data = template_engine.render(config_data)

            logger.info(f"从 {sheet_name} 工作表加载了 {len(config_data)} 个配置项")
            return config_data

        except Exception as e:
            logger.warning(f"读取配置失败: {e}")
            return {}

    def clear_cache(self):
        """清空缓存"""
        self._data_cache.clear()
        self._sheet_cache.clear()
        template_engine.clear_context()
        logger.info("已清空Excel读取器缓存")


# 创建全局实例
excel_reader = ExcelReader()