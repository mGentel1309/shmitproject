#!/usr/bin/env python3
"""
Автоматический коммит с генерацией сообщения через LM Studio
"""

import subprocess
import requests
import json
import sys
import os

# Импортируем конфигурацию
try:
    from config import (
        LM_STUDIO_URL, LM_STUDIO_MODEL, MAX_TOKENS, 
        TEMPERATURE, TIMEOUT, MAX_DIFF_SIZE
    )
except ImportError:
    # Значения по умолчанию если config.py не найден
    LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
    LM_STUDIO_MODEL = "local-model"
    MAX_TOKENS = 50
    TEMPERATURE = 0.3
    TIMEOUT = 30
    MAX_DIFF_SIZE = 2000

def run_git_command(command, show_output=False, args_list=None):
    """Выполнить git команду и вернуть результат"""
    try:
        # Если передан список аргументов, используем его (для команд с русским текстом)
        if args_list:
            cmd_args = args_list
        else:
            cmd_args = command.split()
            
        result = subprocess.run(
            cmd_args, 
            capture_output=True, 
            text=True, 
            check=True
        )
        if show_output and result.stdout:
            print(result.stdout)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Ошибка выполнения команды '{command}'"
        if e.stderr:
            error_msg += f"\nОшибка: {e.stderr.strip()}"
        if e.stdout:
            error_msg += f"\nВывод: {e.stdout.strip()}"
        print(error_msg)
        return None

def get_git_diff():
    """Получить diff изменений"""
    # Сначала добавим все изменения в staging
    run_git_command("git add .")
    
    # Получаем diff staged изменений
    diff = run_git_command("git diff --cached")
    if not diff:
        diff = run_git_command("git diff")
    
    return diff

def get_git_status():
    """Получить статус изменений"""
    return run_git_command("git status --porcelain")

def get_file_changes_info():
    """Получить информацию о состоянии файлов"""
    try:
        # Получаем текущее состояние файлов
        current_files = run_git_command("ls -la")
        
        # Получаем список файлов на последнем коммите (без переключения)
        last_commit_files = run_git_command("git ls-tree -r --name-only HEAD")
        
        # Получаем статистику изменений
        file_stats = run_git_command("git diff --stat HEAD")
        
        return {
            'current_files': current_files,
            'last_commit_files': last_commit_files,
            'file_stats': file_stats
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка при получении информации о файлах: {e}")
        return None

def get_changed_files_summary():
    """Получить краткое описание измененных файлов"""
    status = get_git_status()
    if not status:
        return "Нет изменений"
    
    files_info = []
    for line in status.split('\n'):
        if line.strip():
            status_code = line[:2]
            filename = line[3:]
            
            if status_code.strip() == 'A':
                files_info.append(f"Добавлен: {filename}")
            elif status_code.strip() == 'M':
                files_info.append(f"Изменен: {filename}")
            elif status_code.strip() == 'D':
                files_info.append(f"Удален: {filename}")
            elif status_code.strip() == 'R':
                files_info.append(f"Переименован: {filename}")
            elif '?' in status_code:
                files_info.append(f"Новый: {filename}")
    
    return '\n'.join(files_info)

def clean_commit_message(message):
    """Очистить сообщение коммита от лишнего текста"""
    if not message:
        return message
    
    # Убираем кавычки
    message = message.strip('"\'')
    
    # Убираем лишние пробелы
    message = message.strip()
    
    # Убираем теги <think> и </think>
    import re
    message = re.sub(r'</?think>', '', message, flags=re.IGNORECASE)
    message = message.strip()
    
    # Если есть переносы строк, пытаемся найти полезное содержимое
    if '\n' in message:
        lines = message.split('\n')
        # Ищем строку, которая выглядит как коммит (начинается с глагола)
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(('okay', 'the ', 'let me', 'i ', 'user')):
                # Проверяем, что строка начинается с русского глагола
                if any(line.lower().startswith(verb) for verb in ['добавил', 'исправил', 'обновил', 'удалил', 'создал', 'изменил']):
                    message = line
                    break
        else:
            # Если не нашли подходящую строку, берем первую непустую
            for line in lines:
                line = line.strip()
                if line and len(line) > 5:  # Минимальная длина для осмысленного коммита
                    message = line
                    break
    
    # Убираем "think" и подобные слова в начале
    think_patterns = [
        'think:',
        'think ',
        'think\n',
        'i think:',
        'i think ',
        'let me think',
        'думаю:',
        'думаю ',
        'думаю,',
        'я думаю',
        'let me',
        'well,',
        'хорошо,',
        'итак,',
        'okay,',
        'the user',
        'user wants'
    ]
    
    message_lower = message.lower()
    for pattern in think_patterns:
        if message_lower.startswith(pattern):
            message = message[len(pattern):].strip()
            message_lower = message.lower()
            break
    
    # Убираем объяснительные фразы
    cleanup_patterns = [
        'сообщение коммита:',
        'коммит:',
        'ответ:',
        'гит коммит:',
        'git commit:',
        'commit:',
        'git:',
        'я создал',
        'я создам',
        'можно создать',
        'предлагаю',
        'вот сообщение',
        'можно использовать',
        'commit message:',
        'the commit:',
        'here is:',
        'this is:',
        'вот:',
        'это:',
        'wants a',
        'task is to',
        'about the'
    ]
    
    for pattern in cleanup_patterns:
        if message_lower.startswith(pattern):
            message = message[len(pattern):].strip()
            break
    
    # Убираем двоеточие в начале
    message = message.lstrip(':')
    message = message.strip()
    
    # Убираем многоточие в начале
    message = message.lstrip('.')
    message = message.strip()
    
    # Если сообщение все еще содержит мусор, используем fallback
    if len(message) > 100 or any(word in message.lower() for word in ['okay', 'user wants', 'task is', 'let me']):
        # Ищем ключевые слова для автогенерации
        if 'test.py' in message.lower() or 'новый файл' in message.lower():
            message = "Добавил новый файл"
        elif 'add' in message.lower() and 'file' in message.lower():
            message = "Добавил файл"
        else:
            message = "Обновил код"
    
    # Ограничиваем длину
    if len(message) > 50:
        message = message[:47] + '...'
    
    # Убираем точку в конце
    message = message.rstrip('.')
    
    # Если результат пустой или слишком короткий, используем fallback
    if not message or len(message) < 3:
        message = "Обновил код"
    
    return message

def generate_commit_message(diff_content, status_content, files_info=None):
    """Генерировать сообщение коммита через LM Studio"""
    
    # Получаем краткое описание файлов
    files_summary = get_changed_files_summary()
    
    # Дополнительная информация о файлах
    file_context = ""
    if files_info and files_info.get('file_stats'):
        file_context = f"\nСтатистика: {files_info['file_stats']}"
    
    prompt = f"""
Проанализируй изменения в коде и создай КОРОТКОЕ сообщение коммита.

Файлы:
{files_summary}

Изменения:
{status_content}
{file_context}

Diff (отрывок):
{diff_content[:MAX_DIFF_SIZE]}

Важно:
- Отвечай ТОЛЬКО текстом коммита
- Максимум 50 символов
- Начинай с глагола (Добавил/Исправил/Обновил/Удалил)
- Никаких объяснений и комментариев

Пример: Добавил валидацию email
"""

    try:
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
                        "content": prompt
                    }
                ],
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            
            # Очищаем ответ
            message = clean_commit_message(message)
            
            return message
        else:
            print(f"Ошибка LM Studio API: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к LM Studio: {e}")
        return None

def main():
    """Основная функция"""
    print("🚀 Автоматический коммит с LM Studio")
    
    # Проверяем есть ли изменения
    status = get_git_status()
    if not status:
        print("✅ Нет изменений для коммита")
        return
    
    print("📝 Найдены изменения:")
    print(status)
    
    # Получаем diff
    diff = get_git_diff()
    if not diff:
        print("❌ Не удалось получить diff")
        return
    
    # Получаем информацию о файлах
    print("📁 Анализирую изменения файлов...")
    files_info = get_file_changes_info()
    
    print("\n🤖 Генерирую сообщение коммита...")
    
    # Генерируем сообщение коммита с дополнительной информацией
    commit_message = generate_commit_message(diff, status, files_info)
    
    if not commit_message:
        print("❌ Не удалось сгенерировать сообщение коммита")
        fallback_message = input("Введите сообщение коммита вручную: ")
        commit_message = fallback_message if fallback_message else "Автоматический коммит"
    
    print(f"\n📋 Сообщение коммита: '{commit_message}'")
    
    # Подтверждение
    confirm = input("\n❓ Создать коммит? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes', 'д', 'да', '']:
        print("❌ Коммит отменен")
        return
    
    # Создаем коммит (используем список аргументов для правильной работы с русским текстом)
    commit_result = run_git_command(
        "git commit", 
        args_list=["git", "commit", "-m", commit_message]
    )
    if commit_result is not None:
        print("✅ Коммит успешно создан!")
        
        # Спрашиваем про push
        push_confirm = input("🚀 Отправить на удаленный репозиторий? (y/n): ").lower().strip()
        if push_confirm in ['y', 'yes', 'д', 'да', '']:
            # Пробуем разные варианты push
            current_branch = run_git_command("git branch --show-current")
            
            if current_branch:
                print(f"📤 Отправляю ветку '{current_branch}'...")
                # Сначала пробуем git push origin current_branch
                push_result = run_git_command(f"git push origin {current_branch}", show_output=True)
                
                if push_result is not None:
                    print("🎉 Изменения успешно отправлены!")
                else:
                    print("⚠️ Ошибка с указанием ветки, пробую простой push...")
                    # Пробуем простой git push
                    push_result = run_git_command("git push", show_output=True)
                    
                    if push_result is not None:
                        print("🎉 Изменения успешно отправлены!")
                    else:
                        print("❌ Ошибка при отправке изменений")
                        print("💡 Возможные причины:")
                        print("   - Нет настроенного удаленного репозитория")
                        print("   - Нет прав доступа")
                        print("   - Проблемы с SSH ключами")
                        print("   - Нужно сначала сделать 'git push --set-upstream origin main'")
            else:
                print("❌ Не удалось определить текущую ветку")
    else:
        print("❌ Ошибка создания коммита")

if __name__ == "__main__":
    main()
