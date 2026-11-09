"""Centralized, calibration-backed production-candidate constants."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ValidatorConfig:
    canonical_sr:int=16000
    safe_peak:float=.95
    low_rms_threshold:float=.015
    speech_frame_trigger_count:int=2
    temporal_evidence_required:int=2
    vowel_identity_evidence_required:int=2
    quality_background_evidence_required:int=2
DEFAULT_CONFIG=ValidatorConfig()
