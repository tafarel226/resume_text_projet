from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.summarizer import Summarizer


router = APIRouter()

class SummarizeRequest(BaseModel):
    text: str
    method: Optional[str] = "abstractive"  # "abstractive" | "extractive" | "hybrid"
    params: Optional[Dict[str, Any]] = {}
    lang: Optional[str] = "fr"

summ = Summarizer()
# ... (tes autres services / modèles)

@router.get("/health")
def health():
    return {"ok": True}

    
@router.post("/summarize")
async def summarize(req: SummarizeRequest):
    # Passer lang dans params pour que Summarizer puisse en tenir compte
    params = req.params or {}
    params["lang"] = req.lang

    try:
        raw = await summ.summarize(req.text, method=req.method, params=params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    # Récupérer toujours "summary" si dispo
    summary_text = raw.get("summary")
    if not summary_text:  
        # fallback sur extractive ou sur un tronqué
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
        "lang": req.lang,   # <-- renvoyer aussi la langue utilisée
    }
