from sentence_transformers import SentenceTransformer

MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
SAVE_PATH = './backend/embedding_model_files'

print(f"Downloading model '{MODEL_NAME}'...")
model = SentenceTransformer(MODEL_NAME)

print(f"Saving model to '{SAVE_PATH}'...")
model.save(SAVE_PATH)

print("Download complete.")