echo "🚀 Installing Google Chrome (version 113)..."
mkdir -p /opt/render/chrome
wget -q "https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_113.0.5672.126-1_amd64.deb" -O /opt/render/chrome/chrome.deb
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Installing ChromeDriver (version 113)..."
wget -q "https://chromedriver.storage.googleapis.com/113.0.5672.126/chromedriver_linux64.zip" -O /opt/render/chrome/chromedriver.zip

if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
fi

unzip -o /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver (version 113) installed successfully!"