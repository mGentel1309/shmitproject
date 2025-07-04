#!/bin/bash

# Автоматический коммит с LM Studio
# Использование: ./commit.sh

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Автоматический Git коммит с LM Studio${NC}"

# Проверяем что мы в git репозитории
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Это не Git репозиторий${NC}"
    exit 1
fi

# Проверяем что Python установлен
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 не найден${NC}"
    exit 1
fi

# Проверяем что есть requirements
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 Создаю requirements.txt${NC}"
    echo "requests" > requirements.txt
fi

# Устанавливаем зависимости если нужно
if ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}📦 Устанавливаю зависимости...${NC}"
    pip3 install requests
fi

# Запускаем скрипт
echo -e "${GREEN}🔄 Запуск автоматического коммита...${NC}"
python3 auto_commit.py

echo -e "${GREEN}✅ Готово!${NC}"
