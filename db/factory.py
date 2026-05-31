from typing import Dict, Any
from .logger import get_logger
from .exceptions import handle_error, ValidationError

logger = get_logger()


class DatabaseConnectionFactory:
    """数据库连接工厂类"""

    @staticmethod
    def create_connection(db_type: str, **kwargs):
        """根据数据库类型创建数据库连接对象
        
        Args:
            db_type: 数据库类型，支持 'mysql', 'postgresql', 'oracle'
            **kwargs: 数据库连接参数
        
        Returns:
            DatabaseConnection: 数据库连接对象
        
        Raises:
            ValueError: 不支持的数据库类型
        """
        try:
            logger.info(f"Creating database connection for type: {db_type}")
            if db_type.lower() == 'mysql':
                try:
                    from .mysql import MySQLConnection
                    logger.debug(f"Creating MySQL connection with params: {kwargs}")
                    return MySQLConnection(**kwargs)
                except ImportError as e:
                    raise ValidationError("MySQL 驱动未安装，请运行: pip install pymysql")
            elif db_type.lower() == 'postgresql':
                try:
                    from .postgresql import PostgreSQLConnection
                    logger.debug(f"Creating PostgreSQL connection with params: {kwargs}")
                    return PostgreSQLConnection(**kwargs)
                except ImportError as e:
                    raise ValidationError("PostgreSQL 驱动未安装，请运行: pip install psycopg2-binary")
            elif db_type.lower() == 'oracle':
                try:
                    from .oracle import OracleConnection
                    logger.debug(f"Creating Oracle connection with params: {kwargs}")
                    return OracleConnection(**kwargs)
                except ImportError as e:
                    raise ValidationError("Oracle 驱动未安装，请运行: pip install cx-Oracle")
            else:
                error_message = f"Unsupported database type: {db_type}"
                logger.error(error_message)
                raise ValidationError(error_message)
        except Exception as e:
            handle_error(e, "DatabaseConnectionFactory.create_connection")
            raise
