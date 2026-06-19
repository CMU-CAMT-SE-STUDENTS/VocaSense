from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Iterable

import librosa
import numpy as np
import parselmouth
from parselmouth.praat import call
import antropy as ant
from scipy import signal
from scipy.signal import resample

EPSILON = 1e-10
N_MFCC = 13

# save float conversion and NaN/inf handling in one place
def _safe_float(value: float | int | np.floating | None) -> float:
    if value is None:
        return 0.0
    value = float(value)
    if np.isnan(value) or np.isinf(value):
        return 0.0
    return value

# safe mean and std that ignore NaN/inf and return 0.0 if no valid values
def _safe_mean(values: Iterable[float]) -> float:
    values = np.asarray(list(values), dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0
    return _safe_float(np.mean(values))

# safe std that ignores NaN/inf and returns 0.0 if less than 2 valid values
def _safe_std(values: Iterable[float]) -> float:
    values = np.asarray(list(values), dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return 0.0
    return _safe_float(np.std(values, ddof=0))

# calculate average power in a frequency band from a spectrogram
def _band_power(
    spectrogram_power: np.ndarray,
    frequencies: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> float:
    mask = (frequencies >= low_hz) & (frequencies < high_hz)
    if not np.any(mask):
        return 0.0
    return _safe_float(np.mean(np.sum(spectrogram_power[mask, :], axis=0)))

# extract voice quality features using parselmouth/praat, with error handling
def _extract_voice_quality_features(sound: parselmouth.Sound) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()

    pitch_floor = 75.0
    pitch_ceiling = 600.0

    try:
        point_process = call(sound, "To PointProcess (periodic, cc)", pitch_floor, pitch_ceiling)
        features["jitter_local"] = _safe_float(
            call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        )
        features["shimmer_local"] = _safe_float(
            call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        )
    except Exception:
        features["jitter_local"] = 0.0
        features["shimmer_local"] = 0.0

    try:
        harmonicity = call(sound, "To Harmonicity (cc)", 0.01, pitch_floor, 0.1, 1.0)
        features["hnr_db"] = _safe_float(call(harmonicity, "Get mean", 0, 0))
    except Exception:
        features["hnr_db"] = 0.0

    try:
        power_cepstrogram = call(sound, "To PowerCepstrogram", pitch_floor, 0.002, 5000.0, 50.0)
        features["cpps_db"] = _safe_float(
            call(
                power_cepstrogram,
                "Get CPPS",
                True,
                0.02,
                0.0005,
                pitch_floor,
                330.0,
                0.05,
                "Parabolic",
                0.001,
                0.0,
                "Exponential decay",
                "Robust",
            )
        )
    except Exception:
        features["cpps_db"] = 0.0
    return features

# estimate CPPS from raw audio using cepstral analysis
def _estimate_cpps(y: np.ndarray, sr: int) -> float:
    frame_length = min(2048, max(256, int(round(sr * 0.04))))
    hop_length = max(1, int(round(sr * 0.01)))

    if y.size < frame_length:
        return 0.0

    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length).T
    window = np.hanning(frame_length)
    min_quefrency = int(np.floor(sr / 330.0))
    max_quefrency = int(np.ceil(sr / 75.0))
    max_quefrency = min(max_quefrency, frame_length - 1)

    if min_quefrency >= max_quefrency:
        return 0.0

    cpps_values: list[float] = []
    for frame in frames:
        if np.sqrt(np.mean(frame**2)) < 1e-4:
            continue

        spectrum = np.fft.rfft(frame * window)
        log_power = np.log(np.abs(spectrum) ** 2 + EPSILON)
        cepstrum = np.fft.irfft(log_power, n=frame_length)
        search_region = cepstrum[min_quefrency : max_quefrency + 1]

        if search_region.size < 3:
            continue

        peak_offset = int(np.argmax(search_region))
        peak_index = min_quefrency + peak_offset
        x = np.arange(search_region.size, dtype=float)
        slope, intercept = np.polyfit(x, search_region, deg=1)
        trend_at_peak = slope * peak_offset + intercept
        cpps_values.append(float(cepstrum[peak_index] - trend_at_peak))

    return _safe_mean(cpps_values)

# extract F0 features using librosa.pyin, with error handling
def _extract_f0_features(y: np.ndarray, sr: int) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()

    try:
        f0, _, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("D5"),
            sr=sr,
        )
        voiced_f0 = f0[np.isfinite(f0)]
    except Exception:
        voiced_f0 = np.array([], dtype=float)

    features["f0_mean_hz"] = _safe_mean(voiced_f0)
    features["f0_std_hz"] = _safe_std(voiced_f0)
    features["f0_min_hz"] = _safe_float(np.min(voiced_f0)) if voiced_f0.size else 0.0
    features["f0_max_hz"] = _safe_float(np.max(voiced_f0)) if voiced_f0.size else 0.0
    features["f0_voiced_ratio"] = _safe_float(voiced_f0.size / max(1, len(f0))) if "f0" in locals() else 0.0

    return features

# extract spectral features including alpha ratio, spectral flux, spectral slope, and spectral centroid. Using librosa, with error handling
def _extract_spectral_features(y: np.ndarray, sr: int) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()

    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    power = stft**2
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=2048)

    low_power = _band_power(power, frequencies, 50.0, 1000.0)
    high_power = _band_power(power, frequencies, 1000.0, min(5000.0, sr / 2.0))
    features["alpha_ratio_db"] = _safe_float(10.0 * np.log10((low_power + EPSILON) / (high_power + EPSILON)))

    if stft.shape[1] > 1:
        normalized = stft / np.maximum(np.sum(stft, axis=0, keepdims=True), EPSILON)
        frame_diffs = np.diff(normalized, axis=1)
        features["spectral_flux_mean"] = _safe_float(np.mean(np.sqrt(np.sum(frame_diffs**2, axis=0))))
        features["spectral_flux_std"] = _safe_std(np.sqrt(np.sum(frame_diffs**2, axis=0)))
    else:
        features["spectral_flux_mean"] = 0.0
        features["spectral_flux_std"] = 0.0

    mean_spectrum_db = librosa.amplitude_to_db(np.mean(stft, axis=1) + EPSILON, ref=np.max)
    valid = (frequencies > 0) & np.isfinite(mean_spectrum_db)
    if np.count_nonzero(valid) >= 2:
        slope, _ = np.polyfit(frequencies[valid], mean_spectrum_db[valid], deg=1)
        features["spectral_slope_db_per_hz"] = _safe_float(slope)
    else:
        features["spectral_slope_db_per_hz"] = 0.0

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_centroid_mean_hz"] = _safe_mean(centroid)
    features["spectral_centroid_std_hz"] = _safe_std(centroid)

    return features

# extract MFCC features using librosa, with error handling. Returning mean and std for each coefficient
def _extract_mfcc_features(y: np.ndarray, sr: int) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_means = np.mean(mfcc, axis=1)
    mfcc_stds = np.std(mfcc, axis=1, ddof=0)

    for index, value in enumerate(mfcc_means, start=1):
        features[f"mfcc_{index}_mean"] = _safe_float(value)
    for index, value in enumerate(mfcc_stds, start=1):
        features[f"mfcc_{index}_std"] = _safe_float(value)

    return features

# extract sample entropy features using antropy, with error handling
def _extract_sample_entropy_features(y: np.ndarray, sr: int) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()

    y_small = resample(y, 4000)
    try:
        features["sample_entropy"] = float(
            ant.sample_entropy(y_small)
        )
    except Exception:
        features["sample_entropy"] = 0.0

    return features

# extract spectral entropy features using antropy, with error handling
def _extract_spectral_entropy_features(y: np.ndarray, sr: int) -> OrderedDict[str, float]:
    features: OrderedDict[str, float] = OrderedDict()
    try:
        features["spectral_entropy"] = float(
            ant.spectral_entropy(y, sr)
        )
    except Exception:
        features["spectral_entropy"] = 0.0

    return features

# main feature extraction function that combines all features into a single dictionary, with option to return as NumPy array
def extract_feature_dict(file_path: str | Path) -> OrderedDict[str, float]:
    """
    Extract clinical/acoustic voice features from an audio file.

    Returned features include jitter, shimmer, HNR, CPPS, MFCC, F0, alpha ratio,
    spectral flux, spectral slope, and spectral centroid.
    """
    file_path = str(file_path)
    y, sr = librosa.load(file_path, sr=None, mono=True)

    if y.size == 0:
        raise ValueError("Audio file is empty.")

    y, _ = librosa.effects.trim(y, top_db=35)
    if y.size == 0:
        raise ValueError("Audio file contains only silence.")

    sound = parselmouth.Sound(file_path)

    features: OrderedDict[str, float] = OrderedDict()
    features.update(_extract_voice_quality_features(sound))
    if features["cpps_db"] == 0.0:
        features["cpps_db"] = _estimate_cpps(y, sr)
    features.update(_extract_f0_features(y, sr))
    features.update(_extract_spectral_features(y, sr))
    features.update(_extract_mfcc_features(y, sr))
    features.update(_extract_sample_entropy_features(y, sr))
    features.update(_extract_spectral_entropy_features(y, sr))
    return features

# main extraction function that returns features as a NumPy array, with option to get feature names
def extract_features(file_path: str | Path, as_dict: bool = False) -> np.ndarray | OrderedDict[str, float]:
    """
    Extract features from an audio file.

    By default this keeps the previous module behavior and returns a NumPy vector.
    Pass as_dict=True when feature names are needed.
    """
    features = extract_feature_dict(file_path)
    if as_dict:
        return features
    return np.asarray(list(features.values()), dtype=np.float32)

# helper function to get feature names in the same order as extract_features()
def get_feature_names() -> list[str]:
    """Return feature names in the same order as extract_features()."""
    dummy_names = [
        "jitter_local",
        "shimmer_local",
        "hnr_db",
        "cpps_db",
        "sample_entropy",
        "spectral_entropy",
        "f0_mean_hz",
        "f0_std_hz",
        "f0_min_hz",
        "f0_max_hz",
        "f0_voiced_ratio",
        "alpha_ratio_db",
        "spectral_flux_mean",
        "spectral_flux_std",
        "spectral_slope_db_per_hz",
        "spectral_centroid_mean_hz",
        "spectral_centroid_std_hz",
    ]
    mfcc_mean_names = [f"mfcc_{index}_mean" for index in range(1, N_MFCC + 1)]
    mfcc_std_names = [f"mfcc_{index}_std" for index in range(1, N_MFCC + 1)]
    return dummy_names + mfcc_mean_names + mfcc_std_names

# print("Starting feature extraction test...")
# file_path = Path(r"D:\Work\VocaSense\ml\dataset\ไฟล์เสียง\cold\cold1.mp3")
# features = extract_features(file_path, as_dict=True)
# print(features)