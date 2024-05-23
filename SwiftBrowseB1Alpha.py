import sys
import os
import json
import requests
import threading
from PyQt5.QtCore import QUrl, Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QAction, QTabWidget,
    QPushButton, QWidget, QVBoxLayout, QLabel, QDialog, QGroupBox, QRadioButton,
    QHBoxLayout, QListWidget, QListWidgetItem, QFileDialog
)
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineDownloadItem

CONFIG_FILE = "browser_config.json"

# New Blocklist URLs
NEW_BLOCKLISTS = [
    "https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhosts.txt",
    "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.Spam/hosts",
    "https://v.firebog.net/hosts/static/w3kbl.txt",
    "https://adaway.org/hosts.txt",
    "https://v.firebog.net/hosts/AdguardDNS.txt",
    "https://v.firebog.net/hosts/Admiral.txt",
    "https://raw.githubusercontent.com/anudeepND/blacklist/master/adservers.txt",
    "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt",
    "https://v.firebog.net/hosts/Easylist.txt",
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
    "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/UncheckyAds/hosts",
    "https://raw.githubusercontent.com/bigdargon/hostsVN/master/hosts",
    "https://v.firebog.net/hosts/Easyprivacy.txt",
    "https://v.firebog.net/hosts/Prigent-Ads.txt",
    "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.2o7Net/hosts",
    "https://raw.githubusercontent.com/crazy-max/WindowsSpyBlocker/master/data/hosts/spy.txt",
    "https://hostfiles.frogeye.fr/firstparty-trackers-hosts.txt",
    "https://raw.githubusercontent.com/DandelionSprout/adfilt/master/Alternate%20versions%20Anti-Malware%20List/AntiMalwareHosts.txt",
    "https://osint.digitalside.it/Threat-Intel/lists/latestdomains.txt",
    "https://s3.amazonaws.com/lists.disconnect.me/simple_malvertising.txt",
    "https://v.firebog.net/hosts/Prigent-Crypto.txt",
    "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.Risk/hosts",
    "https://bitbucket.org/ethanr/dns-blacklists/raw/8575c9f96e5b4a1308f2f12394abd86d0927a4a0/bad_lists/Mandiant_APT1_Report_Appendix_D.txt",
    "https://phishing.army/download/phishing_army_blocklist_extended.txt",
    "https://gitlab.com/quidsup/notrack-blocklists/raw/master/notrack-malware.txt",
    "https://v.firebog.net/hosts/RPiList-Malware.txt",
    "https://v.firebog.net/hosts/RPiList-Phishing.txt",
    "https://raw.githubusercontent.com/Spam404/lists/master/main-blacklist.txt",
    "https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/generated/hosts",
    "https://urlhaus.abuse.ch/downloads/hostfile/",
    "https://raw.githubusercontent.com/RPiList/specials/master/Blocklisten/spam.mails"
]

class UrlLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

class Adblocker:
    def __init__(self):
        self.blocklist = set()
        self.enabled = True
        self.loading_thread = threading.Thread(target=self.load_blocklists)
        self.loading_thread.start()

    def is_ad(self, url):
        for pattern in self.blocklist:
            if pattern in url:
                print(f"Blocked ad: {url}")
                return True
        return False

    def load_blocklists(self):
        try:
            for blocklist_url in NEW_BLOCKLISTS:
                self.blocklist.update(self.fetch_blocklist(blocklist_url))
            print(f"Loaded {len(self.blocklist)} ad patterns")
        except Exception as e:
            print(f"Error loading blocklists: {e}")

    def fetch_blocklist(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return set(response.text.splitlines())
            else:
                print(f"Failed to load blocklist from {url}")
                return set()
        except Exception as e:
            print(f"Error fetching blocklist from {url}: {e}")
            return set()

class DownloadManager(QObject):
    download_requested = pyqtSignal(QWebEngineDownloadItem)

    def __init__(self):
        super().__init__()
        self.downloads = []

    def handle_download(self, download_item):
        self.downloads.append(download_item)
        self.download_requested.emit(download_item)
        download_item.accept()

class AdBlockWebEngineView(QWebEngineView):
    def __init__(self, download_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adblocker = Adblocker()
        self.download_manager = download_manager

        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.XSSAuditingEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)

        # Updated user agent string
        self.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )

        self.page().profile().downloadRequested.connect(self.download_manager.handle_download)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if self.adblocker.is_ad(url.toString()):
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

class CloseableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.tab_close_requested)

    def tab_close_requested(self, index):
        widget = self.widget(index)
        self.removeTab(index)
        widget.deleteLater()

        if self.count() == 0:
            self.parent().add_new_tab()

    def change_theme(self, theme):
        style_sheet = """
            QTabBar::tab {{
                background-color: {background_color};
                color: {text_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
            }}

            QTabBar::tab:selected {{
                background-color: {selected_color};
            }}
        """.format(
            background_color="#1F1F1F" if theme == "Dark" else "#F0F0F0",
            text_color="#FFFFFF" if theme == "Dark" else "#000000",
            selected_color="#2F2F2F" if theme == "Dark" else "#D0D0D0"
        )

        self.setStyleSheet(style_sheet)

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the main browser window
        self.setWindowTitle("SwiftBrowse")
        self.resize(800, 600)

        # Create the toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        def refresh_action_triggered(self):
            self.current_web_view().reload()

        # Create the back action
        back_action = QAction("Back", self)
        toolbar.addAction(back_action)

        # Create the forward action
        forward_action = QAction("Forward", self)
        toolbar.addAction(forward_action)

        # Create the refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_action_triggered)
        toolbar.addAction(refresh_action)

        # Create the download manager action
        download_manager_action = QAction("Downloads", self)
        download_manager_action.triggered.connect(self.show_download_manager)
        toolbar.addAction(download_manager_action)

        # Connect the refresh action to a function
        refresh_action.triggered.connect(self.refresh_action_triggered)

        # Create the address bar
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.load_entered_url)
        self.address_bar.mousePressEvent = self.select_url_bar_text
        toolbar.addWidget(self.address_bar)

        # Create the tab widget
        self.tab_widget = CloseableTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        self.setCentralWidget(self.tab_widget)

        # Create the download manager
        self.download_manager = DownloadManager()
        self.download_manager.download_requested.connect(self.on_download_requested)

        # Create the initial tab
        self.add_new_tab()

        # Connect actions to functions
        refresh_action_triggered(self)
        self.current_web_view().reload()

        back_action.triggered.connect(self.back_action_triggered)
        forward_action.triggered.connect(self.forward_action_triggered)
        refresh_action.triggered.connect(self.refresh_action_triggered)

        # Create the "Add Tab" button
        add_tab_button = QPushButton("Add Tab", self)
        add_tab_button.clicked.connect(self.add_new_tab)
        toolbar.addWidget(add_tab_button)

        # Create the settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)

        # Set the default theme
        self.set_theme("Light")
        self.search_engine = "https://www.google.com/search?q="

    def add_new_tab(self):
        web_view = AdBlockWebEngineView(self.download_manager)
        web_view.loadProgress.connect(self.update_progress)
        web_view.urlChanged.connect(self.update_address_bar)
        web_view.titleChanged.connect(self.update_tab_title)

        index = self.tab_widget.addTab(web_view, "New Tab")
        self.tab_widget.setCurrentIndex(index)

    def current_web_view(self):
        return self.tab_widget.currentWidget()

    def load_entered_url(self):
        input_text = self.address_bar.text()
        if '.' in input_text:
            if not input_text.startswith('http://') and not input_text.startswith('https://'):
                url = QUrl.fromUserInput('https://' + input_text)
            else:
                url = QUrl.fromUserInput(input_text)
        else:
            url = QUrl.fromUserInput(self.search_engine + input_text)
        self.current_web_view().load(url)

    def update_address_bar(self, url):
        self.address_bar.setText(url.toString())

    def update_tab_title(self, title):
        current_index = self.tab_widget.currentIndex()
        self.tab_widget.setTabText(current_index, title)

    def update_progress(self, progress):
        if progress < 100:
            self.setWindowTitle("SwiftBrowse - Loading...")
        else:
            self.setWindowTitle("SwiftBrowse")

    def show_download_manager(self):
        dialog = DownloadManagerDialog(self.download_manager, self)
        dialog.exec_()

    def on_download_requested(self, download_item):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", download_item.path())
        if save_path:
            download_item.setPath(save_path)
            download_item.accept()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.search_engine = dialog.get_search_engine()

    def set_theme(self, theme):
        palette = self.palette()
        if theme == "Dark":
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)  # Set button text color
        else:
            palette.setColor(QPalette.Window, Qt.white)
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)  # Set button text color
        self.setPalette(palette)
        self.tab_widget.change_theme(theme)

    def select_url_bar_text(self, event):
        self.address_bar.selectAll()

    def back_action_triggered(self):
        self.current_web_view().back()

    def forward_action_triggered(self):
        self.current_web_view().forward()

    def refresh_action_triggered(self):
        self.current_web_view().reload()

class DownloadManagerDialog(QDialog):
    def __init__(self, download_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setMinimumSize(400, 300)
        self.download_manager = download_manager

        layout = QVBoxLayout()
        self.no_downloads_label = QLabel("No downloads yet", self)
        self.download_list = QListWidget()
        layout.addWidget(self.no_downloads_label)
        layout.addWidget(self.download_list)
        self.setLayout(layout)

        self.download_manager.download_requested.connect(self.add_download_item)

    def add_download_item(self, download_item):
        self.no_downloads_label.hide()
        item = QListWidgetItem(f"Downloading: {download_item.url().toString()}")
        self.download_list.addItem(item)
        download_item.finished.connect(lambda: self.update_download_item(item, download_item))

    def update_download_item(self, item, download_item):
        if download_item.state() == QWebEngineDownloadItem.DownloadCompleted:
            item.setText(f"Completed: {download_item.url().toString()}")
        elif download_item.state() == QWebEngineDownloadItem.DownloadCancelled:
            item.setText(f"Cancelled: {download_item.url().toString()}")
        elif download_item.state() == QWebEngineDownloadItem.DownloadInterrupted:
            item.setText(f"Failed: {download_item.url().toString()}")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Create the dark mode group box
        dark_mode_group_box = QGroupBox("Dark Mode")
        dark_mode_layout = QHBoxLayout()
        self.dark_mode_radio_button1 = QRadioButton("Light")
        self.dark_mode_radio_button1.setChecked(True)
        self.dark_mode_radio_button1.clicked.connect(lambda: self.change_theme("Light"))
        self.dark_mode_radio_button2 = QRadioButton("Dark")
        self.dark_mode_radio_button2.clicked.connect(lambda: self.change_theme("Dark"))
        dark_mode_layout.addWidget(self.dark_mode_radio_button1)
        dark_mode_layout.addWidget(self.dark_mode_radio_button2)
        dark_mode_group_box.setLayout(dark_mode_layout)

        # Create the delete cookies button
        delete_cookies_button = QPushButton("Delete Cookies")
        delete_cookies_button.clicked.connect(self.delete_cookies)

        # Create the search engine group box
        search_engine_group_box = QGroupBox("Search Engine")
        search_engine_layout = QVBoxLayout()
        self.search_engine_radio_button1 = QRadioButton("Google")
        self.search_engine_radio_button1.setChecked(True)
        self.search_engine_radio_button1.clicked.connect(
            lambda: self.set_search_engine("https://www.google.com/search?q="))
        self.search_engine_radio_button2 = QRadioButton("Ecosia")
        self.search_engine_radio_button2.clicked.connect(
            lambda: self.set_search_engine("https://www.ecosia.org/search?q="))
        self.search_engine_radio_button3 = QRadioButton("DuckDuckGo")
        self.search_engine_radio_button3.clicked.connect(
            lambda: self.set_search_engine("https://duckduckgo.com/?q="))
        self.search_engine_radio_button4 = QRadioButton("Bing")
        self.search_engine_radio_button4.clicked.connect(
            lambda: self.set_search_engine("https://www.bing.com/search?q="))
        self.search_engine_radio_button5 = QRadioButton("Qwant")
        self.search_engine_radio_button5.clicked.connect(
            lambda: self.set_search_engine("https://www.qwant.com/?l=en&q="))
        search_engine_layout.addWidget(self.search_engine_radio_button1)
        search_engine_layout.addWidget(self.search_engine_radio_button2)
        search_engine_layout.addWidget(self.search_engine_radio_button3)
        search_engine_layout.addWidget(self.search_engine_radio_button4)
        search_engine_layout.addWidget(self.search_engine_radio_button5)
        search_engine_group_box.setLayout(search_engine_layout)

        # Add the group boxes to the layout
        layout.addWidget(dark_mode_group_box)
        layout.addWidget(delete_cookies_button)
        layout.addWidget(search_engine_group_box)

        self.setLayout(layout)

    def delete_cookies(self):
        web_engine_profile = QWebEngineProfile.defaultProfile()
        web_engine_profile.cookieStore().deleteAllCookies()

    def change_theme(self, theme):
        main_window = self.parent()
        main_window.set_theme(theme)

    def set_search_engine(self, search_engine):
        main_window = self.parent()
        main_window.search_engine = search_engine

    def get_search_engine(self):
        if self.search_engine_radio_button1.isChecked():
            return "https://www.google.com/search?q="
        elif self.search_engine_radio_button2.isChecked():
            return "https://www.ecosia.org/search?q="
        elif self.search_engine_radio_button3.isChecked():
            return "https://duckduckgo.com/?q="
        elif self.search_engine_radio_button4.isChecked():
            return "https://www.bing.com/search?q="
        elif self.search_engine_radio_button5.isChecked():
            return "https://www.qwant.com/?l=en&q="

if __name__ == "__main__":
    # Enable experimental features
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--enable-features=NetworkServiceInProcess'

    app = QApplication(sys.argv)
    browser_window = BrowserWindow()
    browser_window.show()
    sys.exit(app.exec_())
