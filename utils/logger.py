import logging
import sys
from typing import Optional

def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    配置日志系统
    
    :param log_level: 日志级别，如DEBUG, INFO, WARNING, ERROR, CRITICAL
    :param log_file: 日志文件路径，如为None则只输出到控制台
    """
    # 定义日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有的处理器，避免重复输出
    if logger.handlers:
        logger.handlers = []
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        logging.info(f"日志将同时输出到文件: {log_file}")
    
    logging.info(f"日志系统初始化完成，日志级别: {log_level}")
