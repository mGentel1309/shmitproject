import requests
from config import MODEL_CONFIG, SYSTEM_PROMPT

def get_ai_response(user_query: str) -> str:
    """
    Получает ответ от модели на входной запрос.
    Возвращает только текст ответа или сообщение об ошибке.
    """
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

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    user_input = input()
    response = get_ai_response(user_input)
    print(response)
