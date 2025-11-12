#!/usr/bin/env python3
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    print("✅ GTK доступен")
except ImportError as e:
    print(f"❌ Ошибка GTK: {e}")

try:
    import requests
    print("✅ Requests доступен")
except ImportError as e:
    print(f"❌ Ошибка Requests: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv доступен")
except ImportError as e:
    print(f"❌ Ошибка python-dotenv: {e}")

try:
    import subprocess
    subprocess.run(['which', 'mplayer'], check=True, capture_output=True)
    print("✅ mplayer доступен")
except subprocess.CalledProcessError:
    print("❌ mplayer не установлен")
