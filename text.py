# text.py
import sys
import requests
from config import MODEL_CONFIG, SYSTEM_PROMPT

def get_ai_response(user_query: str) -> str:
    """
    Получает ответ от модели через OpenRouter API
    """
    # Check if we should use mock mode for testing (when API key is invalid)

    try:
        response = requests.post(
            url=MODEL_CONFIG["api_url"],
            headers=MODEL_CONFIG["headers"],
            json={
                "model": MODEL_CONFIG["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_query}
                ],
                "temperature": MODEL_CONFIG["temperature"],
                "max_tokens": MODEL_CONFIG["max_tokens"]
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.HTTPError as err:
        if hasattr(err, 'response') and err.response.status_code == 429:
            return "Ошибка: Слишком много запросов (лимит Rate Limit)"
        return f"HTTP ошибка: {err}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    user_input = input()

    response = get_ai_response(user_input)
    print(response)
