import sys
import os
import time
from urllib.parse import urlparse, parse_qs

import requests
import subprocess
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLineEdit,
    QListWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QMainWindow,
    QStatusBar,
    QMenu,
    QMenuBar,
    QInputDialog,
    QMessageBox,
    QGridLayout,
    QSlider
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction
from PyQt6.QtCore import Qt, QUrl, QSettings, QTimer

class fetch_data:
    def __init__(self):
        self.base_url = "https://www.mangacix.net/"

    def fetch_anime_data(self, query):
        search_url = f"{self.base_url}secure/search/{query}?limit=20"
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        return [
            {'name': item.get('name', 'No name field'), 'id': item.get('id', 'No ID field')}
            for item in data.get('results', [])
        ]

    def fetch_anime_eps(self, selected_id):
        data_url = f"https://www.mangacix.net/secure/related-videos?episode=1&season=1&titleId={selected_id}"
        response = requests.get(data_url)
        response.raise_for_status()
        data = response.json()

        episodes = []
        for item in data.get('videos', []):
            episode_name = item.get('name', 'No name field')
            episode_url = item.get('url', 'No URL field')
            episodes.append({'name': episode_name, 'url': episode_url})

        return episodes


class watch_anime:
    def __init__(self):
        self.base_url = "https://www.mangacix.net/"
        self.process = None  # mpv processini saklamak için

    def open_with_video_player(self,url):
        try:
            # Ensure url is a string
            if not isinstance(url, str):
                raise ValueError("Url string olmalı.")
            
            # Print the URL for debugging
            #print(f"Opening URL: {url}")

            # Run the subprocess with the correct command arguments
            self.process = subprocess.Popen(['mpv', url])
        except subprocess.CalledProcessError as e:
            print(f"Oynatılırken Hata Oluştu: {e}")
        except ValueError as e:
            print(f"Bir Hata Oluştu: {e}")

                

    def fetch_anime_api_watch_url(self,url):
        wtch_url = f"https://animecix.net/{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(wtch_url, headers=headers, allow_redirects=True)
        response.raise_for_status()

        # Yanıt URL'sini al
        time.sleep(3)

        final_resp = response.url

        path = urlparse(final_resp).path
        embed_id = path.split('/')[2]  # Örneğin: '63116f91a21596c7104eac99'
        query = urlparse(final_resp).query
        params = parse_qs(query)
        vid = params.get('vid', [None])[0]  # Örneğin: '363320'

        watch_url = f"https://tau-video.xyz/api/video/{embed_id}?vid={vid}"

        response = requests.get(watch_url)
        response.raise_for_status()  # HTTP hatalarını kontrol et

        data = response.json()
        urls = []
        for item in data.get('urls', []):
            episode_url = item.get('url', 'No URL field')
            urls.append({'url': episode_url})
        return urls

    def anime_watch(self, url_list):
        if not isinstance(url_list, list) or not url_list:
            print("Geçerli bir url bulunamadı! ")
            return
        url_indices_to_try = [3,2, 1, 0]

        for index in url_indices_to_try:
            if index < len(url_list):
                url = url_list[index]['url']
                try:
                    #print(f"Trying URL at index {index}: {url}")
                    # URL'yi açmayı deneyin
                    self.open_with_video_player(url)
                    print(f"Bölüm Oynatılıyor... {index}.")
                    return  # URL başarılı bir şekilde açıldığında çıkış yap
                except Exception as e:
                    print(f"Bölüm oynatılırken hata oluştu! {index}: {e}")
        self.open_with_video_player(url)

    def stop_playback(self):
        if self.process:
            self.process.terminate() 

class AnimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime İzleme Uygulaması")
        self.setWindowIcon(QIcon("icon.ico"))  # Uygulama simgesi (icon.ico dosyası ekleyin)

        # Karanlık tema ayarları
        self.palette = QPalette()
        self.palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        self.palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        self.palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        self.palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        self.palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(self.palette)

        self.font = QFont("Arial", 10)
        self.setFont(self.font)

        # Pencere boyutları
        self.setFixedSize(800, 600)

        # Uygulama özellikleri
        self.current_episode_index = None
        self.episodes = []
        self.current_anime_name = None
        self.history = []
        self.favorites = []
        self.search_history = []

        # Ayarlar dosyası
        self.settings = QSettings("AnimeApp", "AnimeApp")

        # Arama bölümü
        self.search_label = QLabel("Anime Ara:")
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.search_anime)  # Enter tuşuna basıldığında arama yap
        self.search_button = QPushButton("Ara")
        self.search_button.clicked.connect(self.search_anime)

        # Bölüm listesi
        self.episode_list = QListWidget()
        self.episode_list.itemDoubleClicked.connect(self.play_selected_episode)  # Çift tıklama ile oynatma

        # Oynatma butonu
        self.play_button = QPushButton("Oynat")
        self.play_button.clicked.connect(self.play_selected_episode)

        # Ses seviyesi kontrolü
        self.volume_label = QLabel("Ses Seviyesi:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)  # Başlangıç ses seviyesi
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Durum çubuğu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Menü çubuğu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Dosya")
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Favori menüsü
        favorites_menu = menubar.addMenu("Favori")
        add_favorite_action = QAction("Favoriye Ekle", self)
        add_favorite_action.triggered.connect(self.add_favorite)
        favorites_menu.addAction(add_favorite_action)
        remove_favorite_action = QAction("Favoriyi Kaldır", self)
        remove_favorite_action.triggered.connect(self.remove_favorite)
        favorites_menu.addAction(remove_favorite_action)
        view_favorites_action = QAction("Favorileri Görüntüle", self)
        view_favorites_action.triggered.connect(self.view_favorites)
        favorites_menu.addAction(view_favorites_action)

        # Geçmiş menüsü
        history_menu = menubar.addMenu("Geçmiş")
        view_history_action = QAction("Geçmişi Görüntüle", self)
        view_history_action.triggered.connect(self.view_history)
        history_menu.addAction(view_history_action)
        clear_history_action = QAction("Geçmişi Temizle", self)
        clear_history_action.triggered.connect(self.clear_history)
        history_menu.addAction(clear_history_action)

        # Layout
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.search_label, 0, 0)
        grid_layout.addWidget(self.search_input, 0, 1)
        grid_layout.addWidget(self.search_button, 0, 2)
        grid_layout.addWidget(self.episode_list, 1, 0, 1, 3)
        grid_layout.addWidget(self.play_button, 2, 0)
        grid_layout.addWidget(self.volume_label, 2, 1)
        grid_layout.addWidget(self.volume_slider, 2, 2)

        central_widget = QWidget()
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

        # Favori ve Geçmiş Pencerelerini Tanımlama
        self.favorites_window = None
        self.history_window = None

        # Ayarlar dosyasından verileri yükle
        self.load_settings()

        # Oynatma kontrolü (mpv)
        self.player = watch_anime()

    def load_settings(self):
        self.favorites = self.settings.value("favorites", [])
        self.history = self.settings.value("history", [])
        self.search_history = self.settings.value("search_history", [])
        last_anime = self.settings.value("last_anime", "")
        last_episode_index = self.settings.value("last_episode_index", -1, type=int)

        if last_anime:
            self.search_input.setText(last_anime)
            self.search_anime()
            if 0 <= last_episode_index < self.episode_list.count():
                self.episode_list.setCurrentRow(last_episode_index)

    def save_settings(self):
        self.settings.setValue("favorites", self.favorites)
        self.settings.setValue("history", self.history)
        self.settings.setValue("search_history", self.search_history)
        self.settings.setValue("last_anime", self.search_input.text())
        self.settings.setValue("last_episode_index", self.episode_list.currentRow())

    def search_anime(self):
        query = self.search_input.text()
        if query not in self.search_history:
            self.search_history.append(query)
        fetch_dt = fetch_data()
        anime_data = fetch_dt.fetch_anime_data(query)

        if not anime_data:
            self.status_bar.showMessage("Sonuç bulunamadı.")
            return

        anime_names = [anime['name'] for anime in anime_data]
        selected_anime, ok = QInputDialog.getItem(self, "Anime Seç", "Lütfen bir anime seçin:", anime_names, 0, False)

        if ok and selected_anime:
            selected_id = next(anime['id'] for anime in anime_data if anime['name'] == selected_anime)
            self.episodes = fetch_data().fetch_anime_eps(selected_id=selected_id)
            if self.episodes:
                self.current_anime_name = selected_anime
                self.current_episode_index = 0

                self.episode_list.clear()
                for i, episode in enumerate(self.episodes):
                    self.episode_list.addItem(f"Bölüm {i+1} - {episode['name']}")  # Bölüm numarası eklendi

                self.status_bar.showMessage(f"{self.current_anime_name} animesi seçildi.")
            else:
                QMessageBox.critical(self, "Hata", "Bölüm bilgileri bulunamadı.")

    def play_episode(self, index):
        if index < len(self.episodes):
            episode = self.episodes[index]
            print(f"Oynatılan bölüm: {episode['name']}")
            url = self.player.fetch_anime_api_watch_url(episode['url'])
            self.player.anime_watch(url)
            self.history.append((self.current_anime_name, episode['name']))
            self.save_settings()  # Ayarlar kaydediliyor

            # Otomatik oynatma
            if index + 1 < len(self.episodes):
                self.current_episode_index += 1
                self.episode_list.setCurrentRow(self.current_episode_index)
                self.play_episode(self.current_episode_index)

    def play_selected_episode(self):
        if self.episode_list.currentRow() != -1:
            self.current_episode_index = self.episode_list.currentRow()
            self.play_episode(self.current_episode_index)
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir bölüm seçin.")

    def select_episode_from_list(self, item):
        self.current_episode_index = self.episode_list.row(item)
        self.status_bar.showMessage(f"{item.text()} seçildi.")

    def add_favorite(self):
        if self.current_anime_name:
            if self.current_anime_name not in self.favorites:
                self.favorites.append(self.current_anime_name)
                QMessageBox.information(self, "Favori", f"{self.current_anime_name} favori listenize eklendi.")
                self.save_settings()
            else:
                QMessageBox.warning(self, "Favori", f"{self.current_anime_name} zaten favori listenizde.")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir anime seçin.")

    def remove_favorite(self):
        if self.current_anime_name:
            if self.current_anime_name in self.favorites:
                self.favorites.remove(self.current_anime_name)
                QMessageBox.information(self, "Favori", f"{self.current_anime_name} favori listenizden kaldırıldı.")
                self.save_settings()
            else:
                QMessageBox.warning(self, "Favori", f"{self.current_anime_name} favori listenizde bulunmuyor.")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir anime seçin.")

    def view_favorites(self):
        if self.favorites:
            if self.favorites_window is None:
                self.favorites_window = QWidget()
                self.favorites_window.setWindowTitle("Favorilerim")
                favorites_layout = QVBoxLayout()

                self.favorites_list = QListWidget(self.favorites_window)
                for favorite in self.favorites:
                    self.favorites_list.addItem(favorite)
                favorites_layout.addWidget(self.favorites_list)

                self.favorites_window.setLayout(favorites_layout)

            self.favorites_window.show()
        else:
            QMessageBox.information(self, "Favori", "Favori listeniz boş.")

    def view_history(self):
        if self.history:
            if self.history_window is None:
                self.history_window = QWidget()
                self.history_window.setWindowTitle("Geçmiş")
                history_layout = QVBoxLayout()

                self.history_list = QListWidget(self.history_window)
                for anime, episode in self.history:
                    self.history_list.addItem(f"{anime} - {episode}")
                history_layout.addWidget(self.history_list)

                self.history_window.setLayout(history_layout)
            
            self.history_window.show()
        else:
            QMessageBox.information(self, "Geçmiş", "İzleme geçmişiniz boş.")

    def clear_history(self):
        if self.history:
            self.history.clear()
            self.save_settings()
            QMessageBox.information(self, "Geçmiş", "İzleme geçmişi temizlendi.")
        else:
            QMessageBox.information(self, "Geçmiş", "İzleme geçmişiniz zaten boş.")

    def set_volume(self, value):
        if self.player.process:
            # mpv'nin ses seviyesini ayarlamak için komut gönderin (0-100 arası)
            subprocess.run(['mpv', '--volume', str(value), '--no-osd'], check=True)

    def closeEvent(self, event):
        self.player.stop_playback()  # Pencere kapatıldığında oynatmayı durdur
        self.save_settings()
        super().closeEvent(event)

    def check_playback(self):
        if self.player.process is not None and self.player.process.poll() is not None:
            # Bir sonraki bölüm varsa oynat
            if self.current_episode_index + 1 < len(self.episodes):
                self.current_episode_index += 1
                self.episode_list.setCurrentRow(self.current_episode_index)
                self.play_episode(self.current_episode_index)
        # Belirli aralıklarla tekrar kontrol et
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_playback)
        self.timer.start(1000)  # 1 saniyede bir kontrol et


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnimeApp()
    window.show()
    sys.exit(app.exec())