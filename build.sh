#!/usr/bin/env bash
set -o errexit  # Exit immediately on any error

# Configure storage paths
STORAGE_DIR=/opt/render/project/.render
CHROME_DIR="$STORAGE_DIR/chrome"
CHROMEDRIVER_PATH="$STORAGE_DIR/chromedriver"

# Install Google Chrome with caching
if [[ ! -d $CHROME_DIR ]]; then
  echo "🚀 Installing Google Chrome..."
  mkdir -p $CHROME_DIR
  cd $CHROME_DIR
  
  # Download latest stable Chrome
  if ! wget -q -L --tries=3 \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    -O chrome.deb; then
    echo "❌ Failed to download Chrome. Exiting..."
    exit 1
  fi

  # Validate and extract package
  if ! dpkg-deb -I chrome.deb >/dev/null 2>&1; then
    echo "❌ Corrupted Chrome package. Exiting..."
    exit 1
  fi
  
  dpkg -x chrome.deb .
  rm chrome.deb
  cd - >/dev/null
else
  echo "✅ Using cached Chrome installation..."
fi

# Set up Chrome in PATH
export PATH="$CHROME_DIR/opt/google/chrome:$PATH"

# Get Chrome version details
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "🔍 Detected Chrome version: $CHROME_VERSION"

# Install ChromeDriver with version matching
if [[ ! -f $CHROMEDRIVER_PATH ]]; then
  echo "🚀 Installing ChromeDriver..."
  
  # Get major version number
  MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
  
  # Find latest compatible ChromeDriver version
  if ! CHROMEDRIVER_VERSION=$(wget -qO- \
    "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$MAJOR_VERSION"); then
    echo "❌ Failed to find ChromeDriver version. Exiting..."
    exit 1
  fi

  # Download ChromeDriver
  if ! wget -q -L --tries=3 \
    "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    -O chromedriver.zip; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
  fi

  # Validate and extract
  if ! unzip -t chromedriver.zip >/dev/null 2>&1; then
    echo "❌ Corrupted ChromeDriver package. Exiting..."
    exit 1
  fi
  
  unzip -o chromedriver.zip -d $STORAGE_DIR/
  rm chromedriver.zip
  chmod +x $CHROMEDRIVER_PATH
else
  echo "✅ Using cached ChromeDriver..."
fi

# Final PATH setup
export PATH="$STORAGE_DIR:$PATH"

echo "✅ Successfully installed Chrome ($CHROME_VERSION) and ChromeDriver ($CHROMEDRIVER_VERSION)"