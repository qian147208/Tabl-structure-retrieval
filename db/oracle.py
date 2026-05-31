import cx_Oracle
from typing import Dict, Any, Optional, List
from .interface import DatabaseConnection
from .logger import get_logger
from .exceptions import ConnectionError, QueryError, ValidationError, handle_error

logger = get_logger()


class OracleConnection(DatabaseConnection):
    """Oracle 数据库连接实现"""

    def __init__(self, **kwargs):
        """初始化 Oracle 数据库连接
        
        Args:
            **kwargs: 数据库连接参数，包括 host, port, user, password, database/service_name 等
        """
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 1521)
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        # 同时支持 database 和 service_name 两种参数名
        self.service_name = kwargs.get('database') or kwargs.get('service_name')
        self.connection = None

    def connect(self):
        """建立 Oracle 数据库连接
        
        Returns:
            cx_Oracle.Connection: Oracle 连接对象
        """
        try:
            if not self.validate_connection_params(host=self.host, port=self.port, user=self.user, 
                                               password=self.password, service_name=self.service_name):
                raise ValidationError("Invalid connection parameters")
            
            logger.info(f"Connecting to Oracle database: {self.host}:{self.port}/{self.service_name}")
            dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
            self.connection = cx_Oracle.connect(
                user=self.user,
                password=self.password,
                dsn=dsn
            )
            logger.info(f"Successfully connected to Oracle database: {self.host}:{self.port}/{self.service_name}")
            return self.connection
        except Exception as e:
            handle_error(ConnectionError(f"Failed to connect to Oracle: {str(e)}"), "OracleConnection.connect")

    def disconnect(self):
        """关闭 Oracle 数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info(f"Disconnected from Oracle database: {self.host}:{self.port}/{self.service_name}")
        except Exception as e:
            handle_error(e, "OracleConnection.disconnect")

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        """执行 SQL 查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            list: 查询结果
        """
        try:
            if not self.connection:
                self.connect()
            
            logger.debug(f"Executing SQL query: {query[:200]}...")
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    logger.debug(f"Query returned {len(result)} rows")
                else:
                    self.connection.commit()
                    result = cursor.rowcount
                    logger.debug(f"Query affected {result} rows")
            return result
        except Exception as e:
            handle_error(QueryError(f"Failed to execute SQL query: {str(e)}"), "OracleConnection.execute")

    def validate_connection_params(self, **kwargs) -> bool:
        """验证 Oracle 连接参数
        
        Args:
            **kwargs: 数据库连接参数
        
        Returns:
            bool: 参数是否有效
        """
        # 同时支持 database 和 service_name 参数名
        service_name = kwargs.get('database') or kwargs.get('service_name')
        required_params = ['user', 'password']
        for param in required_params:
            if param not in kwargs or not kwargs[param]:
                return False
        if not service_name:
            return False
        
        # 验证端口号
        port = kwargs.get('port', 1521)
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False
        
        # 验证主机名
        host = kwargs.get('host', 'localhost')
        if not isinstance(host, str) or not host:
            return False
        
        return True

    def get_tables(self) -> List[str]:
        """获取数据库中的所有表名
        
        Returns:
            List[str]: 表名列表
        """
        query = "SELECT table_name FROM user_tables"
        result = self.execute(query)
        tables = [row[0] for row in result]
        return tables

    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 表结构信息，包含字段名、数据类型、长度、主键信息、nullable状态、字段描述等
        """
        # 获取字段信息
        query = """
        SELECT 
            column_name, 
            data_type, 
            data_length, 
            nullable, 
            data_default, 
            comments
        FROM 
            user_tab_columns 
        WHERE 
            table_name = upper(:table_name)
        ORDER BY 
            column_id
        """
        columns = self.execute(query, {'table_name': table_name})
        
        # 获取主键信息
        pk_query = """
        SELECT 
            column_name 
        FROM 
            user_cons_columns 
        WHERE 
            table_name = upper(:table_name) 
            AND constraint_name IN (
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = upper(:table_name) 
                AND constraint_type = 'P'
            )
        """
        primary_keys_result = self.execute(pk_query, {'table_name': table_name})
        primary_keys = [row[0] for row in primary_keys_result]
        
        fields = []
        for column in columns:
            field_info = {
                'name': column[0],
                'type': column[1],
                'length': column[2],
                'nullable': column[3] == 'Y',
                'primary_key': column[0] in primary_keys,
                'default': column[4],
                'comment': column[5] if column[5] else ''
            }
            fields.append(field_info)
        
        # 获取表注释
        table_comment = ''
        try:
            table_comment_query = "SELECT comments FROM user_tab_comments WHERE table_name = upper(:table_name)"
            table_comment_result = self.execute(table_comment_query, {'table_name': table_name})
            if table_comment_result and len(table_comment_result) > 0:
                table_comment = table_comment_result[0][0] if table_comment_result[0][0] else ''
        except Exception:
            pass
        
        return {
            'table_name': table_name,
            'fields': fields,
            'primary_keys': primary_keys,
            'comment': table_comment
        }
