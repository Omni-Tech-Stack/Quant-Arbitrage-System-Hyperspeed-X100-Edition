#!/usr/bin/env python
"""
Lightweight ONNX model wrapper for inference using onnxruntime.
This module provides a small helper to load an ONNX model and run
predictions for arbitrage feature matrices (numpy arrays).
"""
from typing import Optional
import numpy as np

try:
    import onnxruntime as ort
    ONNXRT_AVAILABLE = True
except Exception:
    ONNXRT_AVAILABLE = False


class ONNXModelWrapper:
    def __init__(self, onnx_path: Optional[str] = None):
        self.session = None
        if onnx_path is not None:
            self.load(onnx_path)

    def load(self, onnx_path: str):
        if not ONNXRT_AVAILABLE:
            raise RuntimeError("onnxruntime is not installed")

        self.session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])

    def predict(self, X: np.ndarray) -> Optional[np.ndarray]:
        """
        Run ONNX inference on feature matrix X (n_samples, n_features).

        Returns a 1-D numpy array of predictions clipped to [0,1], or None on error.
        """
        if self.session is None:
            return None

        try:
            input_name = self.session.get_inputs()[0].name
            result = self.session.run(None, {input_name: X.astype(np.float32)})
            preds = np.array(result[0]).flatten()
            return np.clip(preds, 0.0, 1.0)
        except Exception as e:
            print(f"[ONNXWrapper] Inference error: {e}")
            return None
