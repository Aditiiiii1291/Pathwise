import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

try:
    from app.schemas.features import StudentFeatures
except ImportError:
    from backend.app.schemas.features import StudentFeatures

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "ml" / "models" / "dropout_detector.joblib"
DEFAULT_METADATA_PATH = BASE_DIR / "ml" / "models" / "metadata.json"

class MLPredictor:
    """Inference service for Pathwise Dropout Probability prediction."""

    _instance = None
    _model = None
    _metadata = None

    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        metadata_path: Path = DEFAULT_METADATA_PATH,
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self._ensure_loaded()

    def _ensure_loaded(self):
        """Loads model and metadata lazily/on-demand."""
        if self._model is None or self._metadata is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Trained model artifact not found at '{self.model_path}'. "
                    "Run 'python -m ml.training.train' to train and serialize the model."
                )
            if not self.metadata_path.exists():
                raise FileNotFoundError(
                    f"Model metadata not found at '{self.metadata_path}'."
                )

            self._model = joblib.load(self.model_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

    @property
    def feature_names(self) -> List[str]:
        self._ensure_loaded()
        return self._metadata["feature_names"]

    def predict_dropout_probability(self, features: StudentFeatures) -> float:
        """
        Computes predicted dropout probability for a single student.
        Returns a float between 0.0 and 1.0.
        """
        self._ensure_loaded()
        feat_dict = features.model_dump()

        # Build feature vector in exact order expected by trained model
        feature_vector = []
        for name in self.feature_names:
            if name not in feat_dict:
                raise ValueError(f"Missing required ML feature: '{name}'")
            val = feat_dict[name]
            feature_vector.append(float(val) if isinstance(val, (int, float, bool)) else val)

        x_df = pd.DataFrame([feature_vector], columns=self.feature_names)
        prob = float(self._model.predict_proba(x_df)[0, 1])
        return round(min(1.0, max(0.0, prob)), 4)

    def get_feature_importances(self) -> List[Dict[str, Any]]:
        """Returns global feature importances from model metadata."""
        self._ensure_loaded()
        return self._metadata.get("feature_importances", [])
