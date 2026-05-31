from typing import Dict, Any, List, Optional
from .interface import DatabaseConnection
from .logger import get_logger
from .exceptions import handle_error

logger = get_logger()


class SchemaOrganizer:
    """表结构信息组织器"""

    def __init__(self, connection: DatabaseConnection):
        """初始化表结构组织器
        
        Args:
            connection: 数据库连接对象
        """
        self.connection = connection
        self.schema_cache: Dict[str, Dict[str, Any]] = {}

    def get_normalized_schema(self, table_name: str) -> Dict[str, Any]:
        """获取规范化的表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 规范化的表结构信息
        """
        try:
            if table_name not in self.schema_cache:
                logger.info(f"Getting schema for table: {table_name}")
                raw_structure = self.connection.get_table_structure(table_name)
                normalized_structure = self._normalize_structure(raw_structure)
                self.schema_cache[table_name] = normalized_structure
                logger.info(f"Cached schema for table: {table_name}")
            else:
                logger.debug(f"Using cached schema for table: {table_name}")
            return self.schema_cache[table_name]
        except Exception as e:
            handle_error(e, f"SchemaOrganizer.get_normalized_schema for table {table_name}")

    def _normalize_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """规范化表结构信息
        
        Args:
            structure: 原始表结构信息
        
        Returns:
            Dict[str, Any]: 规范化的表结构信息
        """
        normalized = {
            'table_name': structure['table_name'],
            'fields': [],
            'primary_keys': structure['primary_keys'],
            'metadata': {
                'field_count': len(structure['fields']),
                'primary_key_count': len(structure['primary_keys']),
                'has_primary_key': len(structure['primary_keys']) > 0
            }
        }

        for field in structure['fields']:
            normalized_field = {
                'name': field['name'],
                'type': field['type'].lower(),
                'length': field['length'],
                'nullable': field['nullable'],
                'primary_key': field['primary_key'],
                'default': field['default'],
                'comment': field['comment'] or ''
            }
            normalized['fields'].append(normalized_field)

        return normalized

    def get_all_tables_schema(self) -> Dict[str, Dict[str, Any]]:
        """获取所有表的规范化结构信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 以表名为键的表结构信息字典
        """
        try:
            logger.info("Getting all tables schema")
            tables = self.connection.get_tables()
            logger.info(f"Found {len(tables)} tables")
            schema = {}
            
            for table in tables:
                schema[table] = self.get_normalized_schema(table)
            
            logger.info(f"Successfully retrieved schema for {len(schema)} tables")
            return schema
        except Exception as e:
            handle_error(e, "SchemaOrganizer.get_all_tables_schema")

    def organize_by_table_name(self, schema: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        """按表名组织表结构信息
        
        Args:
            schema: 表结构信息字典，默认为None，会自动获取所有表结构
        
        Returns:
            Dict[str, Dict[str, Any]]: 按表名排序的表结构信息字典
        """
        try:
            logger.info("Organizing schema by table name")
            if schema is None:
                schema = self.get_all_tables_schema()
            
            # 按表名排序
            sorted_schema = {}
            for table_name in sorted(schema.keys()):
                sorted_schema[table_name] = schema[table_name]
            
            logger.info(f"Successfully organized {len(sorted_schema)} tables by name")
            return sorted_schema
        except Exception as e:
            handle_error(e, "SchemaOrganizer.organize_by_table_name")

    def organize_by_module(self, module_mapping: Dict[str, List[str]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """按业务模块组织表结构信息
        
        Args:
            module_mapping: 模块映射，键为模块名，值为该模块包含的表名列表
        
        Returns:
            Dict[str, Dict[str, Dict[str, Any]]]: 按模块组织的表结构信息
        """
        try:
            logger.info("Organizing schema by module")
            all_schema = self.get_all_tables_schema()
            organized_by_module = {}
            
            # 按模块组织
            for module, tables in module_mapping.items():
                logger.debug(f"Processing module: {module} with tables: {tables}")
                organized_by_module[module] = {}
                for table in tables:
                    if table in all_schema:
                        organized_by_module[module][table] = all_schema[table]
                    else:
                        logger.warning(f"Table {table} not found in schema")
            
            # 处理未在映射中的表
            uncategorized_tables = [table for table in all_schema.keys() if not any(table in tables for tables in module_mapping.values())]
            if uncategorized_tables:
                logger.info(f"Found {len(uncategorized_tables)} uncategorized tables")
                organized_by_module['uncategorized'] = {}
                for table in uncategorized_tables:
                    organized_by_module['uncategorized'][table] = all_schema[table]
            
            logger.info(f"Successfully organized schema into {len(organized_by_module)} modules")
            return organized_by_module
        except Exception as e:
            handle_error(e, "SchemaOrganizer.organize_by_module")

    def export_schema(self, format: str = 'dict') -> Any:
        """导出表结构信息
        
        Args:
            format: 导出格式，支持 'dict'、'json'
        
        Returns:
            Any: 导出的表结构信息
        """
        try:
            logger.info(f"Exporting schema in {format} format")
            schema = self.get_all_tables_schema()
            
            if format == 'json':
                import json
                result = json.dumps(schema, ensure_ascii=False, indent=2)
                logger.info(f"Successfully exported schema in JSON format")
                return result
            
            logger.info(f"Successfully exported schema in dict format")
            return schema
        except Exception as e:
            handle_error(e, "SchemaOrganizer.export_schema")