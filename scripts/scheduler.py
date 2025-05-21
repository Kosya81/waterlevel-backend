import os
import sys
import signal
import argparse
import schedule
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import atexit
import asyncio

# Добавляем родительскую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fill_measurements import update_all_stations
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
def setup_logging(log_file='scheduler.log'):
    """Настройка логирования с ротацией файлов"""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настраиваем файловый обработчик с ротацией и UTF-8
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Настраиваем консольный обработчик с UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Настраиваем логгер
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Удаляем все существующие обработчики
    logger.handlers = []
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Отключаем передачу логов родительским логгерам
    logger.propagate = False
    
    return logger

logger = setup_logging()

class Scheduler:
    def __init__(self, interval_minutes=15):
        self.interval_minutes = interval_minutes
        self.running = True
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers"""
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False
        # Принудительно завершаем процесс
        sys.exit(0)
    
    async def job(self):
        """Scheduled job"""
        logger.info("Starting scheduled data update")
        try:
            await update_all_stations()
            logger.info("Scheduled data update completed successfully")
        except Exception as e:
            logger.error(f"Error during scheduled data update: {str(e)}", exc_info=True)
    
    def run(self):
        """Run scheduler"""
        logger.info(f"Scheduler started. Will update data every {self.interval_minutes} minutes.")
        
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Schedule updates
        schedule.every(self.interval_minutes).minutes.do(
            lambda: loop.run_until_complete(self.job())
        )
        
        # Run first update immediately
        loop.run_until_complete(self.job())
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {str(e)}", exc_info=True)
                time.sleep(60)  # Wait a minute before next try on error
        
        # Close event loop
        loop.close()

def run_as_daemon(script_path, pid_file, log_file):
    """Запуск скрипта в фоновом режиме в Windows"""
    # Создаем директорию для PID файла если её нет
    pid_dir = os.path.dirname(pid_file)
    if pid_dir and not os.path.exists(pid_dir):
        os.makedirs(pid_dir)
    
    # Запускаем процесс в фоновом режиме
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=open(log_file, 'a'),
        stderr=open(log_file, 'a'),
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    # Сохраняем PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    # Регистрируем функцию для удаления PID файла при выходе
    atexit.register(lambda: os.remove(pid_file) if os.path.exists(pid_file) else None)
    
    return process.pid

def main():
    """Основная функция для запуска планировщика"""
    parser = argparse.ArgumentParser(description='Water level data scheduler')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--interval', type=int, default=15, help='Update interval in minutes')
    parser.add_argument('--pid-file', default='scheduler.pid', help='PID file path')
    parser.add_argument('--log-file', default='scheduler.log', help='Log file path')
    args = parser.parse_args()
    
    # Получаем интервал из переменных окружения или аргументов
    interval = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', args.interval))
    
    if args.daemon:
        # Запускаем в фоновом режиме
        pid = run_as_daemon(
            os.path.abspath(__file__),
            args.pid_file,
            args.log_file
        )
        print(f"Scheduler started in background mode with PID: {pid}")
    else:
        scheduler = Scheduler(interval_minutes=interval)
        scheduler.run()

if __name__ == "__main__":
    main() 