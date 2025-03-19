#!/bin/bash

echo "🚀 Installing Google Chrome..."
mkdir -p /opt/render/chrome

# Updated Chrome .deb URL to a valid version
CHROME_DEB_URL="https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_113.0.5672.92-1_amd64.deb"
wget -q -L "$CHROME_DEB_URL" -O /opt/render/chrome/chrome.deb

# Check if Chrome download succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to download Google Chrome. Exiting..."
    exit 1
fi

# Extract Chrome .deb
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Installing ChromeDriver..."
# ChromeDriver version matching Chrome 113
CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip"
wget -q -L "$CHROMEDRIVER_URL" -O /opt/render/chrome/chromedriver.zip

# Check if ChromeDriver download succeeded
if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
fi

# Extract and prepare ChromeDriver
unzip -o /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver installed successfully!"