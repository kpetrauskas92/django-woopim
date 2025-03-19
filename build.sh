echo "🚀 Installing Google Chrome..."
mkdir -p /opt/render/chrome
wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O /opt/render/chrome/chrome.deb
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Checking installed Chrome version..."
CHROME_VERSION=$(/opt/render/chrome/opt/google/chrome/google-chrome --version | grep -oP '[0-9]+\.[0-9]+\.[0-9]+')

echo "🚀 Chrome version detected: $CHROME_VERSION"

echo "🚀 Installing ChromeDriver matching version $CHROME_VERSION..."
CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "❌ Failed to get ChromeDriver version. Using fallback latest version..."
    CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
fi

wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /opt/render/chrome/chromedriver.zip

if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
fi

unzip -o /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver installed successfully!"