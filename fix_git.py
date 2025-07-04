#!/usr/bin/env python3
"""
Диагностика и исправление проблем с Git push
"""

import subprocess
import sys

def run_command(command, capture=True):
    """Выполнить команду"""
    try:
        if capture:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip(), True
        else:
            result = subprocess.run(command.split(), check=True)
            return "", True
    except subprocess.CalledProcessError as e:
        if capture and e.stderr:
            return e.stderr.strip(), False
        return str(e), False

def check_git_status():
    """Проверить статус Git"""
    print("🔍 Проверяю статус Git...")
    
    # Проверяем, что мы в Git репозитории
    output, success = run_command("git status")
    if not success:
        print("❌ Это не Git репозиторий")
        return False
    
    print("✅ Git репозиторий найден")
    
    # Проверяем текущую ветку
    branch, success = run_command("git branch --show-current")
    if success and branch:
        print(f"📌 Текущая ветка: {branch}")
    else:
        print("⚠️ Не удалось определить текущую ветку")
    
    return True

def check_remote():
    """Проверить удаленные репозитории"""
    print("\n🌐 Проверяю удаленные репозитории...")
    
    remotes, success = run_command("git remote -v")
    if not success or not remotes:
        print("❌ Нет настроенных удаленных репозиториев")
        return False
    
    print("✅ Найдены удаленные репозитории:")
    print(remotes)
    
    return True

def check_upstream():
    """Проверить upstream ветку"""
    print("\n🔗 Проверяю upstream ветку...")
    
    branch, success = run_command("git branch --show-current")
    if not success:
        print("❌ Не удалось определить текущую ветку")
        return False
    
    upstream, success = run_command(f"git rev-parse --abbrev-ref {branch}@{{upstream}}")
    if not success:
        print(f"⚠️ Ветка '{branch}' не имеет upstream")
        return False
    
    print(f"✅ Upstream ветка: {upstream}")
    return True

def test_push():
    """Тестировать push"""
    print("\n🚀 Тестирую push...")
    
    # Пробуем dry-run push
    output, success = run_command("git push --dry-run")
    if success:
        print("✅ Push должен работать")
        print(f"Результат: {output}")
        return True
    else:
        print("❌ Проблемы с push:")
        print(output)
        return False

def fix_upstream():
    """Исправить upstream"""
    print("\n🔧 Попытка исправить upstream...")
    
    branch, success = run_command("git branch --show-current")
    if not success:
        print("❌ Не удалось определить текущую ветку")
        return False
    
    # Пробуем установить upstream
    print(f"Устанавливаю upstream для ветки '{branch}'...")
    output, success = run_command(f"git push --set-upstream origin {branch}")
    
    if success:
        print("✅ Upstream успешно установлен!")
        return True
    else:
        print(f"❌ Ошибка установки upstream: {output}")
        return False

def check_auth():
    """Проверить аутентификацию"""
    print("\n🔐 Проверяю аутентификацию...")
    
    # Пробуем fetch для проверки доступа
    output, success = run_command("git fetch --dry-run")
    if success:
        print("✅ Аутентификация работает")
        return True
    else:
        print("❌ Проблемы с аутентификацией:")
        print(output)
        print("\n💡 Возможные решения:")
        print("1. Настройте SSH ключи: ssh-keygen -t ed25519 -C 'your_email@example.com'")
        print("2. Добавьте ключ в GitHub: cat ~/.ssh/id_ed25519.pub")
        print("3. Или используйте HTTPS с токеном")
        return False

def main():
    """Основная функция диагностики"""
    print("🩺 Диагностика проблем с Git push\n")
    
    if not check_git_status():
        return
    
    has_remote = check_remote()
    has_upstream = check_upstream()
    auth_works = check_auth()
    
    if not has_remote:
        print("\n🔧 Нужно добавить удаленный репозиторий:")
        print("git remote add origin https://github.com/username/repo.git")
        return
    
    if not auth_works:
        print("\n🔧 Сначала исправьте проблемы с аутентификацией")
        return
    
    if not has_upstream:
        if input("\n❓ Установить upstream для текущей ветки? (y/n): ").lower().strip() in ['y', 'yes', 'д', 'да']:
            fix_upstream()
    
    # Финальный тест
    print("\n🧪 Финальный тест push...")
    if test_push():
        print("\n🎉 Git push готов к работе!")
    else:
        print("\n❌ Все еще есть проблемы с push")
        print("\n💡 Попробуйте:")
        print("1. git push --set-upstream origin main")
        print("2. Проверьте права доступа к репозиторию")
        print("3. Убедитесь что SSH ключи настроены правильно")

if __name__ == "__main__":
    main()
