import pandas as pd
from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers import pipeline
import torch
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from tqdm import tqdm

# Download required NLTK data
nltk.download('punkt')

class ProductQAGenerator:
    def __init__(self):
        # Check if MPS (Metal Performance Shaders) is available for M1/M2
        device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
        
        # Load models with appropriate dtype and device
        print("Loading Flan-T5-large model for better question generation...")
        self.question_model = T5ForConditionalGeneration.from_pretrained(
            'google/flan-t5-large',
            torch_dtype=torch.float32,
            device_map=device
        ).to(device)
        
        # Initialize tokenizer with explicit parameters
        self.question_tokenizer = T5Tokenizer.from_pretrained(
            'google/flan-t5-large',
            model_max_length=1024,
            legacy=True
        )
        
        # Initialize summarizer for reviews
        print("Loading BART model for review summarization...")
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=device
        )
        
        # Set device
        self.device = device
        self.question_model.to(self.device)

    def generate_questions(self, context, num_questions=3, context_type="product"):
        """Generate questions from given context."""
        # Prepare input text with better prompts based on context type
        prompts = {
            "product": [
                f"Given this product description: {context}\n\nGenerate a specific question about the main features of this product.",
                f"Based on this product information: {context}\n\nAsk a question about how this product can be used.",
                f"From this product details: {context}\n\nCreate a question about what makes this product unique."
            ],
            "review": [
                f"Based on these customer reviews: {context}\n\nGenerate a question about customer satisfaction and experience with this product."
            ]
        }
        
        questions = []
        current_prompts = prompts.get(context_type, prompts["product"])
        
        # Generate one question per prompt
        for prompt in current_prompts[:num_questions]:
            # Tokenize input with explicit max_length
            inputs = self.question_tokenizer.encode(
                prompt,
                return_tensors="pt",
                max_length=1024,
                truncation=True,
                padding='max_length'
            ).to(self.device)
            
            # Generate question with sampling enabled
            outputs = self.question_model.generate(
                inputs,
                max_length=64,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                no_repeat_ngram_size=2
            )
            
            question = self.question_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the generated question
            question = question.strip()
            if not question.endswith('?'):
                question += '?'
            if question.lower().startswith('question:'):
                question = question[9:].strip()
            if question.lower().startswith('answer:'):
                continue  # Skip if it generated an answer instead of a question
                
            questions.append(question)
            
        return questions

    def summarize_reviews(self, reviews):
        """Summarize multiple product reviews."""
        if not reviews:
            return "No reviews available."
            
        # Handle different types of review data
        if isinstance(reviews, str):
            # Single review as string
            combined_reviews = reviews
        elif isinstance(reviews, list):
            # List of reviews
            if not reviews:
                return "No reviews available."
            combined_reviews = " ".join([str(review) for review in reviews if review])
        elif isinstance(reviews, pd.Series):
            # Pandas Series of reviews
            if reviews.empty or reviews.isna().all():
                return "No reviews available."
            combined_reviews = " ".join([str(review) for review in reviews if pd.notna(review)])
        else:
            return "Invalid review format."
            
        if not combined_reviews.strip():
            return "No reviews available."
            
        # Count approximate number of words
        word_count = len(combined_reviews.split())
        
        # If the review is very short, return it as is
        if word_count < 30:
            return combined_reviews
            
        # Adjust max_length based on input length, but keep it reasonable
        max_length = min(130, max(30, word_count // 2))
        min_length = min(30, max(10, word_count // 4))
            
        # Generate summary
        try:
            summary = self.summarizer(combined_reviews, 
                                    max_length=max_length, 
                                    min_length=min_length, 
                                    do_sample=False)[0]['summary_text']
            return summary
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return combined_reviews  # Return original text if summarization fails

    def process_product(self, product_data):
        """Process a single product and generate questions and review summary."""
        results = {
            'id': product_data['id'],
            'sku': product_data['sku'],
            'name': product_data['name'],
            'commodity_type': product_data['commodity_type'],
            'products(product-questions-template):question-1': '',
            'products(product-questions-template):question-2': '',
            'products(product-questions-template):question-3': '',
            'feature_questions': [],  # Changed from 'questions' to match main function
            'review_questions': [],
            'review_summary': None
        }
        
        # Combine product features and description for better context
        product_context = ""
        if pd.notna(product_data.get('description')):
            product_context += product_data['description'] + " "
        # if pd.notna(product_data.get('features')):
        #     product_context += product_data['features']
        
        # Generate feature-based questions if we have context
        if product_context.strip():
            print(f"Product context: {product_context}")
            feature_questions = self.generate_questions(
                product_context,
                num_questions=3,
                context_type="product"
            )
            # Safely assign questions only if they exist
            if feature_questions:
                results['products(product-questions-template):question-1'] = feature_questions[0] if len(feature_questions) > 0 else ''
                results['products(product-questions-template):question-2'] = feature_questions[1] if len(feature_questions) > 1 else ''
                results['products(product-questions-template):question-3'] = feature_questions[2] if len(feature_questions) > 2 else ''
                results['feature_questions'] = feature_questions
        
        # Generate review-based questions and summary
        if pd.notna(product_data.get('reviews')):
            # Convert reviews list to string if necessary
            reviews_text = str(product_data['reviews'])
            if reviews_text.strip():
                review_questions = self.generate_questions(
                    reviews_text,
                    num_questions=1,
                    context_type="review"
                )
                results['review_questions'] = review_questions
                
                # Generate review summary
                results['review_summary'] = self.summarize_reviews(product_data['reviews'])
        
        return results

def main():
    # Get product name from command line arguments
    import sys
    if len(sys.argv) != 2:
        print("Usage: python product_qa_generator.py <file_name.csv>")
        print("Example: python product_qa_generator.py store_data.csv")
        sys.exit(1)
        
    file_name = sys.argv[1].lower().replace(" ", "_")
    input_file = f"{file_name}"
    output_file = f"{file_name}_generated_qa.csv"
    
    # Initialize the generator
    generator = ProductQAGenerator()
    
    # Load product data
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} products from {input_file}")
        
        # Process each product
        results = []
        for _, product in tqdm(df.iterrows(), total=len(df)):
            result = generator.process_product(product)
            results.append(result)
            
        # Save results
        output_df = pd.DataFrame(results)
        
        # Convert questions to string format for better CSV readability
        # output_df['feature_questions'] = output_df['feature_questions'].apply(lambda x: '\n'.join(x) if isinstance(x, list) else '')
        # output_df['review_questions'] = output_df['review_questions'].apply(lambda x: '\n'.join(x) if isinstance(x, list) else '')
        
        output_df.to_csv(output_file, index=False)
        print(f"Successfully generated questions and saved results to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        print(f"Please ensure {input_file} exists in the current directory")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 