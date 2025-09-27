from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.summarizer import Summarizer
from ..services.ner_service import NERService
from ..services.intent_service import IntentService
from ..services.matcher import Matcher
from ..db import async_session
from ..models import FAQ, Feedback
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

router = APIRouter()

class SummarizeRequest(BaseModel):
    text: str
    method: Optional[str] = "abstractive"
    params: Optional[Dict[str, Any]] = {}

class AnalyzeRequest(BaseModel):
    text: str

class FeedbackRequest(BaseModel):
    input_text: str
    useful: bool
    comment: Optional[str] = None

# --- MODELS ---
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# --- SCHEMAS ---
class QABase(BaseModel):
    text: str
    question: str

# Charger le modèle une seule fois
model = SentenceTransformer('all-mpnet-base-v2')

# Schéma de la requête
class SimilarityRequest(BaseModel):
    query: str
    corpus: list[str]

# Schéma de la réponse
class SimilarityResponse(BaseModel):
    scores: list[float]
    most_similar_index: int
    most_similar_text: str

# instantiate services (singleton-ish)
summ = Summarizer()
ner = NERService()
intent = IntentService()
matcher = Matcher()

@router.post("/summarize")
async def summarize(req: SummarizeRequest):
    result = summ.summarize(req.text, method=req.method, params=req.params)
    return result

@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    entities = ner.extract(req.text)
    intent_res = intent.predict(req.text)
    matches = matcher.match(req.text, entities)
    return {"entities": entities, "intent": intent_res, "matches": matches}

@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    async with async_session() as s:
        f = Feedback(input_text=req.input_text, useful=req.useful, comment=req.comment)
        s.add(f)
        await s.commit()
    return {"ok": True}


# --- ENDPOINTS ---
@router.post("/qa/")
async def question_answering(data: QABase):
    result = qa_pipeline(question=data.question, context=data.text)
    return {"answer": result["answer"]}

@router.post("/similarity/", response_model=SimilarityResponse)
def compute_similarity(request: SimilarityRequest):
    # Générer les embeddings
    query_emb = model.encode([request.query])
    corpus_emb = model.encode(request.corpus)

    # Calculer la similarité cosinus
    scores = cosine_similarity(query_emb, corpus_emb)[0].tolist()

    # Trouver le texte le plus similaire
    most_similar_index = int(np.argmax(scores))
    most_similar_text = request.corpus[most_similar_index]

    return SimilarityResponse(
        scores=scores,
        most_similar_index=most_similar_index,
        most_similar_text=most_similar_text
    )