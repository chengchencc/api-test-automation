import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import json
import yaml
import tempfile
import shutil

from src.common.excel_reader import ExcelReader
from src.common.template_engine_manager import template_engine


class TestExcelReader:
    """ExcelReader 单元测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.excel_file = Path(self.temp_dir) / "test.xlsx"
        # 创建一个空的Excel文件（实际测试中会模拟读取）
        self.excel_file.touch()

        # 模拟template_engine
        self.template_engine_mock = Mock()
        self.template_engine_mock.render = Mock(return_value={})
        self.template_engine_mock.update_context = Mock()
        self.template_engine_mock.clear_context = Mock()

    def teardown_method(self):
        """每个测试方法后的清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # 恢复模板引擎
        template_engine.render = Mock()
        template_engine.update_context = Mock()
        template_engine.clear_context = Mock()

    def test_init_with_explicit_file(self):
        """测试使用显式文件路径初始化"""
        reader = ExcelReader(self.excel_file)
        assert reader.excel_file == self.excel_file
        assert reader._data_cache == {}
        assert reader._sheet_cache == {}

    def test_init_with_default_file(self):
        """测试使用默认文件路径初始化"""
        # 需要模拟 project_config.EXCEL_FILE
        with patch('src.common.excel_reader.project_config') as mock_config:
            mock_config.EXCEL_FILE = self.excel_file
            reader = ExcelReader()
            assert reader.excel_file == self.excel_file

    def test_init_file_not_found(self):
        """测试文件不存在时抛出异常"""
        non_existent = Path(self.temp_dir) / "nonexistent.xlsx"
        with pytest.raises(FileNotFoundError):
            ExcelReader(non_existent)

    @patch('pandas.read_excel')
    def test_read_sheet_with_name(self, mock_read_excel):
        """测试按名称读取工作表"""
        # 模拟DataFrame
        mock_df = pd.DataFrame({'col1': ['val1'], 'col2': ['val2']})
        mock_read_excel.return_value = mock_df

        reader = ExcelReader(self.excel_file)
        result = reader.read_sheet('test_sheet')

        # 验证调用
        mock_read_excel.assert_called_once_with(
            self.excel_file, sheet_name='test_sheet', dtype=str
        )
        assert result.equals(mock_df)
        # 验证缓存
        assert 'test_sheet' in reader._sheet_cache
        assert reader._sheet_cache['test_sheet'].equals(mock_df)

    @patch('pandas.read_excel')
    def test_read_sheet_without_name(self, mock_read_excel):
        """测试读取第一个工作表（无名称指定）"""
        mock_df = pd.DataFrame({'col1': ['val1']})
        mock_read_excel.return_value = mock_df

        reader = ExcelReader(self.excel_file)
        result = reader.read_sheet()

        mock_read_excel.assert_called_once_with(
            self.excel_file, dtype=str, sheet_name=0
        )
        assert result.equals(mock_df)
        assert 'first_sheet' in reader._sheet_cache

    @patch('pandas.read_excel')
    def test_read_sheet_cache(self, mock_read_excel):
        """测试工作表缓存功能"""
        mock_df = pd.DataFrame({'col1': ['val1']})
        mock_read_excel.return_value = mock_df

        reader = ExcelReader(self.excel_file)
        # 第一次读取
        result1 = reader.read_sheet('cached')
        # 第二次读取应该从缓存获取
        result2 = reader.read_sheet('cached')

        # read_excel应该只被调用一次
        assert mock_read_excel.call_count == 1
        assert result1.equals(result2)
        assert 'cached' in reader._sheet_cache

    @patch('pandas.read_excel')
    def test_read_sheet_cleans_columns_and_nan(self, mock_read_excel):
        """测试读取时清理列名和填充NaN"""
        mock_df = pd.DataFrame({
            ' col1 ': ['val1', None],
            'col2': [None, 'val2']
        })
        mock_read_excel.return_value = mock_df

        reader = ExcelReader(self.excel_file)
        result = reader.read_sheet('test')

        # 验证列名被清理（去除空格）
        assert 'col1' in result.columns
        assert 'col2' in result.columns
        # 验证NaN被替换为空字符串
        assert result.isna().sum().sum() == 0
        assert result.loc[0, 'col2'] == ''
        assert result.loc[1, 'col1'] == ''

    @patch('pandas.ExcelFile')
    def test_get_sheet_names(self, mock_excel_file):
        """测试获取工作表名称"""
        mock_excel_instance = Mock()
        mock_excel_instance.sheet_names = ['Sheet1', 'Sheet2', 'Sheet3']
        mock_excel_file.return_value = mock_excel_instance

        reader = ExcelReader(self.excel_file)
        sheet_names = reader.get_sheet_names()

        mock_excel_file.assert_called_once_with(self.excel_file)
        assert sheet_names == ['Sheet1', 'Sheet2', 'Sheet3']

    @patch('pandas.ExcelFile')
    def test_get_sheet_names_exception(self, mock_excel_file):
        """测试获取工作表名称时发生异常"""
        mock_excel_file.side_effect = Exception("File error")

        reader = ExcelReader(self.excel_file)
        sheet_names = reader.get_sheet_names()

        # 异常时应返回空列表
        assert sheet_names == []

    @patch.object(ExcelReader, 'read_sheet')
    def test_get_test_cases_empty_sheet(self, mock_read_sheet):
        """测试获取空工作表的测试用例"""
        mock_read_sheet.return_value = pd.DataFrame()

        reader = ExcelReader(self.excel_file)
        test_cases = reader.get_test_cases('empty_sheet')

        assert test_cases == []
        mock_read_sheet.assert_called_once_with('empty_sheet')

    @patch.object(ExcelReader, 'read_sheet')
    def test_get_test_cases_missing_columns(self, mock_read_sheet):
        """测试获取缺少必要列的测试用例"""
        mock_read_sheet.return_value = pd.DataFrame({
            'case_name': ['test1'],
            # 缺少'method'和'url'列
        })

        reader = ExcelReader(self.excel_file)
        test_cases = reader.get_test_cases('incomplete_sheet')

        # 即使缺少列，也应该返回空列表（因为没有有效用例）
        assert test_cases == []

    @patch.object(ExcelReader, 'read_sheet')
    @patch.object(ExcelReader, '_clean_case_data')
    @patch.object(ExcelReader, '_render_case_data')
    @patch.object(ExcelReader, '_validate_case_data')
    def test_get_test_cases_full_flow(self, mock_validate, mock_render, mock_clean, mock_read_sheet):
        """测试获取测试用例的完整流程"""
        # 模拟DataFrame
        mock_df = pd.DataFrame({
            'case_name': ['test_case_1'],
            'method': ['GET'],
            'url': ['/api/test']
        })
        mock_read_sheet.return_value = mock_df

        # 模拟各个处理步骤
        mock_clean.return_value = {'case_name': 'test_case_1', 'method': 'GET', 'url': '/api/test'}
        mock_render.return_value = {'case_name': 'test_case_1', 'method': 'GET', 'url': '/api/test'}
        mock_validate.return_value = True

        reader = ExcelReader(self.excel_file)
        test_cases = reader.get_test_cases('test_sheet', render_templates=True, context={'extra': 'value'})

        # 验证调用
        mock_read_sheet.assert_called_once_with('test_sheet')
        mock_clean.assert_called_once()
        mock_render.assert_called_once()
        mock_validate.assert_called_once()

        # 验证结果
        assert len(test_cases) == 1
        assert test_cases[0]['case_name'] == 'test_case_1'

        # 验证缓存键
        cache_key = "test_sheet_True_{'extra': 'value'}"
        assert cache_key in reader._data_cache

    def test_clean_case_data(self):
        """测试用例数据清理"""
        reader = ExcelReader(self.excel_file)

        test_data = {
            'case_name': '  test case  ',
            'method': '  POST  ',
            'value_str': 'null',
            'bool_true': 'True',
            'bool_false': 'FALSE',
            'empty': '',
            'none_str': 'None',
            'nil_str': 'nil'
        }

        cleaned = reader._clean_case_data(test_data)

        # 验证字符串去除空格
        assert cleaned['case_name'] == 'test case'
        assert cleaned['method'] == 'POST'

        # 验证特殊值转换
        assert cleaned['value_str'] is None
        assert cleaned['bool_true'] is True
        assert cleaned['bool_false'] is False
        assert cleaned['empty'] is None
        assert cleaned['none_str'] is None
        assert cleaned['nil_str'] is None

    @patch('src.common.excel_reader.template_engine')
    def test_render_case_data(self, mock_template_engine):
        """测试用例数据模板渲染"""
        reader = ExcelReader(self.excel_file)

        case_data = {
            'case_name': 'test',
            'headers': '{"Content-Type": "application/json"}',
            'data': 'key: value'  # YAML格式
        }
        context = {'extra': 'context'}

        # 模拟模板引擎渲染
        mock_template_engine.render.return_value = {
            'case_name': 'test',
            'headers': '{"Content-Type": "application/json"}',
            'data': 'key: value'
        }

        rendered = reader._render_case_data(case_data, context, 0)

        # 验证模板引擎调用
        mock_template_engine.update_context.assert_called_once()
        mock_template_engine.render.assert_called_once_with(case_data, {
            'row': 1,
            'case': case_data,
            'env': {'case_name': 'test', 'headers': '{"Content-Type": "application/json"}', 'data': 'key: value'},
            'extra': 'context'
        })

        # 验证JSON/YAML解析
        # 注意：实际渲染后，JSON字段应该被解析为字典
        # 但由于我们模拟了render返回值，这里不会发生解析
        # 实际测试中，应该测试完整的渲染流程

    def test_render_case_data_json_yaml_parsing(self):
        """测试渲染后的JSON/YAML解析逻辑"""
        reader = ExcelReader(self.excel_file)

        # 模拟渲染后的数据（包含JSON和YAML字符串）
        rendered_data = {
            'headers': '{"Content-Type": "application/json"}',
            'params': '{"page": 1}',
            'data': 'key: value\nother: 123',
            'json': '{"name": "test"}',
            'expected': '{"status": 200}',
            'setup_data': '{"setup": true}',
            'teardown_data': '{"teardown": true}',
            'other_field': 'not_json'
        }

        # 模拟template_engine.render返回原始数据（不解析）
        with patch('src.common.excel_reader.template_engine') as mock_engine:
            mock_engine.render.return_value = rendered_data

            # 调用_render_case_data（它会触发JSON/YAML解析）
            result = reader._render_case_data(rendered_data, None, 0)

            # 验证JSON字段被解析
            assert isinstance(result['headers'], dict)
            assert result['headers']['Content-Type'] == 'application/json'
            assert isinstance(result['params'], dict)
            assert result['params']['page'] == 1
            assert isinstance(result['data'], dict)  # YAML解析
            assert result['data']['key'] == 'value'
            assert result['data']['other'] == 123
            assert isinstance(result['json'], dict)
            assert result['json']['name'] == 'test'
            # 其他字段保持不变
            assert result['other_field'] == 'not_json'

    def test_validate_case_data(self):
        """测试用例数据验证"""
        reader = ExcelReader(self.excel_file)

        # 有效用例
        valid_case = {
            'case_name': 'test case',
            'method': 'POST',
            'url': '/api/test'
        }
        assert reader._validate_case_data(valid_case) is True
        # 验证方法被转换为大写
        assert valid_case['method'] == 'POST'

        # 缺少用例名称
        invalid_case1 = {
            'method': 'GET',
            'url': '/api/test'
        }
        assert reader._validate_case_data(invalid_case1) is False

        # 缺少方法
        invalid_case2 = {
            'case_name': 'test',
            'url': '/api/test'
        }
        assert reader._validate_case_data(invalid_case2) is False

        # 缺少URL
        invalid_case3 = {
            'case_name': 'test',
            'method': 'GET'
        }
        assert reader._validate_case_data(invalid_case3) is False

        # 无效方法
        invalid_case4 = {
            'case_name': 'test',
            'method': 'INVALID',
            'url': '/api/test'
        }
        assert reader._validate_case_data(invalid_case4) is False

        # 方法小写转换
        lower_case = {
            'case_name': 'test',
            'method': 'get',
            'url': '/api/test'
        }
        assert reader._validate_case_data(lower_case) is True
        assert lower_case['method'] == 'GET'

    @patch.object(ExcelReader, 'get_sheet_names')
    @patch.object(ExcelReader, 'get_test_cases')
    def test_get_test_suites(self, mock_get_test_cases, mock_get_sheet_names):
        """测试获取测试套件"""
        mock_get_sheet_names.return_value = ['config', 'setup', 'test_suite1', 'test_suite2', '说明']
        mock_get_test_cases.side_effect = [
            [],  # config (跳过)
            [],  # setup (跳过)
            [{'case_name': 'case1'}],  # test_suite1
            [{'case_name': 'case2'}],  # test_suite2
            []   # 说明 (跳过)
        ]

        reader = ExcelReader(self.excel_file)
        suites = reader.get_test_suites()

        # 验证结果
        assert 'test_suite1' in suites
        assert 'test_suite2' in suites
        assert 'config' not in suites
        assert 'setup' not in suites
        assert '说明' not in suites
        assert len(suites) == 2
        assert suites['test_suite1'][0]['case_name'] == 'case1'

    @patch.object(ExcelReader, 'read_sheet')
    def test_get_config(self, mock_read_sheet):
        """测试获取配置信息"""
        mock_df = pd.DataFrame({
            'key': ['base_url', 'timeout', 'retry_count'],
            'value': ['http://api.example.com', '30', '{"max": 3}']
        })
        mock_read_sheet.return_value = mock_df

        # 模拟模板引擎渲染
        with patch('src.common.excel_reader.template_engine') as mock_engine:
            mock_engine.render.return_value = {
                'base_url': 'http://api.example.com',
                'timeout': '30',
                'retry_count': {'max': 3}
            }

            reader = ExcelReader(self.excel_file)
            config = reader.get_config('config')

            # 验证读取了正确的工作表
            mock_read_sheet.assert_called_once_with('config')
            # 验证模板引擎调用
            mock_engine.render.assert_called_once()
            # 验证配置内容
            assert config['base_url'] == 'http://api.example.com'
            assert config['timeout'] == '30'
            assert config['retry_count'] == {'max': 3}

    def test_clear_cache(self):
        """测试清空缓存"""
        reader = ExcelReader(self.excel_file)

        # 添加一些缓存数据
        reader._data_cache['key1'] = ['data1']
        reader._sheet_cache['sheet1'] = pd.DataFrame()

        # 清空缓存
        with patch('src.common.excel_reader.template_engine') as mock_engine:
            reader.clear_cache()

            # 验证缓存被清空
            assert reader._data_cache == {}
            assert reader._sheet_cache == {}
            # 验证模板引擎上下文被清空
            mock_engine.clear_context.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])