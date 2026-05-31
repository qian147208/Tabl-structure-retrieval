from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class DatabaseConnection(ABC):
    """数据库连接抽象接口"""

    @abstractmethod
    def __init__(self, **kwargs):
        """初始化数据库连接
        
        Args:
            **kwargs: 数据库连接参数
        """
        pass

    @abstractmethod
    def connect(self):
        """建立数据库连接
        
        Returns:
            数据库连接对象
        """
        pass

    @abstractmethod
    def disconnect(self):
        """关闭数据库连接"""
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """执行 SQL 查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果
        """
        pass

    @abstractmethod
    def validate_connection_params(self, **kwargs) -> bool:
        """验证连接参数
        
        Args:
            **kwargs: 数据库连接参数
        
        Returns:
            bool: 参数是否有效
        """
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """获取数据库中的所有表名
        
        Returns:
            List[str]: 表名列表
        """
        pass

    @abstractmethod
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 表结构信息，包含字段名、数据类型、长度、主键信息、nullable状态、字段描述等
        """
        pass