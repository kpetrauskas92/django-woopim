import time
import os
from django.utils.timezone import now
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from orders.models import Order, RetailVistaOrder  # Import models
from dotenv import load_dotenv

load_dotenv()

# ✅ Retail Vista Credentials
USERNAME = os.getenv("RETAIL_VISTA_USERNAME")
PASSWORD = os.getenv("RETAIL_VISTA_PASSWORD")
COMPANY_NUMBER = os.getenv("RETAIL_VISTA_COMPANY_NUMBER")


# 🚀 Setup WebDriver (MAXIMIZED)
def setup_driver():
    print("🚀 Setting up Selenium WebDriver...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--start-maximized")  # Keep browser visible
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# 🔑 Login Function
def login_to_retail_vista(driver):
    print("🔵 Logging into Retail Vista Login Page...")
    driver.get("https://www.retailvista.net/gcuk/RetailVista.aspx")

    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
    login_window = [w for w in driver.window_handles if w != driver.current_window_handle][0]
    driver.switch_to.window(login_window)
    print("✅ Switched to login window.")

    driver.switch_to.frame("DefaultFrame")
    print("✅ Switched to 'DefaultFrame' iframe.")

    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "ctl00$MasterContent$txtCompanyNumber$TextBox")))
    print("🔍 Login fields detected.")

    driver.find_element(By.NAME, "ctl00$MasterContent$txtCompanyNumber$TextBox").send_keys(COMPANY_NUMBER)
    driver.find_element(By.NAME, "ctl00$MasterContent$txtUsername$TextBox").send_keys(USERNAME)
    driver.find_element(By.NAME, "ctl00$MasterContent$txtPassword$TextBox").send_keys(PASSWORD)

    driver.find_element(By.NAME, "ctl00$MasterContent$cmdLogin").click()
    print("🔑 Logging in...")
    time.sleep(5)
    print(f"✅ Logged in. Current URL: {driver.current_url}")

# 🛒 Open Saleorder Maintenance
def open_saleorder_maintenance(driver):
    try:
        driver.switch_to.default_content()
        driver.switch_to.frame("DefaultFrame")
        print("✅ Switched to 'DefaultFrame' iframe.")

        saleorder_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Saleorder maintenance"))
        )
        print("✅ 'Saleorder Maintenance' link found. Clicking...")
        saleorder_link.click()

    except Exception as e:
        print(f"❌ Error: Could not click 'Saleorder Maintenance': {e}")
        return

    driver.switch_to.default_content()
    print("📄 Saleorder Maintenance link clicked. Waiting for modal...")

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ModalDialogContainer_433")))
        print("✅ Saleorder Maintenance modal detected!")
    except Exception as e:
        print(f"❌ Modal not found. Exiting...\n{e}")
        return

    time.sleep(3)
    modal_iframe = driver.find_elements(By.ID, "ModalDialogIFrame_433")
    if modal_iframe:
        print(f"🔍 Found modal iframe: {modal_iframe[0].get_attribute('id')}")
        driver.switch_to.frame(modal_iframe[0])
        print("✅ Switched to modal iframe.")
    else:
        print("❌ Modal iframe not found.")

# 🔄 Select Saleorder Type, Set Filters, Set Date, and Submit
def select_saleorder_type(driver, selected_date):
    """
    Selects the Saleorder Type, applies filters, and sets the order creation date.
    """

    try:
        print("🔄 Selecting Saleorder Type and filters...")

        # ✅ Select "DC: Webshop"
        try:
            dropdown = Select(driver.find_element(By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcSaleOrderClassId_ListBox"))
            dropdown.select_by_visible_text("DC: Webshop")
            print("✅ Selected 'DC: Webshop' from Saleorder Type.")
        except Exception as e:
            print(f"❌ Error selecting 'DC: Webshop': {e}")
            return

        # ✅ Select "All" for Open Sale Orders
        try:
            open_orders_filter = driver.find_element(By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcIsShowOpenSaleOrdersOnly_BooleanFilter_ALL")
            driver.execute_script("arguments[0].click();", open_orders_filter)
            print("✅ Selected 'All' for Open Sale Orders")
        except Exception as e:
            print(f"❌ Error selecting 'All' for Open Sale Orders: {e}")

        # ✅ Click Advanced tab
        print("🔄 Attempting to switch to 'Advanced' tab...")
        try:
            advanced_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//td[@title='Advanced']/div"))
            )
            driver.execute_script("arguments[0].click();", advanced_tab)
            time.sleep(2)
            print("✅ Clicked 'Advanced' tab.")
        except Exception as e:
            print(f"❌ Error clicking 'Advanced' tab: {e}")
            return

        # ✅ Enter Date
        try:
            date_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcOrderCreatedDateFrom_rvcOrderCreatedDateFrom_CalendarPicker_dateInput_text"))
            )
            date_field.clear()
            date_field.send_keys(selected_date)  # Use the passed date
            print(f"✅ Entered date '{selected_date}'")
        except Exception as e:
            print(f"❌ Error entering date '{selected_date}': {e}")
            return

        # ✅ Click Search button
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_cmdSearch"))
            )
            search_button.click()
            print("🔎 Clicked 'Search' button!")
        except Exception as e:
            print(f"❌ Error clicking 'Search' button: {e}")

    except Exception as e:
        print(f"❌ Unexpected error during selection process: {e}")

CANCEL_FLAG = "cancel_sync.flag"

def reset_sync():
    """Removes the cancel flag before a new sync starts."""
    if os.path.exists(CANCEL_FLAG):
        os.remove(CANCEL_FLAG)

def cancel_sync():
    """Creates a file flag to indicate the sync should be canceled."""
    with open(CANCEL_FLAG, "w") as f:
        f.write("1")

def is_sync_canceled():
    """Checks if sync cancellation flag exists."""
    return os.path.exists(CANCEL_FLAG)

def scrape_orders(log_message, driver, is_sync_canceled, selected_date):
    """Scrapes orders from RetailVista and updates WooCommerce orders."""
    reset_sync()  # Clear cancel flag before starting

    log_message("🚀 WebDriver initialized...")
    log_message(f"📅 Syncing Orders for Date: {selected_date}")

    try:
        login_to_retail_vista(driver)
        log_message("🔑 Logged into RetailVista.")

        open_saleorder_maintenance(driver)
        log_message("📄 Opened Saleorder Maintenance.")

        # ✅ Pass selected date into `select_saleorder_type`
        print(f"Selected Date: {selected_date}") 
        select_saleorder_type(driver, selected_date)
        log_message(f"✅ Orders filtered by selected date: {selected_date}")

        orders = []
        page_number = 1
        new_orders_count = 0  # Track new synced orders

        while True:
            if is_sync_canceled():
                log_message("❌ Sync Canceled! Stopping process.")
                return {"message": "❌ Sync Canceled!", "status": "warning"}

            log_message(f"📄 Scraping page {page_number}...")

            try:
                # ✅ Wait for results table to load
                results_table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_grdSearchResults_RetailVistaWrapper_grdSearchResults_dom"))
                )
                rows = results_table.find_elements(By.TAG_NAME, "tr")

                if len(rows) <= 1:  # No orders found
                    log_message(f"❌ No orders found for {selected_date}.")
                    break  # Exit loop if no orders exist

                for row in rows[1:]:  # Skip header row
                    if is_sync_canceled():
                        log_message("❌ Sync Canceled! Stopping immediately.")
                        return {"message": "❌ Sync Canceled!"}

                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 14:
                        # Extract Order Data
                        order_status = cells[3].text.strip()
                        customer_name_rv = cells[6].text.strip()
                        transport_type = cells[7].text.strip()
                        reference_code = cells[10].text.strip()
                        canceled_status = cells[13].text.strip()

                        # 🔄 Swap customer name format (Surname, Firstname → Firstname Surname)
                        if "," in customer_name_rv:
                            last_name, first_name = customer_name_rv.split(", ")
                            customer_name_rv = f"{first_name} {last_name}"

                        # ✅ Check if WooCommerce order exists
                        wc_order = Order.objects.filter(order_id=reference_code).first()

                        if wc_order:
                            log_message(f"✅ Found WooCommerce order {reference_code}. Updating details.")
                            wc_order.rv_order_status = order_status
                            wc_order.rv_canceled = canceled_status
                            wc_order.rv_last_synced = now()
                            wc_order.save()

                            # ✅ Create or update RetailVista order
                            rv_order, created = RetailVistaOrder.objects.update_or_create(
                                reference_code=reference_code,
                                defaults={
                                    "order_status": order_status,
                                    "customer_name": customer_name_rv,
                                    "transport_type": transport_type,
                                    "canceled_status": canceled_status,
                                    "last_synced": now(),
                                },
                            )

                            if created:
                                new_orders_count += 1
                        else:
                            log_message(f"❌ No matching WooCommerce order for Reference Code: {reference_code}")

                log_message(f"✅ Scraped {len(rows) - 1} orders from page {page_number}")

            except Exception as e:
                log_message(f"❌ Error scraping page {page_number}: {e}")
                break  # Stop if there's an error

            # ✅ Try to go to the next page
            try:
                log_message("➡️ Checking for next page link...")

                # Use the current page number to find and click the next page
                next_page_number = page_number + 1
                next_page = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//table[@class='GridPager']//a[text()='{next_page_number}']")
                    )
                )

                driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                log_message(f"🔍 Next page ({next_page_number}) link found. Clicking...")
                driver.execute_script("arguments[0].click();", next_page)
                log_message(f"✅ Clicked page {next_page_number} successfully.")
                time.sleep(3)
                page_number += 1

            except Exception as e:
                log_message(f"🚫 Pagination issue on page {page_number}: {e}")
                log_message("🚀 No more pages or pagination link issue. Scraping complete!")
                break

        log_message(f"✅ Sync complete! {new_orders_count} new orders synced.")

    except Exception as e:
        log_message(f"❌ Critical error during sync: {e}")
        return {"message": f"❌ Error: {e}", "status": "error"}

    finally:
        if driver:
            driver.quit()  # ✅ Ensure WebDriver quits if it exists

    return {"message": f"✅ Sync complete! {new_orders_count} new orders.", "status": "success"}
