#!/usr/bin/env python3
"""
VK Music Player для Ubuntu
Главный файл приложения
"""

import sys
import subprocess
from config import check_dependencies
from ui import VKMusicApp

def main():
    """Главная функция"""
    print("🎵 VK Music Player для Ubuntu")
    print("=" * 40)
    
    if not check_dependencies():
        sys.exit(1)
    
    app = VKMusicApp()
    app.run()

if __name__ == "__main__":
    main()
