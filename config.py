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
