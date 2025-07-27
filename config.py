# config.py
# Настройки для модели Moonshot AI Kimi через OpenRouter
MODEL_CONFIG = {
    "api_url": "https://openrouter.ai/api/v1/chat/completions",
    "model": "moonshotai/kimi-k2:free",  # Специфичная модель через OpenRouter
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer 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",
        "HTTP-Referer": "https://github.com/mGentel1309/shmitproject",  # Обязательно для OpenRouter
        "X-Title": "Shmit Voice Assistant"  # Рекомендуется для OpenRouter
    },
    "temperature": 0.5,
    "max_tokens": 1024,
    "use_mock": False  # Set to False to use the real API
}

# Системный промт
SYSTEM_PROMPT = ""
