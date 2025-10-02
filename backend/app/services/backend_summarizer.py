"""
Backend prototype pour l'application de résumé de textes
"""

from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx
from typing import Optional

# -------------------- Heavy libs lazy import --------------------
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

# -------------------- NLTK --------------------
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

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Summarizer Backend Prototype")

# -------------------- Pydantic models --------------------
class TextRankParams(BaseModel):
    damping: float = 0.85
    window: int = 2

class ExtractiveParams(BaseModel):
    algo: str = "textrank"
    num_sentences: int = 2
    textrank: TextRankParams = TextRankParams()
    tfidf: Dict[str, Any] = {"ngram": 1}

class AbstractiveParams(BaseModel):
    model: str = None   # sera défini selon lang si vide
    max_tokens: int = 40
    temperature: float = 0.7
    num_beams: int = 4
    style: str = "neutral"

class InterfaceParams(BaseModel):
    length_limit: int = 120
    compress_ratio: float = 0.2

class SummarizeRequest(BaseModel):
    text: str
    method: str = "abstractive"   # "extractive", "abstractive", "hybrid"
    lang: Optional[str] = "fr"             # ⬅️ nouvelle option : "fr" ou "en"
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

# -------------------- Extractive --------------------
def build_sentence_graph(sentences: List[str], vectorizer=None) -> np.ndarray:
    if vectorizer is None:
        vectorizer = TfidfVectorizer(ngram_range=(1,1), stop_words="english")
        X = vectorizer.fit_transform(sentences)
    else:
        X = vectorizer.transform(sentences)
    sim = (X @ X.T).toarray()
    np.fill_diagonal(sim, 0)
    return sim

def textrank_select(sentences: List[str], num_sentences: int, damping=0.85) -> List[int]:
    if len(sentences) == 0:
        return []
    if len(sentences) <= num_sentences:
        return list(range(len(sentences)))
    sim = build_sentence_graph(sentences)
    import networkx as nx
    G = nx.from_numpy_array(sim)
    try:
        scores = nx.pagerank(G, alpha=damping)
    except Exception:
        scores = nx.degree_centrality(G)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted([idx for idx, _ in ranked[:num_sentences]])

def tfidf_select(sentences: List[str], num_sentences: int, ngram: int = 1) -> List[int]:
    if len(sentences) == 0:
        return []
    vect = TfidfVectorizer(ngram_range=(1, ngram), stop_words="english")
    X = vect.fit_transform(sentences)
    scores = np.array(X.sum(axis=1)).ravel()
    ranked = np.argsort(-scores)
    return sorted(ranked[:num_sentences])

# -------------------- Abstractive wrapper --------------------
MODEL_CACHE: Dict[str, Any] = {}
TOKENIZER_CACHE: Dict[str, Any] = {}

def select_model_for_lang(lang: str) -> str:
    """Choisit un modèle en fonction de la langue"""
    if lang.lower() == "fr":
        return "plguillou/t5-base-fr-sum-cnndm"
    elif lang.lower() == "en":
        return "t5-small"
    else:
        return "facebook/mbart-large-50-many-to-one-mmt"  # fallback multi-langue

def load_abstractive_model(name: str):
    if not TRANSFORMERS_AVAILABLE:
        raise RuntimeError("Transformers library not available")
    if name in MODEL_CACHE:
        return TOKENIZER_CACHE[name], MODEL_CACHE[name]
    logger.info(f"Loading model {name} ...")
    tokenizer = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSeq2SeqLM.from_pretrained(name)
    TOKENIZER_CACHE[name] = tokenizer
    MODEL_CACHE[name] = model
    return tokenizer, model

def generate_abstractive(text: str, params: AbstractiveParams, lang: str = "fr") -> str:
    if not TRANSFORMERS_AVAILABLE:
        return " ".join(text.split()[: params.max_tokens//2])

    # 🔥 si français, on force le modèle FR par défaut
    # if lang == "fr" and params.model in ["t5-small", "t5-base"]:
    #     model_name = "plguillou/t5-base-fr-sum-cnndm"
    # else:
    #     model_name = params.model
    model_name = "plguillou/t5-base-fr-sum-cnndm"
    if not model_name:
        model_name = select_model_for_lang(lang)
    #je veux avoir la position de lang
    print("Langue sélectionnée :", lang)
    print("Modèle sélectionné :", model_name)


    tokenizer, model = load_abstractive_model(model_name)
    prefix = "summarize: " if model_name.startswith("t5") else ""
    input_text = prefix + text
    batch = tokenizer([input_text], max_length=1024, truncation=True, return_tensors="pt")
    gen = model.generate(
        **batch,
        max_length=params.max_tokens,
        num_beams=params.num_beams,
        do_sample=(params.temperature > 0.0),
        temperature=params.temperature,
        early_stopping=True,
    )
    return tokenizer.decode(gen[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

# -------------------- Endpoints --------------------
@app.post("/api/summarize")
async def summarize(req: SummarizeRequest):
    valid_methods = ["extractive", "abstractive", "hybrid"]
    method = req.method if req.method in valid_methods else "abstractive"
    lang = getattr(req, "lang", "fr")  # si pas fourni → "fr"

    logger.info(f"⚡ backend_summarizer appelé avec méthode={method}, lang={lang}")

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    sentences = simple_sentence_tokenize(text)
    results = {"summary": "", "extractive_sentences": []}

    # --- extractive ---
    if method in ["extractive", "hybrid"]:
        if req.extractive.algo == "textrank":
            idxs = textrank_select(sentences, req.extractive.num_sentences)
        else:
            idxs = tfidf_select(sentences, req.extractive.num_sentences)
        results["extractive_sentences"] = [sentences[i] for i in idxs]

    # --- abstractive ---
    if method == "abstractive":
        try:
            results["summary"] = generate_abstractive(text, req.abstractive)
        except Exception as e:
            logger.exception(f"Erreur résumés abstractive: {e}")
            results["summary"] = " ".join(sentences[: req.extractive.num_sentences])
    elif method == "extractive":
        results["summary"] = " ".join(results["extractive_sentences"])
    elif method == "hybrid":
        extracted_text = " ".join(results["extractive_sentences"])
        try:
            results["summary"] = generate_abstractive(extracted_text, req.abstractive)
        except Exception as e:
            logger.exception(f"Erreur résumés hybrid: {e}")
            results["summary"] = extracted_text

    return {
        **results,
        "meta": {
            "num_sentences": len(sentences),
            "method": method,
            "lang": lang,
        },
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "transformers": TRANSFORMERS_AVAILABLE}
