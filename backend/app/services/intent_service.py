from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
from ..config import settings

class IntentService:
    def __init__(self):
        try:
            self.model = joblib.load(settings.INTENT_MODEL_PATH)
            self.vectorizer = joblib.load(settings.INTENT_MODEL_PATH + '.vec')
        except Exception:
            self.model = None
            self.vectorizer = None

    def predict(self, text: str):
        if not (self.model and self.vectorizer):
            return {'intent': 'ASK_SUMMARY', 'confidence': 0.6}
        X = self.vectorizer.transform([text])
        proba = self.model.predict_proba(X)[0]
        idx = proba.argmax()
        intent = self.model.classes_[idx]
        return {'intent': intent, 'confidence': float(proba[idx])}

intent = IntentService()
