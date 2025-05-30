from sys import argv
from PyQt5.QtWidgets import QApplication
import user_config
from gui_qt import OverlayWindow

def main():
    user_cfg = user_config.load_user_config()
    app = QApplication(argv)
    window = OverlayWindow(user_cfg)
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()