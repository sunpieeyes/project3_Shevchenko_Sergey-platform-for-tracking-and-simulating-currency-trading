from .settings import SettingsLoader



class Database:
    def __init__(self, data_folder: str = "data"):
        self.data_folder = data_folder
        self.settings = SettingsLoader()

    
    
    def get_all_users(self):
        """Получает всех пользователей."""
        from ..core.utils import load_json
        return load_json(f"{self.data_folder}/users.json")
    
    def save_users(self, users):
        """Сохраняет пользователей."""
        from ..core.utils import save_json
        return save_json(f"{self.data_folder}/users.json", users)
    
    def find_user(self, username):
        """Ищет пользователя по имени."""
        users = self.get_all_users()
        for user in users:
            if user.get('username') == username:
                return user
        return None
    
    def add_user(self, user_data):
        """Добавляет нового пользователя."""
        users = self.get_all_users()
        users.append(user_data)
        return self.save_users(users)
    
    # === Портфели ===
    
    def get_all_portfolios(self):
        """Получает все портфели."""
        from ..core.utils import load_json
        return load_json(f"{self.data_folder}/portfolios.json")
    
    def save_portfolios(self, portfolios):
        """Сохраняет портфели."""
        from ..core.utils import save_json
        return save_json(f"{self.data_folder}/portfolios.json", portfolios)
    
    def get_portfolio(self, user_id):
        """Получает портфель пользователя."""
        portfolios = self.get_all_portfolios()
        for port in portfolios:
            if port.get('user_id') == user_id:
                return port
        return None
    
    def save_portfolio(self, portfolio_data):
        """Сохраняет или обновляет портфель."""
        portfolios = self.get_all_portfolios()
        user_id = portfolio_data['user_id']
        
        # Ищем старый портфель
        found = False
        for i, port in enumerate(portfolios):
            if port.get('user_id') == user_id:
                portfolios[i] = portfolio_data
                found = True
                break
        
        if not found:
            portfolios.append(portfolio_data)
        
        return self.save_portfolios(portfolios)
    
    # === Курсы ===
    
    def get_rates(self):
        """Получает курсы валют."""
        from ..core.utils import load_json
        return load_json(f"{self.data_folder}/rates.json")
    
    def save_rates(self, rates):
        """Сохраняет курсы."""
        from ..core.utils import save_json
        return save_json(f"{self.data_folder}/rates.json", rates)