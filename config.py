# Конфигурация для auto_commit.py

# URL LM Studio (по умолчанию)
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# Название модели в LM Studio
# Замените на название вашей модели
LM_STUDIO_MODEL = "local-model"

# Альтернативные настройки для разных моделей
# Раскомментируйте нужную:

# Для Llama 3.1 8B
# LM_STUDIO_MODEL = "llama-3.1-8b-instruct"

# Для Qwen 2.5 7B
# LM_STUDIO_MODEL = "qwen2.5-7b-instruct"

# Для DeepSeek Coder
# LM_STUDIO_MODEL = "deepseek-coder-6.7b-instruct"

# Настройки генерации (оптимизировано для детального анализа)
MAX_TOKENS = 60  # Увеличили для более подробных сообщений
TEMPERATURE = 0.2  # Немного больше креативности для разнообразия
TIMEOUT = 30

# Максимальный размер diff для анализа (символы)
MAX_DIFF_SIZE = 4000  # Увеличили для лучшего анализа
