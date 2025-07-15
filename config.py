# Настройки для модели в LM Studio
MODEL_CONFIG = {
    "api_url": "http://localhost:1234/v1/chat/completions",
    "model": "claude-3.7-sonnet-reasoning-gemma3-12b",
    "headers": {"Content-Type": "application/json"},
    "temperature": 0.5,
    "max_tokens": 1024
}

# Системный промт (можно изменить под свои задачи)
SYSTEM_PROMPT = """
Ты — AI-ассистент Claude 3.7 Sonnet. Отвечай точно и по делу.
"""
