#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.backend_summarizer import app
import uvicorn

if __name__ == "__main__":
    print("Démarrage du serveur backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
