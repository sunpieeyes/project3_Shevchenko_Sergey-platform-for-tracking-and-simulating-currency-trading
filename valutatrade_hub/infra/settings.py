import os
import json


class SettingsLoader:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config = {}
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """Загружает конфигурацию."""
        self._config = {
            'data_dir': 'data',
            'rates_ttl_seconds': 300,  
            'default_base_currency': 'USD',
            'log_file': 'logs/app.log',
            'log_level': 'INFO',
            
            
            'exchange_rate_api_key': os.getenv('EXCHANGE_RATE_API_KEY', 'demo_key'),
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY', ''),
            
            
            'users_file': 'data/users.json',
            'portfolios_file': 'data/portfolios.json',
            'rates_file': 'data/rates.json',
            'session_file': 'data/session.json'
        }
        
        config_file = 'config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                self._config.update(file_config)
            except Exception:
                pass
    
    def get(self, key, default=None):
        """Получает значение настройки."""
        return self._config.get(key, default)
    
    def reload(self):
        """Перезагружает конфигурацию."""
        self._load_config()
    
    def get_rates_ttl(self):
        """Возвращает TTL для курсов в секундах."""
        return self.get('rates_ttl_seconds', 300)
    
    def get_data_dir(self):
        """Возвращает директорию с данными."""
        return self.get('data_dir', 'data')
    
    def get_default_base_currency(self):
        """Возвращает базовую валюту по умолчанию."""
        return self.get('default_base_currency', 'USD')


settings = SettingsLoader()