# Adobe Hackathon 2025 - Round 1A Submission

This project provides a robust solution for extracting a structured outline (Title, H1, H2, H3) from PDF documents, built to comply with all constraints of the Adobe India Hackathon "Connecting the Dots" challenge.

---

## Approach and Strategy

Our goal was to build a highly accurate and performant solution that could handle a wide variety of PDF structures, from simple articles to complex, inconsistently formatted documents.

### Why a Rule-Based System?

We chose to implement a **sophisticated rule-based (heuristic) system** in Python instead of using a machine learning model. This decision was made for several key reasons:
* [cite_start]**Performance:** A rule-based system has minimal overhead and is incredibly fast, ensuring we stay well under the 10-second execution time limit[cite: 78].
* [cite_start]**Constraint Compliance:** This approach avoids large model files, automatically satisfying the `≤ 200MB` model size constraint[cite: 79]. [cite_start]It also requires no GPU and works entirely offline[cite: 58, 62].
* **Accuracy & Control:** It gives us fine-grained control to build targeted rules for specific challenges in PDF parsing, such as handling tables and lists, which a generic model might struggle with.

### The Development Journey: From Simple Rules to a Robust Engine

Our development was an iterative process focused on solving real-world PDF parsing challenges.

1.  **Initial Challenge - Broken Text:** We first noticed that PDF parsers can split a single line of text into multiple blocks.
    * **Solution:** We implemented a `merge_text_blocks` function. This function intelligently stitches text fragments back together based on their vertical position, ensuring that full, unbroken heading text is analyzed.

2.  **Challenge - The Table of Contents (ToC):** Early tests showed that the ToC was being incorrectly parsed as part of the document outline.
    * **Solution:** We built a specific detector, `is_table_of_contents_page`, that identifies ToC pages by looking for keywords and characteristic dot leaders (`.......`). These pages are then completely excluded from the heading extraction process.

3.  **Challenge - Tables and Lists:** The most difficult challenge was distinguishing headings from text inside tables (like a revision history) and numbered lists.
    * **Solution:** We developed a multi-layered defense:
        * A function, `is_likely_table_row`, filters out text that is formatted in columns.
        * A **word count limit** (`MAX_HEADING_WORD_COUNT`) was introduced. This rule helps the system understand that a line starting with "1." followed by a long sentence is a list item, not a heading.
        * We specifically added common non-heading section titles like "Acknowledgements" to a filter list.

4.  [cite_start]**Final Challenge - Accurate Hierarchy (H1/H2/H3):** Relying only on font size for hierarchy is unreliable, as noted in the challenge's "Pro Tips"[cite: 94].
    * **Solution:** We created a **hybrid classification system**. It first tries to determine the heading level based on its numbering (e.g., `2.1` is an `H2`). If no number is present, it falls back to a font-size-based ranking, making the system both flexible and accurate.

This iterative refinement resulted in a fast, lightweight, and intelligent script that excels at structured data extraction from complex PDFs.

---

## Libraries Used

* **PyMuPDF (`fitz`)**: This high-performance Python library was used for its speed and its ability to extract rich metadata from PDFs, including text content, font information (size, weight), and precise coordinates (bbox).

---

## How to Build and Run

The solution is packaged in a Docker container for easy and consistent execution.

### Prerequisites
* Docker Desktop must be installed and running on your system.

### Step 1: Place PDFs
[cite_start]Place all the PDF files you want to process into the `input` folder in the project directory.

### Step 2: Build the Docker Image
[cite_start]Open a terminal in the project's root directory and run the following command to build the image[cite: 63]. [cite_start]The build must be compatible with `linux/amd64` architecture[cite: 56].

```sh
docker build --platform linux/amd64 -t adobe-solution:latest .
Step 3: Run the Container
Execute the following command to run the solution. This will automatically process all PDFs from the 

input folder and place the JSON results in the output folder.

For Windows Command Prompt:

Bash

docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" --network none adobe-solution:latest
For PowerShell or Linux/macOS:

Bash

docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none adobe-solution:latest
The container will process the files and then exit. The final JSON files, one for each input PDF, will be available in your local 

output directory.
