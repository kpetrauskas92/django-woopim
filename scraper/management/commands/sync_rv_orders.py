import time
import os
import datetime
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import WebDriverException
from django.conf import settings
from orders.models import Order, RetailVistaOrder  # Import models
from scraper.utils import login_to_retail_vista, open_saleorder_maintenance, select_saleorder_type
from dotenv import load_dotenv

load_dotenv()

# ✅ Retail Vista Credentials
USERNAME = os.getenv("RETAIL_VISTA_USERNAME")
PASSWORD = os.getenv("RETAIL_VISTA_PASSWORD")
COMPANY_NUMBER = os.getenv("RETAIL_VISTA_COMPANY_NUMBER")


# Detect Heroku dyno
is_heroku = "DYNO" in os.environ

if is_heroku:
    LOG_FILE = "/tmp/rv_sync.log"
else:
    LOG_DIR = os.path.join(settings.BASE_DIR, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)  # ✅ Ensure it exists only in local dev
    LOG_FILE = os.path.join(LOG_DIR, "rv_sync.log")


class Command(BaseCommand):
    help = "Sync RetailVista orders with WooCommerce"

    def handle(self, *args, **kwargs):
        sync_time = now().strftime("%Y-%m-%d %H:%M:%S")
        unmatched_orders = []

        with open(LOG_FILE, "a", encoding="utf-8") as logfile:

            def log(msg):
                self.stdout.write(msg)
                logfile.write(f"{msg}\n")

            log(f"\n================== SYNC START: {sync_time} ==================\n")

            driver = setup_driver()
            if not driver:
                log("❌ Failed to initialize WebDriver.")
                return

            selected_date = (now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")

            def log_message(msg):
                log(msg)
                if msg.startswith("❌ No matching WooCommerce order"):
                    unmatched_orders.append(msg)

            result = scrape_orders(log_message, driver, selected_date)

            log("\n================== SYNC SUMMARY ==================")
            log(f"🕓 Sync Time: {sync_time}")
            log(result["message"])
            log(f"🔍 Orders on RV but NOT in WooCommerce: {len(unmatched_orders)}")

            if unmatched_orders:
                log("❗ List of missing WooCommerce orders:")
                for msg in unmatched_orders:
                    log(f" - {msg}")

            log("\n================== SYNC COMPLETE ==================\n")


def setup_driver():
    """Sets up Selenium WebDriver for Heroku or local development."""
    print("🚀 Setting up Selenium WebDriver...")

    is_heroku = "DYNO" in os.environ  # Check if running on Heroku
    options = webdriver.ChromeOptions()

    # ✅ Stability Flags to Prevent Crashes
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-popup-blocking")

    if is_heroku:
        print("🌍 Running in HEROKU production mode...")

        # ✅ Chrome & ChromeDriver paths
        chrome_binary = "/app/.chrome-for-testing/chrome-linux64/chrome"
        chromedriver_binary = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"

        # ✅ Verify ChromeDriver binary exists
        if not os.path.exists(chromedriver_binary):
            raise FileNotFoundError(f"🚨 ChromeDriver not found at {chromedriver_binary}")

        # ✅ Set Chrome binary location
        options.binary_location = chrome_binary

        # ✅ Ensure ChromeDriver has execute permissions
        if not os.access(chromedriver_binary, os.X_OK):
            os.chmod(chromedriver_binary, 0o755)

        # ✅ Kill any lingering Chrome processes
        os.system("pkill -f chrome || true")
        os.system("pkill -f chromedriver || true")

        try:
            driver = webdriver.Chrome(service=Service(chromedriver_binary), options=options)
            print("✅ ChromeDriver launched successfully!")
            return driver
        except WebDriverException as e:
            print(f"❌ Failed to launch ChromeDriver: {e}")
            return None

    else:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def scrape_orders(log_message, driver, selected_date):
    """Scrapes orders from RetailVista and updates WooCommerce orders."""
    log_message(f"📅 Syncing Orders for Date: {selected_date}")

    try:
        login_to_retail_vista(driver)
        log_message("🔑 Logged into RetailVista.")

        open_saleorder_maintenance(driver)
        log_message("📄 Opened Saleorder Maintenance.")

        # ✅ Select Saleorder Type & Set Date
        select_saleorder_type(driver, selected_date)
        log_message(f"✅ Orders filtered by selected date: {selected_date}")

        orders = []
        page_number = 1
        new_orders_count = 0

        while True:
            log_message(f"📄 Scraping page {page_number}...")

            try:
                results_table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_grdSearchResults_RetailVistaWrapper_grdSearchResults_dom"))
                )
                rows = results_table.find_elements(By.TAG_NAME, "tr")

                if len(rows) <= 1:
                    log_message(f"❌ No orders found for {selected_date}.")
                    break

                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 14:
                        order_status = cells[3].text.strip()
                        customer_name_rv = cells[6].text.strip()
                        reference_code = cells[10].text.strip()

                        if "," in customer_name_rv:
                            last_name, first_name = customer_name_rv.split(", ")
                            customer_name_rv = f"{first_name} {last_name}"

                        # ✅ Check if WooCommerce order exists
                        wc_order = Order.objects.filter(order_id=reference_code).first()

                        if wc_order:
                            log_message(f"✅ Found WooCommerce order {reference_code}. Updating details.")
                            wc_order.rv_order_status = order_status
                            wc_order.rv_last_synced = now()
                            wc_order.save()

                            # ✅ Create or update RetailVista order
                            rv_order, created = RetailVistaOrder.objects.update_or_create(
                                reference_code=reference_code,
                                defaults={
                                    "order_status": order_status,
                                    "customer_name": customer_name_rv,
                                    "last_synced": now(),
                                },
                            )

                            if created:
                                new_orders_count += 1

                log_message(f"✅ Scraped {len(rows) - 1} orders from page {page_number}")

            except Exception as e:
                log_message(f"❌ Error scraping page {page_number}: {e}")
                break

            try:
                next_page_number = page_number + 1
                next_page = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//table[@class='GridPager']//a[text()='{next_page_number}']"))
                )

                driver.execute_script("arguments[0].click();", next_page)
                log_message(f"✅ Clicked page {next_page_number} successfully.")
                time.sleep(3)
                page_number += 1

            except Exception:
                log_message("🚀 No more pages. Scraping complete!")
                break

        log_message(f"✅ Sync complete! {new_orders_count} new orders synced.")

    except Exception as e:
        log_message(f"❌ Critical error during sync: {e}")
        return {"message": f"❌ Error: {e}", "status": "error"}

    finally:
        if driver:
            driver.quit()

    return {"message": f"✅ Sync complete! {new_orders_count} new orders.", "status": "success"}
