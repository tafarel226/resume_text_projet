# Résumé & QA — Prototype

Démarrage rapide:

1. Construire les services ML (local):
   - python -m venv .venv && source .venv/bin/activate
   - pip install -r backend/requirements.txt
   - python ml/train_intent.py
   - python ml/build_faiss.py

2. Lancer le backend:
   - cd backend
   - uvicorn app.main:app --reload

3. Lancer le frontend:
   - cd frontend
   - npm install
   - npm run dev

Le backend expose /api/summarize, /api/analyze, /api/feedback.



# Textes
{
  "text": "Albert Einstein était un physicien théoricien né en 1879 en Allemagne. Il est célèbre pour avoir développé la théorie de la relativité restreinte et générale. En 1921, il a reçu le prix Nobel de physique pour son explication de l'effet photoélectrique. Il a passé une grande partie de sa carrière aux États-Unis, à l'université de Princeton."
}

{
  "text": "Albert Einstein était un physicien théoricien né en 1879 en Allemagne. Il est célèbre pour avoir développé la théorie de la relativité restreinte et générale. En 1921, il a reçu le prix Nobel de physique pour son explication de l'effet photoélectrique. Il a passé une grande partie de sa carrière aux États-Unis, à l'université de Princeton.",
  "question": "Quand Einstein a-t-il reçu le prix Nobel ?"
}

{
  "query": "Le machine learning permet aux ordinateurs d'apprendre.",
  "corpus": [
    "Le machine learning est une sous-branche de l'intelligence artificielle.",
    "La physique quantique étudie le comportement des particules.",
    "Les ordinateurs peuvent apprendre sans être explicitement programmés."
  ]
}

