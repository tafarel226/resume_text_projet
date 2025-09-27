from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from ..config import settings
from jinja2 import Template
import json

class Matcher:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        # try load faiss index and faq_texts
        try:
            self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
            with open('./data/faq_texts.json', 'r') as f:
                self.faqs = json.load(f)
        except Exception:
            self.index = None
            self.faqs = []

    def match(self, text, entities=None, top_k=5):
        # return simple nearest by embedding if index available
        if not self.index:
            return []
        emb = self.model.encode([text], convert_to_numpy=True)
        faiss.normalize_L2(emb)
        D, I = self.index.search(emb, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            faq = self.faqs[idx]
            # render with jinja but don't fail if missing
            try:
                tmpl = Template(faq['answer_template'])
                mapping = {e['label']: e['text'] for e in (entities or [])}
                rendered = tmpl.render(**mapping)
            except Exception:
                rendered = faq['answer_template']
            results.append({'faq_id': faq.get('id'), 'question':faq.get('question'), 'score':float(score),'answer':rendered})
        return results

matcher = Matcher()
