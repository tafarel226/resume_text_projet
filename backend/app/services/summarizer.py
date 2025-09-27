from transformers import pipeline
from ..config import settings

class Summarizer:
    def __init__(self):
        try:
            self.pipe = pipeline('summarization', model=settings.SUMMARIZER_MODEL)
        except Exception as e:
            print("Warning: summarizer model failed to load:", e)
            self.pipe = None

    def summarize(self, text, method='abstractive', params=None):
        params = params or {}
        if method == 'extractive':
            # simple fallback extractive: return first N sentences
            n = params.get('num_sentences', 3)
            sentences = text.split('.')
            return {'summary': '.'.join(sentences[:n]).strip()}
        else:
            if not self.pipe:
                return {'summary': text[:500]}
            max_length = params.get('max_length', 150)
            min_length = params.get('min_length', 30)
            out = self.pipe(text, max_length=max_length, min_length=min_length)
            return {'summary': out[0]['summary_text']}
