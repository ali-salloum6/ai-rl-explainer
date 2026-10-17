#!/usr/bin/env bash
# Install everything needed to build the video on Ubuntu 24.04 (the Claude Code cloud image).
set -euo pipefail
VENV=${VENV:-/opt/manim-venv}

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev python3-venv build-essential \
  texlive-latex-base texlive-latex-extra texlive-latex-recommended texlive-fonts-recommended \
  texlive-science dvisvgm cm-super fontconfig fonts-inter fonts-jetbrains-mono >/dev/null

if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip setuptools wheel
"$VENV/bin/pip" install -q -r "$(dirname "$0")/requirements.txt"
# Manim encodes scene clips at CRF 23; use 18 (visually lossless) for crisp text on the dark gradient.
WRITER=$("$VENV/bin/python" -c "import manim.scene.scene_file_writer as m; print(m.__file__)")
sed -i 's/"crf": "23"/"crf": "18"/' "$WRITER"
echo "ready: use $VENV/bin/python build.py ..."
