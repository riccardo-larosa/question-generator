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

class AmazonScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_product_links(self, store_url):
        """Get product links from Adidas store page."""
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

            # Find product links
            products = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/dp/']")
            for product in products:
                link = product.get_attribute('href')
                if link and '/dp/' in link:
                    product_links.append(link)
        except Exception as e:
            print(f"Error getting product links: {str(e)}")
        
        return list(set(product_links))  # Remove duplicates

    def get_product_data(self, url):
        """Scrape data for a single product."""
        self.driver.get(url)
        time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
        
        try:
            product_data = {
                'title': '',
                'description': '',
                'features': '',
                'dimensions': '',
                'shipping_info': '',
                'reviews': []
            }
            
            # Get title
            try:
                product_data['title'] = self.wait.until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                ).text.strip()
            except:
                pass

            # Get description
            try:
                product_data['description'] = self.driver.find_element(
                    By.ID, "productDescription"
                ).text.strip()
            except:
                pass

            # Get features
            try:
                feature_bullets = self.driver.find_elements(
                    By.CSS_SELECTOR, "#feature-bullets li"
                )
                product_data['features'] = "\n".join([
                    bullet.text.strip() for bullet in feature_bullets
                ])
            except:
                pass

            # Get dimensions
            try:
                details = self.driver.find_elements(
                    By.CSS_SELECTOR, "#detailBullets_feature_div li"
                )
                for detail in details:
                    if "dimensions" in detail.text.lower():
                        product_data['dimensions'] = detail.text.strip()
                        break
            except:
                pass

            # Get shipping info
            try:
                shipping = self.driver.find_element(
                    By.ID, "deliveryBlockMessage"
                )
                product_data['shipping_info'] = shipping.text.strip()
            except:
                pass

            # Get reviews
            try:
                # Click on reviews tab if it exists
                reviews_link = self.driver.find_element(
                    By.CSS_SELECTOR, "a[href*='#customerReviews']"
                )
                reviews_link.click()
                time.sleep(2)

                reviews = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[data-hook='review']"
                )
                for review in reviews[:10]:  # Get first 10 reviews
                    review_text = review.find_element(
                        By.CSS_SELECTOR, "span[data-hook='review-body']"
                    ).text.strip()
                    product_data['reviews'].append(review_text)
            except:
                pass

            return product_data

        except Exception as e:
            print(f"Error scraping product {url}: {str(e)}")
            return None

    def scrape_store(self, store_url, max_products=50):
        """Scrape products from the Adidas store."""
        print("Getting product links...")
        product_links = self.get_product_links(store_url)
        
        # Limit number of products
        product_links = product_links[:max_products]
        
        print(f"Found {len(product_links)} products. Starting to scrape...")
        products_data = []
        
        for link in product_links:
            print(f"Scraping {link}")
            product_data = self.get_product_data(link)
            if product_data:
                products_data.append(product_data)
            time.sleep(random.uniform(1, 3))  # Random delay between products
        
        # Save to CSV
        df = pd.DataFrame(products_data)
        df.to_csv('product_data.csv', index=False)
        print(f"Scraped {len(products_data)} products successfully!")

    def close(self):
        """Close the browser."""
        self.driver.quit()

def main():
    # Get product name from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python amazon_scraper.py <product_name>")
        print("Example: python amazon_scraper.py adidas")
        sys.exit(1)
        
    product_name = sys.argv[1].lower().replace(" ", "_")
    output_file = f"{product_name}_data.csv"
    
    # Store URL mapping (add more as needed)
    store_urls = {
        "adidas": "https://www.amazon.com/stores/adidas/page/5E398A61-45C7-46F9-A6C6-5B4797CC5063",
        # Add more store URLs here
    }
    
    if product_name not in store_urls:
        print(f"Error: No store URL found for {product_name}")
        print("Available products:", ", ".join(store_urls.keys()))
        sys.exit(1)
    
    store_url = store_urls[product_name]
    
    try:
        scraper = AmazonScraper()
        print(f"Starting to scrape {product_name} products...")
        scraper.scrape_store(store_url)
        
        # Rename the output file to match the product name
        if os.path.exists('product_data.csv'):
            os.rename('product_data.csv', output_file)
            print(f"Saved scraped data to {output_file}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 