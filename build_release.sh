#!/bin/bash
# Build Last Epoch Auto Potion Release
pyinstaller \
  --onefile \
  --name="Last Epoch Auto Potion" \
  --icon=../imgs/PotionIcon.ico \
  --distpath release \
  --workpath build \
  --specpath release \
  src/main.py
