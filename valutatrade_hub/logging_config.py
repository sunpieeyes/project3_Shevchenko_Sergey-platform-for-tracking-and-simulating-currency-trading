import os
import logging
from logging.handlers import RotatingFileHandler
from .infra.settings import settings


def setup_logging():
    """Настраивает систему логирования."""
    log_file = settings.get('log_file', 'logs/app.log')
    log_level = settings.get('log_level', 'INFO').upper()
    
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    logger.handlers.clear()
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("=" * 50)
    logger.info("Система логирования инициализирована")
    logger.info(f"Лог файл: {log_file}")
    logger.info(f"Уровень логирования: {log_level}")
    logger.info("=" * 50)


def get_logger(name):
    """Возвращает логгер с указанным именем."""
    return logging.getLogger(name)


try:
    setup_logging()
except Exception:
    pass