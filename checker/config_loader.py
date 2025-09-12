import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from logging.handlers import RotatingFileHandler
import atexit


def safe_log_message(message: str) -> str:
    """将消息中的非GBK字符替换为安全字符，避免日志编码错误"""
    # 定义常见特殊字符的替换规则
    replace_map = {
        '❌': '[错误]',
        '✅': '[成功]',
        '⚠️': '[警告]',
        'ℹ️': '[信息]',
        '🔴': '[异常]',
        '🟢': '[正常]'
    }

    # 先替换常见特殊字符
    for char, replacement in replace_map.items():
        message = message.replace(char, replacement)

    # 再过滤所有GBK不支持的字符
    try:
        # 尝试用GBK编码，如果失败则替换为'?'
        message.encode('gbk')
        return message
    except UnicodeEncodeError:
        # 逐个字符检查并替换不支持的字符
        safe_chars = []
        for char in message:
            try:
                char.encode('gbk')
                safe_chars.append(char)
            except UnicodeEncodeError:
                safe_chars.append('?')
        return ''.join(safe_chars)


class SafeStreamHandler(logging.StreamHandler):
    """自动处理日志消息中的特殊字符，避免编码错误"""

    def emit(self, record):
        try:
            # 替换消息中的特殊字符
            record.msg = safe_log_message(str(record.msg))
            super().emit(record)
        except Exception:
            self.handleError(record)


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        self._setup_logging()  # 初始化日志
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "./config/config.json"
        self.config: Dict[str, Any] = {}
        self._load_and_validate()

    def _setup_logging(self) -> None:
        """初始化日志系统，使用安全处理器避免编码错误"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        log_formatter = logging.Formatter(
            "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 控制台处理器：使用安全处理器自动替换特殊字符
        console_handler = SafeStreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO)

        # 文件日志处理器（UTF-8编码，保留原始字符）
        log_file_path = os.path.join(os.path.dirname(__file__), "../logs/port-guardian.log")
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024 * 1024 * 5,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.DEBUG)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    def _load_and_validate(self) -> None:
        try:
            self.config = self.load_config()
            self.validate_config()
            self.logger.info("配置文件加载成功 [路径: %s]", self.config_path)
        except Exception as e:
            self.logger.critical("配置初始化失败: %s", str(e), exc_info=True)
            raise

    def load_config(self) -> Dict[str, Any]:
        self.config_path = os.path.abspath(self.config_path)
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"配置文件不存在，请检查路径: \n{self.config_path}\n"
                "提示：确保文件已创建，且路径中无中文/特殊字符"
            )
        if not os.path.isfile(self.config_path):
            raise IsADirectoryError(f"指定路径是目录，不是文件: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.logger.debug("使用UTF-8编码读取配置文件")
                return json.load(f)
        except UnicodeDecodeError:
            raise UnicodeDecodeError(
                "配置文件编码错误",
                b"", 0, 0,
                "当前仅支持UTF-8编码！请用记事本/VSCode将文件转为UTF-8格式（步骤：文件→另存为→编码选UTF-8）"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误 [行: {e.lineno}, 列: {e.colno}]: {e.msg}") from e
        except PermissionError:
            raise PermissionError(f"无权限读取配置文件，请检查文件权限: {self.config_path}")
        except Exception as e:
            raise RuntimeError(f"读取文件时发生未知错误: {str(e)}") from e

    def validate_config(self) -> None:
        required_sections = ['check_interval', 'timeout', 'servers', 'webhook']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"配置缺少必要字段: '{section}'\n"
                                 f"提示：请在config.json中添加 '{section}' 节点")

        servers = self.config['servers']
        if not isinstance(servers, list):
            raise ValueError(f"'servers' 必须是列表类型，当前是: {type(servers).__name__}")
        if len(servers) == 0:
            raise ValueError("'servers' 列表不能为空，请至少配置1台服务器")

        for idx, server in enumerate(servers, 1):
            required_fields = ['name', 'host', 'port', 'protocol']
            for field in required_fields:
                if field not in server:
                    raise ValueError(f"第{idx}台服务器缺少字段: '{field}'\n"
                                     f"当前服务器配置: {server}")

            port = server['port']
            if not isinstance(port, int):
                raise ValueError(f"第{idx}台服务器'port'必须是整数，当前是: {type(port).__name__}")
            if not (1 <= port <= 65535):
                raise ValueError(f"第{idx}台服务器端口无效: {port}\n"
                                 "提示：端口范围必须是 1-65535")

            protocol = server['protocol'].lower()
            if protocol not in ['tcp', 'udp']:
                raise ValueError(f"第{idx}台服务器协议不支持: {server['protocol']}\n"
                                 "提示：仅支持 'TCP' 或 'UDP'（不区分大小写）")

        webhook = self.config['webhook']
        required_webhook_fields = ['url', 'method', 'retry_count', 'retry_interval']
        for field in required_webhook_fields:
            if field not in webhook:
                raise ValueError(f"Webhook缺少字段: '{field}'\n当前Webhook配置: {webhook}")

        webhook_method = webhook['method'].upper()
        if webhook_method not in ['GET', 'POST', 'PUT']:
            raise ValueError(f"Webhook方法不支持: {webhook['method']}\n"
                             "提示：仅支持 'GET'/'POST'/'PUT'（不区分大小写）")

        if not isinstance(self.config['check_interval'], int) or self.config['check_interval'] <= 0:
            raise ValueError(f"检查间隔必须是正整数，当前是: {self.config['check_interval']}")
        if not isinstance(self.config['timeout'], int) or self.config['timeout'] <= 0:
            raise ValueError(f"超时时间必须是正整数，当前是: {self.config['timeout']}")

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def get_servers(self) -> List[Dict[str, Any]]:
        return self.config['servers'].copy()

    def get_check_interval(self) -> int:
        return self.config['check_interval']

    def get_timeout(self) -> int:
        return self.config['timeout']

    def get_webhook_config(self) -> Dict[str, Any]:
        return self.config['webhook'].copy()

    def get_log_level(self) -> str:
        log_level = self.config.get('log_level', 'INFO').upper()
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            self.logger.warning(f"日志级别 '{log_level}' 无效，使用默认级别 INFO")
            return 'INFO'
        return log_level
