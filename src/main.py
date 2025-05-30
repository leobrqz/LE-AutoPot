import sys
from PyQt5.QtWidgets import QApplication
import user_config
from gui_qt import OverlayWindow

def main():
    user_cfg = user_config.load_user_config()
    app = QApplication(sys.argv)
    window = OverlayWindow(user_cfg)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()