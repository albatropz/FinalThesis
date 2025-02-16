from flask import Flask, request, jsonify, render_template
from transformers import PegasusTokenizer, PegasusForConditionalGeneration
import tensorflow as tf
import pdfplumber
import PyPDF2
import torchvision
import openai
import re
import random
import os
import numpy as np
import subprocess
import pickle
import logging  # Add this import
from fetcharticle import fetch_articles  # Import the fetch_articles function


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app = Flask(__name__)

@app.route('/index.html')
def serve_index():
    return render_template('index.html')
@app.route('/citation.html')
def home():
    return render_template('citation.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

def run_command() -> 'subprocess.CompletedProcess[str]':
    return subprocess.run(['command'], capture_output=True, text=True)
# Load your pre-trained model
model = tf.keras.models.load_model('articleclassification1.h5')  # Replace with your model path

# Load the tokenizer and label encoder
with open('tokenizer.pickle', 'rb') as f:
    tokenizer = pickle.load(f)

with open('label_encoder.pickle', 'rb') as f:
    label_encoder = pickle.load(f)

# Preprocess function for article text
def preprocess_text(text):
    if text is None:
        return ''
    # Convert to string if not already
    text = str(text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters and numbers
    text = text.lower()  # Convert to lowercase
    return text

def classify_article(text):
    if not text:
        return {"error": "No text provided"}
        
    try:
        preprocessed_text = preprocess_text(text)
        tokenized_text = tokenizer.texts_to_sequences([preprocessed_text])
        padded_text = tf.keras.preprocessing.sequence.pad_sequences(tokenized_text, maxlen=200)
        padded_text = np.array(padded_text)

        prediction = model.predict(padded_text)
        top_classes = np.argsort(prediction[0])[-3:][::-1]
        predicted_classes = label_encoder.inverse_transform(top_classes)
        confidences = prediction[0][top_classes]
        
        return {
            "predicted_classes": predicted_classes.tolist(),
            "confidences": confidences.tolist()
        }
    except Exception as e:
        return {"error": str(e)}
    
torchvision.disable_beta_transforms_warning()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.urandom(24).hex()  # Required for flashing messages

pegasus_tokenizer = PegasusTokenizer.from_pretrained("google/pegasus-xsum")
pegasus_model = PegasusForConditionalGeneration.from_pretrained(
    "google/pegasus-xsum",
    max_position_embeddings=1024,
    force_download=False
)

# Set OpenAI API key
openai.api_key = "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"

opening_phrases = [
    "According to",
    "As noted by",
    "The study by",
    "Research conducted by",
    "As discussed in",
    "The findings of"
]

def extract_full_text(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
        return re.sub(r'\s{2,}', ' ', text).strip()
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""

def extract_metadata_with_gpt(pdf_text):
    try:
        # Enhance the prompt to be more specific and structured
        prompt = (
            "Extract the following metadata from this academic text. "
            "Format your response exactly like this example:\n"
            "Authors: [List all authors]\n"
            "Year: [Publication year]\n"
            "Title: [Full title of the paper]\n\n"
            "Here are the first few paragraphs of the text to analyze:\n\n"
            f"{pdf_text[:2000]}"  # Increased context length
        )
        
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Using GPT-4 for better accuracy
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting metadata from academic papers. "
                              "Always respond in the exact format requested. "
                              "If you can't find specific information, use 'Unknown' as the value."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3  # Lower temperature for more consistent output
        )
        
        metadata = response.choices[0].message.content
        return parse_metadata_response(metadata)
    except Exception as e:
        print(f"Error extracting metadata with GPT: {str(e)}")
        return ["Unknown Author"], "Unknown Year", "Untitled Study"

def parse_metadata_response(metadata):
    try:
        authors, year, title = [], "n.d.", "Untitled Study"
        
        lines = [line.strip() for line in metadata.split('\n') if line.strip()]
        
        for line in lines:
            if any(line.lower().startswith(prefix) for prefix in ["authors:", "author:", "by:"]):
                author_text = line.split(':', 1)[1].strip()
                # Remove any brackets from author names
                author_text = author_text.replace('[', '').replace(']', '')
                for separator in [',', ';', ' and ']:
                    if separator in author_text:
                        authors = [auth.strip() for auth in author_text.split(separator) if auth.strip()]
                        break
                if not authors:
                    authors = [author_text]
                    
            elif any(line.lower().startswith(prefix) for prefix in ["year:", "date:", "published:"]):
                year_text = line.split(':', 1)[1].strip()
                # Remove any brackets from year
                year_text = year_text.replace('[', '').replace(']', '')
                year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                if year_match:
                    year = year_match.group(0)
                else:
                    year = "n.d."
                    
            elif any(line.lower().startswith(prefix) for prefix in ["title:", "paper:", "article:"]):
                title = line.split(':', 1)[1].strip()
                # Remove any brackets from title
                title = title.replace('[', '').replace(']', '').strip('"\'')
        
        authors = [author.replace('[', '').replace(']', '') for author in authors if author and author.lower() != "unknown"]
        
        return (authors if authors else ["Unknown Author"], 
                year,
                title if title != "Untitled Study" and title else "Untitled Study")
                
    except Exception as e:
        print(f"Error parsing metadata response: {str(e)}")
        return ["Unknown Author"], "n.d.", "Untitled Study"
def parse_metadata_response(metadata):
    try:
        authors, year, title = [], "n.d.", "Untitled Study"
        
        lines = [line.strip() for line in metadata.split('\n') if line.strip()]
        
        for line in lines:
            if any(line.lower().startswith(prefix) for prefix in ["authors:", "author:", "by:"]):
                author_text = line.split(':', 1)[1].strip()
                # Remove any brackets from author names
                author_text = author_text.replace('[', '').replace(']', '')
                for separator in [',', ';', ' and ']:
                    if separator in author_text:
                        authors = [auth.strip() for auth in author_text.split(separator) if auth.strip()]
                        break
                if not authors:
                    authors = [author_text]
                    
            elif any(line.lower().startswith(prefix) for prefix in ["year:", "date:", "published:"]):
                year_text = line.split(':', 1)[1].strip()
                # Remove any brackets from year
                year_text = year_text.replace('[', '').replace(']', '')
                year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                if year_match:
                    year = year_match.group(0)
                else:
                    year = "n.d."
                    
            elif any(line.lower().startswith(prefix) for prefix in ["title:", "paper:", "article:"]):
                title = line.split(':', 1)[1].strip()
                # Remove any brackets from title
                title = title.replace('[', '').replace(']', '').strip('"\'')
        
        authors = [author.replace('[', '').replace(']', '') for author in authors if author and author.lower() != "unknown"]
        
        return (authors if authors else ["Unknown Author"], 
                year,
                title if title != "Untitled Study" and title else "Untitled Study")
                
    except Exception as e:
        print(f"Error parsing metadata response: {str(e)}")
        return ["Unknown Author"], "n.d.", "Untitled Study"

def summarize_with_pegasus(pdf_text):
    if not pdf_text:
        return "No text available for summarization."
    try:
        # Tokenize with proper padding and truncation
        inputs = pegasus_tokenizer(
            pdf_text,
            max_length=512,  # Reduced from 1024 to avoid memory issues
            padding='max_length',
            truncation=True,
            return_tensors="pt"
        )
        
        # Generate summary with safe parameters
        summary_ids = pegasus_model.generate(
            inputs["input_ids"],
            max_length=150,
            min_length=40,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        summary = pegasus_tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        return summary if summary else "Summary generation failed."
    except Exception as e:
        print(f"Error in Pegasus summarization: {str(e)}")
        return "Error in summarization process."
def generate_with_gpt(authors, year, pegasus_summary, user_input, style="APA", title=None):
    try:
        citation = format_citation(authors, year, title, style)
        
        prompt = (
            f"Generate a brief literature review paragraph but with wide vocabulary that:\n"
            f"1. States the main findings using ONLY this citation format: {citation}\n"
            f"2. RELATE IT TO: '{user_input}'\n"
            f"3. Make the summary only for Narrative citation\n"
            f"4. Identifies one research gap and use different word as your starting phrase\n\n"
            f"Requirements:\n"
            f"- Use formal academic language (no personal pronouns)\n"
            f"- Use {opening_phrases} right before {citation}\n"
            f"- DO NOT mention AUTHOR NAMES separately from the citation\n"
            f"- Use the provided citation EXACTLY ONCE after stating main findings\n"
            f"- Use passive voice or third person\n"
            f"- DO NOT use phrases like 'this study will use' or 'will be utilized'\n"
            f"- MAKE IT HUMAN AS MUCH AS POSSIBLE."
            f"- DO NOT repeat the citation in any form\n"
            f"- NEVER CUT YOUR SUMMARY AND ALWAYS FINISH IT.\n"
            f"- Keep the paragraph FOCUSED, BRIEF, CONCISE and COMPLETE\n"
            f"- Ensure the summary concludes with a coherent final sentence that includes the citation, leaving no ideas incomplete."
            f"- Based on this summary: {pegasus_summary}"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in academic writing. Generate a concise paragraph "
                              "that uses the citation exactly once, avoiding any repetition of author "
                              "names or citations. Maintain formal academic tone."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=160,
            temperature=0.5
        )
        
        review_text = response.choices[0].message.content.strip()
        
        # Ensure only one citation exists
        if review_text.count(citation) > 1:
            # Keep only the first citation
            first_citation_index = review_text.index(citation)
            rest_of_text = review_text[first_citation_index + len(citation):]
            review_text = review_text[:first_citation_index + len(citation)] + rest_of_text.replace(citation, '')
        
        return review_text.strip()

    except Exception as e:
        print(f"Error during citation generation with GPT: {str(e)}")
        return "Error generating citation."

def format_citation(authors, year, title, style):
    try:
        # Handle year format
        year_text = 'n.d.' if year in [None, 'unknown', 'unknown year'] or (isinstance(year, str) and year.lower() == 'n.d.') else year
        # Handle no author cases
        if not authors or authors == ["Unknown Author"]:
            if not title or title == "Untitled Study":
                if style == "APA":
                    return f"(Anonymous, {year_text})"
                elif style == "IEEE":
                    return "[1]"  # IEEE uses numbered references
                elif style == "ACM":
                    return f"[Anonymous {year_text}]"
                elif style == "MLA":
                    return "(Anonymous)"
            else:
                shortened_title = ' '.join(title.split()[:3])
                if style == "APA":
                    return f'("{shortened_title}", {year_text})'
                elif style == "IEEE":
                    return "[1]"
                elif style == "ACM":
                    return f"[{title.split()[0]} {year_text}]"
                elif style == "MLA":
                    return f'("{shortened_title}")'
        
        # Format author names
        last_names = [author.split()[-1].title() for author in authors]  # Ensure proper capitalization
        
        if style == "APA":
            if len(last_names) == 1:
                author_text = last_names[0]
            elif len(last_names) == 2:
                 author_text = f"{last_names[0]} & {last_names[1]}"
            else:
                 author_text = f"{last_names[0]} et al."
            year_text = year_text.replace("[", "").replace("]", "")
            return f"({author_text}, {year_text})"
        elif style == "IEEE":
            return "[1]"  # IEEE uses numbered references

        elif style == "ACM":
            if len(last_names) == 1:
                author_text = last_names[0]
            else:
                author_text = f"{last_names[0]} et al."
            return f"[{author_text} {year_text}]"

        elif style == "MLA":
            if len(last_names) == 1:
                author_text = last_names[0]
            elif len(last_names) == 2:
                author_text = f"{last_names[0]} and {last_names[1]}"
            else:
                author_text = f"{last_names[0]} et al."
            return f"({author_text})"

    except Exception as e:
        print(f"Error formatting citation: {str(e)}")
        if style == "IEEE":
            return "[1]"
        elif style == "ACM":
            return "[Unknown n.d.]"
        else:
            return "(Anonymous, n.d.)"
def format_reference_citation(authors, year, title, style="APA"):
    try:
        # Clean and validate inputs
        year_text = 'n.d.' if year in [None, 'unknown', 'unknown year'] or (isinstance(year, str) and year.lower() == 'n.d.') else year
        title_text = title if title and title != "Untitled Study" else "[Untitled]"
        
        # Format author names
        if not authors or authors == ["Unknown Author"]:
            author_text = "Anonymous"
        else:
            # Convert to proper case and format
            last_names = [author.split()[-1].title() for author in authors]
            first_names = [author.split()[0][0].upper() + "." for author in authors]
            
            if style == "APA":
                formatted_authors = [f"{last}, {first}" for last, first in zip(last_names, first_names)]
                author_text = ", ".join(formatted_authors[:-1])
                if len(formatted_authors) > 1:
                    author_text += f", & {formatted_authors[-1]}"
                else:
                    author_text = formatted_authors[0]
                    
            else:
                formatted_authors = [f"{first} {last}" for first, last in zip(first_names, last_names)]
                author_text = ", ".join(formatted_authors)

        # Format citation based on style with italicized title
        if style == "APA":
            return f"{author_text}. ({year_text}). <i>{title_text}</i>."
            
        elif style == "IEEE":
            return f"{author_text}, \"<i>{title_text}</i>,\" {year_text}."
            
        elif style == "ACM":
            return f"{author_text}. {year_text}. <i>{title_text}</i>."
            
        elif style == "MLA":
            return f"{author_text}. \"<i>{title_text}</i>.\" {year_text}."
            
    except Exception as e:
        print(f"Error formatting reference citation: {str(e)}")
        return "Reference information unavailable."
@app.route('/fetch_articles', methods=['GET'])
def fetch_articles_endpoint():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        logger.info(f"Processing query: {query}")
        
        # Classify user input
        user_input_classification = classify_article(query)
        user_classes = user_input_classification['predicted_classes']

        articles = fetch_articles(query)
        classified_articles = []

        for article in articles:
            article_text = article.get('summary', '') or article.get('abstract', '')
            classification_result = classify_article(article_text)
            
            if 'error' in classification_result:
                continue
            
            article_classes = classification_result['predicted_classes']
            
            # Check if there's any overlap between user input classes and article classes
            if any(cls in user_classes for cls in article_classes):
                classified_articles.append({
                    "title": article.get('title', 'No Title Available'),
                    "year": article.get('year', 'Unknown Year'),
                    "abstract": article.get('abstract', 'No Abstract Available'),
                    "authors": article.get('authors', []),
                    "source": article.get('source', article.get('link', 'No Source Available')),
                    "link": article.get('link', 'No URL Available'),
                    "classifications": article_classes,
                    "confidences": classification_result['confidences']
                })

        return jsonify(classified_articles)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    article_text = data.get('article_text', '')

    if not article_text:
        return jsonify({'error': 'No article text provided'}), 400

    result = classify_article(article_text)
    
    return jsonify(result)
    


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'pdf_file' not in request.files or 'study_description' not in request.form:
            return "Missing file or study description", 400
            
        file = request.files['pdf_file']
        user_input = request.form['study_description']
        citation_style = request.form.get('citation_style', 'APA')
        
        if file.filename == '' or not file.filename.endswith('.pdf'):
            return "Invalid file format. Please upload a PDF.", 400
            
        pdf_text = extract_full_text(file)
        if not pdf_text.strip():
            return "Error: No text could be extracted from the PDF.", 400
            
        authors, year, title = extract_metadata_with_gpt(pdf_text)
        pegasus_summary = summarize_with_pegasus(pdf_text)
        in_text_citation = generate_with_gpt(authors, year, pegasus_summary, user_input, citation_style, title)
        reference_citation = format_reference_citation(authors, year, title, citation_style)
        
        return render_template('citation.html', 
                             citations={
                                 "In-text": in_text_citation,
                                 "Reference": reference_citation
                             },
                             full_analysis=pegasus_summary,
                             citation_style=citation_style)
                             
    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return f"An error occurred: {str(e)}", 400
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)