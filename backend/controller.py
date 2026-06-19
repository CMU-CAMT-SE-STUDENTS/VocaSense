from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

from feature_extractor import extract_feature_dict
from voice_quality_analyzer import analyze_voice_quality

# handle noise reduction using noisereduce library, with error handling for missing dependency
def _run_noise_reduction(input_path: Path, output_path: Path) -> None:
    try:
        import noisereduce as nr
        import soundfile as sf
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "noisereduce is not installed. Install backend requirements before running voice analysis."
        ) from exc

    audio, sample_rate = sf.read(input_path)
    denoised_audio = nr.reduce_noise(y=audio, sr=sample_rate, stationary=False)
    sf.write(output_path, denoised_audio, sample_rate)

# main function to analyze uploaded voice sample, returning extracted features and timing information
def analyze_uploaded_voice(content: bytes, original_filename: str | None = None) -> dict:
    if not content:
        raise ValueError("No audio file was uploaded.")

    started_at = perf_counter()
    request_id = uuid4().hex

    with TemporaryDirectory(prefix="vocasense_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_path = tmp_path / f"{request_id}_raw.wav"
        denoised_path = tmp_path / f"{request_id}_denoised.wav"

        raw_path.write_bytes(content)

        noise_reduction_started_at = perf_counter()
        _run_noise_reduction(raw_path, denoised_path)
        noise_reduction_ms = round((perf_counter() - noise_reduction_started_at) * 1000, 2)

        feature_started_at = perf_counter()
        features = extract_feature_dict(denoised_path)
        feature_extraction_ms = round((perf_counter() - feature_started_at) * 1000, 2)
        
        quality = analyze_voice_quality(features)
        analyze_quality_ms = round((perf_counter()- feature_extraction_ms) * 1000,2)

    return {
        "request_id": request_id,
        "input": {
            "filename": original_filename or "voice-sample.wav",
            "content_type": "audio/wav",
            "bytes": len(content),
        },
        "steps": {
            "upload_received": {"status": "done"},
            "noise_reduction": {
                "status": "done",
                "engine": "noisereduce",
                "duration_ms": noise_reduction_ms,
            },
            "feature_extraction": {
                "status": "done",
                "duration_ms": feature_extraction_ms,
                "feature_count": len(features),
            },
            "descriptive_model": {
                "status": "done",
                "duration_ms": analyze_quality_ms,
                "score": len(quality)
            },
            # "supabase_persistence": {
            #     "status": "todo",
            #     "note": "Save feature JSON, factor scores, and final result under the authenticated user.",
            # },
        },
        "features": dict(features),
        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
    }
