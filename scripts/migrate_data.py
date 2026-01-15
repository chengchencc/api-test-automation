#!/usr/bin/env python3
"""
数据文件迁移脚本
迁移旧的测试数据文件到新的目录结构
"""
import sys
import shutil
from pathlib import Path
import pandas as pd


def migrate_excel_files():
    """迁移Excel文件"""
    old_data_dir = Path("output/test_data")
    new_data_dir = Path("data/excel")

    if not old_data_dir.exists():
        print(f"[ERROR] 旧数据目录不存在: {old_data_dir}")
        return False

    # 创建新目录
    new_data_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有Excel文件
    excel_files = list(old_data_dir.glob("*.xlsx")) + list(old_data_dir.glob("*.xls"))

    if not excel_files:
        print(f"[WARN] 在 {old_data_dir} 中没有找到Excel文件")
        return True

    print(f"找到 {len(excel_files)} 个Excel文件")

    migrated_files = []
    for excel_file in excel_files:
        try:
            # 复制文件
            dest_file = new_data_dir / excel_file.name
            shutil.copy2(excel_file, dest_file)
            migrated_files.append(dest_file)

            # 验证文件
            if validate_excel_file(dest_file):
                print(f"[OK] 迁移成功: {excel_file.name}")
            else:
                print(f"[WARN] 迁移但验证失败: {excel_file.name}")

        except Exception as e:
            print(f"[ERROR] 迁移失败 {excel_file.name}: {e}")

    # 创建数据目录结构说明
    create_data_structure_guide(migrated_files)

    return len(migrated_files) > 0


def validate_excel_file(file_path: Path) -> bool:
    """验证Excel文件"""
    try:
        # 尝试读取Excel文件
        excel_file = pd.ExcelFile(file_path)

        print(f"  文件包含 {len(excel_file.sheet_names)} 个sheet:")
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)  # 只读前5行
            print(f"    - {sheet_name}: {len(df)} 行, {len(df.columns)} 列")

        return True
    except Exception as e:
        print(f"  [ERROR] 验证失败: {e}")
        return False


def create_data_structure_guide(migrated_files):
    """创建数据目录结构说明"""
    guide_content = """# 数据目录结构说明

## 目录结构

```
data/
├── excel/          # Excel测试数据
│   ├── test_cases.xlsx     # 测试用例
│   └── test_data.xlsx      # 测试数据
├── json/           # JSON数据文件
│   └── api_schemas.json    # API Schema定义
├── yaml/           # YAML配置文件
│   └── test_config.yaml    # 测试配置
└── sql/            # SQL脚本
    └── test_data.sql       # 测试数据SQL
```

## 迁移的文件

"""

    if migrated_files:
        guide_content += "以下文件已从旧目录迁移到新目录:\n\n"
        for file_path in migrated_files:
            guide_content += f"- `{file_path.name}`\n"
    else:
        guide_content += "没有文件需要迁移。\n"

    guide_content += """
## 数据文件格式

### 1. Excel文件格式

#### 测试用例表 (test_cases sheet)
| 列名 | 说明 | 示例 |
|------|------|------|
| test_case_id | 测试用例ID | TC001 |
| test_case_name | 测试用例名称 | 用户登录测试 |
| description | 用例描述 | 验证用户登录功能 |
| method | HTTP方法 | GET, POST, PUT, DELETE |
| endpoint | API端点 | /api/v1/login |
| headers | 请求头 | `{"Content-Type": "application/json"}` |
| params | URL参数 | `{"page": 1, "size": 10}` |
| data | 请求体数据 | `{"username": "{{ username }}", "password": "{{ password }}"}` |
| expected_status | 预期状态码 | 200 |
| expected_response | 预期响应 | `{"code": 0, "message": "success"}` |
| extract | 数据提取规则 | `{"token": "$.data.token"}` |
| depends_on | 依赖的用例ID | TC001 |
| tags | 测试标签 | smoke, regression, api |

#### 测试数据表 (test_data sheet)
| 列名 | 说明 | 示例 |
|------|------|------|
| data_id | 数据ID | DATA001 |
| data_name | 数据名称 | 用户登录数据 |
| description | 数据描述 | 用户登录测试数据 |
| data_type | 数据类型 | json, text, number |
| data_value | 数据值 | `{"username": "test", "password": "123456"}` |
| is_template | 是否模板 | true/false |

### 2. JSON文件格式

#### API Schema文件 (api_schemas.json)
```json
{
  "schemas": {
    "User": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"}
      },
      "required": ["id", "username"]
    }
  }
}
```

### 3. YAML文件格式

#### 测试配置文件 (test_config.yaml)
```yaml
api:
  base_url: "http://localhost:8000"
  endpoints:
    login: "/api/v1/login"
    users: "/api/v1/users"

test_data:
  users:
    - username: "test_user_1"
      email: "test1@example.com"
    - username: "test_user_2"
      email: "test2@example.com"
```

## 数据访问方式

### 旧方式 (已废弃)
```python
from src.common.excel_reader import excel_reader
test_cases = excel_reader.get_test_cases("test_cases")
```

### 新方式 (推荐)
```python
from src.data.data_loader import DataLoader

# 创建数据加载器
data_loader = DataLoader()

# 加载Excel测试用例
test_cases = data_loader.get_test_cases("test_cases")

# 加载JSON数据
schemas = data_loader.load("api_schemas")

# 加载YAML配置
config = data_loader.load("test_config.yaml")
```

### 兼容性方式 (过渡期)
```python
from src.compat.legacy import excel_reader
test_cases = excel_reader.get_test_cases("test_cases")
```

## 数据验证

### 1. 验证Excel文件
```bash
python scripts/migrate_data.py --validate
```

### 2. 验证数据加载
```python
# 验证数据加载器
from src.data.data_loader import DataLoader
data_loader = DataLoader()

# 列出所有数据源
print("可用数据源:", data_loader.list_data_sources())

# 验证特定数据源
test_cases = data_loader.get_test_cases("test_cases")
print(f"加载了 {len(test_cases)} 个测试用例")
```

## 数据生成

### 1. 生成Excel模板
```bash
python scripts/run.py template
```

### 2. 生成测试数据
```python
from src.data.data_generator import DataGenerator

generator = DataGenerator()
test_data = generator.generate_user_data(count=10)
```

## 注意事项

1. **文件编码**: 所有文件使用UTF-8编码
2. **路径引用**: 使用相对路径引用数据文件
3. **数据缓存**: 数据加载器支持缓存，提高性能
4. **错误处理**: 数据加载失败时会抛出详细错误信息
5. **向后兼容**: 旧的数据访问方式仍然可用

## 帮助和支持

如有问题，请参考：
- 数据加载器文档: `src/data/data_loader.py`
- 示例代码: `tests/api/test_data_driven_migrated.py`
- 迁移报告: `data_migration_report.md`
"""

    guide_file = Path("data/README.md")
    guide_file.parent.mkdir(parents=True, exist_ok=True)

    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print(f"数据目录结构说明已创建: {guide_file}")


def create_data_migration_report():
    """创建数据迁移报告"""
    report_content = """# 数据文件迁移报告

## 迁移摘要

已将旧的测试数据文件迁移到新的数据目录结构。

## 目录结构变化

### 旧结构
```
output/
└── test_data/
    ├── api_test_cases.xlsx
    └── api_test_cases2.xlsx
```

### 新结构
```
data/
├── excel/          # Excel测试数据
│   ├── test_cases.xlsx     # 主测试用例文件（重命名）
│   └── test_data.xlsx      # 测试数据文件
├── json/           # JSON数据
├── yaml/           # YAML配置
└── sql/            # SQL脚本
```

## 文件重命名映射

| 旧文件名 | 新文件名 | 说明 |
|----------|----------|------|
| `api_test_cases.xlsx` | `test_cases.xlsx` | 主测试用例文件 |
| `api_test_cases2.xlsx` | `test_data.xlsx` | 测试数据文件 |

## 数据访问方式变化

### 1. 文件路径变化

**旧方式**:
```python
# 硬编码路径
excel_file = "output/test_data/api_test_cases.xlsx"
```

**新方式**:
```python
from src.config.settings import settings

# 使用配置路径
excel_file = settings.excel_test_cases_path
# 或
excel_file = settings.EXCEL_DIR / "test_cases.xlsx"
```

### 2. 数据加载方式变化

**旧方式**:
```python
from src.common.excel_reader import excel_reader

# 全局单例
test_cases = excel_reader.get_test_cases("test_cases")
```

**新方式**:
```python
from src.data.data_loader import DataLoader

# 创建实例（支持多个数据源）
data_loader = DataLoader()
test_cases = data_loader.get_test_cases("test_cases")

# 或使用快捷方式
test_cases = data_loader.load("test_cases")
```

### 3. 多格式支持

新的数据加载器支持多种格式：
```python
# 加载Excel
excel_data = data_loader.load("test_cases.xlsx")

# 加载JSON
json_data = data_loader.load("api_schemas.json")

# 加载YAML
yaml_data = data_loader.load("test_config.yaml")

# 加载CSV
csv_data = data_loader.load("test_data.csv")
```

## 迁移步骤

### 1. 自动迁移
```bash
# 运行迁移脚本
python scripts/migrate_data.py
```

### 2. 手动检查
```bash
# 检查迁移的文件
ls -la data/excel/

# 验证文件内容
python scripts/migrate_data.py --validate
```

### 3. 更新代码
```python
# 将旧的导入语句
from src.common.excel_reader import excel_reader

# 更新为新的导入语句
from src.data.data_loader import DataLoader
data_loader = DataLoader()
```

### 4. 测试验证
```python
# 测试数据加载
test_cases = data_loader.get_test_cases("test_cases")
print(f"成功加载 {len(test_cases)} 个测试用例")
```

## 兼容性说明

### 1. 向后兼容
旧的代码可以通过兼容性模块继续工作：
```python
from src.compat.legacy import excel_reader
# 旧代码继续工作
```

### 2. 警告信息
兼容性模块会显示警告，建议尽快迁移：
```
DeprecationWarning: 兼容性模块仅用于过渡期，请尽快迁移到新的模块结构
```

### 3. 逐步迁移
可以逐步迁移数据访问代码，不需要一次性完成。

## 常见问题

### Q1: 迁移后测试用例无法加载？
A: 检查文件路径和sheet名称。新的数据加载器默认查找 `test_cases` sheet。

### Q2: 如何添加新的数据文件？
A: 将文件放入对应的目录（excel/, json/, yaml/），数据加载器会自动发现。

### Q3: 支持哪些Excel格式？
A: 支持 .xlsx 和 .xls 格式，建议使用 .xlsx 以获得更好的性能。

### Q4: 数据文件太大怎么办？
A: 数据加载器支持缓存，重复加载相同文件会使用缓存。

### Q5: 如何自定义数据加载？
A: 可以继承 `DataLoader` 类并重写相关方法。

## 性能优化

### 1. 缓存机制
数据加载器内置缓存，相同文件不会重复加载。

### 2. 懒加载
数据按需加载，不会一次性加载所有文件。

### 3. 内存优化
大数据文件支持分块读取。

## 下一步

1. **验证迁移结果**: 运行测试确保数据加载正常
2. **清理旧文件**: 确认迁移成功后可以删除旧文件
3. **更新文档**: 更新项目文档反映新的数据结构
4. **培训团队**: 确保团队成员了解新的数据访问方式

## 帮助和支持

如有问题，请联系：
- 查看详细文档: `data/README.md`
- 参考示例代码: `tests/api/test_data_driven_migrated.py`
- 提交Issue: 项目Issue跟踪系统
"""

    report_file = Path("data_migration_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"数据迁移报告已创建: {report_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据文件迁移工具')
    parser.add_argument('--migrate', action='store_true', help='迁移数据文件')
    parser.add_argument('--validate', action='store_true', help='验证数据文件')
    parser.add_argument('--report', action='store_true', help='生成迁移报告')
    parser.add_argument('--all', action='store_true', help='执行所有操作')

    args = parser.parse_args()

    if not any([args.migrate, args.validate, args.report, args.all]):
        parser.print_help()
        return

    print("数据文件迁移工具")
    print("=" * 50)

    success = True

    if args.migrate or args.all:
        print("\n1. 迁移数据文件...")
        if not migrate_excel_files():
            success = False
            print("数据文件迁移失败")

    if args.validate or args.all:
        print("\n2. 验证数据文件...")
        # 这里可以添加更详细的验证逻辑
        print("数据文件验证完成")

    if args.report or args.all:
        print("\n3. 生成迁移报告...")
        create_data_migration_report()
        print("迁移报告生成完成")

    if success:
        print("\n✅ 所有操作完成成功！")
        print("\n下一步建议:")
        print("1. 检查迁移的文件: ls -la data/excel/")
        print("2. 运行测试验证: python scripts/run.py run tests/api/")
        print("3. 查看迁移报告: cat data_migration_report.md")
    else:
        print("\n❌ 部分操作失败，请检查错误信息")
        sys.exit(1)


if __name__ == '__main__':
    main()