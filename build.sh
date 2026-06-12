#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# 1. Install your Python packages
pip install -r requirements.txt

# 2. Download the official static (portable) build of FFmpeg for Linux
echo "Downloading FFmpeg..."
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# 3. Extract the downloaded archive
tar -xf ffmpeg-release-amd64-static.tar.xz

# 4. Create a 'bin' folder and move the executable files into it
mkdir -p bin
mv ffmpeg-*-static/ffmpeg bin/
mv ffmpeg-*-static/ffprobe bin/

# 5. Clean up the leftover archive files to save space
rm -rf ffmpeg-*-static ffmpeg-release-amd64-static.tar.xz

echo "Build complete! FFmpeg is ready."

