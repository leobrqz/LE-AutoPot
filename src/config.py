# === User Settings ===

# Hotkeys
HOTKEY_TOGGLE = 'num /'           # Enable/disable Auto Potion
HOTKEY_CLOSE = 'ctrl+alt+num -'   # Close the overlay immediately
HOTKEY_HIDE_SHOW = 'ctrl+alt+num /'   # Hide/show overlay
HOTKEY_LOCK_MOVE = 'ctrl+alt+num *'   # Lock/unlock window movement

# Potion logic
POTION_KEY = "1"                  # Key used for potion
POTION_COOLDOWN = 0.2             # Seconds between allowed uses
THRESHOLD_PCT = 0.6               # HP percent to trigger potion
STABLE_HP_DURATION = 5.0          # Seconds to consider HP stable

# === Technical/Advanced Settings ===
LAST_EPOCH_VERSION = "1.2.5.1" # offsets version

PROCESS_NAME = "Last Epoch.exe"
WINDOW_TITLE = "Last Epoch"
MODULE_NAME = "GameAssembly.dll"
BASE_OFFSET = 0x040A0338
OFFSETS = [0xB8, 0x0, 0xA0, 0x6C]

INTERVAL = 0.1
WAIT_INTERVAL_PROCESS = 5
WAIT_INTERVAL_MEMORY = 1

LAST_POTION_TIME_INIT = 0  # initial value for the last potion use timestamp

COLOR_OFF = "red"
COLOR_ON = "green"
COLOR_WAITING = "orange"
COLOR_ERROR = "red"
COLOR_PAUSED = "blue"
