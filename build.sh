echo "🚀 Installing Google Chrome..."
mkdir -p /opt/render/chrome
wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O /opt/render/chrome/chrome.deb
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9]+' | head -1)
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /opt/render/chrome/chromedriver.zip
unzip /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver installed successfully!"