import gensim.downloader as api
import os

# This model contains 100-dimensional vectors for 400,000 words
MODEL_NAME = 'glove-wiki-gigaword-100'
MODEL_PATH = './model'
MODEL_FILE = os.path.join(MODEL_PATH, 'glove.kv')

if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH)

    print(f"Downloading GloVe model: {MODEL_NAME}")
    # Download the model
    word_vectors = api.load(MODEL_NAME)
    # Save it in a format we can load offline
    word_vectors.save(MODEL_FILE)
    
    print(f"Model saved successfully to {MODEL_FILE}")