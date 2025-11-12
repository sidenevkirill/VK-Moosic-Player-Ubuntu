"""
Конфигурация и настройки приложения
"""

import os
import logging
import subprocess
import sys
from dotenv import load_dotenv

# Попытка импорта GTK
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject, GLib, Pango
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы приложения
APP_NAME = "VK Music Player для Ubuntu"
APP_VERSION = "1.0"
DEFAULT_WINDOW_SIZE = (900, 700)
DOWNLOAD_FOLDER = os.path.expanduser("~/VK_Music_Downloads")

# VK API настройки
VK_API_VERSION = "5.131"
KATE_USER_AGENT = "KateMobileAndroid/51.1-442 (Android 11; SDK 30; arm64-v8a; Samsung SM-G991B; ru_RU)"

def check_dependencies():
    """Проверить зависимости"""
    # Проверяем mplayer для воспроизведения
    try:
        subprocess.run(['which', 'mplayer'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("⚠️  Внимание: mplayer не установлен. Установите его для воспроизведения музыки:")
        print("sudo apt update && sudo apt install mplayer")
    
    # Проверяем python3-gi
    if not GTK_AVAILABLE:
        print("❌ Ошибка: GTK3 не доступен. Установите python3-gi:")
        print("sudo apt update && sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        return False
    
    return True
