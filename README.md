# Product QA Generator

This script uses AI models to automatically generate relevant questions and summarize reviews for products listed in a CSV file. It utilizes state-of-the-art language models to create insightful questions based on product descriptions and customer feedback.

## Features

*   Generates up to 3 feature-based questions from product descriptions.
*   Generates 1 question based on customer reviews.
*   Summarizes customer reviews using a summarization model.
*   Processes products from a CSV file.
*   Outputs results to a new CSV file.
*   Supports GPU acceleration on Apple Silicon (MPS) if available, otherwise uses CPU.

## Models Used

*   **Question Generation:** `google/flan-t5-large`
*   **Review Summarization:** `facebook/bart-large-cnn`

## Requirements

*   Python 3.x
*   Libraries: `pandas`, `transformers`, `torch`, `nltk`, `tqdm`
*   NLTK data: `punkt` tokenizer

## Setup

1.  **Clone the repository (if applicable):**
   ```bash
   # git clone <repository_url>
   # cd <repository_directory>
   ```

2.  **Install dependencies:**
   It's recommended to use a virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install pandas torch transformers nltk tqdm
   ```
   *Note: Ensure you have the correct PyTorch version installed for your system (CPU/GPU/MPS). Refer to the [official PyTorch installation guide](https://pytorch.org/get-started/locally/).*

3.  **Download NLTK data:**
   The script automatically attempts to download the necessary `punkt` data package on first run. If this fails, you can run the following in a Python interpreter:
   ```python
   import nltk
   nltk.download('punkt')
   ```

## Usage

Run the script from your terminal, providing the path to your input CSV file as a command-line argument:

```bash
python product_qa_generator.py <your_product_data.csv>
```

For example:
```bash
python product_qa_generator.py store_data.csv
