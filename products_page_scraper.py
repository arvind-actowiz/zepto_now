import os
import requests
from core.database import DatabaseManager
from core.config import DB_CONFIG

class ProductHTMLSaver:
    def __init__(self, db_config: dict, output_dir: str = "product_html"):
        """
        Initialize the HTML saver with database config and output directory
        
        Args:
            db_config: Database configuration dictionary
            output_dir: Directory to save HTML files (default: 'product_html')
        """
        self.db_config = db_config
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_products(self) -> list:
        """Fetch all products from the database"""
        with DatabaseManager(self.db_config) as db:
            db.cursor.execute("SELECT id, product_name, product_url FROM products")
            return db.cursor.fetchall()

    def save_html_for_products(self):
        """Process all products, fetch their HTML and save to files"""
        products = self.fetch_products()
        print(f"Found {len(products)} products to process")

        for product in products:
            try:
                product_id = product['id']
                product_name = self.sanitize_filename(product['product_name'])
                url = product['product_url']

                product_uid = url.split('/')[-1]
                
                print(f"Processing product {product_id}: {product_name}")
                print(f"Product UID: {product_uid}")

                # Check if file already exists
                filename = f"{product_uid}.html"
                filepath = os.path.join(self.output_dir, filename)
                
                if os.path.exists(filepath):
                    print(f"HTML file already exists for product {product_id}, skipping download")
                    continue

                # Fetch HTML content
                html_content = self.fetch_html(url)
                if not html_content:
                    continue

                # Save to file
                self.save_to_file(filepath, html_content)
                
                print(f"Saved HTML for product {product_id} to {filepath}")

            except Exception as e:
                print(f"Failed to process product {product.get('id')}: {str(e)}")
                continue

    def fetch_html(self, url: str) -> str:
        """Fetch HTML content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL {url}: {str(e)}")
            return None

    def save_to_file(self, filepath: str, content: str):
        """Save content to a file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            print(f"Failed to save file {filepath}: {str(e)}")
            raise

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize the filename to remove invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]  # Limit filename length


if __name__ == "__main__":
    # Create and run the HTML saver
    html_saver = ProductHTMLSaver(DB_CONFIG)
    html_saver.save_html_for_products()