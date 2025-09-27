"""
Wrapper pour le service de résumé
"""

from typing import Dict, Any
from .backend_summarizer import SummarizeRequest as BackendSummarizeRequest, summarize as backend_summarize

class Summarizer:
    """Service de résumé qui utilise le backend_summarizer"""
    
    def __init__(self):
        pass
    
    def summarize(self, text: str, method: str = "extractive", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Résume un texte avec la méthode spécifiée"""
        if params is None:
            params = {}
            
        # Créer une requête compatible avec le backend
        req = BackendSummarizeRequest(
            text=text,
            method=method,
            extractive=params.get('extractive', {}),
            abstractive=params.get('abstractive', {}),
            interface=params.get('interface', {})
        )
        
        # Appeler la fonction de résumé du backend
        import asyncio
        return asyncio.run(backend_summarize(req))
