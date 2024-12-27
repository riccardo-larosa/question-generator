# Product Question Generator

This Python application generates relevant questions and summarizes reviews for product data. It uses pre-trained transformer models to generate questions about product features, usage context, and customer feedback.

## Features

- Scrapes product data from Amazon store pages
- Generates 2-4 contextual questions per product about:
  - Product features
  - Usage context
  - Customer feedback
- Summarizes customer reviews
- Saves results in CSV format

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

## Usage

1. First, scrape product data:
   ```bash
   python amazon_scraper.py
   ```
   This will create a `product_data.csv` file with the scraped product information.

2. Generate questions and summaries:
   ```bash
   python product_qa_generator.py
   ```
   This will create a `generated_qa.csv` file containing the generated questions and review summaries.

## Output Format

The generated CSV file will contain:
- Product title
- Generated questions (2-4 per product)
- Review summary (when available)

## Notes

- The application uses rate limiting and delays to avoid being blocked by Amazon
- The number of products scraped is limited to 50 by default
- The application requires an active internet connection
- Some products may not have all information available
