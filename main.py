import logging
from checker.config_loader import ConfigLoader
from checker.port_checker import PortChecker
from notifier.webhook_notifier import WebhookNotifier
from scheduler.task_scheduler import TaskScheduler
from utils.logger import setup_logger

class PortGuardian:
    def __init__(self):
        # 加载配置
        self.config_loader = ConfigLoader()
        config = self.config_loader.get_config()
        
        # 初始化日志
        setup_logger(config.get('log_level', 'INFO'), config.get('log_file'))
        
        # 初始化模块
        self.port_checker = PortChecker(self.config_loader.get_timeout())
        self.webhook_notifier = WebhookNotifier(self.config_loader.get_webhook_config())
        self.scheduler = TaskScheduler()
        
        # 注册信号处理器
        self.scheduler.setup_signal_handlers()
        
        logging.info("PortGuardian 初始化完成")

    def run_check_task(self) -> None:
        """执行端口检查任务"""
        logging.info("开始执行端口检查任务")
        servers = self.config_loader.get_servers()
        results = self.port_checker.check_all_servers(servers)
        
        # 处理检查结果，发送通知
        for result in results:
            if result['status_changed']:
                self.webhook_notifier.notify_port_status_change(result)
        
        logging.info("端口检查任务执行完成")

    def start(self) -> None:
        """启动服务"""
        # 立即执行一次检查
        self.run_check_task()
        
        # 调度定期检查任务
        check_interval = self.config_loader.get_check_interval()
        self.scheduler.schedule_task(check_interval, self.run_check_task)
        
        # 启动调度器
        self.scheduler.start()
        
        # 保持主进程运行
        try:
            while True:
                # 主循环，保持程序运行
                import time
                time.sleep(3600)  # 休眠1小时
        except KeyboardInterrupt:
            logging.info("用户中断，程序退出")
            self.scheduler.stop()

if __name__ == "__main__":
    try:
        port_guardian = PortGuardian()
        port_guardian.start()
    except Exception as e:
        logging.critical(f"程序启动失败: {str(e)}", exc_info=True)
        exit(1)
