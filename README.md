# Zepto Scraper

A Python project to scrape brand and product data from Zepto and store it in a MySQL database.

## Features

- Scrapes brand information from Zepto
- Scrapes product details for each brand
- Stores scraped data in a MySQL database
- Tracks scraping status for brands

## Project Structure
```
zepto_now/
├── .env.example - Environment variables template
├── .gitignore - Git ignore file
├── README.md - This file
├── init.py - Python package initialization
├── brands_scraper.py - Script for scraping brands
├── products_scraper.py - Script for scraping products
├── requirements.txt - Python dependencies
└── core/ - Core functionality package
```


## Database Schema

### Brands Table
```sql
CREATE TYPE status_enum AS ENUM ('pending', 'done');

CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    url VARCHAR(512) NOT NULL UNIQUE,
    status status_enum NOT NULL DEFAULT 'pending'
);
```

### Products Table
```sql
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_url VARCHAR(512) NOT NULL,
    brand_name VARCHAR(255),
    brand_url VARCHAR(512)
);
```

## Setup Instructions

Clone the repository:
```
git clone https://github.com/arvind-actowiz/zepto-scraper.git
cd zepto-scraper
```

Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Create a .env file based on .env.example and configure your database connection:
```
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Set up your MySQL database with the provided schema.

Usage
Run the brand scraper:

`python brands_scraper.py`

Run the product scraper:
`python products_scraper.py`
