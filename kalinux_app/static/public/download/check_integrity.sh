#!/bin/bash

# Скрипт проверки целостности Kalinux Security
# Автор: Kalinux
# Версия: 1.0

echo "=== Kalinux Security: Проверка целостности ==="

USERNAME=/home/
# Проверка наличия файла пакета
PACKAGE_PATH="/home/$USERNAME/kalinux_security"

if [ ! -d "$PACKAGE_PATH" ]; then
    echo "Ошибка: Пакет Kalinux Security не найден в $PACKAGE_PATH"
    exit 1
fi

# Хэш-сумма эталонного пакета
EXPECTED_HASH="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Вычисление текущей хэш-суммы
CURRENT_HASH=$(find "$PACKAGE_PATH" -type f -exec sha256sum {} + | sort | sha256sum | awk '{print $1}')

if [ "$CURRENT_HASH" == "$EXPECTED_HASH" ]; then
    echo "Целостность пакета подтверждена."
    exit 0
else
    echo "Ошибка: Целостность пакета нарушена!"
    exit 1
fi
