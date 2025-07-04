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
    file_types = {'added': [], 'modified': [], 'deleted': [], 'renamed': [], 'new': []}
    
    for line in status.split('\n'):
        if line.strip():
            status_code = line[:2]
            filename = line[3:]
            
            if status_code.strip() == 'A':
                file_types['added'].append(filename)
            elif status_code.strip() == 'M':
                file_types['modified'].append(filename)
            elif status_code.strip() == 'D':
                file_types['deleted'].append(filename)
            elif status_code.strip() == 'R':
                file_types['renamed'].append(filename)
            elif '?' in status_code:
                file_types['new'].append(filename)
    
    # Создаем более структурированное описание
    summary_parts = []
    if file_types['new']:
        summary_parts.append(f"Новые файлы: {', '.join(file_types['new'])}")
    if file_types['added']:
        summary_parts.append(f"Добавлены: {', '.join(file_types['added'])}")
    if file_types['modified']:
        summary_parts.append(f"Изменены: {', '.join(file_types['modified'])}")
    if file_types['deleted']:
        summary_parts.append(f"Удалены: {', '.join(file_types['deleted'])}")
    if file_types['renamed']:
        summary_parts.append(f"Переименованы: {', '.join(file_types['renamed'])}")
    
    return '\n'.join(summary_parts), file_types

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
    
    # Ограничиваем длину
    if len(message) > 50:
        message = message[:47] + '...'
    
    # Убираем точку в конце
    message = message.rstrip('.')
    
    # Если результат пустой или слишком короткий, возвращаем None для fallback
    if not message or len(message) < 3:
        return None
    
    return message

def analyze_file_content_changes(diff_content):
    """Анализировать содержимое изменений в файлах"""
    if not diff_content:
        return {}
    
    analysis = {
        'functions_added': [],
        'functions_modified': [],
        'functions_removed': [],
        'classes_added': [],
        'classes_modified': [],
        'imports_added': [],
        'imports_removed': [],
        'variables_added': [],
        'comments_added': [],
        'lines_added': 0,
        'lines_removed': 0,
        'files_changed': [],
        'config_changes': [],
        'style_changes': [],
        'test_changes': [],
        'bug_fixes': [],
        'features': []
    }
    
    lines = diff_content.split('\n')
    current_file = None
    
    for line in lines:
        # Определяем текущий файл
        if line.startswith('diff --git') or line.startswith('+++'):
            if 'b/' in line:
                current_file = line.split('b/')[-1].strip()
                if current_file not in analysis['files_changed']:
                    analysis['files_changed'].append(current_file)
        
        # Считаем добавленные и удаленные строки
        if line.startswith('+') and not line.startswith('+++'):
            analysis['lines_added'] += 1
            line_content = line[1:].strip()
            
            # Анализируем добавленные строки
            if line_content:
                # Функции
                if line_content.startswith('def ') and '(' in line_content:
                    func_name = line_content.split('def ')[1].split('(')[0].strip()
                    analysis['functions_added'].append(func_name)
                elif line_content.startswith('function ') and '(' in line_content:
                    func_name = line_content.split('function ')[1].split('(')[0].strip()
                    analysis['functions_added'].append(func_name)
                
                # Классы
                elif line_content.startswith('class '):
                    class_name = line_content.split('class ')[1].split('(')[0].split(':')[0].strip()
                    analysis['classes_added'].append(class_name)
                
                # Импорты
                elif line_content.startswith('import ') or line_content.startswith('from '):
                    analysis['imports_added'].append(line_content)
                
                # Переменные и константы
                elif '=' in line_content and not line_content.startswith('#'):
                    var_name = line_content.split('=')[0].strip()
                    if var_name.isupper():  # Константы
                        analysis['variables_added'].append(var_name)
                
                # Комментарии
                elif line_content.startswith('#') or line_content.startswith('//'):
                    analysis['comments_added'].append(line_content)
                
                # Анализ ключевых слов
                line_lower = line_content.lower()
                
                # Исправления багов
                if any(word in line_lower for word in ['fix', 'bug', 'error', 'исправ', 'ошибк', 'баг']):
                    analysis['bug_fixes'].append(line_content)
                
                # Новые фичи
                elif any(word in line_lower for word in ['feature', 'add', 'new', 'нов', 'добав', 'функция']):
                    analysis['features'].append(line_content)
                
                # Конфигурация
                elif any(word in line_lower for word in ['config', 'setting', 'env', 'конфиг', 'настройк']):
                    analysis['config_changes'].append(line_content)
                
                # Стили
                elif any(word in line_lower for word in ['style', 'css', 'color', 'font', 'margin', 'padding', 'стиль']):
                    analysis['style_changes'].append(line_content)
                
                # Тесты
                elif any(word in line_lower for word in ['test', 'assert', 'expect', 'тест']):
                    analysis['test_changes'].append(line_content)
        
        elif line.startswith('-') and not line.startswith('---'):
            analysis['lines_removed'] += 1
            line_content = line[1:].strip()
            
            # Анализируем удаленные строки
            if line_content.startswith('def ') and '(' in line_content:
                func_name = line_content.split('def ')[1].split('(')[0].strip()
                analysis['functions_removed'].append(func_name)
            elif line_content.startswith('import ') or line_content.startswith('from '):
                analysis['imports_removed'].append(line_content)
    
    return analysis

def generate_smart_commit_message(analysis, file_types):
    """Генерировать умное сообщение коммита на основе анализа содержимого"""
    
    # Приоритетные сообщения на основе содержимого
    
    # 1. Исправления багов (максимальный приоритет)
    if analysis['bug_fixes']:
        if len(analysis['bug_fixes']) == 1:
            return "Исправил ошибку"
        else:
            return f"Исправил {len(analysis['bug_fixes'])} ошибок"
    
    # 2. Новые функции и классы
    if analysis['functions_added']:
        if len(analysis['functions_added']) == 1:
            func_name = analysis['functions_added'][0]
            if len(func_name) < 20:  # Если имя короткое
                return f"Добавил функцию {func_name}"
            else:
                return "Добавил новую функцию"
        else:
            return f"Добавил {len(analysis['functions_added'])} функций"
    
    if analysis['classes_added']:
        if len(analysis['classes_added']) == 1:
            class_name = analysis['classes_added'][0]
            if len(class_name) < 20:
                return f"Добавил класс {class_name}"
            else:
                return "Добавил новый класс"
        else:
            return f"Добавил {len(analysis['classes_added'])} классов"
    
    # 3. Удаления
    if analysis['functions_removed']:
        if len(analysis['functions_removed']) == 1:
            return f"Удалил функцию {analysis['functions_removed'][0]}"
        else:
            return f"Удалил {len(analysis['functions_removed'])} функций"
    
    # 4. Импорты
    if analysis['imports_added'] and not analysis['imports_removed']:
        return "Добавил импорты"
    elif analysis['imports_removed'] and not analysis['imports_added']:
        return "Удалил импорты"
    elif analysis['imports_added'] and analysis['imports_removed']:
        return "Обновил импорты"
    
    # 5. Специальные типы изменений
    if analysis['test_changes']:
        return "Обновил тесты"
    
    if analysis['config_changes']:
        return "Обновил конфигурацию"
    
    if analysis['style_changes']:
        return "Обновил стили"
    
    # 6. Общие фичи
    if analysis['features']:
        return "Добавил новые возможности"
    
    # 7. По статистике строк
    if analysis['lines_added'] > analysis['lines_removed'] * 3:  # Много добавлено
        return f"Добавил {analysis['lines_added']} строк кода"
    elif analysis['lines_removed'] > analysis['lines_added'] * 2:  # Много удалено
        return f"Удалил {analysis['lines_removed']} строк кода"
    
    # 8. По типам файлов (как fallback)
    return generate_fallback_commit_message(file_types, "")

def generate_fallback_commit_message(file_types, diff_content):
    """Генерировать fallback сообщение коммита на основе анализа файлов"""
    
    # Анализируем типы изменений
    total_files = sum(len(files) for files in file_types.values())
    
    if file_types['new']:
        # Новые файлы - анализируем что добавлено
        new_files = file_types['new']
        
        if any('.py' in f for f in new_files):
            return "Добавил Python скрипты"
        elif any('.js' in f or '.ts' in f for f in new_files):
            return "Добавил JavaScript файлы"
        elif any('.html' in f for f in new_files):
            return "Добавил HTML страницы"
        elif any('.css' in f for f in new_files):
            return "Добавил стили CSS"
        elif any('.md' in f for f in new_files):
            return "Добавил документацию"
        elif any('.json' in f for f in new_files):
            return "Добавил конфигурационные файлы"
        elif any('test' in f.lower() for f in new_files):
            return "Добавил тесты"
        else:
            if len(new_files) == 1:
                return f"Добавил {new_files[0]}"
            else:
                return f"Добавил {len(new_files)} новых файлов"
    
    elif file_types['modified']:
        # Изменены существующие файлы - анализируем diff
        modified_files = file_types['modified']
        
        if diff_content:
            # Анализируем содержимое diff
            diff_lower = diff_content.lower()
            
            if 'def ' in diff_lower or 'function' in diff_lower:
                return "Обновил функции"
            elif 'class ' in diff_lower:
                return "Обновил классы"
            elif 'import ' in diff_lower or 'from ' in diff_lower:
                return "Обновил импорты"
            elif 'config' in diff_lower or 'settings' in diff_lower:
                return "Обновил конфигурацию"
            elif 'test' in diff_lower:
                return "Обновил тесты"
            elif 'fix' in diff_lower or 'bug' in diff_lower or 'error' in diff_lower:
                return "Исправил ошибки"
            elif any(word in diff_lower for word in ['style', 'css', 'color', 'font']):
                return "Обновил стили"
            elif any(word in diff_lower for word in ['readme', 'doc', 'comment']):
                return "Обновил документацию"
        
        # Анализируем по типам файлов
        if any('.py' in f for f in modified_files):
            return "Обновил Python код"
        elif any('.js' in f or '.ts' in f for f in modified_files):
            return "Обновил JavaScript код"
        elif any('.html' in f for f in modified_files):
            return "Обновил HTML разметку"
        elif any('.css' in f for f in modified_files):
            return "Обновил стили"
        elif any('.md' in f for f in modified_files):
            return "Обновил документацию"
        elif any('.json' in f for f in modified_files):
            return "Обновил конфигурацию"
        else:
            if len(modified_files) == 1:
                return f"Обновил {modified_files[0]}"
            else:
                return f"Обновил {len(modified_files)} файлов"
    
    elif file_types['deleted']:
        deleted_files = file_types['deleted']
        if len(deleted_files) == 1:
            return f"Удалил {deleted_files[0]}"
        else:
            return f"Удалил {len(deleted_files)} файлов"
    
    elif file_types['renamed']:
        return "Переименовал файлы"
    
    # Общий fallback
    return "Обновил код"

def generate_commit_message(diff_content, status_content, files_info=None):
    """Генерировать сообщение коммита через LM Studio"""
    
    # Получаем краткое описание файлов
    files_summary, file_types = get_changed_files_summary()
    
    # Дополнительная информация о файлах
    file_context = ""
    if files_info and files_info.get('file_stats'):
        file_context = f"\nСтатистика: {files_info['file_stats']}"
    
    prompt = f"""
Анализируя git diff, создай короткое сообщение коммита на русском языке.

Файлы:
{files_summary}

Изменения:
{status_content}
{file_context}

Diff (первые символы):
{diff_content[:MAX_DIFF_SIZE]}

Требования:
1. ТОЛЬКО текст коммита, без объяснений
2. Максимум 50 символов
3. Начинай с глагола: Добавил/Исправил/Обновил/Удалил/Создал
4. На русском языке

Примеры хороших коммитов:
- Добавил функцию расчета
- Исправил ошибку валидации
- Обновил конфигурацию API
- Удалил неиспользуемые файлы

Отвечай ТОЛЬКО сообщением коммита:
"""

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты генератор git коммитов. Отвечай СТРОГО ТОЛЬКО сообщением коммита на русском языке. Начинай с глагола (Добавил/Исправил/Обновил/Удалил). Максимум 50 символов. Никаких объяснений, предисловий или комментариев."
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
            cleaned_message = clean_commit_message(message)
            
            # Если очистка не дала результата, используем fallback
            if not cleaned_message:
                return generate_fallback_commit_message(file_types, diff_content)
            
            return cleaned_message
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
    
    # Сначала пробуем умный анализ содержимого
    print("🔍 Анализирую содержимое изменений...")
    content_analysis = analyze_file_content_changes(diff)
    
    # Получаем типы файлов
    _, file_types = get_changed_files_summary()
    
    # Пробуем сгенерировать умное сообщение на основе анализа
    smart_message = generate_smart_commit_message(content_analysis, file_types)
    
    if smart_message and smart_message != "Обновил код":
        print(f"✨ Создал сообщение на основе анализа содержимого")
        commit_message = smart_message
    else:
        # Если умный анализ не дал результата, пробуем LM Studio
        print("🤖 Генерирую сообщение через LM Studio...")
        commit_message = generate_commit_message(diff, status, files_info)
        
        if not commit_message:
            print("❌ Не удалось сгенерировать сообщение коммита")
            print("📊 Статистика анализа:")
            print(f"   - Функций добавлено: {len(content_analysis.get('functions_added', []))}")
            print(f"   - Классов добавлено: {len(content_analysis.get('classes_added', []))}")
            print(f"   - Строк добавлено: {content_analysis.get('lines_added', 0)}")
            print(f"   - Строк удалено: {content_analysis.get('lines_removed', 0)}")
            
            fallback_message = input("Введите сообщение коммита вручную: ")
            commit_message = fallback_message if fallback_message else smart_message
    
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
