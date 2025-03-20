#!/bin/bash
pip install --upgrade pip
pip install playwright
playwright install-deps
playwright install chromium

# Manually install Chromium in Streamlit's Linux environment
apt-get update && apt-get install -y wget
mkdir -p /home/adminuser/.cache/ms-playwright
wget -qO- https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.60/linux64/chrome-linux64.zip | busybox unzip - -d /home/adminuser/.cache/ms-playwright/
chmod +x /home/adminuser/.cache/ms-playwright/chrome-linux64/chrome

echo "✅ Playwright and Chromium installed successfully!"
