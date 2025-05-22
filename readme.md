# Last Epoch Auto Potion 🧙‍♂


[![Last Epoch Version](https://img.shields.io/badge/Last%20Epoch%20Version-1.2.4.1-purple)]()
[![Windows](https://img.shields.io/badge/Platform-Windows%20%7C%20pywin32-blue)](https://github.com/mhammond/pywin32)

A Windows overlay tool for Last Epoch that automatically uses potions when your HP drops below a configurable threshold. Features a PyQt5 overlay, hotkey controls, and direct memory reading for reliable automation.

**> Warning**: This tool is intended for offline use. While it may work online, use it at your own discretion and risk.

Based on [Skalety's Auto Potion](https://www.unknowncheats.me/forum/other-mmorpg-and-strategy/699378-epoch-auto-potion-copied-games.html) <3



## ✨ Features
<p align="center">
  <img src="imgs/OverlayOFF.png" alt="Overlay OFF" width="45%"/>
  <img src="imgs/OverlayON.png" alt="Overlay ON" width="45%"/>
</p>

- **Auto Potion**: Automatically triggers a potion when HP falls below a set percentage.
- **Potion log**: The overlay displays a log of recent potion uses, showing HP values and timestamps for each use.
- **Overlay UI**: Movable, lockable PyQt5 overlay showing status, HP, and logs.
- **Customizable Hotkeys**: Easily change hotkeys for toggling, hiding, and closing the overlay.
- **Safe & Configurable**: All settings in a user-friendly config file.



## 🛠️ Setup Instructions

You can use the tool in three ways:

### 1. Download the Executable
- Download the latest release from the [Releases page](<your-release-url>).
- Run the `.exe` file directly (no Python required).

### 2. Build the Executable Yourself
- Clone the repository:
  ```bash
  git clone <your-repo-url>
  cd Last-Epoch-Auto-Potion
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Build the executable with PyInstaller:
  ```bash
  build_release.sh
  ```
- The executable will be in the `release/` folder.

### 3. Run Natively with Python
- Clone the repository:
  ```bash
  git clone <your-repo-url>
  cd Last-Epoch-Auto-Potion
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Run the application:
  ```bash
  python src/main.py
  ```


## ⚙️ Configuration
- **config_user.ini** is auto-generated on first run.
- Change hotkeys, potion key, HP threshold, cooldown, and overlay position in this file.
- Default hotkeys:
  - Toggle: `num /`
  - Close: `ctrl+alt+num -`
  - Hide/Show: `ctrl+alt+num /`
  - Lock/Unlock Move: `ctrl+alt+num *`
- Default potion settings:
  - Potion Key: `1` 
  - Potion Cooldown: `0.2` s
  - HP Threshold: `0.6` (60%)
  - Stable HP Duration: `5.0` s
- Overlay settings:
  - Default position on bottom left corner before the player health
  - INITIAL_POS_X: 200
  - INITIAL_POS_Y: 880


## 🖥️ Requirements
- Windows 10+
- Python 3.8+
- Game: Last Epoch (tested on version 1.2.4.1)
- Admin rights may be required to access game memory


## Credits

Check out [Skalety's Auto Potion](https://www.unknowncheats.me/forum/other-mmorpg-and-strategy/699378-epoch-auto-potion-copied-games.html) 


