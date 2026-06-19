from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

from feature_extractor import extract_feature_dict
from voice_quality_analyzer import analyze_voice_quality
    
# main function to analyze uploaded voice sample, returning extracted features and timing information
def analyze_uploaded_voice(content: bytes, original_filename: str | None = None) -> dict:
    if not content:
        raise ValueError("No audio file was uploaded.")

    started_at = perf_counter()
    request_id = uuid4().hex

    with TemporaryDirectory(prefix="vocasense_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_path = tmp_path / f"{request_id}_raw.wav"

        feature_started_at = perf_counter()
        raw_path.write_bytes(content)

        features = extract_feature_dict(raw_path)
        feature_extraction_ms = round((perf_counter() - feature_started_at) * 1000, 2)
        quality_started_at = perf_counter()
        quality = analyze_voice_quality(features)
        analyze_quality_ms = round((perf_counter()- quality_started_at) * 1000,2)
        
    return {
        "request_id": request_id,
        "input": {
            "filename": original_filename or "voice-sample.wav",
            "content_type": "audio/wav",
            "bytes": len(content),
        },
        "steps": {
            "upload_received": {"status": "done"},
            "feature_extraction": {
                "status": "done",
                "duration_ms": feature_extraction_ms,
                "feature_count": len(features),
            },
            "analyze_quality": {
                "status": "done",
                "duration_ms": analyze_quality_ms,
                "score": quality
            },
            # "supabase_persistence": {
            #     "status": "todo",
            #     "note": "Save feature JSON, factor scores, and final result under the authenticated user.",
            # },
        },
        "features": dict(features),
        "quality": dict(quality),
        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
    }
