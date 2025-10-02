from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.summarizer import Summarizer
from rouge_score import rouge_scorer

router = APIRouter()

class SummarizeRequest(BaseModel):
    text: str
    method: Optional[str] = "abstractive"  # "abstractive" | "extractive" | "hybrid"
    params: Optional[Dict[str, Any]] = {}
    lang: Optional[str] = "fr"

# ✅ Ajoute ta classe ici
class EvaluateRequest(BaseModel):
    generated: str
    reference: str

summ = Summarizer()

@router.get("/health")
def health():
    return {"ok": True}

@router.post("/summarize")
async def summarize(req: SummarizeRequest):
    params = req.params or {}
    params["lang"] = req.lang

    try:
        raw = await summ.summarize(req.text, method=req.method, params=params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    summary_text = raw.get("summary")
    if not summary_text:  
        summary_text = " ".join(raw.get("extractive_sentences", [])) or req.text[:200]

    original_len = len(req.text or "")
    summary_len = len(summary_text or "")
    compression = round((1 - (summary_len / original_len)) * 100, 2) if original_len else 0

    return {
        "summary": summary_text,
        "original_length": original_len,
        "summary_length": summary_len,
        "compression": compression,
        "meta": raw.get("meta", {}),
        "method": req.method,
        "lang": req.lang,
    }

@router.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    try:
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(req.reference, req.generated)

        return {
            "rouge1": {
                "precision": round(scores['rouge1'].precision, 4),
                "recall": round(scores['rouge1'].recall, 4),
                "fmeasure": round(scores['rouge1'].fmeasure, 4)
            },
            "rouge2": {
                "precision": round(scores['rouge2'].precision, 4),
                "recall": round(scores['rouge2'].recall, 4),
                "fmeasure": round(scores['rouge2'].fmeasure, 4)
            },
            "rougeL": {
                "precision": round(scores['rougeL'].precision, 4),
                "recall": round(scores['rougeL'].recall, 4),
                "fmeasure": round(scores['rougeL'].fmeasure, 4)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
