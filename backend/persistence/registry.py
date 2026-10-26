"""Import once to register all model metadata."""

from backend.persistence import foundations, models

metadata = models.Base.metadata
__all__ = ["foundations", "metadata", "models"]
