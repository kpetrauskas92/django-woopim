echo "🚀 Installing Google Chrome..."
mkdir -p /opt/render/chrome
wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O /opt/render/chrome/chrome.deb
dpkg -x /opt/render/chrome/chrome.deb /opt/render/chrome/
rm /opt/render/chrome/chrome.deb
export PATH="/opt/render/chrome/opt/google/chrome/:$PATH"

echo "🚀 Checking installed Chrome version..."
CHROME_VERSION=$(/opt/render/chrome/opt/google/chrome/google-chrome --version | grep -oP '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

echo "🚀 Chrome version detected: $CHROME_VERSION"

# Extract major version only (e.g., 134 from 134.0.6998)
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)

echo "🚀 Fetching latest compatible ChromeDriver for major version: $CHROME_MAJOR_VERSION"

# Fetch the latest available ChromeDriver version for the detected Chrome version
CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION")

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "❌ No exact match found. Fetching the latest available ChromeDriver version..."
    CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
fi

echo "🚀 Downloading ChromeDriver version: $CHROMEDRIVER_VERSION..."
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /opt/render/chrome/chromedriver.zip

if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
fi

echo "✅ Extracting ChromeDriver..."
unzip -o /opt/render/chrome/chromedriver.zip -d /opt/render/chrome/
rm /opt/render/chrome/chromedriver.zip
chmod +x /opt/render/chrome/chromedriver
export PATH="/opt/render/chrome/:$PATH"

echo "✅ Chrome & ChromeDriver installed successfully!"