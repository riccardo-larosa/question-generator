# Product Question Generator

This Python application generates relevant questions and summarizes reviews for product data. It uses pre-trained transformer models to generate questions about product features, usage context, and customer feedback.

## Features

- Scrapes product data from various online stores (Amazon, Shopify, etc.)
- Generates 2-4 contextual questions per product about:
  - Product features
  - Usage context
  - Customer feedback
- Summarizes customer reviews
- Saves results in CSV format
- Configurable store settings via JSON

## Requirements

- Python 3.8+
- Chrome browser (for web scraping)
- ChromeDriver (for Selenium)

## Installation

1. Clone this repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
   ```
3. Install ChromeDriver for your Chrome version:
   - Download from: https://sites.google.com/chromium.org/driver/
   - Add it to your system PATH
   ```bash
   export PATH="$PATH:/<directory>/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS"
   ```

To add a new store:
1. Add its configuration to `store_config.json`
2. Ensure the store type is supported in `web_scraper.py`

## Usage

1. First, scrape product data:
   ```bash
   python web_scraper.py <store_name>
   ```
   Example:
   ```bash
   python web_scraper.py adidas
   ```
   This will create `<store_name>_data.csv` (e.g., `adidas_data.csv`)

2. Generate questions and summaries:
   ```bash
   python product_qa_generator.py <file_name>
   ```
   Example:
   ```bash
   python product_qa_generator.py adidas
   ```
   This will create `<file_name>_generated_qa.csv` (e.g., `adidas_generated_qa.csv`)

## Currently Supported Store Types

- `amazon_store`: Amazon brand stores
- `amazon_search`: Amazon search results
- `shopify`: Shopify stores
- More coming soon...

## Currently Available Stores

- adidas (Amazon Store)
- nike (Amazon Store)
- puma (Amazon Store)
- More can be added via `store_config.json`

## Output Format

The generated CSV file will contain:
- Product title
- Feature questions (2-3 questions about product features and usage)
- Review questions (1 question about customer experience)
- Review summary (when available)

## Notes

- The application uses rate limiting and delays to avoid being blocked by stores
- The number of products scraped is limited to 50 by default
- The application requires an active internet connection
- Some products may not have all information available
- Respect the terms of service and robots.txt of the websites you scrape
