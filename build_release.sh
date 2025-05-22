#!/bin/bash
# Build Last Epoch Auto Potion Release
pyinstaller \
  --onefile \
  --name="LE-AutoPot" \
  --icon=../imgs/PotionIcon.ico \
  --distpath release \
  --workpath build \
  --specpath release \
  src/main.py
