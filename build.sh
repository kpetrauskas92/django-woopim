#!/usr/bin/env bash
set -o errexit   # Exit immediately on any error
set -o nounset   # Exit on unset variables
set -o xtrace    # Print commands as they are executed (debug mode)

echo "==== Starting build.sh script ===="
echo "Timestamp: $(date)"
echo "Current directory: $(pwd)"

# Configure storage paths
STORAGE_DIR="/opt/render/project/.render"
CHROME_DIR="$STORAGE_DIR/chrome"
CHROMEDRIVER_PATH="$STORAGE_DIR/chromedriver"

echo "STORAGE_DIR: $STORAGE_DIR"
echo "CHROME_DIR: $CHROME_DIR"
echo "CHROMEDRIVER_PATH: $CHROMEDRIVER_PATH"

# Install Google Chrome with caching
if [[ ! -d $CHROME_DIR ]]; then
  echo "🚀 Installing Google Chrome..."
  mkdir -p "$CHROME_DIR"
  cd "$CHROME_DIR" || { echo "❌ Failed to cd into $CHROME_DIR"; exit 1; }
  
  # Download latest stable Chrome
  echo "Downloading Chrome from https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
  if ! wget -q -L --tries=3 "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O chrome.deb; then
    echo "❌ Failed to download Chrome. Exiting..."
    exit 1
  fi
  echo "Download complete. Verifying package integrity..."
  
  # Validate the package
  if ! dpkg-deb -I chrome.deb >/dev/null 2>&1; then
    echo "❌ Corrupted Chrome package detected. Exiting..."
    exit 1
  fi
  
  echo "Package integrity verified. Extracting Chrome package..."
  dpkg -x chrome.deb .
  rm chrome.deb
  echo "Chrome package extracted successfully."
  cd - || { echo "❌ Failed to return to previous directory"; exit 1; }
else
  echo "✅ Using cached Chrome installation..."
fi

# Set up Chrome in PATH
export PATH="$CHROME_DIR/opt/google/chrome:$PATH"
echo "Updated PATH for Chrome: $PATH"

# Verify google-chrome is available
if ! command -v google-chrome >/dev/null 2>&1; then
  echo "❌ google-chrome command not found in PATH. Exiting..."
  exit 1
fi

# Get Chrome version details
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "🔍 Detected Chrome version: $CHROME_VERSION"

# Install ChromeDriver with version matching
if [[ ! -f $CHROMEDRIVER_PATH ]]; then
  echo "🚀 Installing ChromeDriver..."
  
  # Get major version number
  MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
  echo "Extracted Chrome major version: $MAJOR_VERSION"
  
  if [[ "$MAJOR_VERSION" -eq 134 ]]; then
    echo "Detected Chrome major version 134. Using stable ChromeDriver for testing."
    CHROMEDRIVER_VERSION="134.0.6998.90"
    DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
  else
    # Find latest compatible ChromeDriver version using version-specific endpoint
    CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$MAJOR_VERSION" || true)
    echo "ChromeDriver version from version-specific endpoint: '$CHROMEDRIVER_VERSION'"
    
    # Fallback to latest release if version-specific endpoint returns empty
    if [[ -z "$CHROMEDRIVER_VERSION" ]]; then
      echo "⚠️ ChromeDriver version for Chrome major version $MAJOR_VERSION not found. Trying fallback to latest release."
      CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE" || true)
      echo "ChromeDriver version from fallback endpoint: '$CHROMEDRIVER_VERSION'"
    fi
    
    if [[ -z "$CHROMEDRIVER_VERSION" ]]; then
      echo "❌ Failed to retrieve a ChromeDriver version. Exiting..."
      exit 1
    fi
    
    DRIVER_URL="https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
  fi

  echo "Downloading ChromeDriver from $DRIVER_URL"
  if ! wget -q -L --tries=3 "$DRIVER_URL" -O chromedriver.zip; then
    echo "❌ Failed to download ChromeDriver from $DRIVER_URL. Exiting..."
    exit 1
  fi

  echo "Verifying ChromeDriver zip file integrity..."
  if ! unzip -t chromedriver.zip >/dev/null 2>&1; then
    echo "❌ ChromeDriver package appears to be corrupted. Exiting..."
    exit 1
  fi
  
  echo "Extracting ChromeDriver zip to $STORAGE_DIR..."
  unzip -o chromedriver.zip -d "$STORAGE_DIR/"
  rm chromedriver.zip
  chmod +x "$CHROMEDRIVER_PATH"
  echo "ChromeDriver installed successfully."
else
  echo "✅ Using cached ChromeDriver..."
  CHROMEDRIVER_VERSION=$("$CHROMEDRIVER_PATH" --version | awk '{print $2}')
fi

# Final PATH setup
export PATH="$STORAGE_DIR:$PATH"
echo "Final PATH including ChromeDriver: $PATH"

echo "✅ Successfully installed Chrome ($CHROME_VERSION) and ChromeDriver ($CHROMEDRIVER_VERSION)"
echo "==== build.sh script completed ===="
