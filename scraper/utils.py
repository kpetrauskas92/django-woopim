import time
import os
from django.utils.timezone import now
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import WebDriverException, TimeoutException
from orders.models import Order, RetailVistaOrder
from dotenv import load_dotenv

load_dotenv()

# Configuration
USERNAME = os.getenv("RETAIL_VISTA_USERNAME")
PASSWORD = os.getenv("RETAIL_VISTA_PASSWORD")
COMPANY_NUMBER = os.getenv("RETAIL_VISTA_COMPANY_NUMBER")
CHROME_VERSION = "114.0.5735.90"  # Stable Chrome for Testing version

def setup_driver():
    """Configure ChromeDriver with Heroku-compatible settings"""
    print("🚀 Initializing WebDriver...")
    
    options = webdriver.ChromeOptions()
    is_heroku = "DYNO" in os.environ
    
    # Common Chrome options
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920x1080")

    if is_heroku:
        print("🌍 Configuring for Heroku environment")
        chrome_bin = "/app/.chrome-for-testing/chrome-linux64/chrome"
        chromedriver_bin = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"

        # Verify binaries
        if not all([os.path.exists(chrome_bin), os.path.exists(chromedriver_bin)]):
            raise FileNotFoundError("Missing Chrome binaries")

        # Set execute permissions
        if not os.access(chromedriver_bin, os.X_OK):
            os.chmod(chromedriver_bin, 0o755)

        # Cleanup previous processes
        os.system("pkill -f chrome || true")
        os.system("pkill -f chromedriver || true")

        options.binary_location = chrome_bin

        # Retry initialization
        for attempt in range(3):
            try:
                driver = webdriver.Chrome(
                    service=Service(chromedriver_bin),
                    options=options
                )
                print("✅ ChromeDriver initialized successfully")
                return driver
            except WebDriverException as e:
                print(f"⚠️ Attempt {attempt+1}/3 failed: {str(e)[:100]}")
                time.sleep(2)
        raise RuntimeError("Failed to initialize ChromeDriver after 3 attempts")
    
    else:  # Local development
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

def login_to_retail_vista(driver):
    """Robust login handling with explicit waits"""
    print("🔐 Starting login process...")
    
    driver.get("https://www.retailvista.net/gcuk/RetailVista.aspx")

    try:
        # Wait for login window
        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))
        windows = driver.window_handles
        driver.switch_to.window(windows[1])
        
        # Frame handling
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it("DefaultFrame")
        )
        
        # Form interaction
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "ctl00$MasterContent$txtCompanyNumber$TextBox"))
        ).send_keys(COMPANY_NUMBER)
        
        driver.find_element(By.NAME, "ctl00$MasterContent$txtUsername$TextBox").send_keys(USERNAME)
        driver.find_element(By.NAME, "ctl00$MasterContent$txtPassword$TextBox").send_keys(PASSWORD)
        driver.find_element(By.NAME, "ctl00$MasterContent$cmdLogin").click()
        
        # Verify successful login
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ctl00_Header1_lblContext"))
        )
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        raise

def handle_modal_interaction(driver):
    """Handle modal dialogs and frame switching"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "ModalDialogIFrame_433"))
        )
        driver.switch_to.frame("ModalDialogIFrame_433")
        print("✅ Switched to modal frame")
        return True
    except TimeoutException:
        print("⚠️ Modal dialog not found")
        return False

def perform_search(driver, selected_date):
    """Execute search with date filtering"""
    print(f"🔍 Searching orders for {selected_date}")
    
    try:
        # Select sale order type
        Select(driver.find_element(By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcSaleOrderClassId_ListBox")
            ).select_by_visible_text("DC: Webshop")
        
        # Set date filter
        driver.find_element(By.XPATH, "//td[@title='Advanced']/div").click()
        date_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcOrderCreatedDateFrom_rvcOrderCreatedDateFrom_CalendarPicker_dateInput_text"))
        )
        date_field.clear()
        date_field.send_keys(selected_date)
        
        # Execute search
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_cmdSearch"))
        ).click()
        
        print("✅ Search executed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return False

def scrape_orders(log_message, selected_date):
    """Main scraping workflow with enhanced error handling"""
    driver = None
    try:
        driver = setup_driver()
        login_to_retail_vista(driver)
        
        # Navigate to sales orders
        driver.find_element(By.LINK_TEXT, "Saleorder maintenance").click()
        if not handle_modal_interaction(driver):
            return {"status": "error", "message": "Modal interaction failed"}
        
        if not perform_search(driver, selected_date):
            return {"status": "error", "message": "Search failed"}
        
        # Pagination handling
        page_number = 1
        while True:
            print(f"📖 Processing page {page_number}")
            
            # Process orders
            orders_table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_grdSearchResults_RetailVistaWrapper_grdSearchResults_dom"))
            )
            process_orders(orders_table, log_message)
            
            # Pagination
            try:
                next_page = driver.find_element(By.XPATH, f"//a[text()='{page_number + 1}']")
                driver.execute_script("arguments[0].scrollIntoView();", next_page)
                next_page.click()
                page_number += 1
                time.sleep(2)  # Allow page load
            except:
                print("✅ Reached last page")
                break
        
        return {"status": "success", "message": "Sync completed"}
    
    except Exception as e:
        log_message(f"❌ Critical error: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

def process_orders(table, log_message):
    """Process individual orders from table"""
    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 14:
            continue
            
        # Extract order data
        order_data = {
            "status": cells[3].text.strip(),
            "customer": cells[6].text.replace(",", ""),  # Simple name formatting
            "reference": cells[10].text.strip(),
            "canceled": cells[13].text.strip()
        }
        
        # Update database
        try:
            order, created = RetailVistaOrder.objects.update_or_create(
                reference_code=order_data["reference"],
                defaults={
                    "order_status": order_data["status"],
                    "customer_name": order_data["customer"],
                    "canceled_status": order_data["canceled"],
                    "last_synced": now()
                }
            )
            log_message(f"🔄 {'Created' if created else 'Updated'} order {order_data['reference']}")
        except Exception as e:
            log_message(f"❌ Database error: {str(e)}")