from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"
    FAISS_INDEX_PATH: str = "./data/faiss.index"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    SUMMARIZER_MODEL: str = "facebook/bart-large-cnn"
    NER_MODEL_PATH: str = "./data/ner_model"
    INTENT_MODEL_PATH: str = "./data/intent_model.pkl"

settings = Settings()

