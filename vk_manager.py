"""
Класс для работы с VK API
"""

import os
import requests
from config import logger, DOWNLOAD_FOLDER, VK_API_VERSION, KATE_USER_AGENT

class VKMusicManager:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.user_info = None
        self.kate_user_agent = KATE_USER_AGENT
        self.headers = {
            'User-Agent': self.kate_user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }
        self.download_folder = DOWNLOAD_FOLDER
        self.create_download_folder()

    def create_download_folder(self):
        """Создать папку для загрузок если её нет"""
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

    def set_token(self, token):
        """Установить токен"""
        self.token = token
        if token and '.' in token:
            parts = token.split('.')
            if len(parts) > 0:
                try:
                    self.user_id = int(parts[0])
                except ValueError:
                    self.user_id = None
        else:
            self.user_id = None

    def load_token_from_file(self, filename='vk_token.txt'):
        """Загрузить токен из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        self.set_token(token)
                        return True, "Токен загружен из файла"
            return False, "Файл не найден или пуст"
        except Exception as e:
            return False, f"Ошибка при чтении файла: {e}"

    def save_token_to_file(self, filename='vk_token.txt'):
        """Сохранить токен в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.token)
            return True, "Токен сохранен в файл"
        except Exception as e:
            return False, f"Ошибка при сохранении токена: {e}"

    def check_token_validity(self):
        """Проверить валидность токена"""
        if not self.token:
            return {"valid": False, "error_msg": "Токен не установлен"}
        
        url = "https://api.vk.com/method/users.get"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "fields": "first_name,last_name"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                self.user_info = data["response"][0]
                self.user_id = self.user_info.get('id')
                return {"valid": True, "user_info": self.user_info}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"valid": False, "error_msg": error_msg}
                
        except Exception as e:
            return {"valid": False, "error_msg": f"Ошибка запроса: {e}"}

    def get_my_audio_list(self, offset=0, count=200):
        """Получить список аудиозаписей с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "count": count,
            "offset": offset,
            "owner_id": self.user_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "audio_list": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_all_my_audio(self, progress_callback=None):
        """Получить все аудиозаписи пользователя с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        all_audio = []
        offset = 0
        count = 200
        
        # Сначала получаем первую страницу чтобы узнать общее количество
        first_result = self.get_my_audio_list(offset=0, count=1)
        if not first_result["success"]:
            return first_result
        
        total_count = first_result["total_count"]
        
        while offset < total_count:
            if progress_callback:
                progress_callback(offset, total_count)
                
            result = self.get_my_audio_list(offset=offset, count=count)
            if not result["success"]:
                return result
            
            audio_list = result["audio_list"]
            all_audio.extend(audio_list)
            offset += count
            
            # Если загрузили все треки, выходим
            if len(audio_list) < count:
                break
        
        return {
            "success": True, 
            "audio_list": all_audio,
            "total_count": total_count
        }

    def get_recommendations(self, offset=0, count=100):
        """Получить рекомендации"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        # Пробуем метод audio.getRecommendations
        url = "https://api.vk.com/method/audio.getRecommendations"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "count": count,
            "offset": offset,
            "shuffle": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "audio_list": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                # Если метод не доступен, используем популярную музыку
                return self.get_popular_music(offset, count)
                
        except Exception as e:
            # В случае ошибки используем популярную музыку
            return self.get_popular_music(offset, count)

    def get_popular_music(self, offset=0, count=100):
        """Получить популярную музыку"""
        popular_queries = [
            "популярные песни 2024", "хиты", "top hits", "новинки музыки",
            "русские хиты", "зарубежные хиты", "топ чарт", "billboard top 100"
        ]
        
        import random
        query = random.choice(popular_queries)
        
        url = "https://api.vk.com/method/audio.search"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "q": query,
            "count": count,
            "offset": offset,
            "auto_complete": 1,
            "sort": 2  # Сортировка по популярности
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "audio_list": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_playlists(self, offset=0, count=200):
        """Получить список плейлистов с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.getPlaylists"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "owner_id": self.user_id,
            "count": count,
            "offset": offset
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "playlists": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_all_playlists(self, progress_callback=None):
        """Получить все плейлисты с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        all_playlists = []
        offset = 0
        count = 200
        
        first_result = self.get_playlists(offset=0, count=1)
        if not first_result["success"]:
            return first_result
        
        total_count = first_result["total_count"]
        
        while offset < total_count:
            if progress_callback:
                progress_callback(offset, total_count)
                
            result = self.get_playlists(offset=offset, count=count)
            if not result["success"]:
                return result
            
            playlists = result["playlists"]
            all_playlists.extend(playlists)
            offset += count
            
            if len(playlists) < count:
                break
        
        return {
            "success": True, 
            "playlists": all_playlists,
            "total_count": total_count
        }

    def get_playlist_tracks(self, playlist_id, offset=0, count=200):
        """Получить треки из плейлиста с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "album_id": playlist_id,
            "owner_id": self.user_id,
            "count": count,
            "offset": offset
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "audio_list": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_all_playlist_tracks(self, playlist_id, progress_callback=None):
        """Получить все треки из плейлиста с пагинацией"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен"}
        
        all_audio = []
        offset = 0
        count = 200
        
        first_result = self.get_playlist_tracks(playlist_id, offset=0, count=1)
        if not first_result["success"]:
            return first_result
        
        total_count = first_result["total_count"]
        
        while offset < total_count:
            if progress_callback:
                progress_callback(offset, total_count)
                
            result = self.get_playlist_tracks(playlist_id, offset=offset, count=count)
            if not result["success"]:
                return result
            
            audio_list = result["audio_list"]
            all_audio.extend(audio_list)
            offset += count
            
            if len(audio_list) < count:
                break
        
        return {
            "success": True, 
            "audio_list": all_audio,
            "total_count": total_count
        }

    def search_audio(self, query, offset=0, count=200):
        """Поиск музыки с пагинацией"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.search"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "q": query,
            "count": count,
            "offset": offset,
            "auto_complete": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "results": data["response"]["items"],
                    "total_count": data["response"]["count"],
                    "offset": offset
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def search_all_audio(self, query, max_results=1000, progress_callback=None):
        """Поиск музыки с пагинацией (все результаты)"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        all_results = []
        offset = 0
        count = 200
        
        first_result = self.search_audio(query, offset=0, count=1)
        if not first_result["success"]:
            return first_result
        
        total_count = min(first_result["total_count"], max_results)
        
        while offset < total_count:
            if progress_callback:
                progress_callback(offset, total_count)
                
            result = self.search_audio(query, offset=offset, count=count)
            if not result["success"]:
                return result
            
            results_page = result["results"]
            all_results.extend(results_page)
            offset += count
            
            if len(results_page) < count:
                break
        
        return {
            "success": True, 
            "results": all_results,
            "total_count": total_count
        }

    def download_track(self, track, folder=None):
        """Скачать трек"""
        if not folder:
            folder = self.download_folder
        
        artist = track.get('artist', 'Unknown Artist')
        title = track.get('title', 'Unknown Title')
        
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        
        filename = f"{safe_artist} - {safe_title}.mp3"
        filepath = os.path.join(folder, filename)
        
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            name, ext = os.path.splitext(original_filepath)
            filepath = f"{name} ({counter}){ext}"
            counter += 1
        
        track_url = track.get('url')
        if not track_url:
            return False, "Нет ссылки для скачивания"
        
        try:
            headers = self.headers.copy()
            headers.update({
                'Referer': 'https://vk.com/',
                'Origin': 'https://vk.com'
            })
            
            response = requests.get(track_url, stream=True, headers=headers)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return True, filepath
            else:
                return False, f"Ошибка HTTP: {response.status_code}"
                
        except Exception as e:
            return False, f"Ошибка скачивания: {e}"
