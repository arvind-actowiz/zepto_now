from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from core.driver_setup import get_driver
from core.database import DatabaseManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from core.config import DB_CONFIG
from threading import Thread
from queue import Queue
import traceback

# Thread-safe queue for tasks and results
task_queue = Queue()
result_queue = Queue()

def worker():
    """Worker function for each thread to process brands"""
    # Each thread gets its own driver instance
    driver = get_driver(headless=True)
    actions = ActionChains(driver)
    
    while True:
        brand = task_queue.get()
        if brand is None:  # Poison pill to stop the worker
            driver.quit()
            task_queue.task_done()
            break
            
        try:
            print(f"Processing brand: {brand['brand_name']} in thread")
            products = scrape_brand_products(driver, actions, brand['url'])
            
            # Add brand info to each product
            for product in products:
                product.update({
                    'brand_name': brand['brand_name'],
                    'brand_url': brand['url']
                })
            
            result_queue.put({
                'products': products,
                'brand_id': brand['id']
            })
        except Exception as e:
            print(f"Failed to process brand {brand['brand_name']}: {e}")
            traceback.print_exc()
        finally:
            task_queue.task_done()

def scrape_brand_products(driver, actions, brand_url):
    """Scrape product names and URLs from a brand's product page using pure Selenium"""
    try:
        # Open URL in current tab
        driver.get(brand_url)

        try:
            driver.find_element(
                "xpath", 
                '//h2[contains(text(), "No products found for this brand")]'
            )
            print("No products available for this brand")
            return []
        except NoSuchElementException:
            print("Products are available")

        # Wait for products to load initially
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-card"]'))
        )
        
        # Scroll to load all products
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            faq_ele = driver.find_element(By.XPATH, "//h2[text()='Frequently Asked Questions']")
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
                faq_ele
            )

            # Wait to get products loaded
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No products to load further")
                break
            last_height = new_height
        
        products = []
        # Find all product cards
        product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"]')
                
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
        pass

if __name__ == "__main__":
    # Number of threads (adjust based on your system capabilities)
    NUM_THREADS = 4
    
    # Create and start worker threads
    threads = []
    for i in range(NUM_THREADS):
        t = Thread(target=worker)
        t.start()
        threads.append(t)
    
    with DatabaseManager(DB_CONFIG) as db:
        # Get all brands to process
        brands = db.get_pending_brands()
        print(f"Found {len(brands)} brands to process")
        
        # Add brands to the task queue
        for brand in brands:
            task_queue.put(brand)
        
        # Process results as they come in
        processed = 0
        while processed < len(brands):
            result = result_queue.get()
            try:
                # Store products
                db.insert_products(result['products'])
                # Mark brand as completed in DB
                db.mark_brand_completed(result['brand_id'])
                processed += 1
                print(f"Completed {processed}/{len(brands)} brands")
            except Exception as e:
                print(f"Error saving results for brand ID {result['brand_id']}: {e}")
            finally:
                result_queue.task_done()
    
    # Stop workers by sending None for each thread
    for i in range(NUM_THREADS):
        task_queue.put(None)
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print("All brands processed")