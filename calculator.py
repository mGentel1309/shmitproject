def calculate_total(items):
    """Новая функция для подсчета общей суммы"""
    total = 0
    for item in items:
        total += item.get('price', 0)
    return total

def format_currency(amount):
    """Функция форматирования валюты"""
    return f"${amount:.2f}"

def calculate_tax(amount, rate=0.1):
    """Расчет налога от суммы"""
    return amount * rate

