from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from core.driver_setup import get_driver
from core.database import DatabaseManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from core.config import DB_CONFIG


def scrape_brand_products(driver, actions, brand_url):
    """Scrape product names and URLs from a brand's product page using pure Selenium"""
    try:
        # Open new tab and switch to it
        driver.execute_script(f"window.open('{brand_url}');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            driver.find_element(
                "xpath", 
                '//h2[contains(text(), "No products found for this brand")]'
            )
            print("No products available for this brand")
            return []
        except NoSuchElementException:
            print(" Products are available")

        # Wait for products to load initially
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-card"]'))
        )
        
        # Scroll to load all products
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll to the last product element to load products
            product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"]')
            actions.move_to_element(product_cards[-1]).perform()

            # Wait to get products loaded
            time.sleep(2)
            new_height= driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No products to load further")
                break
            last_height = new_height
        
        products = []
        # Find all product cards
        product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"]')
                
        products = []
        for product in product_cards:
            try:
                name_element = product.find_element(By.CSS_SELECTOR, "h5")
                product_name = name_element.text.strip()
                product_url = product.get_attribute("href")
                
                # Ensure URL is absolute
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www.zeptonow.com{product_url}"
                
                products.append({
                    "product_name": product_name,
                    "product_url": product_url
                })
            except Exception as e:
                print(f"Error processing a product: {str(e)}")
                continue
                
        return products
    
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

if __name__ == "__main__":
    # Initialize driver
    driver = get_driver(headless=False)
    actions = ActionChains(driver)

    with DatabaseManager(DB_CONFIG) as db:
        brands = db.get_pending_brands()
        print(f"Found {len(brands)} brands to process")

        for brand in brands:
            try:
                print(f"Processing brand: {brand['brand_name']}")
                
                # Scrape products
                products = scrape_brand_products(driver, actions, brand['url'])
                
                # Add brand info to each product
                for product in products:
                    product.update({
                        'brand_name': brand['brand_name'],
                        'brand_url': brand['url']
                    })

                # Store products
                db.insert_products(products)

                # Mark brand as completed in DB
                db.mark_brand_completed(brand['id'])
            except Exception as e:
                print(f"Failed to process brand {brand['brand_name']}: {e}")
                continue
