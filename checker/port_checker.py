import socket
import logging
from typing import Dict, Tuple, Optional
import time

class PortChecker:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.previous_states = {}  # 存储上一次检查的状态，用于比较状态变化
        logging.info(f"初始化端口检查器，超时时间: {self.timeout}秒")

    def check_tcp_port(self, host: str, port: int) -> Tuple[bool, Optional[float]]:
        """检查TCP端口是否可达"""
        start_time = time.time()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                result = s.connect_ex((host, port))
                response_time = time.time() - start_time
                return result == 0, response_time
        except socket.error as e:
            logging.error(f"TCP连接错误 {host}:{port} - {str(e)}")
            return False, None

    def check_udp_port(self, host: str, port: int) -> Tuple[bool, Optional[float]]:
        """检查UDP端口是否可达（简单检测，不保证100%准确）"""
        start_time = time.time()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(self.timeout)
                # 发送一个空数据包
                s.sendto(b'', (host, port))
                
                try:
                    # 尝试接收响应
                    s.recvfrom(1024)
                    response_time = time.time() - start_time
                    return True, response_time
                except socket.timeout:
                    # 对于UDP，超时不一定表示端口不可达，因为有些服务不回复
                    # 这里我们认为超时也是一种成功，因为至少主机是可达的
                    response_time = time.time() - start_time
                    return True, response_time
        except socket.error as e:
            logging.error(f"UDP连接错误 {host}:{port} - {str(e)}")
            return False, None

    def check_server(self, server: Dict[str, any]) -> Dict[str, any]:
        """检查单个服务器的端口状态"""
        host = server['host']
        port = server['port']
        protocol = server['protocol'].lower()
        name = server['name']
        
        logging.debug(f"检查 {name} ({host}:{port}/{protocol})")
        
        if protocol == 'tcp':
            is_alive, response_time = self.check_tcp_port(host, port)
        elif protocol == 'udp':
            is_alive, response_time = self.check_udp_port(host, port)
        else:
            logging.error(f"不支持的协议: {protocol}")
            return {
                'server': server,
                'is_alive': False,
                'response_time': None,
                'status_changed': False,
                'error': f"不支持的协议: {protocol}"
            }
        
        # 检查状态是否发生变化
        server_key = f"{host}:{port}:{protocol}"
        previous_state = self.previous_states.get(server_key, None)
        status_changed = previous_state is not None and previous_state != is_alive
        
        # 更新状态记录
        self.previous_states[server_key] = is_alive
        
        result = {
            'server': server,
            'is_alive': is_alive,
            'response_time': round(response_time * 1000, 2) if response_time else None,  # 转换为毫秒
            'status_changed': status_changed,
            'checked_at': time.time()
        }
        
        status = "存活" if is_alive else "不可达"
        logging.info(f"{name} ({host}:{port}/{protocol}) 状态: {status}，响应时间: {result['response_time']}ms")
        
        return result

    def check_all_servers(self, servers: list) -> list:
        """检查所有服务器的端口状态"""
        results = []
        for server in servers:
            result = self.check_server(server)
            results.append(result)
        return results
