# Install Google Chrome
echo "🚀 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update && sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
echo "🚀 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9]+' | head -1)
wget -q "https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
rm chromedriver_linux64.zip

echo "✅ Chrome & ChromeDriver installed successfully!"