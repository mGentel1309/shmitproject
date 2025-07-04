#!/usr/bin/env python3
"""
Тест подключения к LM Studio
"""

import requests
import json

# Импортируем конфигурацию
try:
    from config import LM_STUDIO_URL, LM_STUDIO_MODEL, TIMEOUT
except ImportError:
    LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
    LM_STUDIO_MODEL = "local-model"
    TIMEOUT = 30

# Импортируем функцию очистки
try:
    from auto_commit import clean_commit_message
except ImportError:
    def clean_commit_message(message):
        return message.strip('"\'')

def test_lm_studio_connection():
    """Тестирование подключения к LM Studio"""
    print("🧪 Тестирование подключения к LM Studio...")
    print(f"URL: {LM_STUDIO_URL}")
    print(f"Модель: {LM_STUDIO_MODEL}")
    
    try:
        # Простой тестовый запрос
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": "Привет! Ответь одним словом: работает?"
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            print(f"✅ Подключение успешно!")
            print(f"📝 Ответ модели: {message}")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к LM Studio")
        print("💡 Убедитесь что:")
        print("   - LM Studio запущен")
        print("   - Сервер включен (Server -> Start Server)")
        print("   - URL правильный (по умолчанию localhost:1234)")
        return False
    except requests.exceptions.Timeout:
        print("❌ Тайм-аут подключения")
        print("💡 Проверьте что модель загружена в LM Studio")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_commit_generation():
    """Тестирование генерации коммита"""
    print("\n🧪 Тестирование генерации коммита...")
    
    # Пример diff для тестирования
    test_diff = """
+++ b/test.py
@@ -1,3 +1,5 @@
 def hello():
+    # Добавил комментарий
     print("Hello")
+    return True
"""
    
    test_status = "M  test.py"
    
    try:
        prompt = f"""
Создай короткое сообщение коммита на русском.

Изменения: {test_status}
Код: {test_diff}

Отвечай ТОЛЬКО текстом коммита:
- Максимум 30 символов
- Начинай с глагола
- Никаких объяснений

Пример: Добавил комментарий
"""
        
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты помощник для создания git коммитов. Отвечай только сообщением коммита, без лишних слов."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.3
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            
            # Очищаем сообщение
            message = clean_commit_message(message)
            
            print(f"✅ Генерация успешна!")
            print(f"📝 Сообщение коммита: '{message}'")
            print(f"📊 Длина: {len(message)} символов")
            return True
        else:
            print(f"❌ Ошибка генерации: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при генерации коммита: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование LM Studio для автоматических коммитов\n")
    
    # Тест подключения
    if not test_lm_studio_connection():
        print("\n❌ Тест подключения провален")
        return
    
    # Тест генерации коммита
    if not test_commit_generation():
        print("\n❌ Тест генерации коммита провален")
        return
    
    print("\n🎉 Все тесты пройдены успешно!")
    print("✅ Можно использовать auto_commit.py")

if __name__ == "__main__":
    main()
