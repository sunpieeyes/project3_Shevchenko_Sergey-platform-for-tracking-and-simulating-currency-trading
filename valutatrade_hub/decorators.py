import functools
import time
from datetime import datetime
from .infra.settings import settings


def log_action(action_name=None, verbose=False):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            action = action_name or func.__name__.upper()
            
            log_info = {
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'function': func.__name__
            }
            
            try:
                # Ищем username в аргументах
                if args and len(args) > 1:
                    if 'username' in str(args[1:]):
                        for arg in args[1:]:
                            if isinstance(arg, str):
                                log_info['username'] = arg
                                break
                
                if 'username' in kwargs:
                    log_info['username'] = kwargs['username']
            except Exception:
                pass
            
            # Добавляем аргументы если verbose
            if verbose:
                log_info['args'] = str(args)
                log_info['kwargs'] = str(kwargs)
            
            start_time = time.time()
            result = None
            error = None
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                log_info['status'] = 'SUCCESS'
                
                # Добавляем результат если verbose
                if verbose and result:
                    log_info['result'] = str(result)[:100]  # Ограничиваем длину
                
                return result
                
            except Exception as e:
                log_info['status'] = 'ERROR'
                log_info['error'] = str(e)
                raise
                
            finally:
                log_info['duration_ms'] = int((time.time() - start_time) * 1000)
                
                _write_log(log_info)
        
        return wrapper
    return decorator


def _write_log(log_info):
    """Записывает лог в файл."""
    try:
        log_file = settings.get('log_file', 'logs/app.log')

        import os

        log_dir = os.path.dirname(log_file)
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Форматируем запись
        timestamp = log_info.get('timestamp', datetime.now().isoformat())
        action = log_info.get('action', 'UNKNOWN')
        status = log_info.get('status', 'UNKNOWN')
        username = log_info.get('username', 'unknown')
        duration = log_info.get('duration_ms', 0)
        
        log_line = f"{timestamp} | {action} | user={username} | status={status} | time={duration}ms"
        
        if 'error' in log_info:
            log_line += f" | error={log_info['error']}"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
            
    except Exception:
        pass


def simple_log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Вызов {func.__name__} с args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} вернул: {result}")
        return result
    return wrapper