"""
Excepciones personalizadas del dominio de TecniDesk.
"""


class TecniDeskException(Exception):
    """Excepción base para errores específicos de la aplicación."""
    def __init__(self, message: str = "Error interno de la aplicación"):
        self.message = message
        super().__init__(self.message)


class EmbeddingServiceUnavailableError(TecniDeskException):
    """
    Se lanza cuando el servicio local de embeddings (Ollama / Tailscale Funnel)
    no responde, devuelve un error HTTP o supera el timeout.
    """
    def __init__(
        self,
        message: str = "Local embedding service unavailable. Please check Tailscale Funnel / Mac mini Ollama status.",
    ):
        super().__init__(message)
