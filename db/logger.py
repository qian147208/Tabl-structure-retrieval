import logging
import os
from datetime import datetime

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 生成日志文件名
log_file = os.path.join(log_dir, f"db_extractor_{datetime.now().strftime('%Y-%m-%d')}.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# 创建日志记录器
logger = logging.getLogger('db_extractor')

def get_logger(name=None):
    """获取日志记录器"""
    if name:
        return logging.getLogger(name)
    return logger
