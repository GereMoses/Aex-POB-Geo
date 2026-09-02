"""
Face verification for punch selfies.

Optional by design. The models and their runtime add roughly 300MB to an
image, which is a lot to impose on a deployment that may be happy with a
supervisor reviewing photos by eye. If the dependencies are absent the service
reports itself unavailable and the punch path falls back to PENDING_REVIEW —
exactly the behaviour before this module existed.

Install with:  pip install -r requirements-face.txt

What gets stored is a 512-float embedding, never the photo. An embedding
cannot be inverted back into a face, so a database leak does not hand anyone a
biometric photo library.
"""

from __future__ import annotations

import base64
import binascii
import logging
import threading
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_NAME = "buffalo_s"
EMBEDDING_DIMS = 512

# Detection struggles below roughly 160px: a pre-cropped thumbnail carries no
# surrounding context for the detector to lock onto, so small images are
# upscaled before detection rather than being reported as faceless.
_MIN_DETECT_PX = 160

_lock = threading.Lock()
_app = None
_unavailable_reason: Optional[str] = None


class FaceResult:
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NO_FACE = "NO_FACE"
    NOT_ENROLLED = "NOT_ENROLLED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class Comparison:
    verdict: str
    score: Optional[float] = None


def _load():
    """
    Load the model once, on first use.

    Deliberately lazy: the first load downloads and initialises several hundred
    megabytes, which must not happen during application startup — a warehouse
    waiting to clock in should not be held up by a cold model.
    """
    global _app, _unavailable_reason
    if _app is not None or _unavailable_reason is not None:
        return _app
    with _lock:
        if _app is not None or _unavailable_reason is not None:
            return _app
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(
                name=MODEL_NAME,
                providers=["CPUExecutionProvider"],
                allowed_modules=["detection", "recognition"],
            )
            app.prepare(ctx_id=-1, det_size=(640, 640))
            _app = app
            logger.info("Face verification ready (%s)", MODEL_NAME)
        except ImportError as e:
            _unavailable_reason = f"dependencies not installed ({e})"
            logger.info("Face verification unavailable — %s", _unavailable_reason)
        except Exception as e:
            _unavailable_reason = str(e)
            logger.warning("Face verification could not start: %s", e)
    return _app


def is_available() -> bool:
    return _load() is not None


def unavailable_reason() -> Optional[str]:
    _load()
    return _unavailable_reason


def _decode(image_b64: str):
    """Decode a base64 image into a BGR array, or None if it is not an image."""
    import numpy as np
    import cv2

    payload = image_b64.split(",", 1)[-1] if image_b64.startswith("data:") else image_b64
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return None
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    if min(h, w) < _MIN_DETECT_PX:
        scale = _MIN_DETECT_PX / min(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


def embed(image_b64: str):
    """
    The face embedding for the largest face in an image, or None.

    Largest, not first: a punch selfie taken at a warehouse gate may catch a
    colleague in the background, and the person holding the phone is the one
    filling the frame.
    """
    app = _load()
    if app is None:
        return None
    img = _decode(image_b64)
    if img is None:
        return None
    faces = app.get(img)
    if not faces:
        return None

    import numpy as np

    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    v = np.asarray(largest.normed_embedding, dtype="float32")
    norm = np.linalg.norm(v)
    return (v / norm) if norm else None


def to_bytes(vec) -> bytes:
    return vec.astype("float32").tobytes()


def from_bytes(raw: bytes):
    import numpy as np
    return np.frombuffer(raw, dtype="float32")


def similarity(a, b) -> float:
    """Cosine similarity of two normalised embeddings, in [-1, 1]."""
    import numpy as np
    return float(np.dot(a, b))


def verify(selfie_b64: str, reference: Optional[bytes], threshold: float) -> Comparison:
    """
    Compare a punch selfie against an employee's enrolled face.

    Every outcome other than MATCH/MISMATCH means "could not decide", and the
    caller treats those as a photo for a human rather than as an accusation.
    """
    if not is_available():
        return Comparison(FaceResult.UNAVAILABLE)
    if not reference:
        return Comparison(FaceResult.NOT_ENROLLED)

    probe = embed(selfie_b64)
    if probe is None:
        return Comparison(FaceResult.NO_FACE)

    score = similarity(probe, from_bytes(reference))
    return Comparison(
        FaceResult.MATCH if score >= threshold else FaceResult.MISMATCH,
        round(score, 4),
    )
