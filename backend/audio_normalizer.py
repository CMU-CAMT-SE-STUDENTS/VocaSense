"""Canonical waveform standardizer; it never decides whether audio is Ah."""
from dataclasses import dataclass
import math,numpy as np
from scipy.signal import resample_poly
import input_validator as legacy
from validator_config import DEFAULT_CONFIG
@dataclass
class NormalizationResult:
    audio:np.ndarray; sample_rate:int; native_sample_rate:int; analysis_sample_rate:int; applied_gain:float; initial_peak:float; final_peak:float; initial_voiced_rms_median:float; final_voiced_rms_median:float; low_rms_rescue_used:bool; low_rms_rescue_limited:bool; low_rms_rescue_unmet:bool; dc_offset_before:float; dc_offset_after:float
def normalize_for_voice_analysis(audio,sample_rate):
    x=np.asarray(audio,dtype=np.float32)
    if x.ndim>1:x=x.mean(axis=-1)
    native=int(sample_rate);g=math.gcd(native,DEFAULT_CONFIG.canonical_sr)
    if native!=DEFAULT_CONFIG.canonical_sr:x=resample_poly(x,DEFAULT_CONFIG.canonical_sr//g,native//g).astype(np.float32)
    dc=float(np.mean(x));x=x-dc;initial_peak=float(np.max(np.abs(x))) if len(x) else 0.
    initial=legacy.validate_sustained_ah(legacy.AudioData(x,DEFAULT_CONFIG.canonical_sr))['voiced_rms_median'];requested=1.;gain=1.
    if initial<DEFAULT_CONFIG.low_rms_threshold:
        requested=DEFAULT_CONFIG.low_rms_threshold/max(initial,1e-8);gain=min(requested,DEFAULT_CONFIG.safe_peak/max(initial_peak,1e-8));x=x*gain
    final_peak=float(np.max(np.abs(x))) if len(x) else 0.;final=legacy.validate_sustained_ah(legacy.AudioData(x.astype(np.float32),DEFAULT_CONFIG.canonical_sr))['voiced_rms_median']
    return NormalizationResult(x.astype(np.float32),DEFAULT_CONFIG.canonical_sr,native,DEFAULT_CONFIG.canonical_sr,float(gain),initial_peak,final_peak,initial,final,gain!=1.,gain+1e-12<requested,bool(gain!=1. and final<DEFAULT_CONFIG.low_rms_threshold),dc,float(np.mean(x)))
