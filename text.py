import requests
import re
from config import (
    LM_STUDIO_URL,
    LM_STUDIO_MODEL,
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    TIMEOUT,
    MAX_DIFF_SIZE
)

def clean_response(text):
    """Удаляет <think> теги и лишние размышления из ответа"""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'\(.*?\)', '', text)  # Удаляем скобочные комментарии
    return text.strip()

def query_model(prompt, user_message, max_retries=3):
    """Отправляет запрос к модели через LM Studio API"""
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

    for attempt in range(max_retries):
        try:
            response = requests.post(
                LM_STUDIO_URL,
                json=payload,
                headers=headers,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return clean_response(result['choices'][0]['message']['content'])

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                return f"Error after {max_retries} attempts: {str(e)}"
            continue

    return "Error: No response from model"

def analyze_code(code_block):
    """Анализирует блок кода с помощью модели"""
    if len(code_block) > MAX_DIFF_SIZE:
        return "Error: Code block exceeds maximum size limit"

    prompt = f"""Проанализируй следующий код и предоставь:
    1. Краткое описание его функциональности
    2. Потенциальные проблемы
    3. Предложения по улучшению

    Код:
    {code_block}"""

    return query_model(SYSTEM_PROMPT, prompt)

def main():

    user_input = input()


    response = query_model(SYSTEM_PROMPT, user_input)
    print(response)

if __name__ == "__main__":
    main()
