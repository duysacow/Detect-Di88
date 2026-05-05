from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction
from ClassPath import get_resource_path

class TrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # Load Icon
        icon_path = get_resource_path("di88vp.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Macro By Di88")
        
        # Setup Menu
        self.setup_menu()
        
        # Connect Actions
        self.tray_icon.activated.connect(self.on_tray_activated)
        
    def setup_menu(self):
        menu = QMenu()
        
        # Restore Action
        action_show = QAction("Show", self.main_window)
        action_show.triggered.connect(self.main_window.restore_window)
        menu.addAction(action_show)
        
        # Exit Action
        action_exit = QAction("Exit", self.main_window)
        action_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(menu)
        
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.restore_window()
            
    def show(self):
        self.tray_icon.show()
        
    def hide(self):
        self.tray_icon.hide()
