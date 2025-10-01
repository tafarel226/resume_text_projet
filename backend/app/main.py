from fastapi import FastAPI
from .api.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Résumé & QA Service")
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"status":"ok","service":"Résumé & Autres"}

@app.get("/health")
async def health():
    return {"status": "ok"}


# Autoriser les appels du frontend (ex: vite sur localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ton frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
