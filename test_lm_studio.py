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
                        "role": "system",
                        "content": "Ты помощник для создания git коммитов. Отвечай только сообщением коммита, без лишних слов."
                    },
                    {
                        "role": "user",
                        "content": "Создай короткое сообщение коммита: добавлен новый файл test.py. Отвечай ТОЛЬКО текстом коммита, максимум 30 символов."
                    }
                ],
                "max_tokens": 30,
                "temperature": 0.1
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ Подключение успешно!")
            print(f"📝 Сырой ответ модели: '{message}'")
            print(f"📊 Длина ответа: {len(message)} символов")
            
            # Показываем каждый символ для диагностики
            print("🔍 Анализ символов:")
            for i, char in enumerate(message):
                if char == '\n':
                    print(f"  [{i}]: '\\n' (перенос строки)")
                elif char == '\r':
                    print(f"  [{i}]: '\\r' (возврат каретки)")
                elif char == '\t':
                    print(f"  [{i}]: '\\t' (табуляция)")
                elif char == ' ':
                    print(f"  [{i}]: ' ' (пробел)")
                else:
                    print(f"  [{i}]: '{char}'")
            
            return True, message
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к LM Studio")
        print("💡 Убедитесь что:")
        print("   - LM Studio запущен")
        print("   - Сервер включен (Server -> Start Server)")
        print("   - URL правильный (по умолчанию localhost:1234)")
        return False, None
    except requests.exceptions.Timeout:
        print("❌ Тайм-аут подключения")
        print("💡 Проверьте что модель загружена в LM Studio")
        return False, None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False, None

def test_clean_function():
    """Тестирование функции очистки"""
    print("\n🧪 Тестирование функции очистки...")
    
    # Импортируем функцию очистки
    try:
        from auto_commit import clean_commit_message
    except ImportError:
        print("❌ Не удалось импортировать функцию clean_commit_message")
        return
    
    # Тестовые случаи
    test_cases = [
        "think: Добавил новый файл",
        "I think: Добавил новый файл", 
        "Let me think... Добавил новый файл",
        "Думаю, что Добавил новый файл",
        "Добавил новый файл",
        "\"Добавил новый файл\"",
        "'Добавил новый файл'",
        "Сообщение коммита: Добавил новый файл",
        "Коммит: Добавил новый файл",
        "think\nДобавил новый файл",
        "think Добавил новый файл"
    ]
    
    for test_input in test_cases:
        cleaned = clean_commit_message(test_input)
        print(f"Входная строка: '{test_input}'")
        print(f"Очищенная: '{cleaned}'")
        print("---")

if __name__ == "__main__":
    print("🚀 Диагностика проблемы с 'think' в коммитах\n")
    
    # Тест подключения
    success, raw_message = test_lm_studio_connection()
    
    if success and raw_message:
        # Тест очистки
        test_clean_function()
        
        # Применим очистку к полученному сообщению
        try:
            from auto_commit import clean_commit_message
            cleaned = clean_commit_message(raw_message)
            print(f"\n🔧 Результат очистки:")
            print(f"Исходное: '{raw_message}'")
            print(f"Очищенное: '{cleaned}'")
        except ImportError:
            print("❌ Не удалось импортировать функцию очистки")
    else:
        print("\n❌ Не удалось подключиться к LM Studio")
