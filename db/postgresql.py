import psycopg2
from typing import Dict, Any, Optional, List
from .interface import DatabaseConnection
from .logger import get_logger
from .exceptions import ConnectionError, QueryError, ValidationError, handle_error

logger = get_logger()


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL 数据库连接实现"""

    def __init__(self, **kwargs):
        """初始化 PostgreSQL 数据库连接
        
        Args:
            **kwargs: 数据库连接参数，包括 host, port, user, password, database, schema 等
        """
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 5432)
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')
        self.schema = kwargs.get('schema', 'public')  # 默认查询 public schema
        self.connection = None

    def connect(self):
        """建立 PostgreSQL 数据库连接
        
        Returns:
            psycopg2.extensions.connection: PostgreSQL 连接对象
        """
        try:
            if not self.validate_connection_params(host=self.host, port=self.port, user=self.user, 
                                               password=self.password, database=self.database):
                raise ValidationError("Invalid connection parameters")
            
            logger.info(f"Connecting to PostgreSQL database: {self.host}:{self.port}/{self.database}")
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info(f"Successfully connected to PostgreSQL database: {self.host}:{self.port}/{self.database}")
            return self.connection
        except Exception as e:
            handle_error(ConnectionError(f"Failed to connect to PostgreSQL: {str(e)}"), "PostgreSQLConnection.connect")

    def disconnect(self):
        """关闭 PostgreSQL 数据库连接"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info(f"Disconnected from PostgreSQL database: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            handle_error(e, "PostgreSQLConnection.disconnect")

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
            handle_error(QueryError(f"Failed to execute SQL query: {str(e)}"), "PostgreSQLConnection.execute")

    def validate_connection_params(self, **kwargs) -> bool:
        """验证 PostgreSQL 连接参数
        
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
        port = kwargs.get('port', 5432)
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
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s
        """
        result = self.execute(query, (self.schema,))
        tables = [row[0] for row in result]
        return tables

    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 表结构信息，包含字段名、数据类型、长度、主键信息、nullable状态、字段描述等
        """
        # 获取字段信息（不包括注释）
        query = """
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length, 
            is_nullable, 
            column_default
        FROM 
            information_schema.columns 
        WHERE 
            table_schema = %s
            AND table_name = %s
        ORDER BY 
            ordinal_position
        """
        columns = self.execute(query, (self.schema, table_name,))
        
        # 获取主键信息
        pk_query = """
        SELECT 
            column_name 
        FROM 
            information_schema.key_column_usage 
        WHERE 
            table_schema = %s
            AND table_name = %s 
            AND constraint_name LIKE '%_pkey'
        """
        primary_keys_result = self.execute(pk_query, (self.schema, table_name,))
        primary_keys = [row[0] for row in primary_keys_result]
        
        # 获取列注释
        comment_query = """
        SELECT a.attname, col_description(a.attrelid, a.attnum)
        FROM pg_class c
        JOIN pg_attribute a ON a.attrelid = c.oid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
        AND c.relname = %s
        AND a.attnum > 0
        AND NOT a.attisdropped
        """
        comment_result = self.execute(comment_query, (self.schema, table_name,))
        comments = {row[0]: (row[1] if row[1] else '') for row in comment_result}
        
        fields = []
        for column in columns:
            field_info = {
                'name': column[0],
                'type': column[1],
                'length': column[2],
                'nullable': column[3] == 'YES',
                'primary_key': column[0] in primary_keys,
                'default': column[4],
                'comment': comments.get(column[0], '') or ''
            }
            fields.append(field_info)
        
        # 获取表注释
        table_comment = ''
        try:
            table_comment_query = """
                SELECT obj_description((%s || '.' || %s)::regclass, 'pg_class') AS table_comment
            """
            table_comment_result = self.execute(table_comment_query, (self.schema, table_name,))
            if table_comment_result and len(table_comment_result) > 0:
                table_comment = table_comment_result[0][0] or ''
        except Exception:
            pass
        
        return {
            'table_name': table_name,
            'fields': fields,
            'primary_keys': primary_keys,
            'comment': table_comment
        }