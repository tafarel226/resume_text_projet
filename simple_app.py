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
    """Résumé intelligent basé sur la fréquence des mots"""
    text = request.text.strip()
    if not text:
        return SummarizeResponse(summary="", original_length=0, summary_length=0)
    
    # Diviser en phrases
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in '.!?':
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    if len(sentences) <= 2:
        return SummarizeResponse(
            summary=text,
            original_length=len(text),
            summary_length=len(text)
        )
    
    # Compter la fréquence des mots (sans ponctuation)
    word_freq = {}
    for sentence in sentences:
        words = sentence.lower().replace(',', '').replace(';', '').replace(':', '').replace('(', '').replace(')', '').split()
        for word in words:
            if len(word) > 3:  # Ignorer les mots trop courts
                word_freq[word] = word_freq.get(word, 0) + 1
    
    # Calculer un score pour chaque phrase
    sentence_scores = []
    for sentence in sentences:
        score = 0
        words = sentence.lower().replace(',', '').replace(';', '').replace(':', '').replace('(', '').replace(')', '').split()
        for word in words:
            if len(word) > 3:
                score += word_freq.get(word, 0)
        sentence_scores.append(score)
    
    # Sélectionner les 2 phrases avec les scores les plus élevés
    if len(sentences) >= 2:
        # Trier par score décroissant
        scored_sentences = list(zip(sentences, sentence_scores))
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Prendre les 2 meilleures phrases
        top_sentences = [sent for sent, score in scored_sentences[:2]]
        
        # Reconstituer le résumé en gardant l'ordre original
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences and sentence not in summary_sentences:
                summary_sentences.append(sentence)
        
        summary = ' '.join(summary_sentences)
    else:
        summary = text
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(text),
        summary_length=len(summary)
    )


if __name__ == "__main__":
    print("🚀 Démarrage de l'application simple...")
    print("📝 Accédez à la documentation sur: http://localhost:8000/docs")
    print("🔗 API disponible sur: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
