"""
Backend prototype pour l'application de résumé de textes
Fichier: backend_summarizer.py

- Framework: FastAPI
- Endpoints:
  - POST /api/summarize  -> param: { text, method, extractive, abstractive, interface }
  - POST /api/evaluate   -> param: { text, summary }
  - POST /api/compare    -> param: { text, params }

Fonctionnalités incluses:
- Extractive: TextRank (graph + PageRank) et TF-IDF sentence scoring
- Abstractive: wrapper Hugging Face Transformers pour T5 / mBART (avec chargement lazy)
- Hybrid: extractive -> abstractive pipeline
- Évaluation: ROUGE-1/2/L via rouge_score; cohérence approximée via embeddings (sentence-transformers)
- Mode fallback (mock) si modèle absent

Instructions rapides:
1) Installer dépendances (idéalement dans un venv):
   pip install fastapi uvicorn transformers sentence-transformers scikit-learn rouge-score networkx nltk python-multipart
   (pour la lecture PDF: pip install PyMuPDF)

2) Lancer le serveur:
   uvicorn backend_summarizer:app --host 0.0.0.0 --port 8000 --reload

3) Tester:
   POST http://localhost:8000/api/summarize avec JSON {"text": "...", "method": "extractive", "extractive": {...}}

Remarque: Le chargement des modèles HF peut prendre du temps et de la mémoire; prévoir GPU pour gros modèles.

"""

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import math
import logging

# NLP libs
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx

# Try importing heavy libs lazily; if unavailable, the server will still start with mock behavior
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except Exception:
    ROUGE_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    S_BERT_AVAILABLE = True
except Exception:
    S_BERT_AVAILABLE = False

# Optional: nltk sentence tokenizer
try:
    import nltk
    nltk.data.find("tokenizers/punkt")
except Exception:
    try:
        import nltk
        nltk.download("punkt")
    except Exception:
        pass
from nltk.tokenize import sent_tokenize

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Summarizer Backend Prototype")

# -------------------- Pydantic models --------------------
class TextRankParams(BaseModel):
    damping: float = 0.85
    window: int = 2

class ExtractiveParams(BaseModel):
    algo: str = "textrank"  # textrank | tfidf
    num_sentences: int = 3
    textrank: TextRankParams = TextRankParams()
    tfidf: Dict[str, Any] = {"ngram": 1}

class AbstractiveParams(BaseModel):
    model: str = "t5-small"  # t5-small | t5-base | mbart
    max_tokens: int = 150
    temperature: float = 0.0
    num_beams: int = 4
    style: str = "neutral"

class InterfaceParams(BaseModel):
    length_limit: int = 120
    compress_ratio: float = 0.2

class SummarizeRequest(BaseModel):
    text: str
    method: str = "extractive"  # extractive | abstractive | hybrid
    extractive: ExtractiveParams = ExtractiveParams()
    abstractive: AbstractiveParams = AbstractiveParams()
    interface: InterfaceParams = InterfaceParams()

class EvaluateRequest(BaseModel):
    text: str
    summary: str

class CompareRequest(BaseModel):
    text: str
    params: SummarizeRequest

# -------------------- Utilities --------------------

def simple_sentence_tokenize(text: str) -> List[str]:
    sents = sent_tokenize(text)
    return [s.strip() for s in sents if s.strip()]


def build_sentence_graph(sentences: List[str], vectorizer=None) -> np.ndarray:
    # Represent sentences using TF-IDF vectors (or provided vectorizer)
    if vectorizer is None:
        vectorizer = TfidfVectorizer(ngram_range=(1,1), stop_words='english')
        X = vectorizer.fit_transform(sentences)
    else:
        X = vectorizer.transform(sentences)
    # cosine similarity
    sim = (X @ X.T).toarray()
    # zero diagonal
    np.fill_diagonal(sim, 0)
    return sim


def textrank_select(sentences: List[str], num_sentences: int, damping=0.85) -> List[int]:
    if len(sentences) == 0:
        return []
    if len(sentences) <= num_sentences:
        return list(range(len(sentences)))
    sim = build_sentence_graph(sentences)
    # build graph
    G = nx.from_numpy_array(sim)
    try:
        scores = nx.pagerank(G, alpha=damping)
    except Exception:
        # fallback: degree centrality
        scores = nx.degree_centrality(G)
    # sort sentences by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    selected_indices = [idx for idx, score in ranked[:num_sentences]]
    # preserve original order
    selected_indices = sorted(selected_indices)
    return selected_indices


def tfidf_select(sentences: List[str], num_sentences: int, ngram: int = 1) -> List[int]:
    if len(sentences) == 0:
        return []
    vect = TfidfVectorizer(ngram_range=(1, ngram), stop_words='english')
    X = vect.fit_transform(sentences)
    # sentence score = sum of tfidf weights
    scores = np.array(X.sum(axis=1)).ravel()
    ranked = np.argsort(-scores)
    selected = sorted(ranked[:num_sentences])
    return selected

# -------------------- Abstractive wrapper --------------------
MODEL_CACHE: Dict[str, Any] = {}
TOKENIZER_CACHE: Dict[str, Any] = {}
SENTENCE_EMBED_MODEL = None


def load_abstractive_model(name: str):
    if not TRANSFORMERS_AVAILABLE:
        raise RuntimeError("Transformers library not available")
    if name in MODEL_CACHE:
        return TOKENIZER_CACHE[name], MODEL_CACHE[name]
    logger.info(f"Loading model {name} ...")
    # mapping for friendly names
    mapping = {
        "t5-small": "t5-small",
        "t5-base": "t5-base",
        "mbart": "facebook/mbart-large-50-many-to-one-mmt"
    }
    model_name = mapping.get(name, name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    TOKENIZER_CACHE[name] = tokenizer
    MODEL_CACHE[name] = model
    return tokenizer, model


def generate_abstractive(text: str, params: AbstractiveParams) -> str:
    if not TRANSFORMERS_AVAILABLE:
        # fallback: return a naive truncation
        words = text.split()
        return " ".join(words[: params.length_limit if hasattr(params, 'length_limit') else 50])
    tokenizer, model = load_abstractive_model(params.model)
    # prepare input for T5-style models
    prefix = "summarize: " if params.model.startswith("t5") else ""
    input_text = prefix + text
    batch = tokenizer([input_text], max_length=1024, truncation=True, return_tensors="pt")
    gen = model.generate(
        **batch,
        max_length=params.max_tokens,
        num_beams=params.num_beams,
        do_sample=(params.temperature > 0.0),
        temperature=params.temperature,
        early_stopping=True
    )
    out = tokenizer.decode(gen[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return out

# -------------------- Evaluation --------------------

def compute_rouge(reference: str, prediction: str) -> Dict[str, float]:
    if not ROUGE_AVAILABLE:
        return {"rouge1": None, "rouge2": None, "rougel": None}
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return {
        "rouge1": scores["rouge1"].fmeasure,
        "rouge2": scores["rouge2"].fmeasure,
        "rougel": scores["rougeL"].fmeasure,
    }


def coherence_score(sentences: List[str]) -> float:
    # approximate coherence: average cosine similarity between consecutive sentence embeddings
    global SENTENCE_EMBED_MODEL
    if not S_BERT_AVAILABLE:
        # fallback heuristic: ratio of sentences length variance (bad) -> return 0.5
        return 0.5
    if SENTENCE_EMBED_MODEL is None:
        SENTENCE_EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    embs = SENTENCE_EMBED_MODEL.encode(sentences)
    if len(embs) < 2:
        return 1.0
    sims = []
    for i in range(len(embs) - 1):
        a = embs[i]
        b = embs[i+1]
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            sims.append(0.0)
        else:
            sims.append(float(np.dot(a, b) / denom))
    return float(np.mean(sims))

# -------------------- Endpoints --------------------
@app.post("/api/summarize")
async def summarize(req: SummarizeRequest):
    text = req.text or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    sentences = simple_sentence_tokenize(text)
    results = {"summary": "", "extractive_sentences": []}

    # Extractive
    if req.method in ["extractive", "hybrid"]:
        if req.extractive.algo == "textrank":
            idxs = textrank_select(sentences, req.extractive.num_sentences, req.extractive.textrank.damping)
        else:
            idxs = tfidf_select(sentences, req.extractive.num_sentences, ngram=req.extractive.tfidf.get('ngram', 1))
        selected = [sentences[i] for i in idxs]
        results["extractive_sentences"] = selected

    # Abstractive
    if req.method == "abstractive":
        try:
            abstr = generate_abstractive(text, req.abstractive)
            results["summary"] = abstr
        except Exception as e:
            logger.exception("Abstractive generation failed")
            # fallback to first N sentences
            results["summary"] = " ".join(sentences[: req.extractive.num_sentences])
    elif req.method == "extractive":
        results["summary"] = " ".join(results["extractive_sentences"]) if results["extractive_sentences"] else (" ".join(sentences[:req.extractive.num_sentences]))
    elif req.method == "hybrid":
        # feed extracted content to abstractive model for compression/rewrite
        extracted_text = " ".join(results["extractive_sentences"]) if results["extractive_sentences"] else " ".join(sentences[:req.extractive.num_sentences])
        try:
            abstr = generate_abstractive(extracted_text, req.abstractive)
            results["summary"] = abstr
        except Exception:
            results["summary"] = extracted_text

    # meta
    meta = {"num_sentences": len(sentences), "method": req.method}
    return {**results, "meta": meta}


@app.post("/api/evaluate")
async def evaluate(req: EvaluateRequest):
    if not req.text or not req.summary:
        raise HTTPException(status_code=400, detail="text and summary required")
    # Use first paragraph of text as pseudo-reference if real reference not provided
    # In practical use, pass a human reference summary for ROUGE.
    reference = req.text  # naive
    rouge = compute_rouge(reference, req.summary)
    sents = simple_sentence_tokenize(req.summary)
    coh = coherence_score(sents)
    return {"rouge": rouge, "coherence": coh}


@app.post("/api/compare")
async def compare(req: CompareRequest):
    # Run extractive and abstractive with given params and return side-by-side
    sr = req.params
    # force extractive
    extractive_req = SummarizeRequest(text=req.text, method="extractive", extractive=sr.extractive)
    abstractive_req = SummarizeRequest(text=req.text, method="abstractive", abstractive=sr.abstractive)
    ex = await summarize(extractive_req)
    ab = await summarize(abstractive_req)
    # hybrid
    hybrid_req = SummarizeRequest(text=req.text, method="hybrid", extractive=sr.extractive, abstractive=sr.abstractive)
    hy = await summarize(hybrid_req)
    return {
        "extractive": ex,
        "abstractive": ab,
        "hybrid": hy,
    }

# -------------------- Health endpoint --------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "transformers": TRANSFORMERS_AVAILABLE, "rouge": ROUGE_AVAILABLE, "sbert": S_BERT_AVAILABLE}

# -------------------- If run as script --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend_summarizer:app", host="127.0.0.1", port=8000, reload=True)
