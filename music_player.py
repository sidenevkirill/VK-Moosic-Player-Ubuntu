"""
Класс для управления воспроизведением музыки
"""

import os
import tempfile
import subprocess
import threading
import requests
from config import logger

class MusicPlayer:
    """Класс для управления воспроизведением музыки"""
    def __init__(self):
        self.process = None
        self.current_track = None
        self.is_playing = False
        self.current_position = 0
        self.track_duration = 0
        self.playlist = []
        self.current_index = -1
        self.temp_files = []
        
    def play(self, track_url, track_info=None):
        """Воспроизвести трек"""
        self.stop()
        
        try:
            # Скачиваем трек во временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            self.temp_files.append(temp_filename)
            
            headers = {
                'User-Agent': 'KateMobileAndroid/51.1-442 (Android 11; SDK 30; arm64-v8a; Samsung SM-G991B; ru_RU)',
                'Referer': 'https://vk.com/',
                'Origin': 'https://vk.com'
            }
            
            response = requests.get(track_url, stream=True, headers=headers)
            if response.status_code == 200:
                with open(temp_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Получаем длительность трека
                self.track_duration = track_info.get('duration', 0) if track_info else 0
                
                # Запускаем mplayer в режиме управления
                self.process = subprocess.Popen(
                    ['mplayer', '-slave', '-quiet', '-identify', temp_filename],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Запускаем мониторинг вывода для получения позиции
                self.monitor_thread = threading.Thread(target=self._monitor_player, daemon=True)
                self.monitor_thread.start()
                
                self.is_playing = True
                self.current_track = track_info
                return True, temp_filename
            return False, "Ошибка загрузки"
            
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")
            return False, f"Ошибка воспроизведения: {e}"
    
    def _monitor_player(self):
        """Мониторинг вывода mplayer для получения позиции"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                # Парсим позицию воспроизведения
                if line.startswith('ANS_TIME_POSITION='):
                    try:
                        self.current_position = float(line.split('=')[1].strip())
                    except:
                        pass
                        
            except:
                break
    
    def get_position(self):
        """Получить текущую позицию воспроизведения"""
        return self.current_position
    
    def get_duration(self):
        """Получить длительность трека"""
        return self.track_duration
    
    def seek(self, position):
        """Переместиться к позиции"""
        if self.process and self.is_playing:
            self.process.stdin.write(f"seek {position} 2\n")
            self.process.stdin.flush()
            self.current_position = position
            return True
        return False
    
    def pause(self):
        """Пауза/продолжение воспроизведения"""
        if self.process and self.is_playing:
            self.process.stdin.write("pause\n")
            self.process.stdin.flush()
            self.is_playing = False
            return True
        elif self.process and not self.is_playing:
            self.process.stdin.write("pause\n")
            self.process.stdin.flush()
            self.is_playing = True
            return True
        return False
    
    def stop(self):
        """Остановить воспроизведение"""
        if self.process:
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                self.process.kill()
            finally:
                self.process = None
        
        # Удаляем временные файлы
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.temp_files = []
        
        self.is_playing = False
        self.current_track = None
        self.current_position = 0
        self.track_duration = 0
    
    def set_volume(self, volume):
        """Установить громкость (0-100)"""
        if self.process and self.is_playing:
            # mplayer принимает громкость от 0 до 100
            self.process.stdin.write(f"volume {volume} 1\n")
            self.process.stdin.flush()
    
    def next_track(self):
        """Следующий трек"""
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            return self.playlist[self.current_index]
        return None
    
    def previous_track(self):
        """Предыдущий трек"""
        if self.playlist and self.current_index > 0:
            self.current_index -= 1
            return self.playlist[self.current_index]
        return None
    
    def set_playlist(self, playlist):
        """Установить плейлист"""
        self.playlist = playlist
        self.current_index = -1
    
    def get_current_track_info(self):
        """Получить информацию о текущем треке"""
        return self.current_track
