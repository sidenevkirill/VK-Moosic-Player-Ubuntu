"""
Главный класс GUI приложения
"""

import os
import threading
import subprocess
from config import GTK_AVAILABLE, APP_NAME, DEFAULT_WINDOW_SIZE, logger
from music_player import MusicPlayer
from vk_manager import VKMusicManager
from widgets import create_tracks_treeview, create_playlists_treeview, create_downloads_treeview

if GTK_AVAILABLE:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject, GLib, Pango

class VKMusicApp:
    def __init__(self):
        self.manager = VKMusicManager()
        self.player = MusicPlayer()
        self.current_tracks = []
        self.current_playlist = None
        self.current_track_index = -1
        self.loading_more = False
        
        # Создание главного окна
        self.window = Gtk.Window(title=APP_NAME)
        self.window.set_default_size(*DEFAULT_WINDOW_SIZE)
        self.window.set_border_width(10)
        self.window.connect("destroy", self.on_destroy)
        
        # Главный контейнер
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(main_box)
        
        # Заголовок
        # header = Gtk.Label()
        # header.set_markup("<span size='x-large' weight='bold'>🎵 VK Music Player</span>")
        # main_box.pack_start(header, False, False, 0)
        
        # Панель управления плеером
        self.create_player_controls(main_box)
        
        # Статус бар
        self.status_bar = Gtk.Statusbar()
        main_box.pack_end(self.status_bar, False, False, 0)
        
        # Ноутбук с вкладками
        notebook = Gtk.Notebook()
        main_box.pack_start(notebook, True, True, 0)
        
        # Вкладка авторизации
        self.create_auth_tab(notebook)
        
        # Вкладка музыки
        self.create_music_tab(notebook)
        
        # Вкладка плейлистов
        self.create_playlists_tab(notebook)
        
        # Вкладка поиска
        self.create_search_tab(notebook)
        
        # Вкладка рекомендаций
        self.create_recommendations_tab(notebook)
        
        # Вкладка загрузок
        self.create_downloads_tab(notebook)
        
        # Вкладка о программе
        self.create_about_tab(notebook)
        
        # Запуск обновления статуса плеера
        GLib.timeout_add(1000, self.update_player_status)

    def create_player_controls(self, parent):
        """Панель управления плеером"""
        player_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        player_box.set_margin_bottom(10)
        parent.pack_start(player_box, False, False, 0)
        
        # Текущий трек
        self.current_track_label = Gtk.Label()
        self.current_track_label.set_markup("<b>Трек не выбран</b>")
        self.current_track_label.set_ellipsize(Pango.EllipsizeMode.END)
        player_box.pack_start(self.current_track_label, False, False, 0)
        
        # Ползунок прогресса
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        player_box.pack_start(progress_box, False, False, 0)
        
        self.position_label = Gtk.Label(label="0:00")
        self.position_label.set_size_request(40, -1)
        progress_box.pack_start(self.position_label, False, False, 0)
        
        self.progress_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress_scale.set_draw_value(False)
        self.progress_scale.set_hexpand(True)
        self.progress_scale.connect("button-release-event", self.on_seek)
        progress_box.pack_start(self.progress_scale, True, True, 0)
        
        self.duration_label = Gtk.Label(label="0:00")
        self.duration_label.set_size_request(40, -1)
        progress_box.pack_start(self.duration_label, False, False, 0)
        
        # Кнопки управления
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        player_box.pack_start(controls_box, False, False, 0)
        
        # Предыдущий трек
        self.prev_btn = Gtk.Button.new_from_icon_name("media-skip-backward", Gtk.IconSize.BUTTON)
        self.prev_btn.connect("clicked", self.on_previous_track)
        self.prev_btn.set_tooltip_text("Предыдущий трек")
        controls_box.pack_start(self.prev_btn, False, False, 0)
        
        # Плей/Пауза
        self.play_btn = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
        self.play_btn.connect("clicked", self.on_play_pause)
        self.play_btn.set_tooltip_text("Воспроизвести/Пауза")
        controls_box.pack_start(self.play_btn, False, False, 0)
        
        # Следующий трек
        self.next_btn = Gtk.Button.new_from_icon_name("media-skip-forward", Gtk.IconSize.BUTTON)
        self.next_btn.connect("clicked", self.on_next_track)
        self.next_btn.set_tooltip_text("Следующий трек")
        controls_box.pack_start(self.next_btn, False, False, 0)
        
        # Стоп
        self.stop_btn = Gtk.Button.new_from_icon_name("media-playback-stop", Gtk.IconSize.BUTTON)
        self.stop_btn.connect("clicked", self.on_stop)
        self.stop_btn.set_tooltip_text("Стоп")
        controls_box.pack_start(self.stop_btn, False, False, 0)
        
        # Громкость
        volume_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        controls_box.pack_start(volume_box, False, False, 0)
        
        volume_label = Gtk.Label(label="Громкость:")
        volume_box.pack_start(volume_label, False, False, 0)
        
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.volume_scale.set_value(80)
        self.volume_scale.set_size_request(100, -1)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        volume_box.pack_start(self.volume_scale, False, False, 0)
        
        # Статус воспроизведения
        self.player_status_label = Gtk.Label(label="Остановлено")
        player_box.pack_start(self.player_status_label, False, False, 0)

    def create_auth_tab(self, notebook):
        """Вкладка авторизации"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="🔐 Авторизация")
        notebook.append_page(box, label)
        
        # Токен из файла
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(file_box, False, False, 0)
        
        file_btn = Gtk.Button(label="Загрузить токен из файла")
        file_btn.connect("clicked", self.on_load_token_from_file)
        file_box.pack_start(file_btn, False, False, 0)
        
        # Ручной ввод токена
        token_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.pack_start(token_box, False, False, 0)
        
        token_label = Gtk.Label(label="Введите токен вручную:")
        token_label.set_xalign(0)
        token_box.pack_start(token_label, False, False, 0)
        
        token_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        token_box.pack_start(token_entry_box, False, False, 0)
        
        self.token_entry = Gtk.Entry()
        self.token_entry.set_placeholder_text("Введите ваш VK токен...")
        self.token_entry.set_width_chars(40)
        token_entry_box.pack_start(self.token_entry, True, True, 0)
        
        token_save_btn = Gtk.Button(label="Сохранить токен")
        token_save_btn.connect("clicked", self.on_save_token)
        token_entry_box.pack_start(token_save_btn, False, False, 0)
        
        # Информация о пользователе
        self.user_info_label = Gtk.Label()
        self.user_info_label.set_markup("<i>Токен не загружен</i>")
        box.pack_start(self.user_info_label, False, False, 0)
        
        # Инструкция
        help_btn = Gtk.Button(label="📖 Инструкция по получению токена")
        help_btn.connect("clicked", self.on_show_help)
        box.pack_start(help_btn, False, False, 0)

    def create_music_tab(self, notebook):
        """Вкладка моей музыки"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="🎵 Моя музыка")
        notebook.append_page(box, label)
        
        # Панель управления
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(control_box, False, False, 0)
        
        load_btn = Gtk.Button(label="Показать мою музыку")
        load_btn.connect("clicked", self.on_load_my_music)
        control_box.pack_start(load_btn, False, False, 0)
        
        self.load_more_btn = Gtk.Button(label="📥 Показать больше треков")
        self.load_more_btn.connect("clicked", self.on_load_more_music)
        self.load_more_btn.set_sensitive(False)
        control_box.pack_start(self.load_more_btn, False, False, 0)
        
        # Прогресс бар
        self.music_progress = Gtk.ProgressBar()
        self.music_progress.set_show_text(True)
        self.music_progress.set_visible(False)
        box.pack_start(self.music_progress, False, False, 0)
        
        # Информация о загрузке
        self.music_info_label = Gtk.Label()
        box.pack_start(self.music_info_label, False, False, 0)
        
        # Список треков
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scrolled, True, True, 0)
        
        # TreeView для списка треков
        self.tracks_treeview, self.tracks_liststore = create_tracks_treeview()
        self.tracks_treeview.connect("row-activated", self.on_track_activated)
        scrolled.add(self.tracks_treeview)
        
        # Панель действий
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(action_box, False, False, 0)
        
        self.download_btn = Gtk.Button(label="💾 Скачать выбранный")
        self.download_btn.connect("clicked", self.on_download_track)
        action_box.pack_start(self.download_btn, False, False, 0)
        
        self.download_all_btn = Gtk.Button(label="💾 Скачать все")
        self.download_all_btn.connect("clicked", self.on_download_all_music)
        action_box.pack_start(self.download_all_btn, False, False, 0)

    def create_playlists_tab(self, notebook):
        """Создать вкладку плейлистов"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="📋 Плейлисты")
        notebook.append_page(box, label)
        
        # Панель управления
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(control_box, False, False, 0)
        
        load_btn = Gtk.Button(label="Показать плейлисты")
        load_btn.connect("clicked", self.on_load_playlists)
        control_box.pack_start(load_btn, False, False, 0)
        
        self.load_more_playlists_btn = Gtk.Button(label="📥 Показать еще плейлисты")
        self.load_more_playlists_btn.connect("clicked", self.on_load_more_playlists)
        self.load_more_playlists_btn.set_sensitive(False)
        control_box.pack_start(self.load_more_playlists_btn, False, False, 0)
        
        # Прогресс бар для плейлистов
        self.playlists_progress = Gtk.ProgressBar()
        self.playlists_progress.set_show_text(True)
        self.playlists_progress.set_visible(False)
        box.pack_start(self.playlists_progress, False, False, 0)
        
        # Список плейлистов и треков
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(hbox, True, True, 0)
        
        # Список плейлистов
        playlists_scrolled = Gtk.ScrolledWindow()
        playlists_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        playlists_scrolled.set_size_request(200, -1)
        hbox.pack_start(playlists_scrolled, False, False, 0)
        
        self.playlists_treeview, self.playlists_liststore = create_playlists_treeview()
        self.playlists_treeview.connect("cursor-changed", self.on_playlist_selected)
        playlists_scrolled.add(self.playlists_treeview)
        
        # Список треков плейлиста
        tracks_scrolled = Gtk.ScrolledWindow()
        tracks_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        hbox.pack_start(tracks_scrolled, True, True, 0)
        
        self.playlist_tracks_treeview, self.playlist_tracks_liststore = create_tracks_treeview()
        self.playlist_tracks_treeview.connect("row-activated", self.on_playlist_track_activated)
        tracks_scrolled.add(self.playlist_tracks_treeview)
        
        # Панель управления треками плейлиста
        playlist_actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(playlist_actions_box, False, False, 0)
        
        self.load_more_playlist_tracks_btn = Gtk.Button(label="📥 Показать больше треков из плейлиста")
        self.load_more_playlist_tracks_btn.connect("clicked", self.on_load_more_playlist_tracks)
        self.load_more_playlist_tracks_btn.set_sensitive(False)
        playlist_actions_box.pack_start(self.load_more_playlist_tracks_btn, False, False, 0)

    def create_search_tab(self, notebook):
        """Вкладка поиска"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="🔍 Поиск")
        notebook.append_page(box, label)
        
        # Поисковая строка
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(search_box, False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Введите запрос для поиска...")
        self.search_entry.connect("activate", self.on_search)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        search_btn = Gtk.Button(label="Искать")
        search_btn.connect("clicked", self.on_search)
        search_box.pack_start(search_btn, False, False, 0)
        
        self.load_more_search_btn = Gtk.Button(label="📥 Показать еще результатов")
        self.load_more_search_btn.connect("clicked", self.on_load_more_search)
        self.load_more_search_btn.set_sensitive(False)
        search_box.pack_start(self.load_more_search_btn, False, False, 0)
        
        # Прогресс бар для поиска
        self.search_progress = Gtk.ProgressBar()
        self.search_progress.set_show_text(True)
        self.search_progress.set_visible(False)
        box.pack_start(self.search_progress, False, False, 0)
        
        # Список результатов
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scrolled, True, True, 0)
        
        self.search_results_treeview, self.search_results_liststore = create_tracks_treeview()
        self.search_results_treeview.connect("row-activated", self.on_search_track_activated)
        scrolled.add(self.search_results_treeview)

    def create_recommendations_tab(self, notebook):
        """Вкладка рекомендаций"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="🎯 Рекомендации")
        notebook.append_page(box, label)
        
        # Панель управления
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(control_box, False, False, 0)
        
        load_btn = Gtk.Button(label="🎯 Показать рекомендации")
        load_btn.connect("clicked", self.on_load_recommendations)
        control_box.pack_start(load_btn, False, False, 0)
        
        popular_btn = Gtk.Button(label="🔥 Популярная музыка")
        popular_btn.connect("clicked", self.on_load_popular)
        control_box.pack_start(popular_btn, False, False, 0)
        
        self.load_more_recommendations_btn = Gtk.Button(label="📥 Показать еще рекомендации")
        self.load_more_recommendations_btn.connect("clicked", self.on_load_more_recommendations)
        self.load_more_recommendations_btn.set_sensitive(False)
        control_box.pack_start(self.load_more_recommendations_btn, False, False, 0)
        
        # Прогресс бар для рекомендаций
        self.recommendations_progress = Gtk.ProgressBar()
        self.recommendations_progress.set_show_text(True)
        self.recommendations_progress.set_visible(False)
        box.pack_start(self.recommendations_progress, False, False, 0)
        
        # Информация о рекомендациях
        self.recommendations_info_label = Gtk.Label()
        box.pack_start(self.recommendations_info_label, False, False, 0)
        
        # Список рекомендаций
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scrolled, True, True, 0)
        
        self.recommendations_treeview, self.recommendations_liststore = create_tracks_treeview()
        self.recommendations_treeview.connect("row-activated", self.on_recommendation_activated)
        scrolled.add(self.recommendations_treeview)
        
        # Панель действий
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(action_box, False, False, 0)
        
        self.recommendations_download_btn = Gtk.Button(label="💾 Скачать выбранный")
        self.recommendations_download_btn.connect("clicked", self.on_download_recommendation)
        action_box.pack_start(self.recommendations_download_btn, False, False, 0)

    def create_downloads_tab(self, notebook):
        """Вкладка загрузок"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="💾 Загрузки")
        notebook.append_page(box, label)
        
        # Панель управления
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(control_box, False, False, 0)
        
        open_btn = Gtk.Button(label="📁 Открыть папку загрузок")
        open_btn.connect("clicked", self.on_open_downloads_folder)
        control_box.pack_start(open_btn, False, False, 0)
        
        refresh_btn = Gtk.Button(label="🔄 Обновить список")
        refresh_btn.connect("clicked", self.on_refresh_downloads)
        control_box.pack_start(refresh_btn, False, False, 0)
        
        # Список загруженных файлов
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scrolled, True, True, 0)
        
        self.downloads_treeview, self.downloads_liststore = create_downloads_treeview()
        self.downloads_treeview.connect("row-activated", self.on_play_downloaded_file)
        scrolled.add(self.downloads_treeview)
        
        # Информация о папке
        self.downloads_info_label = Gtk.Label()
        box.pack_start(self.downloads_info_label, False, False, 0)
        
        self.update_downloads_list()

    def create_about_tab(self, notebook):
        """Вкладка о программе"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)
        
        label = Gtk.Label(label="ℹ️ О программе")
        notebook.append_page(box, label)
        
        # Заголовок
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>VK Music Player & Ubuntu</span>")
        box.pack_start(title_label, False, False, 0)
        
        # Версия
        version_label = Gtk.Label(label="Версия 1.0")
        box.pack_start(version_label, False, False, 0)
        
        # Описание
        desc_label = Gtk.Label()
        desc_label.set_markup(
            "Полнофункциональный графический плеер для прослушивания музыки из VK\n\n"
            "<b>Возможности:</b>\n"
            "• Моя музыка\n"
            "• Плейлисты\n"
            "• Поиск музыки\n"
            "• Рекомендации\n"
            "• Скачивание треков\n"
        )
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(50)
        box.pack_start(desc_label, False, False, 0)
        
        # Разработчик
        dev_label = Gtk.Label()
        dev_label.set_markup(
            "<b>Разработчик:</b> https://t.me/lisdevs\n\n"
            "<b>GitHub:</b> https://github.com/sidenevkirill/VK-Moosic-Player-Ubuntu"
        )
        box.pack_start(dev_label, False, False, 0)
        
        # Зависимости
        deps_label = Gtk.Label()
        deps_label.set_markup(
            "<b>Зависимости:</b>\n"
            "• Python 3.6+\n"
            "• GTK 3.0\n"
            "• mplayer\n"
            "• python3-gi\n"
            "• python3-requests\n"
            "• python-dotenv"
        )
        box.pack_start(deps_label, False, False, 0)
        
        # Кнопка проверки зависимостей
        check_btn = Gtk.Button(label="🔧 Проверить зависимости")
        check_btn.connect("clicked", self.on_check_dependencies)
        box.pack_start(check_btn, False, False, 0)
        
        # Результат проверки
        self.deps_status_label = Gtk.Label()
        self.deps_status_label.set_line_wrap(True)
        box.pack_start(self.deps_status_label, False, False, 0)

    def on_check_dependencies(self, widget):
        """Проверить зависимости"""
        def check_deps():
            missing_deps = []
            
            # Проверка mplayer
            try:
                subprocess.run(['which', 'mplayer'], check=True, capture_output=True)
                mplayer_status = "✅ mplayer установлен"
            except subprocess.CalledProcessError:
                mplayer_status = "❌ mplayer не установлен"
                missing_deps.append("mplayer")
            
            # Проверка Python модулей
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                gtk_status = "✅ GTK3 доступен"
            except ImportError:
                gtk_status = "❌ GTK3 не доступен"
                missing_deps.append("python3-gi")
            
            try:
                import requests
                requests_status = "✅ requests доступен"
            except ImportError:
                requests_status = "❌ requests не доступен"
                missing_deps.append("python3-requests")
            
            try:
                from dotenv import load_dotenv
                dotenv_status = "✅ python-dotenv доступен"
            except ImportError:
                dotenv_status = "❌ python-dotenv не доступен"
                missing_deps.append("python-dotenv")
            
            status_text = f"{mplayer_status}\n{gtk_status}\n{requests_status}\n{dotenv_status}"
            
            if missing_deps:
                status_text += f"\n\n❌ Отсутствуют зависимости: {', '.join(missing_deps)}"
                status_text += "\n\nУстановите их с помощью команды:"
                status_text += "\nsudo apt install mplayer python3-gi python3-requests"
                status_text += "\npip3 install python-dotenv"
            else:
                status_text += "\n\n✅ Все зависимости установлены!"
            
            GLib.idle_add(self.deps_status_label.set_text, status_text)
        
        threading.Thread(target=check_deps, daemon=True).start()

    # Обработчики управления плеером
    def on_seek(self, widget, event):
        """Обработчик перемещения по треку"""
        position = self.progress_scale.get_value()
        duration = self.player.get_duration()
        
        if duration > 0:
            seek_position = (position / 100.0) * duration
            self.player.seek(seek_position)

    def update_player_status(self):
        """Статус плеера"""
        if self.player.is_playing:
            self.player_status_label.set_text("▶️ Играет")
            
            # Обновляем прогресс
            position = self.player.get_position()
            duration = self.player.get_duration()
            
            if duration > 0:
                # Обновляем метки времени
                pos_min = int(position // 60)
                pos_sec = int(position % 60)
                dur_min = int(duration // 60)
                dur_sec = int(duration % 60)
                
                self.position_label.set_text(f"{pos_min}:{pos_sec:02d}")
                self.duration_label.set_text(f"{dur_min}:{dur_sec:02d}")
                
                # Обновляем ползунок
                progress = (position / duration) * 100
                self.progress_scale.set_value(progress)
        else:
            self.player_status_label.set_text("⏸️ Остановлено")
            
        return True

    def on_play_pause(self, widget):
        """Обработчик плей/паузы"""
        if self.player.is_playing:
            self.player.pause()
            self.play_btn.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
            self.update_status("Пауза")
        else:
            if self.player.current_track:
                self.player.pause()  # Продолжить
                self.play_btn.set_image(Gtk.Image.new_from_icon_name("media-playback-pause", Gtk.IconSize.BUTTON))
                self.update_status("Воспроизведение продолжено")
            else:
                self.update_status("Нет трека для воспроизведения")

    def on_stop(self, widget):
        """Обработчик остановки"""
        self.player.stop()
        self.play_btn.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
        self.progress_scale.set_value(0)
        self.position_label.set_text("0:00")
        self.duration_label.set_text("0:00")
        self.update_status("Воспроизведение остановлено")

    def on_previous_track(self, widget):
        """Обработчик предыдущего трека"""
        track = self.player.previous_track()
        if track:
            self.play_track(track)
        else:
            self.update_status("Нет предыдущего трека")

    def on_next_track(self, widget):
        """Обработчик следующего трека"""
        track = self.player.next_track()
        if track:
            self.play_track(track)
        else:
            self.update_status("Нет следующего трека")

    def on_volume_changed(self, widget):
        """Обработчик изменения громкости"""
        volume = self.volume_scale.get_value()
        self.player.set_volume(volume)

    def play_track(self, track_data):
        """Воспроизвести трек"""
        def play_thread():
            url = track_data.get('url')
            artist = track_data.get('artist', 'Unknown')
            title = track_data.get('title', 'Unknown')
            
            success, message = self.player.play(url, track_data)
            
            GLib.idle_add(lambda: self.update_status(
                f"Воспроизводится: {artist} - {title}" if success else f"Ошибка: {message}"
            ))
            
            if success:
                GLib.idle_add(lambda: self.current_track_label.set_markup(
                    f"<b>Сейчас играет:</b> {artist} - {title}"
                ))
                GLib.idle_add(lambda: self.play_btn.set_image(
                    Gtk.Image.new_from_icon_name("media-playback-pause", Gtk.IconSize.BUTTON)
                ))
                
                # Сбрасываем прогресс
                GLib.idle_add(lambda: self.progress_scale.set_value(0))
                GLib.idle_add(lambda: self.position_label.set_text("0:00"))
                
                duration = track_data.get('duration', 0)
                if duration > 0:
                    dur_min = int(duration // 60)
                    dur_sec = int(duration % 60)
                    GLib.idle_add(lambda: self.duration_label.set_text(f"{dur_min}:{dur_sec:02d}"))
        
        threading.Thread(target=play_thread, daemon=True).start()

    # Методы для работы с рекомендациями
    def on_load_recommendations(self, widget):
        """Загрузить рекомендации"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_recommendations():
            GLib.idle_add(self.update_status, "Загружаем рекомендации...")
            result = self.manager.get_recommendations(offset=0, count=100)
            GLib.idle_add(self.on_recommendations_loaded, result)
        
        threading.Thread(target=load_recommendations, daemon=True).start()

    def on_load_popular(self, widget):
        """Загрузить популярную музыку"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_popular():
            GLib.idle_add(self.update_status, "Загружаем популярную музыку...")
            result = self.manager.get_popular_music(offset=0, count=100)
            GLib.idle_add(self.on_recommendations_loaded, result)
        
        threading.Thread(target=load_popular, daemon=True).start()

    def on_recommendations_loaded(self, result):
        """Обработчик загрузки рекомендаций"""
        if result["success"]:
            self.recommendations_liststore.clear()
            recommendations = result["audio_list"]
            
            # Создаем плейлист для плеера
            playlist = []
            for track in recommendations:
                artist = track.get('artist', 'Unknown')
                title = track.get('title', 'Unknown')
                duration = track.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                self.recommendations_liststore.append([artist, title, duration_str, track.get('url', ''), track])
                playlist.append(track)
            
            self.player.set_playlist(playlist)
            
            total_count = result.get("total_count", len(recommendations))
            loaded_count = len(recommendations)
            
            self.recommendations_info_label.set_text(f"Загружено {loaded_count} рекомендаций")
            
            # Активируем кнопку "Загрузить еще" если есть еще рекомендации
            if loaded_count < total_count:
                self.load_more_recommendations_btn.set_sensitive(True)
                self.load_more_recommendations_btn.set_label(f"📥 Загрузить еще ({total_count - loaded_count} треков)")
            else:
                self.load_more_recommendations_btn.set_sensitive(False)
            
            self.update_status(f"Загружено {loaded_count} рекомендаций")
        else:
            self.show_error_dialog(f"Ошибка загрузки рекомендаций: {result.get('error')}")

    def on_recommendation_activated(self, treeview, path, column):
        """Обработчик активации рекомендации"""
        model = treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter is not None:
            track_data = model[treeiter][4]
            self.player.current_index = path[0]
            self.play_track(track_data)

    def on_download_recommendation(self, widget):
        """Скачать выбранную рекомендацию"""
        selection = self.recommendations_treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            track_data = model[treeiter][4]
            artist = track_data.get('artist', 'Unknown Artist')
            title = track_data.get('title', 'Unknown Title')
            
            def download():
                GLib.idle_add(self.update_status, f"Скачиваем: {artist} - {title}")
                success, message = self.manager.download_track(track_data)
                GLib.idle_add(lambda: self.update_status(
                    f"Скачан: {artist} - {title}" if success else f"Ошибка: {message}"
                ))
                GLib.idle_add(self.update_downloads_list)
            
            threading.Thread(target=download, daemon=True).start()

    def on_load_more_recommendations(self, widget):
        """Загрузить еще рекомендаций"""
        self.show_info_dialog("Функция загрузки дополнительных рекомендаций будет реализована в следующей версии")

    # Методы для работы с музыкой
    def on_load_my_music(self, widget):
        """Загрузить мою музыку (первые 200 треков)"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_music():
            GLib.idle_add(self.update_status, "Загружаем вашу музыку...")
            result = self.manager.get_my_audio_list(offset=0, count=200)
            GLib.idle_add(self.on_music_loaded, result)
        
        threading.Thread(target=load_music, daemon=True).start()

    def on_music_loaded(self, result):
        """Обработчик загрузки музыки"""
        self.music_progress.set_visible(False)
        
        if result["success"]:
            self.current_tracks = result["audio_list"]
            self.tracks_liststore.clear()
            
            # Создаем плейлист для плеера
            playlist = []
            for track in self.current_tracks:
                artist = track.get('artist', 'Unknown')
                title = track.get('title', 'Unknown')
                duration = track.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                self.tracks_liststore.append([artist, title, duration_str, track.get('url', ''), track])
                playlist.append(track)
            
            self.player.set_playlist(playlist)
            
            total_count = result.get("total_count", len(self.current_tracks))
            loaded_count = len(self.current_tracks)
            
            self.music_info_label.set_text(f"Загружено {loaded_count} из {total_count} треков")
            
            # Активируем кнопку "Загрузить еще" если есть еще треки
            if loaded_count < total_count:
                self.load_more_btn.set_sensitive(True)
                self.load_more_btn.set_label(f"📥 Загрузить еще ({total_count - loaded_count} треков)")
            else:
                self.load_more_btn.set_sensitive(False)
            
            self.update_status(f"Загружено {loaded_count} треков (всего {total_count})")
        else:
            self.show_error_dialog(f"Ошибка загрузки: {result.get('error')}")

    def on_track_activated(self, treeview, path, column):
        """Обработчик активации трека (двойной клик)"""
        model = treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter is not None:
            track_data = model[treeiter][4]
            self.player.current_index = path[0]  # Устанавливаем текущий индекс
            self.play_track(track_data)

    def on_download_track(self, widget):
        """Скачать выбранный трек"""
        selection = self.tracks_treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            track_data = model[treeiter][4]
            artist = track_data.get('artist', 'Unknown Artist')
            title = track_data.get('title', 'Unknown Title')
            
            def download():
                GLib.idle_add(self.update_status, f"Скачиваем: {artist} - {title}")
                success, message = self.manager.download_track(track_data)
                GLib.idle_add(lambda: self.update_status(
                    f"Скачан: {artist} - {title}" if success else f"Ошибка: {message}"
                ))
                GLib.idle_add(self.update_downloads_list)
            
            threading.Thread(target=download, daemon=True).start()

    def on_download_all_music(self, widget):
        """Скачать всю музыку"""
        if not self.current_tracks:
            self.show_error_dialog("Нет треков для скачивания")
            return
        
        def download_all():
            successful = 0
            total = len(self.current_tracks)
            
            for i, track in enumerate(self.current_tracks):
                artist = track.get('artist', 'Unknown Artist')
                title = track.get('title', 'Unknown Title')
                
                GLib.idle_add(self.update_status, f"Скачиваем {i+1}/{total}: {artist} - {title}")
                
                success, message = self.manager.download_track(track)
                if success:
                    successful += 1
                
                # Обновляем прогресс
                progress = (i + 1) / total
                GLib.idle_add(self.music_progress.set_fraction, progress)
                GLib.idle_add(self.music_progress.set_text, f"Скачано: {i+1}/{total}")
            
            GLib.idle_add(self.update_status, f"Скачано {successful} из {total} треков")
            GLib.idle_add(self.music_progress.set_visible, False)
            GLib.idle_add(self.update_downloads_list)
        
        self.music_progress.set_visible(True)
        self.music_progress.set_fraction(0)
        threading.Thread(target=download_all, daemon=True).start()

    # Методы для работы с плейлистами
    def on_load_playlists(self, widget):
        """Загрузить плейлисты (первые 200)"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_playlists():
            GLib.idle_add(self.update_status, "Загружаем плейлисты...")
            result = self.manager.get_playlists(offset=0, count=200)
            GLib.idle_add(self.on_playlists_loaded, result)
        
        threading.Thread(target=load_playlists, daemon=True).start()

    def on_playlists_loaded(self, result):
        """Обработчик загрузки плейлистов"""
        self.playlists_progress.set_visible(False)
        
        if result["success"]:
            self.playlists_liststore.clear()
            for playlist in result["playlists"]:
                title = playlist.get('title', 'Без названия')
                playlist_id = str(playlist.get('id', ''))
                count = playlist.get('count', 0)
                self.playlists_liststore.append([title, playlist_id, count])
            
            total_count = result.get("total_count", len(result["playlists"]))
            loaded_count = len(result["playlists"])
            
            # Активируем кнопку "Загрузить еще" если есть еще плейлисты
            if loaded_count < total_count:
                self.load_more_playlists_btn.set_sensitive(True)
                self.load_more_playlists_btn.set_label(f"📥 Загрузить еще ({total_count - loaded_count} плейлистов)")
            else:
                self.load_more_playlists_btn.set_sensitive(False)
            
            self.update_status(f"Загружено {loaded_count} плейлистов (всего {total_count})")
        else:
            self.show_error_dialog(f"Ошибка загрузки плейлистов: {result.get('error')}")

    def on_playlist_selected(self, treeview):
        """Обработчик выбора плейлиста"""
        selection = treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            playlist_id = model[treeiter][1]
            
            def load_playlist_tracks():
                GLib.idle_add(self.update_status, "Загружаем треки плейлиста...")
                result = self.manager.get_playlist_tracks(playlist_id, offset=0, count=200)
                GLib.idle_add(self.on_playlist_tracks_loaded, result)
            
            threading.Thread(target=load_playlist_tracks, daemon=True).start()

    def on_playlist_tracks_loaded(self, result):
        """Обработчик загрузки треков плейлиста"""
        if result["success"]:
            self.playlist_tracks_liststore.clear()
            playlist_tracks = result["audio_list"]
            
            # Создаем плейлист для плеера
            playlist = []
            for track in playlist_tracks:
                artist = track.get('artist', 'Unknown')
                title = track.get('title', 'Unknown')
                duration = track.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                self.playlist_tracks_liststore.append([artist, title, duration_str, track.get('url', ''), track])
                playlist.append(track)
            
            self.player.set_playlist(playlist)
            
            total_count = result.get("total_count", len(playlist_tracks))
            loaded_count = len(playlist_tracks)
            
            # Активируем кнопку "Загрузить еще" если есть еще треки
            if loaded_count < total_count:
                self.load_more_playlist_tracks_btn.set_sensitive(True)
                self.load_more_playlist_tracks_btn.set_label(f"📥 Загрузить еще ({total_count - loaded_count} треков)")
            else:
                self.load_more_playlist_tracks_btn.set_sensitive(False)
            
            self.update_status(f"Загружено {len(playlist_tracks)} треков из плейлиста (всего {total_count})")
        else:
            self.show_error_dialog(f"Ошибка загрузки треков: {result.get('error')}")

    def on_playlist_track_activated(self, treeview, path, column):
        """Обработчик активации трека в плейлисте"""
        model = treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter is not None:
            track_data = model[treeiter][4]
            self.player.current_index = path[0]
            self.play_track(track_data)

    # Методы для работы с поиском
    def on_search(self, widget):
        """Обработчик поиска (первые 200 результатов)"""
        query = self.search_entry.get_text().strip()
        if not query:
            self.show_error_dialog("Введите поисковый запрос")
            return
        
        def perform_search():
            GLib.idle_add(self.update_status, f"Ищем: {query}")
            result = self.manager.search_audio(query, offset=0, count=200)
            GLib.idle_add(self.on_search_completed, result, query)
        
        threading.Thread(target=perform_search, daemon=True).start()

    def on_search_completed(self, result, query):
        """Обработчик завершения поиска"""
        self.search_progress.set_visible(False)
        
        if result["success"]:
            self.search_results_liststore.clear()
            search_tracks = result["results"]
            
            # Создаем плейлист для плеера
            playlist = []
            for track in search_tracks:
                artist = track.get('artist', 'Unknown')
                title = track.get('title', 'Unknown')
                duration = track.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                self.search_results_liststore.append([artist, title, duration_str, track.get('url', ''), track])
                playlist.append(track)
            
            self.player.set_playlist(playlist)
            
            total_count = result.get("total_count", len(search_tracks))
            loaded_count = len(search_tracks)
            
            # Активируем кнопку "Загрузить еще" если есть еще результаты
            if loaded_count < total_count:
                self.load_more_search_btn.set_sensitive(True)
                self.load_more_search_btn.set_label(f"📥 Загрузить еще ({total_count - loaded_count} треков)")
            else:
                self.load_more_search_btn.set_sensitive(False)
            
            self.update_status(f"Найдено {len(search_tracks)} треков по запросу '{query}' (всего {total_count})")
        else:
            self.show_error_dialog(f"Ошибка поиска: {result.get('error')}")

    def on_search_track_activated(self, treeview, path, column):
        """Обработчик активации трека в результатах поиска"""
        model = treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter is not None:
            track_data = model[treeiter][4]
            self.player.current_index = path[0]
            self.play_track(track_data)

    # Методы для работы с загрузками
    def on_open_downloads_folder(self, widget):
        """Открыть папку загрузок"""
        try:
            subprocess.Popen(['xdg-open', self.manager.download_folder])
            self.update_status("Папка загрузок открыта")
        except Exception as e:
            self.show_error_dialog(f"Не удалось открыть папку: {e}")

    def on_refresh_downloads(self, widget):
        """Обновить список загрузок"""
        self.update_downloads_list()

    def on_play_downloaded_file(self, treeview, path, column):
        """Воспроизвести загруженный файл"""
        model = treeview.get_model()
        treeiter = model.get_iter(path)
        if treeiter is not None:
            filepath = model[treeiter][1]
            try:
                subprocess.Popen(['mplayer', filepath], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                self.update_status(f"Воспроизводится: {model[treeiter][0]}")
            except Exception as e:
                self.show_error_dialog(f"Не удалось воспроизвести файл: {e}")

    def update_downloads_list(self):
        """Обновить список загруженных файлов"""
        self.downloads_liststore.clear()
        
        if not os.path.exists(self.manager.download_folder):
            return
        
        total_size = 0
        mp3_files = []
        
        for filename in os.listdir(self.manager.download_folder):
            if filename.lower().endswith('.mp3'):
                filepath = os.path.join(self.manager.download_folder, filename)
                size = os.path.getsize(filepath)
                total_size += size
                
                # Форматируем размер
                if size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/1024/1024:.1f} MB"
                
                mp3_files.append((filename, filepath, size_str))
        
        # Сортируем по имени файла
        mp3_files.sort(key=lambda x: x[0])
        
        for filename, filepath, size_str in mp3_files:
            self.downloads_liststore.append([filename, filepath, size_str])
        
        # Обновляем информацию о папке
        if total_size < 1024 * 1024:
            total_size_str = f"{total_size/1024:.1f} KB"
        else:
            total_size_str = f"{total_size/1024/1024:.1f} MB"
        
        self.downloads_info_label.set_text(
            f"Файлов: {len(mp3_files)}, Общий размер: {total_size_str}"
        )

    # Методы пагинации
    def on_load_more_music(self, widget):
        """Загрузить еще треков из моей музыки"""
        self.load_all_music()

    def on_load_more_playlists(self, widget):
        """Загрузить еще плейлистов"""
        self.load_all_playlists()

    def on_load_more_playlist_tracks(self, widget):
        """Загрузить еще треков из выбранного плейлиста"""
        selection = self.playlists_treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            playlist_id = model[treeiter][1]
            self.load_all_playlist_tracks(playlist_id)

    def on_load_more_search(self, widget):
        """Загрузить еще результатов поиска"""
        query = self.search_entry.get_text().strip()
        if query:
            self.load_all_search_results(query)

    def load_all_music(self):
        """Загрузить всю музыку с пагинацией"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_music():
            def progress_callback(offset, total):
                progress = offset / total if total > 0 else 0
                GLib.idle_add(self.music_progress.set_fraction, progress)
                GLib.idle_add(self.music_progress.set_text, f"Загружено: {offset}/{total}")
                GLib.idle_add(self.music_info_label.set_text, f"Загружено {offset} из {total} треков")
            
            GLib.idle_add(self.music_progress.set_visible, True)
            GLib.idle_add(self.music_progress.set_fraction, 0)
            GLib.idle_add(self.update_status, "Загружаем всю вашу музыку...")
            
            result = self.manager.get_all_my_audio(progress_callback)
            GLib.idle_add(self.on_music_loaded, result)
        
        threading.Thread(target=load_music, daemon=True).start()

    def load_all_playlists(self):
        """Загрузить все плейлисты с пагинацией"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_playlists():
            def progress_callback(offset, total):
                progress = offset / total if total > 0 else 0
                GLib.idle_add(self.playlists_progress.set_fraction, progress)
                GLib.idle_add(self.playlists_progress.set_text, f"Загружено: {offset}/{total}")
            
            GLib.idle_add(self.playlists_progress.set_visible, True)
            GLib.idle_add(self.playlists_progress.set_fraction, 0)
            GLib.idle_add(self.update_status, "Загружаем все плейлисты...")
            
            result = self.manager.get_all_playlists(progress_callback)
            GLib.idle_add(self.on_playlists_loaded, result)
        
        threading.Thread(target=load_playlists, daemon=True).start()

    def load_all_playlist_tracks(self, playlist_id):
        """Загрузить все треки из плейлиста с пагинацией"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def load_playlist_tracks():
            GLib.idle_add(self.update_status, "Загружаем все треки из плейлиста...")
            
            result = self.manager.get_all_playlist_tracks(playlist_id)
            GLib.idle_add(self.on_playlist_tracks_loaded, result)
        
        threading.Thread(target=load_playlist_tracks, daemon=True).start()

    def load_all_search_results(self, query):
        """Загрузить все результаты поиска с пагинацией"""
        if not self.manager.token:
            self.show_error_dialog("Сначала загрузите токен!")
            return
        
        def perform_search():
            def progress_callback(offset, total):
                progress = offset / total if total > 0 else 0
                GLib.idle_add(self.search_progress.set_fraction, progress)
                GLib.idle_add(self.search_progress.set_text, f"Загружено: {offset}/{total}")
            
            GLib.idle_add(self.search_progress.set_visible, True)
            GLib.idle_add(self.search_progress.set_fraction, 0)
            GLib.idle_add(self.update_status, f"Ищем все результаты по запросу: {query}")
            
            result = self.manager.search_all_audio(query, progress_callback=progress_callback)
            GLib.idle_add(self.on_search_completed, result, query)
        
        threading.Thread(target=perform_search, daemon=True).start()

    # Вспомогательные методы
    def update_status(self, message):
        """Обновить статус бар"""
        context_id = self.status_bar.get_context_id("status")
        self.status_bar.push(context_id, message)

    def show_error_dialog(self, message):
        """Показать диалог ошибки"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, message):
        """Показать информационный диалог"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def on_destroy(self, widget):
        """Обработчик закрытия приложения"""
        self.player.stop()
        Gtk.main_quit()

    def on_load_token_from_file(self, widget):
        """Обработчик загрузки токена из файла"""
        success, message = self.manager.load_token_from_file()
        if success:
            self.update_user_info()
            self.show_info_dialog("Токен успешно загружен!")
        else:
            self.show_error_dialog(message)

    def on_save_token(self, widget):
        """Обработчик сохранения токена"""
        token = self.token_entry.get_text().strip()
        if not token:
            self.show_error_dialog("Токен не может быть пустым")
            return
        
        self.manager.set_token(token)
        validity = self.manager.check_token_validity()
        
        if validity["valid"]:
            success, message = self.manager.save_token_to_file()
            if success:
                self.update_user_info()
                self.show_info_dialog("Токен успешно сохранен и проверен!")
            else:
                self.show_error_dialog(message)
        else:
            self.show_error_dialog(f"Токен невалиден: {validity.get('error_msg')}")

    def on_show_help(self, widget):
        """Показать инструкцию"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Инструкция по получению VK токена"
        )
        dialog.format_secondary_text(
            "1. Откройте браузер и перейдите по ссылке:\n"
            "https://oauth.vk.com/authorize?client_id=2685278&scope=1073737727&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1\n"
            "2. Авторизуйтесь в VK\n"
            "3. Скопируйте токен из адресной строки (параметр access_token)\n"
            "4. Вставьте токен в программу"
        )
        dialog.run()
        dialog.destroy()

    def update_user_info(self):
        """Обновить информацию о пользователе"""
        if self.manager.user_info:
            user = self.manager.user_info
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            self.user_info_label.set_markup(f"<b>👤 Пользователь:</b> {name}")
        else:
            validity = self.manager.check_token_validity()
            if validity["valid"]:
                user = validity["user_info"]
                name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
                self.user_info_label.set_markup(f"<b>👤 Пользователь:</b> {name}")
            else:
                self.user_info_label.set_markup("<i>Токен не загружен</i>")

    def run(self):
        """Запустить приложение"""
        self.window.show_all()
        self.update_status("Готов к работе")
        Gtk.main()
