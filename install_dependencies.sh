#!/bin/bash
echo "Установка зависимостей для VK Music Player..."

# Обновление пакетов
sudo apt update

# Установка системных зависимостей
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests mplayer

# Установка Python зависимостей через pip
pip3 install --user python-dotenv requests

echo "Зависимости установлены!"
