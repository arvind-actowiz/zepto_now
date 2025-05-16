from bs4 import BeautifulSoup
import time
from core.driver_setup import get_driver
from core.database import DatabaseManager

def scrape_xml_urls(xml_url):
    """Scrape brand URLs and names from XML sitemap"""
    driver = get_driver(headless=True)
    try:
        # Fetch the XML page
        driver.get(xml_url)
        time.sleep(2)  # Wait for the page to load
        
        # Parse the XML content
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Extract data
        data = []
        for url_tag in soup.find_all('url'):
            loc = url_tag.find('loc')
            if loc:
                url = loc.text.strip()
                # Extract brand name from URL (assuming format: .../brand/BRAND_NAME/...)
                brand_name = url.split('/brand/')[-1].split('/')[0].replace('_', ' ')
                data.append({
                    'brand_name': brand_name,
                    'url': url,
                })
        
        return data
    
    finally:
        driver.quit()

if __name__ == "__main__":
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'zepto',
        'user': 'root',
        'password': 'actowiz',
        'port': 3306
    }

    xml_url = "https://www.zeptonow.com/sitemap/brands.xml"
    scraped_data = scrape_xml_urls(xml_url)
    
    with DatabaseManager(DB_CONFIG) as db:
        for item in scraped_data:
            print(f"Brand: {item['brand_name']}")
            print(f"URL: {item['url']}")
            print("-" * 50)

        db.insert_brands(scraped_data)
        
    print(f"Total brands scraped: {len(scraped_data)}")