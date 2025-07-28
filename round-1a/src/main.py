import fitz  # PyMuPDF
import json
import os
import re
from collections import Counter

# --- Configuration for Heuristics ---
MIN_FONT_SIZE_INCREASE = 1.05
# A heading should not be a long sentence
MAX_HEADING_WORD_COUNT = 15 
Y_TOLERANCE = 2.0  
COMMON_HEADER_FOOTER_WORDS = ["overview", "page", "international software testing qualifications board", "istqb"]

def is_bold(span):
    """Check if a text span is bold."""
    font_name = span.get('font', '').lower()
    return "bold" in font_name or "black" in font_name

def get_most_common_style(spans):
    """Find the most common font size and font for body text."""
    if not spans: return 0, ""
    # Analyze style of text that looks like paragraphs
    styles = [(s['size'], s['font']) for s in spans if s['text'].strip() and len(s['text'].split()) > 5]
    if not styles: return 0, ""
    return Counter(styles).most_common(1)[0][0]

def merge_text_blocks(blocks):
    """Merge text blocks that are on the same line."""
    merged_lines = []
    if not blocks: return []
    current_line = blocks[0]
    for i in range(1, len(blocks)):
        next_block = blocks[i]
        if abs(current_line['bbox'][1] - next_block['bbox'][1]) < Y_TOLERANCE:
            current_line['text'] += " " + next_block['text']
            current_line['bbox'] = (min(current_line['bbox'][0], next_block['bbox'][0]), min(current_line['bbox'][1], next_block['bbox'][1]), max(current_line['bbox'][2], next_block['bbox'][2]), max(current_line['bbox'][3], next_block['bbox'][3]))
        else:
            merged_lines.append(current_line)
            current_line = next_block
    merged_lines.append(current_line)
    return merged_lines

def is_table_of_contents_page(page):
    """Check if a page is likely a Table of Contents."""
    text = page.get_text().lower()
    if "table of contents" in text: return True
    return len(re.findall(r'\.{5,}', text)) > 4

def is_likely_table_row(text):
    """A more robust check for table rows."""
    if len(re.findall(r'\s{3,}', text)) >= 2: return True
    if re.match(r'^\d\.\d\s+\d{1,2}\s+[A-Z]+\s+\d{4}', text): return True
    return False

def get_heading_level_from_number(text):
    """Determine heading level from numbering (e.g., '2.1' -> H2)."""
    match = re.match(r'^(\d+(\.\d+)*)', text)
    if match:
        level = len(match.group(1).split('.'))
        return f"H{level}" if level <= 3 else "H3"
    return None

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_spans = []
    all_blocks = []
    
    toc_pages = {p.number for p in doc if is_table_of_contents_page(p)}
    
    for page_num, page in enumerate(doc):
        if page.number in toc_pages: continue
        page_dict = page.get_text("dict")
        for block in page_dict['blocks']:
            if 'lines' in block and block['lines']:
                line_text = " ".join(" ".join(span['text'] for span in line['spans']) for line in block['lines']).strip()
                if not line_text: continue
                
                first_span = block['lines'][0]['spans'][0]
                block_info = {'text': line_text, 'bbox': block['bbox'], 'page': page_num + 1, 'size': first_span['size'], 'font': first_span['font'], 'bold': is_bold(first_span)}
                all_blocks.append(block_info)
                
                for line in block['lines']: all_spans.extend(line['spans'])

    if not all_blocks: return {"title": "", "outline": []}

    body_size, body_font = get_most_common_style(all_spans)

    all_blocks.sort(key=lambda b: (b['page'], b['bbox'][1]))
    merged_lines = merge_text_blocks(all_blocks)
    
    headings = []
    
    # Un-numbered sections to filter out
    unwanted_sections = ["revision history", "acknowledgements"]

    for block in merged_lines:
        text = block['text']
        text_lower = text.lower()
        
        # --- Final, Stricter Filtering ---
        if not text or is_likely_table_row(text): continue
        if any(word in text_lower for word in COMMON_HEADER_FOOTER_WORDS) and len(text.split()) < 7: continue
        if text.isdigit() or text_lower in unwanted_sections: continue

        is_heading_candidate = False
        level_from_num = get_heading_level_from_number(text)

        # --- Final Classification Logic ---
        if level_from_num:
            # If it looks like a numbered heading, check word count to ensure it's not a list item
            if len(text.split()) < MAX_HEADING_WORD_COUNT:
                is_heading_candidate = True
        # Stricter rule for non-numbered headings
        elif block['bold'] and block['size'] > body_size * (MIN_FONT_SIZE_INCREASE + 0.1):
            if len(text.split()) < MAX_HEADING_WORD_COUNT:
                 is_heading_candidate = True

        if is_heading_candidate:
            block['level_from_num'] = level_from_num
            headings.append(block)

    title_text = ""
    if headings:
        first_page_headings = sorted([h for h in headings if h['page'] == 1], key=lambda h: (h['size'], h['bold']), reverse=True)
        if first_page_headings:
            title_candidate = first_page_headings[0]
            title_text = title_candidate['text']
            headings = [h for h in headings if h != title_candidate]

    outline = []
    if headings:
        heading_sizes = sorted(list(set(h['size'] for h in headings)), reverse=True)
        size_map = {size: f"H{i+1}" for i, size in enumerate(heading_sizes[:3])}

        for h in headings:
            level = h['level_from_num'] if h['level_from_num'] else size_map.get(h['size'], "H3")
            outline.append({"level": level, "text": h['text'], "page": h['page']})

    return {"title": title_text, "outline": outline}

if __name__ == "__main__":
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
        
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            try:
                result = process_pdf(pdf_path)
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Failed to process {filename}. Error: {e}")