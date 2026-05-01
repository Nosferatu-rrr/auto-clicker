#!/bin/bash
# Скрипт запуска Auto Clicker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "Виртуальное окружение не найдено. Создаю..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей
echo "Обновление зависимостей..."
pip install -r requirements.txt --upgrade

# Запуск приложения
echo "=================================="
echo "Запуск Auto Clicker..."
echo "Для выхода нажмите Ctrl+C"
echo "=================================="
python3 main.py

# Ожидание перед закрытием (чтобы увидеть ошибки)
echo ""
echo "=================================="
echo "Программа завершена."
echo "Нажмите Enter для выхода..."
read
