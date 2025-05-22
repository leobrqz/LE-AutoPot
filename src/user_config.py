import os
import config
import configparser
import sys

USER_CONFIG_FILE = "config_user.ini"

DEFAULTS = {
    "Hotkeys": {
        "HOTKEY_TOGGLE": config.HOTKEY_TOGGLE,
        "HOTKEY_CLOSE": config.HOTKEY_CLOSE,
        "HOTKEY_HIDE_SHOW": config.HOTKEY_HIDE_SHOW,
        "HOTKEY_LOCK_MOVE": config.HOTKEY_LOCK_MOVE,
    },
    "Potion": {
        "POTION_KEY": config.POTION_KEY,
        "POTION_COOLDOWN": str(config.POTION_COOLDOWN),
        "THRESHOLD_PCT": str(config.THRESHOLD_PCT),
        "STABLE_HP_DURATION": str(config.STABLE_HP_DURATION),
    }
}

def write_default_config_ini():
    with open(USER_CONFIG_FILE, "w") as f:
        f.write("""# === User Configurations ===\n\n""")
        f.write("[Hotkeys]\n")
        f.write("# HOTKEY_TOGGLE: Enable/disable Auto Potion\n")
        f.write(f"HOTKEY_TOGGLE = {config.HOTKEY_TOGGLE}\n")
        f.write("# HOTKEY_CLOSE: Close the overlay immediately\n")
        f.write(f"HOTKEY_CLOSE = {config.HOTKEY_CLOSE}\n")
        f.write("# HOTKEY_HIDE_SHOW: Hide/show overlay\n")
        f.write(f"HOTKEY_HIDE_SHOW = {config.HOTKEY_HIDE_SHOW}\n")
        f.write("# HOTKEY_LOCK_MOVE: Lock/unlock window movement with mouse\n")
        f.write(f"HOTKEY_LOCK_MOVE = {config.HOTKEY_LOCK_MOVE}\n\n")
        
        f.write("[Potion]\n")
        f.write("# POTION_KEY: Key used for potion\n")
        f.write(f"POTION_KEY = {config.POTION_KEY}\n")
        f.write("# POTION_COOLDOWN: Seconds between allowed uses\n")
        f.write(f"POTION_COOLDOWN = {config.POTION_COOLDOWN}\n")
        f.write("# THRESHOLD_PCT: HP percent to trigger potion\n")
        f.write(f"THRESHOLD_PCT = {config.THRESHOLD_PCT}\n")
        f.write("# STABLE_HP_DURATION: Seconds to consider HP stable\n")
        f.write(f"STABLE_HP_DURATION = {config.STABLE_HP_DURATION}\n\n")

        f.write("[Overlay]\n")
        f.write("# INITIAL_POS_X: Initial X position of the overlay window\n")
        f.write("INITIAL_POS_X = 200\n")
        f.write("# INITIAL_POS_Y: Initial Y position of the overlay window\n")
        f.write("INITIAL_POS_Y = 880\n\n")

def ensure_user_config_exists():
    if not os.path.exists(USER_CONFIG_FILE):
        write_default_config_ini()
        print("--------------------------------------------------------")
        print("'config_user.ini' was created.")
        print("[Attention] It may be needed to restart the application in the first time to work properly.")

def load_user_config():
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(USER_CONFIG_FILE)
    user_cfg = {}
    for section in parser.sections():
        for k, v in parser[section].items():
            try:
                user_cfg[k] = float(v) if "." in v or "e" in v.lower() else int(v)
            except Exception:
                user_cfg[k] = v
    print("--------------------------------------------------------")
    print("'config_user.ini' was loaded.")
    return user_cfg 