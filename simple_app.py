#!/usr/bin/env python3
"""
Application simple pour tester le projet
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Résumé de Textes - Application Simple")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    text: str
    method: Optional[str] = "simple"

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int

@app.get("/")
async def root():
    return {"message": "Application de résumé de textes - Version simple"}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "simple"}

@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """Résumé simple : prend les premières phrases"""
    text = request.text.strip()
    if not text:
        return SummarizeResponse(summary="", original_length=0, summary_length=0)
    
    # Résumé très simple : prendre les 2 premières phrases
    sentences = text.split('. ')
    if len(sentences) > 2:
        summary = '. '.join(sentences[:2]) + '.'
    else:
        summary = text
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(text),
        summary_length=len(summary)
    )

@app.post("/api/qa")
async def question_answering(request: dict):
    """Question-answering simple"""
    text = request.get("text", "")
    question = request.get("question", "")
    
    # Réponse simple basée sur des mots-clés
    if not text or not question:
        return {"answer": "Veuillez fournir un texte et une question"}
    
    # Recherche simple de mots-clés
    question_words = question.lower().split()
    text_sentences = text.split('. ')
    
    for sentence in text_sentences:
        if any(word in sentence.lower() for word in question_words):
            return {"answer": sentence.strip()}
    
    return {"answer": "Aucune réponse trouvée dans le texte"}

if __name__ == "__main__":
    print("🚀 Démarrage de l'application simple...")
    print("📝 Accédez à la documentation sur: http://localhost:8000/docs")
    print("🔗 API disponible sur: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
