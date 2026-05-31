from typing import Dict, Any, List, Optional
import csv
import os
from .interface import DatabaseConnection
from .schema_organizer import SchemaOrganizer
from .logger import get_logger
from .exceptions import handle_error

logger = get_logger()


class CSVExporter:
    """CSV文件导出器"""

    def __init__(self, connection: DatabaseConnection):
        """初始化CSV导出器
        
        Args:
            connection: 数据库连接对象
        """
        self.connection = connection
        self.organizer = SchemaOrganizer(connection)

    def export_table_schema_to_csv(self, table_name: str, output_path: str) -> None:
        """导出单个表的结构到CSV文件
        
        Args:
            table_name: 表名
            output_path: 输出文件路径
        """
        try:
            logger.info(f"Exporting table schema: {table_name} to {output_path}")
            # 获取表结构
            schema = self.organizer.get_normalized_schema(table_name)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 定义CSV字段
            csv_fields = [
                'Field Name', 'Data Type', 'Length', 'Nullable', 
                'Primary Key', 'Default Value', 'Comment'
            ]
            
            # 写入CSV文件
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                
                # 写入表头
                writer.writerow(csv_fields)
                
                # 写入字段信息
                for field in schema['fields']:
                    row = [
                        field['name'],
                        field['type'],
                        field['length'],
                        'YES' if field['nullable'] else 'NO',
                        'YES' if field['primary_key'] else 'NO',
                        field['default'] if field['default'] is not None else '',
                        field['comment']
                    ]
                    writer.writerow(row)
            logger.info(f"Successfully exported table schema: {table_name} to {output_path}")
        except Exception as e:
            handle_error(e, f"CSVExporter.export_table_schema_to_csv for table {table_name}")

    def export_all_tables_to_csv(self, output_dir: str, organization: str = 'flat') -> None:
        """导出所有表的结构到CSV文件
        
        Args:
            output_dir: 输出目录
            organization: 组织方式，支持 'flat'（扁平）、'module'（按模块）
        """
        try:
            logger.info(f"Exporting all tables to {output_dir} with {organization} organization")
            # 获取所有表结构
            all_schema = self.organizer.get_all_tables_schema()
            
            if organization == 'flat':
                # 扁平结构：所有CSV文件直接放在输出目录
                for table_name in all_schema.keys():
                    output_path = os.path.join(output_dir, f"{table_name}.csv")
                    self.export_table_schema_to_csv(table_name, output_path)
            elif organization == 'module':
                # 按模块组织：为每个模块创建子目录
                self.export_by_module(output_dir, {'all': list(all_schema.keys())})
            else:
                raise ValueError(f"Unsupported organization type: {organization}")
            logger.info(f"Successfully exported all tables to {output_dir}")
        except Exception as e:
            handle_error(e, "CSVExporter.export_all_tables_to_csv")
        
    def export_by_module(self, output_dir: str, module_mapping: Dict[str, List[str]]) -> None:
        """按业务模块导出表结构到CSV文件
        
        Args:
            output_dir: 输出目录
            module_mapping: 模块映射，键为模块名，值为该模块包含的表名列表
        """
        try:
            logger.info(f"Exporting tables by module to {output_dir}")
            # 按模块组织表结构
            organized_by_module = self.organizer.organize_by_module(module_mapping)
            
            # 为每个模块创建目录并导出CSV文件
            for module, tables in organized_by_module.items():
                logger.info(f"Exporting module: {module} with tables: {tables}")
                for table_name in tables:
                    output_path = os.path.join(output_dir, module, f"{table_name}.csv")
                    self.export_table_schema_to_csv(table_name, output_path)
            logger.info(f"Successfully exported tables by module to {output_dir}")
        except Exception as e:
            handle_error(e, "CSVExporter.export_by_module")

    def export_with_directory_structure(self, base_dir: str, structure_config: Dict[str, Any]) -> None:
        """按预设目录结构组织并导出CSV文件
        
        Args:
            base_dir: 基础目录
            structure_config: 目录结构配置
        """
        try:
            logger.info(f"Exporting tables with directory structure to {base_dir}")
            # 递归处理目录结构
            def process_config(current_dir: str, config: Dict[str, Any]) -> None:
                # 处理该目录下的表
                if 'tables' in config:
                    for table in config['tables']:
                        output_path = os.path.join(current_dir, f"{table}.csv")
                        self.export_table_schema_to_csv(table, output_path)
                
                # 处理子目录
                if 'submodules' in config:
                    for submodule, subconfig in config['submodules'].items():
                        submodule_dir = os.path.join(current_dir, submodule)
                        process_config(submodule_dir, subconfig)
            
            # 处理顶层模块
            for module, config in structure_config.items():
                module_dir = os.path.join(base_dir, module)
                process_config(module_dir, config)
            logger.info(f"Successfully exported tables with directory structure to {base_dir}")
        except Exception as e:
            handle_error(e, "CSVExporter.export_with_directory_structure")