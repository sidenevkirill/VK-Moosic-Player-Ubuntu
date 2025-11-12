"""
Вспомогательные виджеты и компоненты UI
"""

from config import GTK_AVAILABLE
if GTK_AVAILABLE:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Pango

def create_tracks_treeview():
    """Создать TreeView для списка треков"""
    liststore = Gtk.ListStore(str, str, str, str, object)  # artist, title, duration, url, track_data
    treeview = Gtk.TreeView(model=liststore)
    
    # Настройка колонок
    renderer = Gtk.CellRendererText()
    
    column = Gtk.TreeViewColumn("Исполнитель", renderer, text=0)
    column.set_expand(True)
    treeview.append_column(column)
    
    column = Gtk.TreeViewColumn("Название", renderer, text=1)
    column.set_expand(True)
    treeview.append_column(column)
    
    column = Gtk.TreeViewColumn("Длительность", renderer, text=2)
    treeview.append_column(column)
    
    return treeview, liststore

def create_playlists_treeview():
    """Создать TreeView для списка плейлистов"""
    liststore = Gtk.ListStore(str, str, int)  # название, ID, количество треков
    treeview = Gtk.TreeView(model=liststore)
    
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Плейлисты", renderer, text=0)
    treeview.append_column(column)
    
    column = Gtk.TreeViewColumn("Треков", renderer, text=2)
    treeview.append_column(column)
    
    return treeview, liststore

def create_downloads_treeview():
    """Создать TreeView для списка загрузок"""
    liststore = Gtk.ListStore(str, str, str)  # имя, путь, размер
    treeview = Gtk.TreeView(model=liststore)
    
    renderer = Gtk.CellRendererText()
    
    column = Gtk.TreeViewColumn("Файл", renderer, text=0)
    treeview.append_column(column)
    
    column = Gtk.TreeViewColumn("Размер", renderer, text=2)
    treeview.append_column(column)
    
    return treeview, liststore
