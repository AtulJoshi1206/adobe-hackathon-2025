# Approach Explanation for Round 1B

Our solution for the "Persona-Driven Document Intelligence" challenge is a multi-stage pipeline designed to be efficient, accurate, and fully compliant with the competition's strict constraints. Our core strategy was to pair advanced document structuring with a lightweight, powerful semantic analysis engine.

### Stage 1: Advanced Document Structuring

Recognizing that the quality of our analysis depends on the quality of our input, we began by creating a sophisticated document chunking module. Instead of naively splitting PDFs by paragraphs or pages, we integrated the advanced heuristic logic from Round 1A. This process identifies structural headings based on a combination of font size, weight, and layout cues. We then define a "chunk" as a heading and all the text that follows it until the next major heading. This method produces semantically coherent blocks of text that are perfectly suited for relevance analysis, giving our system a significant advantage.

### Stage 2: Lightweight Semantic Analysis with Gensim

To meet the demanding constraints on image size and performance while maintaining high accuracy, we made a strategic decision to avoid heavy frameworks like PyTorch or TensorFlow. Instead, we built our semantic core using **Gensim** and a pre-trained **GloVe word-embedding model** (`glove-wiki-gigaword-100`).

This approach has two key benefits:
1.  **Small Footprint:** Gensim and its dependencies are very lightweight, allowing our final Docker image to be well under the specified limits.
2.  **Semantic Power:** By averaging the vectors of words within a sentence, we can generate meaningful sentence embeddings that capture the text's intent without the massive overhead of a transformer model's framework.

We generate a single embedding for the user's `persona` and `job-to-be-done`, which serves as our query. We then generate an embedding for each document chunk.

### Stage 3: Ranking and Refinement

With numerical representations of the query and the content, we use **cosine similarity** to calculate the relevance of each document chunk to the user's task. The chunks are then ranked in descending order of their similarity score to produce the final `extracted_section` list.

To maximize the "Sub-Section Relevance" score, we perform a second level of analysis. For the highest-ranked sections, we extract the most relevant individual sentences by comparing them directly to the user's query. This allows us to pinpoint and present the most potent information within a relevant section, fulfilling the `sub-section_analysis` requirement.

This end-to-end pipeline is a fast, entirely offline, and highly effective system for identifying and ranking the precise information a user needs from a large collection of documents.