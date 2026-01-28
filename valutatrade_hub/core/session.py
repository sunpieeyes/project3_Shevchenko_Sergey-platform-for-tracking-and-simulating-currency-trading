class Session:
    """Хранит текущего пользователя."""
    
    def __init__(self):
        self.current_user = None
    
    def login(self, user):
        """Вход пользователя."""
        self.current_user = user
    
    def logout(self):
        """Выход."""
        self.current_user = None
    
    def is_logged_in(self):
        """Проверяет, вошел ли пользователь."""
        return self.current_user is not None
    
    def get_user_id(self):
        """Получает ID текущего пользователя."""
        if not self.is_logged_in():
            from .exceptions import NotLoggedInError
            raise NotLoggedInError("Сначала войдите в систему")
        
        if self.current_user is None:
            raise NotLoggedInError("Нет текущего пользователя")
        
        return self.current_user.user_id
    
    def get_username(self):
        """Получает имя текущего пользователя."""
        if self.is_logged_in():
            return self.current_user.username
        return None


session = Session()