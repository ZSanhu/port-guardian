import schedule
import time
import logging
from threading import Thread
from typing import Callable
import signal
import sys

class TaskScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        logging.info("初始化任务调度器")

    def schedule_task(self, interval_seconds: int, task: Callable) -> None:
        """按指定间隔（秒）调度任务"""
        logging.info(f"调度任务，执行间隔: {interval_seconds}秒")
        schedule.every(interval_seconds).seconds.do(task)

    def run_scheduler(self) -> None:
        """运行调度器"""
        self.running = True
        logging.info("启动任务调度器")
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
        logging.info("任务调度器已停止")

    def start(self) -> None:
        """在新线程中启动调度器"""
        self.scheduler_thread = Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logging.info("任务调度器线程已启动")

    def stop(self) -> None:
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logging.info("任务调度器已停止")

    def setup_signal_handlers(self) -> None:
        """设置信号处理器，用于优雅退出"""
        def signal_handler(signum, frame):
            logging.info(f"接收到信号 {signum}，准备退出...")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logging.info("信号处理器已设置")
