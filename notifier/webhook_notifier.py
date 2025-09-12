import requests
import logging
import time
from typing import Dict, Any
import json


def replace_special_chars(text: str) -> str:
    """替换GBK不支持的特殊字符，避免日志编码错误"""
    char_map = {
        "✅": "[成功]",
        "❌": "[错误]",
        "⚠️": "[警告]",
        "ℹ️": "[信息]"
    }
    for special_char, replacement in char_map.items():
        text = text.replace(special_char, replacement)
    return text


class WebhookNotifier:
    def __init__(self, config: Dict[str, Any]):
        self.url = config['url']
        self.method = config['method'].upper()
        self.headers = config.get('headers', {}).copy() or {}
        self.retry_count = config['retry_count']
        self.retry_interval = config['retry_interval']
        # 从配置读取msg_type（灵活适配不同Webhook服务）
        self.msg_type = config.get('msg_type', 'text')  # 默认值改为'text'，适配更多服务

        # 确保重试参数合法性
        self.retry_count = max(0, int(self.retry_count))
        self.retry_interval = max(1, int(self.retry_interval))

        # 设置默认Content-Type
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'

        # 初始化日志
        safe_url = replace_special_chars(self.url)
        logging.info(f"初始化Webhook通知器 - URL: {safe_url}, 方法: {self.method}, msg_type: {self.msg_type}")
        logging.debug(f"Webhook头部信息: {self.headers}")

    def _send_request(self, payload: Dict[str, Any]) -> bool:
        """发送单个Webhook请求，增强错误详情和调试信息"""
        try:
            # 打印请求详情（便于调试）
            safe_payload = replace_special_chars(json.dumps(payload, ensure_ascii=False, indent=2))
            logging.debug(f"Webhook请求 - 方法: {self.method}, URL: {self.url}, 数据: {safe_payload}")

            response = None
            if self.method == 'POST':
                if self.headers.get('Content-Type') == 'application/json':
                    response = requests.post(
                        self.url,
                        headers=self.headers,
                        json=payload,
                        timeout=15  # 延长超时时间，适配更多服务
                    )
                else:
                    response = requests.post(
                        self.url,
                        headers=self.headers,
                        data=payload,
                        timeout=15
                    )
            elif self.method == 'GET':
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    params=payload,
                    timeout=15
                )
            else:
                logging.error(f"不支持的HTTP方法: {self.method}（仅支持GET/POST）")
                return False

            # 检查HTTP状态码
            response.raise_for_status()

            # 处理成功响应
            safe_response = replace_special_chars(
                response.text[:500] + "..." if len(response.text) > 500 else response.text
            )
            logging.info(f"Webhook发送成功 - 状态码: {response.status_code}, 响应: {safe_response}")
            return True

        except requests.exceptions.HTTPError as e:
            # 详细HTTP错误信息（含响应内容）
            status_code = e.response.status_code if e.response else '未知'
            response_text = e.response.text[:500] if e.response else '无'
            logging.error(f"Webhook HTTP错误 - 状态码: {status_code}, 响应: {response_text}")
        except requests.exceptions.ConnectionError:
            logging.error(f"Webhook连接失败 - 无法访问URL: {self.url}（检查网络和URL）")
        except requests.exceptions.Timeout:
            logging.error(f"Webhook超时 - URL: {self.url}（超过15秒未响应）")
        except Exception as e:
            logging.error(f"Webhook发送失败 - 未知错误: {str(e)}", exc_info=True)
        return False

    def send_notification(self, payload: Dict[str, Any]) -> bool:
        """发送通知并处理重试逻辑"""
        if self.retry_count == 0:
            logging.info("Webhook通知：尝试发送（不启用重试）")
            return self._send_request(payload)

        for attempt in range(1, self.retry_count + 1):
            logging.info(f"Webhook通知：第 {attempt}/{self.retry_count} 次尝试")
            if self._send_request(payload):
                return True
            if attempt < self.retry_count:
                logging.info(f"等待 {self.retry_interval} 秒后重试...")
                time.sleep(self.retry_interval)

        logging.error(f"Webhook通知：达到最大重试次数（{self.retry_count}次），发送失败")
        return False

    def format_port_status_message(self, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化通知消息，适配不同平台的Webhook格式"""
        server = check_result['server']
        status = "恢复正常" if check_result['is_alive'] else "出现异常"
        status_emoji = "✅" if check_result['is_alive'] else "❌"

        # 检查是否为飞书Webhook
        if "feishu.cn" in self.url or "larksuite.com" in self.url:
            # 飞书Webhook格式
            message = {
                "msg_type": self.msg_type,  # 使用配置的msg_type，如text, post等
                "content": {
                    "text": f"{status_emoji} 服务器端口{status}\n"
                            f"服务器名称: {server['name']}\n"
                            f"主机地址: {server['host']}\n"
                            f"端口: {server['port']}\n"
                            f"协议: {server['protocol']}\n"
                            f"状态: {'UP' if check_result['is_alive'] else 'DOWN'}\n"
                            f"响应时间: {check_result.get('response_time', '未知')}ms\n"
                            f"检查时间: {check_result.get('checked_at', time.strftime('%Y-%m-%d %H:%M:%S'))}"
                }
            }
        # 检查是否为钉钉Webhook
        elif "dingtalk.com" in self.url:
            # 钉钉Webhook格式
            message = {
                "msgtype": "text",
                "text": {
                    "content": f"{status_emoji} 服务器端口{status}\n"
                               f"服务器名称: {server['name']}\n"
                               f"主机地址: {server['host']}\n"
                               f"端口: {server['port']}\n"
                               f"协议: {server['protocol']}\n"
                               f"状态: {'UP' if check_result['is_alive'] else 'DOWN'}\n"
                               f"响应时间: {check_result.get('response_time', '未知')}ms"
                }
            }
        else:
            # 通用Webhook格式
            message = {
                "msg_type": self.msg_type,
                "title": f"{status_emoji} 服务器端口{status}",
                "server_name": server['name'],
                "host": server['host'],
                "port": server['port'],
                "protocol": server['protocol'],
                "status": "UP" if check_result['is_alive'] else "DOWN",
                "response_time_ms": check_result.get('response_time', '未知'),
                "checked_at": check_result.get('checked_at', time.strftime("%Y-%m-%d %H:%M:%S")),
                "timestamp": time.time()
            }

        return message

    def notify_port_status_change(self, check_result: Dict[str, Any]) -> bool:
        """端口状态变化时发送通知，优化日志和触发逻辑"""
        # 验证状态变化标志
        if not check_result.get('status_changed', False):
            logging.debug(f"端口状态未变化，跳过通知 - 服务器: {check_result['server']['name']}")
            return True

        # 生成并发送通知
        message = self.format_port_status_message(check_result)

        # 获取安全的日志信息
        if "feishu.cn" in self.url or "larksuite.com" in self.url:
            safe_title = replace_special_chars(message['content']['text'].split('\n')[0])
        else:
            safe_title = replace_special_chars(message.get('title', '端口状态通知'))

        safe_server_name = replace_special_chars(check_result['server']['name'])
        logging.info(f"触发端口状态通知: {safe_title} - {safe_server_name}")

        return self.send_notification(message)
