"""Attach journey-stage predictions to the labeled review frame."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    COL_REVIEW,
    COL_STARS,
    COL_STORE_NAME,
    JOURNEY_CLASSES,
    JOURNEY_MERGE_CSV,
    JOURNEY_MODEL_CONFIG,
    JOURNEY_MODEL_WEIGHTS,
    PACKAGE_ROOT,
)

logger = logging.getLogger(__name__)

STAGE_DIR = PACKAGE_ROOT / "journey_classification"


class JourneyClassificationError(RuntimeError):
    """Raised when journey predictions cannot be produced."""


def _pred_columns() -> list[str]:
    cols: list[str] = []
    for name in JOURNEY_CLASSES:
        cols.extend([f"{name}_prob", f"{name}_pred"])
    return cols


def _tokenize(text: object) -> list[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", str(text).lower())
    return cleaned.split()


def _tokens_to_padded(
    token_lists: list[list[str]], vocab: dict[str, int], max_len: int
) -> np.ndarray:
    unk = vocab.get("<UNK>", 1)
    pad = vocab.get("<PAD>", 0)
    sequences = []
    for tokens in token_lists:
        seq = [vocab.get(tok, unk) for tok in tokens][:max_len]
        if len(seq) < max_len:
            seq = seq + [pad] * (max_len - len(seq))
        sequences.append(seq)
    return np.asarray(sequences, dtype=np.int64)


def _infer_with_model(df: pd.DataFrame) -> pd.DataFrame:
    """Run local BiLSTM inference when model artifacts are present."""
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise JourneyClassificationError(
            "PyTorch is required for local journey inference. "
            "Install torch or provide reviews_with_journey_preds.csv for merge mode."
        ) from exc

    with JOURNEY_MODEL_CONFIG.open(encoding="utf-8") as f:
        config = json.load(f)
    vocab: dict[str, int] = config["vocab"]
    max_len = int(config["max_len"])

    class BiLSTMClassifier(nn.Module):
        def __init__(
            self,
            vocab_size: int,
            embedding_dim: int = 128,
            hidden_dim: int = 128,
            num_classes: int = 4,
            dropout: float = 0.3,
        ) -> None:
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
            self.lstm = nn.LSTM(
                embedding_dim,
                hidden_dim,
                num_layers=1,
                bidirectional=True,
                batch_first=True,
            )
            self.dropout = nn.Dropout(dropout)
            self.fc = nn.Linear(hidden_dim * 2, num_classes)

        def forward(self, text: torch.Tensor) -> torch.Tensor:
            embedded = self.dropout(self.embedding(text))
            lstm_out, _ = self.lstm(embedded)
            pooled, _ = torch.max(lstm_out, dim=1)
            return self.fc(self.dropout(pooled))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BiLSTMClassifier(vocab_size=len(vocab)).to(device)
    state = torch.load(JOURNEY_MODEL_WEIGHTS, map_location=device)
    model.load_state_dict(state)
    model.eval()

    sequences = _tokens_to_padded(
        [_tokenize(t) for t in df[COL_REVIEW].tolist()], vocab, max_len
    )
    probs_all: list[np.ndarray] = []
    batch_size = 64
    with torch.no_grad():
        for start in range(0, len(sequences), batch_size):
            batch = torch.tensor(
                sequences[start : start + batch_size], dtype=torch.long, device=device
            )
            logits = model(batch)
            probs_all.append(torch.sigmoid(logits).cpu().numpy())
    probs = np.concatenate(probs_all, axis=0)
    preds = (probs > 0.5).astype(int)

    out = df.copy()
    for i, name in enumerate(JOURNEY_CLASSES):
        out[f"{name}_prob"] = probs[:, i]
        out[f"{name}_pred"] = preds[:, i]
    logger.info(
        "Journey classification via local model (%s rows)", len(out)
    )
    return out


def _merge_saved_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """Merge Colab/export predictions onto the current frame."""
    pred_df = pd.read_csv(JOURNEY_MERGE_CSV)
    needed = [COL_STORE_NAME, COL_STARS, COL_REVIEW, *_pred_columns()]
    missing = [c for c in needed if c not in pred_df.columns]
    if missing:
        raise JourneyClassificationError(
            f"{JOURNEY_MERGE_CSV.name} missing columns: {missing}"
        )

    keys = [COL_STORE_NAME, COL_STARS, COL_REVIEW]
    slim = pred_df[needed].drop_duplicates(subset=keys, keep="first")
    merged = df.merge(slim, on=keys, how="left")

    for name in JOURNEY_CLASSES:
        prob_col = f"{name}_prob"
        pred_col = f"{name}_pred"
        missing_mask = merged[pred_col].isna()
        if missing_mask.any():
            logger.warning(
                "Journey merge: %s rows missing %s; filling with 0",
                int(missing_mask.sum()),
                pred_col,
            )
        merged[prob_col] = merged[prob_col].fillna(0.0)
        merged[pred_col] = merged[pred_col].fillna(0).astype(int)

    logger.info(
        "Journey classification via saved predictions merge (%s rows from %s)",
        len(merged),
        JOURNEY_MERGE_CSV.name,
    )
    return merged


def apply_journey_classification(df: pd.DataFrame) -> pd.DataFrame:
    """Add multi-label journey probabilities and predictions.

    Preference order:
      1) local model artifacts under journey_classification/model/
      2) merge reviews_with_journey_preds.csv
    """
    has_model = JOURNEY_MODEL_WEIGHTS.exists() and JOURNEY_MODEL_CONFIG.exists()
    has_merge = JOURNEY_MERGE_CSV.exists()

    if has_model:
        return _infer_with_model(df)
    if has_merge:
        logger.info(
            "Model artifacts not found under %s; using saved predictions CSV.",
            STAGE_DIR / "model",
        )
        return _merge_saved_predictions(df)

    raise JourneyClassificationError(
        "Journey classification assets missing. Either place "
        f"{JOURNEY_MODEL_WEIGHTS.name} and {JOURNEY_MODEL_CONFIG.name} in "
        f"{STAGE_DIR / 'model'}, or provide {JOURNEY_MERGE_CSV}."
    )
