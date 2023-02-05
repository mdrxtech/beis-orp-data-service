import pandas as pd
import numpy as np    
import re
import pikepdf
import nltk
from preprocess.preprocess_functions import preprocess
from postprocess.postprocess_functions import postprocess_title

# Import pre-trained title extraction model
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM 
tokenizer = AutoTokenizer.from_pretrained("fabiochiu/t5-small-medium-title-generation")
model = AutoModelForSeq2SeqLM.from_pretrained("fabiochiu/t5-small-medium-title-generation")

my_pattern = re.compile(r'\s+')

# Extract title from metadata of document
def extract_title(doc_bytes_io):
    '''Extracts title from PDF streaming input'''

    pdf = pikepdf.Pdf.open(doc_bytes_io)
    meta = pdf.open_metadata()
    try:
        title = meta['{http://purl.org/dc/elements/1.1/}title']
    except KeyError:
        title = pdf.docinfo.get('/Title')

    return title

# Heuristic-based function to decide on approach to title extraction
def use_automatic_title_extraction(title):
    # Remove punctuation
    title = re.sub(r"[^\w\s]", "", title).strip()
    # Remove Microsoft Word from titles
    title = re.sub("Microsoft Word", "", title)
    # Remove excess white space
    title = re.sub(my_pattern, " ", title)
    # Heuristic: if the number of tokens in the title is less than 4
    # Then use automatic title extraction
    if len(title.split(" ")) < 4:
        return True
    else:
        return False

# Define predictor function
def title_predictor(text):
    # Preprocess the text
    text = preprocess(text)
    inputs = ["summarize: " + text]
    inputs = tokenizer(inputs, truncation=True, return_tensors="pt")
    output = model.generate(**inputs, num_beams=10, do_sample=False, min_length=10, max_new_tokens=25)
    decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
    predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]
    # Postprocess the text
    processed_title = postprocess_title(predicted_title)
    return processed_title

def handler():
    metadata_title = extract_title()
    if use_automatic_title_extraction(title):
        title = title_predictor(DOCUMENT_TEXT)
        return title
    else:
        title = re.sub("Microsoft Word - ", "", metadata_title)
        title = re.sub(my_pattern, " ", title)
        return title