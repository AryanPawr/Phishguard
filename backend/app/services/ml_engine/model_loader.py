from functools import lru_cache

from app.core.config import get_settings
from app.services.ml_engine.inference import PhishingModel


@lru_cache
def get_model() -> PhishingModel:
    return PhishingModel(get_settings().model_path)

