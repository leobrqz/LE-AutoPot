from PyQt5.QtCore import Qt, QPoint, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPalette
from keyboard import add_hotkey, remove_hotkey
from worker import AutoPotionWorker
import config

class OverlayWindow(QWidget):
    status_signal = pyqtSignal(str, str)
    hp_signal = pyqtSignal(float, float)
    threshold_signal = pyqtSignal(float)
    log_signal = pyqtSignal(float, float)

    def __init__(self, user_cfg):
        self.user_cfg = user_cfg
        self.print_startup_info()
        super().__init__()
        self.old_pos = None
        self.auto_potion_enabled = False
        self._max_logs = 5
        self._potion_logs = []
        self._status_color_mapping = {
            config.COLOR_OFF: "red",
            config.COLOR_ON: "green",
            config.COLOR_WAITING: "orange",
            config.COLOR_ERROR: "darkred",
            config.COLOR_PAUSED: "blue"
        }
        self._default_status_color = "white"
        self.status_signal.connect(self.set_status)
        self.hp_signal.connect(self.set_hp)
        self.threshold_signal.connect(self.set_threshold)
        self.log_signal.connect(self.add_potion_log)
        self.move_locked = True
        self.init_ui()
        self._register_hotkey()
        self._start_worker()

    def print_startup_info(self):
        self.print_startup_header()
        print("\nHotkeys:")
        print(f"  {self.user_cfg['HOTKEY_TOGGLE']:<20} - Toggle Auto Potion")
        print(f"  {self.user_cfg['HOTKEY_HIDE_SHOW']:<20} - Show/Hide Overlay")
        print(f"  {self.user_cfg['HOTKEY_CLOSE']:<20} - Close overlay")
        print(f"  {self.user_cfg['HOTKEY_LOCK_MOVE']:<20} - Lock/Unlock movement")
        print("\nAuto Potion configuration:")
        print(f"  Potion Key: {self.user_cfg['POTION_KEY']}")
        print(f"  Threshold: {int(float(self.user_cfg['THRESHOLD_PCT'])*100)}%")
        print(f"  Potion Cooldown: {int(float(self.user_cfg['POTION_COOLDOWN'])*1000)} ms")
        print(f"  Stable HP Duration: {int(float(self.user_cfg['STABLE_HP_DURATION']))} s")
        print(f"  Initial Position: x={int(self.user_cfg['INITIAL_POS_X'])}, y={int(self.user_cfg['INITIAL_POS_Y'])}")
        print("\n--------------------------------------------------------")

    def print_startup_header(self):
        print("\n--------------------------------------------------------")
        if self.user_cfg['DEVELOPER_DEBUG']:
            print(f"[Last Epoch Auto Potion - v{config.APP_VERSION} (Developer Mode)]")
            print(f"For Last Epoch version: {config.LAST_EPOCH_VERSION}\n")
            print(f"> Module name: {config.MODULE_NAME}")
            print(f"> Using pointer chain: base={config.BASE_OFFSET}, offsets={config.OFFSETS}")
        else:
            print(f"[Last Epoch Auto Potion - v{config.APP_VERSION}]")
            print(f"For Last Epoch version: {config.LAST_EPOCH_VERSION}")

    
    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        pos_x = int(self.user_cfg['INITIAL_POS_X'])
        pos_y = int(self.user_cfg['INITIAL_POS_Y'])
        self.setFixedSize(182, 170)
        self.move(pos_x, pos_y)

        # Palette for white text
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)

        font = QFont('Segoe UI', 11)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(4)

        self.status_label = QLabel('Status: OFF')
        self.status_label.setFont(font)
        self.status_label.setStyleSheet('color: white;')
        self.layout.addWidget(self.status_label)

        self.hp_label = QLabel('HP: 1000/1000')
        self.hp_label.setFont(font)
        self.hp_label.setStyleSheet('color: white;')
        self.layout.addWidget(self.hp_label)

        self.threshold_label = QLabel('Threshold: 60%')
        self.threshold_label.setFont(font)
        self.threshold_label.setStyleSheet('color: white;')
        self.layout.addWidget(self.threshold_label)

        self.log_labels = []
        for _ in range(self._max_logs):
            log_label = QLabel('')
            log_label.setFont(QFont('Segoe UI', 10))
            log_label.setStyleSheet('color: #AAAAAA;')
            self.layout.addWidget(log_label)
            self.log_labels.append(log_label)

        self.setLayout(self.layout)
        self.update_log(["..."]*self._max_logs)

    @pyqtSlot(str, str)
    def set_status(self, status_text, color_key):
        self.status_label.setText(f'Status: {status_text}')
        color = self._status_color_mapping.get(color_key, self._default_status_color)
        self.status_label.setStyleSheet(f'color: {color};')

    @pyqtSlot(float, float)
    def set_hp(self, current_hp, max_hp):
        if current_hp is not None and max_hp is not None and max_hp > 0:
            hp_pct = (current_hp / max_hp) * 100
            self.hp_label.setText(f'HP: {int(current_hp)}/{int(max_hp)} ({hp_pct:5.1f}%)')
        else:
            self.hp_label.setText('HP: -')

    @pyqtSlot(float)
    def set_threshold(self, threshold):
        if threshold is not None:
            self.threshold_label.setText(f'Threshold: {int(threshold)}')
        else:
            self.threshold_label.setText('Threshold: -')

    @pyqtSlot(float, float)
    def add_potion_log(self, hp_value, max_hp=None):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        if max_hp is not None and max_hp > 0:
            hp_pct = (hp_value / max_hp) * 100
            log_entry = f"{timestamp}   {int(hp_value):>5}   {hp_pct:5.1f}%"
        else:
            log_entry = f"{timestamp}   {int(hp_value):>5}"
        self._potion_logs.insert(0, log_entry)
        self._potion_logs = self._potion_logs[:self._max_logs]
        self.update_log(self._potion_logs)

    def update_log(self, log_lines):
        for i, label in enumerate(self.log_labels):
            label.setText(log_lines[i] if i < len(log_lines) else '')

    def toggle_auto_potion(self):
        self.auto_potion_enabled = not self.auto_potion_enabled
        if self.auto_potion_enabled:
            self.set_status("ON", config.COLOR_ON)
        else:
            self.set_status("OFF", config.COLOR_OFF)

    def _register_hotkey(self):
        add_hotkey(self.user_cfg['HOTKEY_TOGGLE'], self.toggle_auto_potion)
        add_hotkey(self.user_cfg['HOTKEY_CLOSE'], self._close_via_hotkey)
        add_hotkey(self.user_cfg['HOTKEY_HIDE_SHOW'], self.toggle_visibility)
        add_hotkey(self.user_cfg['HOTKEY_LOCK_MOVE'], self.toggle_move_lock)

    def _unregister_hotkey(self):
        remove_hotkey(self.user_cfg['HOTKEY_TOGGLE'])
        remove_hotkey(self.user_cfg['HOTKEY_CLOSE'])
        remove_hotkey(self.user_cfg['HOTKEY_HIDE_SHOW'])
        remove_hotkey(self.user_cfg['HOTKEY_LOCK_MOVE'])

    def _close_via_hotkey(self):
        self.close()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            print("[Overlay] Window hidden")
        else:
            self.show()
            print("[Overlay] Window visible")

    def toggle_move_lock(self):
        self.move_locked = not self.move_locked
        print(f"[Overlay] Move lock: {'ON' if self.move_locked else 'OFF'}")

    def _start_worker(self):
        self.worker_thread = AutoPotionWorker(
            status_text_var=None,
            status_color_var=None,
            enabled_flag=self,
            add_potion_log_callback=self.add_potion_log,
            gui=self,
            user_cfg=self.user_cfg
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()

    # Allow dragging the window
    def mousePressEvent(self, event):
        if self.move_locked:
            return
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.move_locked:
            return
        if self.old_pos is not None:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if self.move_locked:
            return
        self.old_pos = None

    def closeEvent(self, event):
        self._unregister_hotkey()
        if hasattr(self, 'worker_thread') and self.worker_thread.is_alive():
            self.worker_thread.signal_shutdown()
        event.accept()
        import os
        os._exit(0)

    # For the worker to access the enabled state
    def get(self):
        return self.auto_potion_enabled
