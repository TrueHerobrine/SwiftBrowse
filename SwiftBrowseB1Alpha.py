import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QAction, QTabWidget, QPushButton, QWidget, \
    QVBoxLayout, QLabel, QDialog, QGroupBox, QRadioButton, QHBoxLayout
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineSettings


class AdBlockWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page().setWebEngineProfile(QWebEngineProfile.defaultProfile())

        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)

        self.page().profile().setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                               "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")


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

        # Create the stop action
        stop_action = QAction("Stop", self)
        toolbar.addAction(stop_action)

        # Create the refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_action_triggered)
        toolbar.addAction(refresh_action)

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

        # Create the initial tab
        self.add_new_tab()

        # Connect actions to functions
        refresh_action_triggered(self)
        self.current_web_view().reload()

        back_action.triggered.connect(self.back_action_triggered)
        forward_action.triggered.connect(self.forward_action_triggered)
        stop_action.triggered.connect(self.stop_action_triggered)
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
        web_view = AdBlockWebEngineView()
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

    def stop_action_triggered(self):
        self.current_web_view().stop()

    def refresh_action_triggered(self):
        self.current_web_view().reload()


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


class AdBlockWebEngineView(QWebEngineView):
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        host = url.host()

        # Block ads from specific hosts
        blocked_hosts = ["adsense.google.com", "2mdn.net", "googleadservices.com", "adservice.google.ca", "doubleclick.com", "doubleclick.net", "adsense.com", "pubads.g.doubleclick.net", "www.youtube.com/pagead/", "googleads.g.doubleclick.net", "s.ytimg.com/yts/jsbin/", "i.ytimg.com"]

        # Block YouTube ads by checking the URL
        if host == "www.youtube.com" and "/watch?" in url.path() and ("ad" in url.queryItems() or "ads" in url.queryItems()):
            return False

        # Block ads from the blocked_hosts list
        if host in blocked_hosts:
            return False

        return super().acceptNavigationRequest(url, _type, isMainFrame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser_window = BrowserWindow()
    browser_window.show()
    sys.exit(app.exec_())
