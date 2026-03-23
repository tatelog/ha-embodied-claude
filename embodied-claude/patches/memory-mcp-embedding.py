"""カスタム埋め込み関数モジュール。

intfloat/multilingual-e5-base の ONNX ベース軽量ラッパー。
e5 モデルはクエリと文書で異なるプレフィックスが必要。

PyTorch (sentence-transformers) の代わりに ONNX Runtime を使用し、
メモリ使用量を ~4GB から ~500MB に削減。
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class E5EmbeddingFunction:
    """intfloat/multilingual-e5-base 用埋め込み関数。

    e5 モデルの仕様:
    - 文書（passage）保存時: "passage: {text}" としてエンコード
    - クエリ検索時: "query: {text}" としてエンコード

    ONNX Runtime + tokenizers を使用した軽量実装。

    Args:
        model_name: Hugging Face モデル名
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-base") -> None:
        self._model_name = model_name
        self._session: Any = None
        self._tokenizer: Any = None

    def _load_model(self) -> None:
        """モデルを遅延ロード。"""
        if self._session is not None:
            return

        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
        except ImportError as e:
            raise ImportError(
                "onnxruntime, huggingface_hub, tokenizers が必要です。"
            ) from e

        # ONNX モデルをダウンロード
        try:
            model_path = hf_hub_download(
                repo_id=self._model_name,
                filename="onnx/model.onnx",
            )
        except Exception:
            # ONNX が無い場合、optimum で変換済みのモデルを試す
            model_path = hf_hub_download(
                repo_id=f"onnx-community/{self._model_name.split('/')[-1]}",
                filename="onnx/model.onnx",
            )

        tokenizer_path = hf_hub_download(
            repo_id=self._model_name,
            filename="tokenizer.json",
        )

        self._session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = Tokenizer.from_file(tokenizer_path)
        self._tokenizer.enable_padding()
        self._tokenizer.enable_truncation(max_length=512)

        logger.info("E5EmbeddingFunction: loaded ONNX model %s", self._model_name)

    def _encode(self, texts: list[str]) -> list[list[float]]:
        """テキストを埋め込みベクトルに変換。"""
        self._load_model()

        encoded = self._tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)

        input_names = [inp.name for inp in self._session.get_inputs()]
        feeds = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if "token_type_ids" in input_names:
            feeds["token_type_ids"] = np.zeros_like(input_ids, dtype=np.int64)

        outputs = self._session.run(None, feeds)

        # Mean pooling
        token_embeddings = outputs[0]  # (batch, seq_len, hidden_dim)
        mask_expanded = attention_mask[:, :, np.newaxis].astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-9, a_max=None)
        embeddings = embeddings / norms

        return embeddings.tolist()

    def __call__(self, input: list[str]) -> list[list[float]]:
        """文書保存用埋め込み（passage: プレフィックス）。"""
        prefixed = [f"passage: {doc}" for doc in input]
        return self._encode(prefixed)

    def encode_query(self, texts: list[str]) -> list[list[float]]:
        """クエリ検索用埋め込み（query: プレフィックス）。"""
        prefixed = [f"query: {t}" for t in texts]
        return self._encode(prefixed)
