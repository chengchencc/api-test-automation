"""
数据加载器模块
提供多种数据源的数据加载功能
"""
import json
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from src.config.settings import settings
from src.utils.logger import logger


@dataclass
class DataSource:
    """数据源配置"""
    name: str
    type: str  # excel, json, yaml, csv, sql
    path: Path
    sheet_name: Optional[str] = None
    encoding: str = "utf-8"


class DataLoader:
    """
    数据加载器
    支持多种数据源的数据加载
    """

    def __init__(self):
        self._cache = {}
        self._data_sources = self._discover_data_sources()

    def _discover_data_sources(self) -> Dict[str, DataSource]:
        """发现数据源"""
        data_sources = {}

        # Excel数据源
        excel_files = list(settings.EXCEL_DIR.glob("*.xlsx")) + list(settings.EXCEL_DIR.glob("*.xls"))
        for excel_file in excel_files:
            name = excel_file.stem
            data_sources[name] = DataSource(
                name=name,
                type="excel",
                path=excel_file
            )

        # JSON数据源
        json_files = list(settings.JSON_DIR.glob("*.json"))
        for json_file in json_files:
            name = json_file.stem
            data_sources[name] = DataSource(
                name=name,
                type="json",
                path=json_file
            )

        # YAML数据源
        yaml_files = list(settings.YAML_DIR.glob("*.yaml")) + list(settings.YAML_DIR.glob("*.yml"))
        for yaml_file in yaml_files:
            name = yaml_file.stem
            data_sources[name] = DataSource(
                name=name,
                type="yaml",
                path=yaml_file
            )

        return data_sources

    def load(self, data_source: str, **kwargs) -> Any:
        """
        加载数据

        Args:
            data_source: 数据源名称或路径
            **kwargs: 加载参数

        Returns:
            加载的数据
        """
        # 检查缓存
        cache_key = f"{data_source}_{str(kwargs)}"
        if cache_key in self._cache and settings.CACHE_ENABLED:
            logger.debug(f"从缓存加载数据: {data_source}")
            return self._cache[cache_key]

        # 加载数据
        if data_source in self._data_sources:
            data = self._load_from_source(self._data_sources[data_source], **kwargs)
        elif Path(data_source).exists():
            data = self._load_from_file(Path(data_source), **kwargs)
        else:
            raise ValueError(f"数据源不存在: {data_source}")

        # 缓存数据
        if settings.CACHE_ENABLED:
            self._cache[cache_key] = data

        return data

    def _load_from_source(self, source: DataSource, **kwargs) -> Any:
        """从数据源加载数据"""
        try:
            if source.type == "excel":
                return self._load_excel(source.path, **kwargs)
            elif source.type == "json":
                return self._load_json(source.path, **kwargs)
            elif source.type == "yaml":
                return self._load_yaml(source.path, **kwargs)
            elif source.type == "csv":
                return self._load_csv(source.path, **kwargs)
            else:
                raise ValueError(f"不支持的数据源类型: {source.type}")
        except Exception as e:
            logger.error(f"加载数据源失败 {source.name}: {e}")
            raise

    def _load_from_file(self, file_path: Path, **kwargs) -> Any:
        """从文件加载数据"""
        suffix = file_path.suffix.lower()

        try:
            if suffix in ['.xlsx', '.xls']:
                return self._load_excel(file_path, **kwargs)
            elif suffix == '.json':
                return self._load_json(file_path, **kwargs)
            elif suffix in ['.yaml', '.yml']:
                return self._load_yaml(file_path, **kwargs)
            elif suffix == '.csv':
                return self._load_csv(file_path, **kwargs)
            else:
                raise ValueError(f"不支持的文件格式: {suffix}")
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
            raise

    def _load_excel(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """加载Excel文件"""
        try:
            sheet_name = kwargs.get('sheet_name')
            if sheet_name:
                # 加载指定sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
                return df.to_dict('records')
            else:
                # 加载所有sheet
                excel_file = pd.ExcelFile(file_path)
                data = {}
                for sheet in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet, **kwargs)
                    data[sheet] = df.to_dict('records')
                return data
        except Exception as e:
            logger.error(f"加载Excel文件失败 {file_path}: {e}")
            raise

    def _load_json(self, file_path: Path, **kwargs) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            raise

    def _load_yaml(self, file_path: Path, **kwargs) -> Any:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载YAML文件失败 {file_path}: {e}")
            raise

    def _load_csv(self, file_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """加载CSV文件"""
        try:
            df = pd.read_csv(file_path, **kwargs)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"加载CSV文件失败 {file_path}: {e}")
            raise

    def get_test_cases(self, source: str = "test_cases", **kwargs) -> List[Dict[str, Any]]:
        """
        获取测试用例

        Args:
            source: 数据源名称
            **kwargs: 加载参数

        Returns:
            测试用例列表
        """
        data = self.load(source, **kwargs)

        if isinstance(data, dict):
            # 如果是字典，尝试获取test_cases sheet
            if 'test_cases' in data:
                return data['test_cases']
            else:
                # 返回第一个sheet的数据
                first_key = next(iter(data))
                return data[first_key]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(f"测试用例数据格式不正确: {type(data)}")

    def get_test_data(self, source: str = "test_data", **kwargs) -> Dict[str, Any]:
        """
        获取测试数据

        Args:
            source: 数据源名称
            **kwargs: 加载参数

        Returns:
            测试数据字典
        """
        data = self.load(source, **kwargs)

        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            # 如果是列表，转换为字典
            result = {}
            for i, item in enumerate(data):
                if isinstance(item, dict) and 'key' in item and 'value' in item:
                    result[item['key']] = item['value']
                else:
                    result[f"item_{i}"] = item
            return result
        else:
            raise ValueError(f"测试数据格式不正确: {type(data)}")

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("数据缓存已清除")

    def list_data_sources(self) -> List[str]:
        """列出所有数据源"""
        return list(self._data_sources.keys())

    def add_data_source(self, name: str, file_path: Union[str, Path], **kwargs):
        """
        添加数据源

        Args:
            name: 数据源名称
            file_path: 文件路径
            **kwargs: 数据源配置
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            data_type = "excel"
        elif suffix == '.json':
            data_type = "json"
        elif suffix in ['.yaml', '.yml']:
            data_type = "yaml"
        elif suffix == '.csv':
            data_type = "csv"
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

        self._data_sources[name] = DataSource(
            name=name,
            type=data_type,
            path=file_path,
            **kwargs
        )

        logger.info(f"已添加数据源: {name} ({data_type})")

    def remove_data_source(self, name: str):
        """移除数据源"""
        if name in self._data_sources:
            del self._data_sources[name]
            logger.info(f"已移除数据源: {name}")
        else:
            logger.warning(f"数据源不存在: {name}")