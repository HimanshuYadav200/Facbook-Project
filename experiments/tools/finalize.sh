#!/bin/zsh
# Normalize loudness to social-media level (-14 LUFS, peaks under -1.5 dB). Video is copied untouched.
# Usage: tools/finalize.sh <in.mp4> <out.mp4>
ffmpeg -hide_banner -loglevel error -y -i "$1" -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:v copy -c:a aac -b:a 192k "$2"
