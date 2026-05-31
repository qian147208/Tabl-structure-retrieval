import pymysql
from typing import Dict, Any, Optional, List
from .interface import DatabaseConnection
from .logger import get_logger
from .exceptions import ConnectionError, QueryError, ValidationError, handle_error

logger = get_logger()


class MySQLConnection(DatabaseConnection):
    """MySQL 数据库连接实现"""

    def __init__(self, **kwargs):
        """初始化 MySQL 数据库连接
        
        Args:
            **kwargs: 数据库连接参数，包括 host, port, user, password, database 等
        """
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 3306)
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')
        self.connection = None

    def connect(self):
        """建立 MySQL 数据库连接
        
        Returns:
            pymysql.connections.Connection: MySQL 连接对象
        """
        try:
            if not self.validate_connection_params(host=self.host, port=self.port, user=self.user, 
                                               password=self.password, database=self.database):
                raise ValidationError("Invalid connection parameters")
            
            logger.info(f"Connecting to MySQL database: {self.host}:{self.port}/{self.database}")
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"Successfully connected to MySQL database: {self.host}:{self.port}/{self.database}")
            return self.connection
        except Exception as e:
            handle_error(ConnectionError(f"Failed to connect to MySQL: {str(e)}"), "MySQLConnection.connect")

    def disconnect(self):
        """关闭 MySQL 数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info(f"Disconnected from MySQL database: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            handle_error(e, "MySQLConnection.disconnect")

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
                # 处理 SELECT 和 SHOW 语句
                if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('SHOW'):
                    result = cursor.fetchall()
                    logger.debug(f"Query returned {len(result)} rows")
                else:
                    self.connection.commit()
                    result = cursor.rowcount
                    logger.debug(f"Query affected {result} rows")
            return result
        except Exception as e:
            handle_error(QueryError(f"Failed to execute SQL query: {str(e)}"), "MySQLConnection.execute")

    def validate_connection_params(self, **kwargs) -> bool:
        """验证 MySQL 连接参数
        
        Args:
            **kwargs: 数据库连接参数
        
        Returns:
            bool: 参数是否有效
        """
        required_params = ['user', 'password', 'database']
        for param in required_params:
            if param not in kwargs or not kwargs[param]:
                return False
        
        # 验证端口号
        port = kwargs.get('port', 3306)
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
        query = "SHOW TABLES"
        result = self.execute(query)
        tables = []
        for row in result:
            tables.append(list(row.values())[0])
        return tables

    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 表结构信息，包含字段名、数据类型、长度、主键信息、nullable状态、字段描述等
        """
        import re
        
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Invalid table name")
        
        valid_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        if not valid_pattern.match(table_name):
            raise ValueError(f"Invalid table name format: {table_name}")
        
        escaped_table_name = table_name.replace('`', '``')
        query = f"SHOW FULL COLUMNS FROM `{escaped_table_name}`"
        columns = self.execute(query)
        
        fields = []
        primary_keys = []
        
        # 获取表注释
        table_comment = ''
        try:
            comment_query = "SELECT table_comment FROM information_schema.TABLES WHERE table_schema = DATABASE() AND table_name = %s"
            comment_result = self.execute(comment_query, (table_name,))
            if comment_result and len(comment_result) > 0:
                table_comment = comment_result[0].get('table_comment', '') or ''
        except Exception:
            pass
        
        for column in columns:
            # 解析数据类型和长度
            data_type = column['Type']
            length = None
            if '(' in data_type and ')' in data_type:
                type_part = data_type.split('(')[0]
                length_part = data_type.split('(')[1].rstrip(')')
                try:
                    length = int(length_part)
                except ValueError:
                    length = length_part
                data_type = type_part
            
            # 检查是否为主键
            is_primary = column['Key'] == 'PRI'
            if is_primary:
                primary_keys.append(column['Field'])
            
            field_info = {
                'name': column['Field'],
                'type': data_type,
                'length': length,
                'nullable': column['Null'] == 'YES',
                'primary_key': is_primary,
                'default': column['Default'],
                'comment': column['Comment']
            }
            fields.append(field_info)
        
        return {
            'table_name': table_name,
            'fields': fields,
            'primary_keys': primary_keys,
            'comment': table_comment
        }