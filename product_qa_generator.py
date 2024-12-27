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
        self.question_model = T5ForConditionalGeneration.from_pretrained(
            't5-base',
            torch_dtype=torch.float32,  # Use float32 for better compatibility
            device_map=device
        ).to(device)
        
        # Initialize tokenizer with explicit parameters
        self.question_tokenizer = T5Tokenizer.from_pretrained(
            't5-base',
            model_max_length=1024,  # Explicitly set max length
            legacy=True  # Explicitly set legacy mode
        )
        
        # Initialize summarizer for reviews
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=device
        )
        
        # Set device
        self.device = device
        self.question_model.to(self.device)

    def generate_questions(self, context, num_questions=3):
        """Generate questions from given context."""
        # Prepare input text with better prompt
        input_text = f"generate {num_questions} questions about this product: {context}"
        
        # Tokenize input with explicit max_length
        inputs = self.question_tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
            padding='max_length'
        ).to(self.device)
        
        # Generate questions with sampling enabled
        outputs = self.question_model.generate(
            inputs,
            max_length=128,
            num_return_sequences=num_questions,
            do_sample=True,
            temperature=0.8,
            top_k=50,
            top_p=0.95,
            no_repeat_ngram_size=2
        )
        
        questions = []
        for output in outputs:
            question = self.question_tokenizer.decode(output, skip_special_tokens=True)
            # Clean up the generated question
            question = question.strip()
            if not question.endswith('?'):
                question += '?'
            if question.lower().startswith('question:'):
                question = question[9:].strip()
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
            'title': product_data['title'],
            'feature_questions': [],
            'review_questions': [],
            'review_summary': None
        }
        
        # Combine product features and description for better context
        product_context = ""
        if pd.notna(product_data.get('description')):
            product_context += product_data['description'] + " "
        if pd.notna(product_data.get('features')):
            product_context += product_data['features']
        
        # Generate feature-based questions if we have context
        if product_context.strip():
            feature_questions = self.generate_questions(
                product_context,
                num_questions=3
            )
            results['feature_questions'] = feature_questions
        
        # Generate review-based questions and summary
        if pd.notna(product_data.get('reviews')):
            # Convert reviews list to string if necessary
            reviews_text = str(product_data['reviews'])
            if reviews_text.strip():
                review_questions = self.generate_questions(
                    reviews_text,
                    num_questions=1
                )
                results['review_questions'] = review_questions
                
                # Generate review summary
                results['review_summary'] = self.summarize_reviews(product_data['reviews'])
        
        return results

def main():
    # Initialize the generator
    generator = ProductQAGenerator()
    
    # Load product data
    try:
        df = pd.read_csv('product_data.csv')
        print(f"Loaded {len(df)} products")
        
        # Process each product
        results = []
        for _, product in tqdm(df.iterrows(), total=len(df)):
            result = generator.process_product(product)
            results.append(result)
            
        # Save results
        output_df = pd.DataFrame(results)
        
        # Convert questions to string format for better CSV readability
        output_df['feature_questions'] = output_df['feature_questions'].apply(lambda x: '\n'.join(x) if x else '')
        output_df['review_questions'] = output_df['review_questions'].apply(lambda x: '\n'.join(x) if x else '')
        
        output_df.to_csv('generated_qa.csv', index=False)
        print("Successfully generated questions and saved results to generated_qa.csv")
        
    except FileNotFoundError:
        print("Please ensure product_data.csv exists in the current directory")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 