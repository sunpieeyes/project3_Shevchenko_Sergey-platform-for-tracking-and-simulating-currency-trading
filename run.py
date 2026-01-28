#!/usr/bin/env python3
"""
Скрипт запуска.
"""
import sys
import os

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Инициализировать логирование
try:
    from valutatrade_hub.logging_config import setup_logging
    setup_logging()
except ImportError:
    print("Внимание: модуль логирования не найден")
except Exception as e:
    print(f"Внимание: ошибка настройки логирования: {e}")

from valutatrade_hub.cli.interface import main

if __name__ == '__main__':
    main()