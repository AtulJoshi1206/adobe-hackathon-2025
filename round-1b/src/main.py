import fitz
import json
import os
import re
import numpy as np
import datetime
from gensim.models import KeyedVectors
from collections import Counter
from numpy.linalg import norm

# --- Configuration ---
MODEL_FILE = '/app/model/glove.kv'
INPUT_DIR = '/app/input'
OUTPUT_DIR = '/app/output'
TOP_N_SECTIONS = 10
TOP_M_SENTENCES = 3

# --- Gensim Helper ---
def get_sentence_embedding(text, model):
    """Creates a sentence embedding by averaging the vectors of its words."""
    words = text.lower().split()
    word_vectors = [model[word] for word in words if word in model]
    if not word_vectors:
        return np.zeros(model.vector_size)
    return np.mean(word_vectors, axis=0)

# --- Advanced Document Structuring Logic ---
def structure_and_chunk_pdf(pdf_path):
    """
    Parses a PDF using a more lenient heuristic to create meaningful semantic chunks.
    This version is designed to handle documents with less standard formatting.
    """
    doc = fitz.open(pdf_path)
    chunks = []
    
    # Extract all text lines with metadata
    all_lines = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0 and 'lines' in b:
                for line in b['lines']:
                    if line['spans']:
                        span = line['spans'][0]
                        line_text = "".join(s['text'] for s in line['spans']).strip()
                        if line_text:
                            all_lines.append({
                                "text": line_text, "font": span['font'], "size": span['size'],
                                "bold": "bold" in span['font'].lower() or "black" in span['font'].lower(),
                                "page": page_num + 1, "y0": line['bbox'][1]
                            })

    if not all_lines:
        return []

    # Get the style of the body text
    font_sizes = [line['size'] for line in all_lines if len(line['text'].split()) > 5]
    body_size = Counter(font_sizes).most_common(1)[0][0] if font_sizes else 10

    # Find potential headings with more lenient rules
    potential_headings = []
    for i, line in enumerate(all_lines):
        is_bold_and_larger = line['bold'] and line['size'] >= body_size
        is_much_larger = line['size'] > body_size * 1.1
        has_space_above = i > 0 and (line['y0'] - all_lines[i-1]['y0'] > 20)
        
        if (is_bold_and_larger or is_much_larger or has_space_above):
             if 1 < len(line['text'].split()) < 15:
                potential_headings.append(line)
    
    if not potential_headings:
        full_text = "".join(p.get_text() for p in doc)
        return [{'title': 'Full Document', 'content': full_text, 'page': 1}]

    # Group text under the identified headings
    for i, heading in enumerate(potential_headings):
        start_page, start_y = heading['page'], heading['y0']
        end_page = potential_headings[i+1]['page'] if i + 1 < len(potential_headings) else len(doc)
        end_y = potential_headings[i+1]['y0'] if i + 1 < len(potential_headings) else 9999
        content = ""
        for page_num in range(start_page - 1, end_page):
            page = doc.load_page(page_num)
            clip_y_start = start_y if page_num == start_page - 1 else 0
            clip_y_end = end_y if page_num == end_page - 1 else page.rect.height
            clip_rect = fitz.Rect(0, clip_y_start + 1, page.rect.width, clip_y_end)
            content += page.get_text(clip=clip_rect)
        chunks.append({'title': heading['text'].strip(), 'content': content.strip().replace('\n', ' '), 'page': heading['page']})
    return chunks

def get_refined_text(text, query_embedding, model):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 3]
    if not sentences: return text[:500]
    sentence_embeddings = np.array([get_sentence_embedding(s, model) for s in sentences])
    query_embedding_norm = norm(query_embedding)
    sentence_embeddings_norm = norm(sentence_embeddings, axis=1)
    
    # Avoid division by zero
    valid_indices = (sentence_embeddings_norm > 0)
    if not np.any(valid_indices): return text[:500]
    
    similarities = np.zeros(len(sentences))
    similarities[valid_indices] = np.dot(sentence_embeddings[valid_indices], query_embedding) / (query_embedding_norm * sentence_embeddings_norm[valid_indices])
    
    top_indices = np.argsort(similarities)[-TOP_M_SENTENCES:]
    top_indices_sorted = sorted(top_indices.tolist())
    refined_text = ". ".join([sentences[i] for i in top_indices_sorted])
    return refined_text + "." if not refined_text.endswith('.') else refined_text

if __name__ == "__main__":
    print("Starting Gensim-based document intelligence process...")
    
    # 1. Load Model and Inputs
    print("Loading GloVe model...")
    model = KeyedVectors.load(MODEL_FILE)
    
    try:
        with open(os.path.join(INPUT_DIR, 'persona.txt'), 'r', encoding='utf-8') as f: persona = f.read().strip()
    except FileNotFoundError:
        print("Warning: persona.txt not found.")
        persona = ""
        
    try:
        with open(os.path.join(INPUT_DIR, 'job.txt'), 'r', encoding='utf-8') as f: job = f.read().strip()
    except FileNotFoundError:
        print("Warning: job.txt not found.")
        job = ""

    query = f"User Persona: {persona}. User Task: {job}"
    print(f"Generated Query: {query}")
    query_embedding = get_sentence_embedding(query, model)

    # 2. Ingest and Chunk all PDFs
    print("Processing and chunking documents...")
    doc_dir = os.path.join(INPUT_DIR, 'documents')
    all_chunks, doc_files = [], [f for f in os.listdir(doc_dir) if f.lower().endswith('.pdf')]
    for doc_name in doc_files:
        pdf_path = os.path.join(doc_dir, doc_name)
        pdf_chunks = structure_and_chunk_pdf(pdf_path)
        for chunk in pdf_chunks:
            if chunk['content']:
                chunk['document'] = doc_name
                all_chunks.append(chunk)

    # 3. Generate Embeddings and Rank
    print(f"Generating embeddings for {len(all_chunks)} chunks and ranking...")
    chunk_embeddings = np.array([get_sentence_embedding(chunk['title'] + " " + chunk['content'], model) for chunk in all_chunks])
    query_embedding_norm = norm(query_embedding)
    chunk_embeddings_norm = norm(chunk_embeddings, axis=1)
    
    valid_indices = (chunk_embeddings_norm > 0)
    similarities = np.zeros(len(all_chunks))
    similarities[valid_indices] = np.dot(chunk_embeddings[valid_indices], query_embedding) / (query_embedding_norm * chunk_embeddings_norm[valid_indices])
    
    ranked_indices = np.argsort(similarities)[::-1]

    # 4. Generate JSON Output
    print("Generating final JSON output...")
    output_data = {"metadata": {"input_documents": doc_files, "persona": persona, "job_to_be_done": job, "processing_timestamp": datetime.datetime.now().isoformat()}, "extracted_section": [], "sub-section_analysis": []}
    for i, idx in enumerate(ranked_indices[:TOP_N_SECTIONS]):
        chunk = all_chunks[idx]
        output_data["extracted_section"].append({"document": chunk['document'], "page_number": chunk['page'], "section_title": chunk['title'], "importance_rank": i + 1})
        refined_text = get_refined_text(chunk['content'], query_embedding, model)
        output_data["sub-section_analysis"].append({"document": chunk['document'], "refined_text": refined_text, "page_number": chunk['page']})

    output_path = os.path.join(OUTPUT_DIR, 'result.json')
    with open(output_path, 'w', encoding='utf-8') as f: json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"Processing complete. Output saved to {output_path}")