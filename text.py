import requests
import re
from config import (
    LM_STUDIO_URL,
    LM_STUDIO_MODEL,
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    TIMEOUT
)

def clean_response(text):
    """Очищает ответ от служебных тегов и лишних пробелов"""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)  # Удаляем теги размышлений
    text = re.sub(r'[\s]+', ' ', text)  # Нормализуем пробелы
    return text.strip()

def get_model_response(user_message):
    """Получает ответ от модели через API"""
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "stream": False
    }

    try:
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",  # Используем базовый URL из конфига
            json=payload,
            headers=headers,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()

        if 'choices' in result and result['choices']:
            return clean_response(result['choices'][0]['message']['content'])

        return "Ошибка: пустой ответ от модели"

    except requests.exceptions.RequestException as e:
        return f"Ошибка соединения: {str(e)}"
    except Exception as e:
        return f"Неожиданная ошибка: {str(e)}"

if __name__ == "__main__":
    # Пример использования
    user_input = input()
    response = get_model_response(user_input)
    print(response)
