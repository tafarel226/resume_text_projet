import spacy
from ..config import settings

class NERService:
    def __init__(self):
        try:
            # try to load an existing fine-tuned model first
            self.nlp = spacy.load(settings.NER_MODEL_PATH)
        except Exception:
            try:
                self.nlp = spacy.load('fr_core_news_sm')
            except Exception:
                # fallback minimal pipeline
                self.nlp = None

    def extract(self, text: str):
        if not self.nlp:
            return []
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append({'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char})
        return entities

# expose singleton
ner = NERService()
