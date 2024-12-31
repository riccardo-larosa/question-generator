from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import sys
import os
import json

class WebScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_product_links(self, store_url, store_type):
        """Get product links based on store type."""
        self.driver.get(store_url)
        time.sleep(3)  # Allow page to load
        
        product_links = []
        try:
            # Scroll to load more products
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Different selectors for different store types
            selectors = {
                "amazon_store": "a[href*='/dp/']",
                "amazon_search": "a[href*='/dp/']",
                "shopify": "a[href*='/products/']",
                # Add more store types and their selectors here
            }
            
            selector = selectors.get(store_type, "a[href*='/dp/']")  # Default to Amazon selector
            products = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            for product in products:
                link = product.get_attribute('href')
                if link and (('/dp/' in link) or ('/products/' in link)):
                    product_links.append(link)
                    
        except Exception as e:
            print(f"Error getting product links: {str(e)}")
        
        return list(set(product_links))  # Remove duplicates

    def get_product_data(self, url, store_type):
        """Scrape data for a single product based on store type."""
        self.driver.get(url)
        time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
        
        try:
            # Initialize with common fields
            product_data = {
                'title': '',
                'description': '',
                'features': '',
                'price': '',
                'dimensions': '',
                'shipping_info': '',
                'reviews': []
            }
            
            # Different selectors for different store types
            selectors = {
                "amazon_store": {
                    "title": (By.ID, "productTitle"),
                    "description": (By.ID, "productDescription"),
                    "features": (By.CSS_SELECTOR, "#feature-bullets li"),
                    "price": (By.CSS_SELECTOR, ".a-price .a-offscreen"),
                    "reviews": (By.CSS_SELECTOR, "div[data-hook='review']")
                },
                "shopify": {
                    "title": (By.CSS_SELECTOR, ".product-title"),
                    "description": (By.CSS_SELECTOR, ".product-description"),
                    "price": (By.CSS_SELECTOR, ".product-price"),
                    "reviews": (By.CSS_SELECTOR, ".product-reviews")
                }
                # Add more store types and their selectors
            }
            
            store_selectors = selectors.get(store_type, selectors["amazon_store"])
            
            # Get title
            try:
                product_data['title'] = self.wait.until(
                    EC.presence_of_element_located(store_selectors["title"])
                ).text.strip()
            except:
                pass

            # Get description
            try:
                product_data['description'] = self.driver.find_element(*store_selectors["description"]).text.strip()
            except:
                pass

            # Get features for Amazon-like stores
            if "features" in store_selectors:
                try:
                    feature_elements = self.driver.find_elements(*store_selectors["features"])
                    product_data['features'] = "\n".join([elem.text.strip() for elem in feature_elements])
                except:
                    pass

            # Get price
            try:
                product_data['price'] = self.driver.find_element(*store_selectors["price"]).text.strip()
            except:
                pass

            # Get reviews
            try:
                review_elements = self.driver.find_elements(*store_selectors["reviews"])
                for review in review_elements[:10]:  # Get first 10 reviews
                    review_text = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text.strip()
                    product_data['reviews'].append(review_text)
            except:
                pass

            return product_data

        except Exception as e:
            print(f"Error scraping product {url}: {str(e)}")
            return None

    def scrape_store(self, store_url, store_type, max_products=50):
        """Scrape products from the store."""
        print("Getting product links...")
        product_links = self.get_product_links(store_url, store_type)
        
        # Limit number of products
        product_links = product_links[:max_products]
        
        print(f"Found {len(product_links)} products. Starting to scrape...")
        products_data = []
        
        for link in product_links:
            print(f"Scraping {link}")
            product_data = self.get_product_data(link, store_type)
            if product_data:
                products_data.append(product_data)
            time.sleep(random.uniform(1, 3))  # Random delay between products
        
        return products_data

    def close(self):
        """Close the browser."""
        self.driver.quit()

def load_store_config():
    """Load store configurations from config file."""
    try:
        with open('store_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "stores": {
                "adidas": {
                    "url": "https://www.amazon.com/stores/adidas/page/5E398A61-45C7-46F9-A6C6-5B4797CC5063",
                    "type": "amazon_store"
                }
                # Add more stores here
            }
        }

def main():
    # Get store name from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python web_scraper.py <store_name>")
        print("Example: python web_scraper.py adidas")
        sys.exit(1)
        
    store_name = sys.argv[1].lower().replace(" ", "_")
    output_file = f"{store_name}_data.csv"
    
    # Load store configurations
    config = load_store_config()
    stores = config.get("stores", {})
    
    if store_name not in stores:
        print(f"Error: No configuration found for {store_name}")
        print("Available stores:", ", ".join(stores.keys()))
        sys.exit(1)
    
    store_config = stores[store_name]
    
    try:
        scraper = WebScraper()
        print(f"Starting to scrape {store_name} products...")
        products_data = scraper.scrape_store(
            store_config["url"],
            store_config["type"]
        )
        
        # Save to CSV
        df = pd.DataFrame(products_data)
        df.to_csv(output_file, index=False)
        print(f"Saved scraped data to {output_file}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 