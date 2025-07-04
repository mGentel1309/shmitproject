class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        # Новая функция для добавления пользователей
        user = {'name': name, 'email': email}
        self.users.append(user)
        return user
        
    def validate_email(self, email):
        # Исправил баг с валидацией email
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
