import time
import django
import os
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from scraper.models import RetailVistaOrder  # Import your Django model


class Command(BaseCommand):
    help = "Scrapes orders from Retail Vista and updates the database"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting Retail Vista order scraping...")

        driver = setup_driver()
        login_to_retail_vista(driver)
        open_saleorder_maintenance(driver)
        driver.quit()

        self.stdout.write(self.style.SUCCESS("✅ Scraping complete!"))


# ✅ Retail Vista Credentials
USERNAME = "Karolis"
PASSWORD = "Karpet157"
COMPANY_NUMBER = "25"

# 🚀 Setup WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Runs browser in background
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


# 🔑 Login Function
def login_to_retail_vista(driver):
    driver.get("https://www.retailvista.net/gcuk/RetailVista.aspx")
    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

    login_window = [w for w in driver.window_handles if w != driver.current_window_handle][0]
    driver.switch_to.window(login_window)
    driver.switch_to.frame("DefaultFrame")

    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "ctl00$MasterContent$txtCompanyNumber$TextBox")))

    driver.find_element(By.NAME, "ctl00$MasterContent$txtCompanyNumber$TextBox").send_keys(COMPANY_NUMBER)
    driver.find_element(By.NAME, "ctl00$MasterContent$txtUsername$TextBox").send_keys(USERNAME)
    driver.find_element(By.NAME, "ctl00$MasterContent$txtPassword$TextBox").send_keys(PASSWORD)
    driver.find_element(By.NAME, "ctl00$MasterContent$cmdLogin").click()

    time.sleep(5)  # Wait for login


# 🛒 Open Saleorder Maintenance
def open_saleorder_maintenance(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame("DefaultFrame")

    saleorder_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Saleorder maintenance"))
    )
    saleorder_link.click()

    driver.switch_to.default_content()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ModalDialogContainer_433")))
    time.sleep(3)

    modal_iframe = driver.find_elements(By.ID, "ModalDialogIFrame_433")
    if modal_iframe:
        driver.switch_to.frame(modal_iframe[0])
        select_saleorder_type(driver)


# 🔄 Select Saleorder Type, Set Filters, Set Date, and Submit
def select_saleorder_type(driver):
    dropdown = Select(driver.find_element(By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcSaleOrderClassId_ListBox"))
    dropdown.select_by_visible_text("DC: Webshop")

    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, 
        "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcIsShowOpenSaleOrdersOnly_BooleanFilter_ALL"))
    
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, 
        "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcHasPendingPrePaymentsOnly_BooleanFilter_ALL"))
    
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, 
        "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcIsCancelledOnly_BooleanFilter_ALL"))

    # ✅ Click "Advanced" tab
    advanced_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//td[@title='Advanced']/div"))
    )
    driver.execute_script("arguments[0].click();", advanced_tab)
    time.sleep(2)

    # ✅ Enter Date
    date_field = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_rvcOrderCreatedDateFrom_rvcOrderCreatedDateFrom_CalendarPicker_dateInput_text"))
    )
    date_field.clear()
    date_field.send_keys("1/1/2025 1:00 AM")

    # ✅ Click Search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_cmdSearch"))
    )
    search_button.click()

    # ✅ Scrape Search Results
    scrape_orders(driver)


# 🏆 Function to scrape and store orders in Django DB
def scrape_orders(driver):
    page_number = 1

    while True:
        print(f"📄 Scraping page {page_number}...")

        try:
            results_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_ctl00_MasterContent_MainContent_ctl00_grdSearchResults_RetailVistaWrapper_grdSearchResults_dom"))
            )
            
            rows = results_table.find_elements(By.TAG_NAME, "tr")

            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")

                if len(cells) >= 14:
                    reference_code = cells[10].text.strip()
                    order_status = cells[3].text.strip()
                    customer = cells[6].text.strip()
                    transport_type = cells[7].text.strip()
                    canceled_status = cells[13].text.strip()

                    order, created = RetailVistaOrder.objects.update_or_create(
                        reference_code=reference_code,
                        defaults={
                            "order_status": order_status,
                            "customer": customer,
                            "transport_type": transport_type,
                            "canceled_status": canceled_status
                        }
                    )

                    print(f"{'🆕 New' if created else '🔄 Updated'} order: {reference_code}")

        except:
            print("🚀 No more pages. Scraping complete!")
            break
