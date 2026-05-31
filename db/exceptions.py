from .logger import get_logger

logger = get_logger()


class DatabaseError(Exception):
    """数据库操作基础异常"""
    pass


class ConnectionError(DatabaseError):
    """数据库连接异常"""
    pass


class QueryError(DatabaseError):
    """SQL查询异常"""
    pass


class ValidationError(DatabaseError):
    """参数验证异常"""
    pass


def handle_error(error, context="Unknown context"):
    """全局错误处理函数
    
    Args:
        error: 异常对象
        context: 错误发生的上下文
    """
    error_message = f"Error in {context}: {str(error)}"
    
    # 记录错误日志
    logger.error(error_message)
    
    # 根据异常类型进行不同处理
    if isinstance(error, ValidationError):
        logger.warning(f"Validation error: {str(error)}")
    elif isinstance(error, ConnectionError):
        logger.critical(f"Connection error: {str(error)}")
    elif isinstance(error, QueryError):
        logger.error(f"Query error: {str(error)}")
    else:
        logger.error(f"Unexpected error: {str(error)}")
    
    # 明确重新抛出异常，让调用者决定如何处理
    raise error
