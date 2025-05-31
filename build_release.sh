#!/bin/bash
# Build Last Epoch Auto Potion Release
pyinstaller \
  --clean \
  --onefile \
  --name="LE-AutoPot-v1.2.1" \
  --icon=../imgs/PotionIcon.ico \
  --distpath release \
  --workpath build \
  --specpath release \
  src/main.py
