#!/usr/bin/env bash
set -euo pipefail

# Add Google's apt repo
sudo apt-get update -y
sudo apt-get install -y wget gnupg
wget -qO- https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-linux-signing-key.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Install Chrome + dependencies
sudo apt-get update -y
sudo apt-get install -y google-chrome-stable

# Sanity check
which google-chrome && google-chrome --version
echo "[ok] Google Chrome installed."

