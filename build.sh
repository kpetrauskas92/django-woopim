#!/usr/bin/env bash
set -o errexit  # Exit on error

# Configure storage paths
STORAGE_DIR=/opt/render/project/.render
CHROME_DIR="$STORAGE_DIR/chrome"
CHROMEDRIVER_PATH="$STORAGE_DIR/chromedriver"

# Install Google Chrome with caching
if [[ ! -d $CHROME_DIR ]]; then
  echo "🚀 Installing Google Chrome..."
  mkdir -p $CHROME_DIR
  cd $CHROME_DIR

  if ! wget -q -L --tries=3 \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    -O chrome.deb; then
    echo "❌ Failed to download Chrome. Exiting..."
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
CHROME_VERSION=$("$CHROME_DIR/opt/google/chrome/google-chrome" --version | awk '{print $3}')
echo "🔍 Detected Chrome version: $CHROME_VERSION"

# Install ChromeDriver with version matching
if [[ ! -f $CHROMEDRIVER_PATH ]]; then
  echo "🚀 Installing ChromeDriver..."

  MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
  CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$MAJOR_VERSION")

  if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "❌ Could not find matching ChromeDriver version. Exiting..."
    exit 1
  fi

  echo "🚀 Downloading ChromeDriver version: $CHROMEDRIVER_VERSION..."
  if ! wget -q -L --tries=3 \
    "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    -O chromedriver.zip; then
    echo "❌ Failed to download ChromeDriver. Exiting..."
    exit 1
  fi

  echo "📂 Extracting ChromeDriver..."
  unzip -o chromedriver.zip -d $STORAGE_DIR/
  rm chromedriver.zip
  chmod +x $CHROMEDRIVER_PATH

  if [[ -f $CHROMEDRIVER_PATH ]]; then
    echo "✅ ChromeDriver successfully installed at $CHROMEDRIVER_PATH"
  else
    echo "❌ ChromeDriver installation failed!"
    exit 1
  fi
else
  echo "✅ Using cached ChromeDriver..."
fi

# Final PATH setup
export PATH="$STORAGE_DIR:$PATH"

echo "✅ Successfully installed Chrome ($CHROME_VERSION) and ChromeDriver ($CHROMEDRIVER_VERSION)"