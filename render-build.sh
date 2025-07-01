#!/usr/bin/env bash

# Installer ffmpeg
apt-get update
apt-get install -y ffmpeg

# Installer les dépendances Python
pip install -r requirements.txt
