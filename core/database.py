import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_config: Dict):
        """
        Initialize database connection with configuration
        
        Args:
            db_config: Dictionary containing database credentials
                {
                    'host': 'localhost',
                    'database': 'your_db',
                    'user': 'your_user',
                    'password': 'your_password',
                    'port': 3306
                }
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None

    def __enter__(self):
        """Connect to database when entering context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context manager"""
        self.close()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            print("Successfully connected to database")
        except Error as e:
            print(f"Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None):
        """Execute a single SQL query"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor
        except Error as e:
            self.connection.rollback()
            print(f"Query failed: {e}\nQuery: {query}")
            raise
    
    def get_pending_brands(self) -> List[Dict]:
        """Fetch brands that haven't been processed yet"""
        self.cursor.execute("""
            SELECT id, brand_name, url 
            FROM brands 
            WHERE status IS NULL OR status != 'done'
        """)
        return self.cursor.fetchall()
    
    def mark_brand_completed(self, brand_id: int):
        """Update brand status to 'done' after processing"""
        try:
            self.cursor.execute("""
                UPDATE brands 
                SET status = 'done'
                WHERE id = %s
            """, (brand_id,))
            self.connection.commit()
            print(f"Marked brand with ID {brand_id} as completed")
        except Error as e:
            self.connection.rollback()
            print(f"Failed to update brand status: {e}")
            raise

    def insert_products(self, products: List[Dict]):
        """
        Insert scraped products into database
        Args:
            products: List of product dictionaries with:
                - product_name
                - product_url
                - brand_name
                - brand_url
        """
        try:
            insert_query = """
                INSERT INTO products (
                    product_name, product_url, brand_name, brand_url
                ) VALUES (
                    %(product_name)s, %(product_url)s, %(brand_name)s, %(brand_url)s)
            """
            
            self.cursor.executemany(insert_query, products)
            self.connection.commit()
            print(f"Inserted/updated {len(products)} products")

        except Error as e:
            self.connection.rollback()
            print(f"Product insertion failed: {e}")
            raise

    def insert_brands(self, brands: List[Dict]):
        """
        Insert multiple brands into the database
        
        Args:
            brands: List of dictionaries with brand data
                [{
                    'brand_name': 'Brand Name',
                    'url': 'https://example.com/brand',
                }]
        """
        try:
            # Insert brands in batch
            insert_query = """
                INSERT INTO brands (brand_name, url)
                VALUES (%(brand_name)s, %(url)s)
            """
            
            self.cursor.executemany(insert_query, brands)
            self.connection.commit()
            print(f"Successfully inserted/updated {len(brands)} brands")
            
        except Error as e:
            self.connection.rollback()
            print(f"Failed to insert brands: {e}")
            raise

    def get_all_brands(self) -> List[Dict]:
        """Fetch all brands from the database"""
        self.cursor.execute("""
            SELECT brand_name, url, status
            FROM brands
            ORDER BY brand_name
        """)
        return self.cursor.fetchall()

if __name__ == "__main__":
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'zepto',
        'user': 'root',
        'password': 'actowiz',
        'port': 3306
    }

    # Sample brand data
    sample_brands = [
        {'brand_name': 'Borges', 'url': 'https://www.zeptonow.com/brand/Borges/f2e7c6e7-1636-4251-ad8b-3deb50875378'},
        {'brand_name': 'Beanly', 'url': 'https://www.zeptonow.com/brand/Beanly/baa84966-485c-4a2e-b783-d41aa9676c70'}
    ]

    # Using context manager for automatic connection handling
    with DatabaseManager(DB_CONFIG) as db:
        db.insert_brands(sample_brands)
        
        # Retrieve and print all brands
        all_brands = db.get_all_brands()
        print("\nCurrent brands in database:")
        for brand in all_brands:
            print(f"{brand['brand_name']}: {brand['url']}")