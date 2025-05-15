from bs4 import BeautifulSoup
import time
from core.driver_setup import get_driver

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
                    'lastmod': url_tag.find('lastmod').text if url_tag.find('lastmod') else None
                })
        
        return data
    
    finally:
        driver.quit()

if __name__ == "__main__":
    xml_url = "https://www.zeptonow.com/sitemap/brands.xml"
    scraped_data = scrape_xml_urls(xml_url)
    
    for item in scraped_data:
        print(f"Brand: {item['brand_name']}")
        print(f"URL: {item['url']}")
        if item['lastmod']:
            print(f"Last Modified: {item['lastmod']}")
        print("-" * 50)
    
    print(f"Total brands scraped: {len(scraped_data)}")