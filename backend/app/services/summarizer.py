"""
Wrapper pour le service de résumé
"""
from typing import Dict, Any
from .backend_summarizer import (
    SummarizeRequest as BackendSummarizeRequest,
    summarize as backend_summarize,
)

class Summarizer:
    """Service de résumé qui utilise le backend_summarizer"""

    def __init__(self) -> None:
        pass

    async def summarize(
        self,
        text: str,
        method: str = "abstractive",
        params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        params = params or {}
        req = BackendSummarizeRequest(
            text=text,
            method=method,
            extractive=params.get("extractive", {}),
            abstractive=params.get("abstractive", {}),
            interface=params.get("interface", {}),
        )
        # !!! on attend la coroutine directement
        return await backend_summarize(req)
