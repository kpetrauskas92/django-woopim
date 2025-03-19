#!/bin/bash

echo "🚀 Installing Google Chrome..."
mkdir -p /opt/render/chrome

# Verified working Chrome .deb URL (version 113.0.5672.126)
CHROME_DEB_URL="https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_113.0.5672.126-1_amd64.deb"
wget -q -L --tries=3 "$CHROME_DEB_URL" -O /opt/render/chrome/chrome.deb

# Check if download succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to download Google Chrome. Exiting..."
    exit 1
fi

# Validate the .deb file integrity
if ! dpkg-deb -I /opt/render/chrome/chrome.deb >/dev/null 2>&1; then
    echo "❌ Downloaded Chrome .deb file is corrupted. Exiting..."
    exit 1
fi

# Extract and install Chrome
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Installing ChromeDriver..."
# Matching ChromeDriver version (113.0.5672.63)
CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip"
wget -q -L --tries=3 "$CHROMEDRIVER_URL" -O /opt/render/chrome/chromedriver.zip

# Check if download succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
fi

# Validate the ZIP file
if ! unzip -t /opt/render/chrome/chromedriver.zip >/dev/null 2>&1; then
    echo "❌ Downloaded ChromeDriver ZIP is corrupted. Exiting..."
    exit 1
fi

# Extract and prepare ChromeDriver
unzip -o /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver installed successfully!"