import io
import math
import numpy as np
import scipy.io.wavfile as wavfile
from dataclasses import dataclass


@dataclass
class AudioData:
    samples: np.ndarray
    sample_rate: int


def _percentile_exact(values: np.ndarray, ratio: float) -> float:
    """Matches the exact rounding logic of the original percentile function."""
    if len(values) == 0:
        return 0.0
    sorted_values = np.sort(values)
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * ratio)))
    return float(sorted_values[index])


def read_wav_mono(content: bytes) -> AudioData:
    """Reads WAV bytes directly into a normalized float32 NumPy array."""
    try:
        sample_rate, data = wavfile.read(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("Only WAV audio can be analyzed by this helper.") from exc

    if data.ndim > 1:
        data = data.mean(axis=1)

    # Normalize to -1.0 to 1.0 based on native dtype
    if data.dtype == np.uint8:
        samples = (data.astype(np.float32) - 128.0) / 128.0
    elif data.dtype == np.int16:
        samples = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        samples = data.astype(np.float32) / 2147483648.0
    else:
        samples = data.astype(np.float32)
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples /= max_val

    samples = np.clip(samples, -1.0, 1.0)
    if len(samples) == 0:
        raise ValueError("Audio file is empty.")
    return AudioData(samples=samples, sample_rate=sample_rate)


def _frame_audio_np(audio: AudioData, frame_ms: int = 40, hop_ms: int = 20) -> np.ndarray:
    """Splits audio into overlapping frames using efficient NumPy memory strides."""
    frame_size = max(1, round(audio.sample_rate * frame_ms / 1000))
    hop_size = max(1, round(audio.sample_rate * hop_ms / 1000))
    n_samples = len(audio.samples)
    
    if n_samples < frame_size:
        return np.array([audio.samples])
    
    shape = ((n_samples - frame_size) // hop_size + 1, frame_size)
    strides = (audio.samples.strides[0] * hop_size, audio.samples.strides[0])
    return np.lib.stride_tricks.as_strided(audio.samples, shape=shape, strides=strides)


def _dft_powers(frames: np.ndarray, sample_rate: int, freqs: np.ndarray) -> np.ndarray:
    """
    Vectorized mathematical equivalent of the original Goertzel algorithm.
    Computes exact power bins for ALL frames and ALL specified frequencies simultaneously.
    """
    n_frames, frame_len = frames.shape
    
    # Hann-like window
    window = 0.5 - 0.5 * np.cos((2.0 * np.pi * np.arange(frame_len)) / max(frame_len - 1, 1))
    windowed = frames * window
    
    t = np.arange(frame_len) / sample_rate
    omega = 2.0 * np.pi * freqs
    # Compute DFT matrix multiplication (Phase complex exponentials)
    dft_matrix = np.exp(-1j * omega[:, None] * t[None, :])
    complex_dft = np.dot(windowed, dft_matrix.T)
    
    return np.abs(complex_dft) ** 2


def _autocorrelation_pitch_np(frames: np.ndarray, sample_rate: int) -> np.ndarray:
    """Vectorized autocorrelation matching the original even-index hopping logic."""
    n_frames, frame_len = frames.shape
    min_hz, max_hz = 70, 450
    min_lag = max(1, sample_rate // max_hz)
    max_lag = min(frame_len // 2, sample_rate // min_hz)
    
    pitches = np.full(n_frames, None, dtype=object)
    if max_lag <= min_lag:
        return pitches

    energy = np.sum(frames ** 2, axis=1)
    valid_mask = energy > 1e-8
    
    best_lags = np.zeros(n_frames)
    best_corrs = np.zeros(n_frames)
    
    # Vectorized computation across all frames over valid lags
    for lag in range(min_lag, max_lag + 1):
        slice1 = frames[:, 0 : frame_len - lag : 2]
        slice2 = frames[:, lag : frame_len : 2]
        corr = np.sum(slice1 * slice2, axis=1)
        normalized = np.zeros(n_frames)
        normalized[valid_mask] = corr[valid_mask] / energy[valid_mask]
        
        update_mask = valid_mask & (normalized > best_corrs)
        best_corrs[update_mask] = normalized[update_mask]
        best_lags[update_mask] = lag
        
    pitch_mask = valid_mask & (best_corrs >= 0.18) & (best_lags > 0)
    pitches[pitch_mask] = sample_rate / best_lags[pitch_mask]
    return pitches


def _log_frequency_bins(sample_rate: int, count: int = 72) -> np.ndarray:
    min_freq = 80.0
    max_freq = min(7800.0, sample_rate / 2 - 80.0)
    if max_freq <= min_freq:
        return np.array([min_freq])
    ratio = max_freq / min_freq
    indices = np.arange(count)
    return min_freq * (ratio ** (indices / (count - 1)))


def _mel_filter_weights(bin_freqs: np.ndarray, sample_rate: int, filter_count: int = 24) -> np.ndarray:
    min_freq = 80.0
    max_freq = min(7800.0, sample_rate / 2 - 80.0)
    mel_min = 2595.0 * math.log10(1.0 + min_freq / 700.0)
    mel_max = 2595.0 * math.log10(1.0 + max_freq / 700.0)
    
    edges_mel = mel_min + (mel_max - mel_min) * np.arange(filter_count + 2) / (filter_count + 1)
    edges = 700.0 * (10 ** (edges_mel / 2595.0) - 1.0)
    
    filters = np.zeros((filter_count, len(bin_freqs)))
    for i in range(1, filter_count + 1):
        left, center, right = edges[i - 1], edges[i], edges[i + 1]
        for j, freq in enumerate(bin_freqs):
            if left < freq <= center:
                filters[i - 1, j] = (freq - left) / max(center - left, 1e-6)
            elif center < freq < right:
                filters[i - 1, j] = (right - freq) / max(right - center, 1e-6)
    return filters


def analyze_snr(audio: AudioData) -> dict:
    frames = _frame_audio_np(audio)
    rms_values = np.sqrt(np.mean(frames ** 2, axis=1))
    
    noise_floor = max(_percentile_exact(rms_values, 0.1), 1e-5)
    signal_level = max(_percentile_exact(rms_values, 0.9), noise_floor)
    reliable = noise_floor < signal_level * 0.55
    snr_db = 20 * math.log10(signal_level / noise_floor) if reliable else None
    
    return {
        "snr_db": round(snr_db, 2) if snr_db is not None else None,
        "reliable": reliable,
        "noise_floor": round(float(noise_floor), 6),
        "signal_level": round(float(signal_level), 6),
    }


def validate_sustained_ah(audio: AudioData) -> dict:
    frames = _frame_audio_np(audio)
    rms_values = np.sqrt(np.mean(frames ** 2, axis=1))
    
    noise_floor = max(_percentile_exact(rms_values, 0.1), 1e-5)
    voice_threshold = max(_percentile_exact(rms_values, 0.55) * 0.55, 0.008)

    voiced_indexes = np.where(rms_values >= voice_threshold)[0]
    voiced_frames = frames[voiced_indexes]
    voiced_ratio = len(voiced_frames) / max(len(frames), 1)
    voiced_duration_sec = len(voiced_frames) * 0.02
    
    if len(voiced_frames) == 0:
        # Fallback to prevent division by zero in entirely silent files
        voiced_frames = np.zeros((1, frames.shape[1]))
        voiced_indexes = np.array([0])

    # ZCR Vectorization
    sign_changes = (voiced_frames[:, :-1] >= 0) != (voiced_frames[:, 1:] >= 0)
    zcr_values = np.sum(sign_changes, axis=1) / (voiced_frames.shape[1] - 1)
    zcr_median = _percentile_exact(zcr_values, 0.5)
    zcr_std = float(np.std(zcr_values, ddof=0)) if len(zcr_values) >= 2 else 0.0
    
    voiced_rms_values = rms_values[voiced_indexes]
    voiced_rms_median = _percentile_exact(voiced_rms_values, 0.5)
    envelope_modulation = float(np.std(voiced_rms_values, ddof=0) / max(voiced_rms_median, 1e-5)) if len(voiced_rms_values) >= 2 else 0.0

    # Spectral Profile Vectorization (every 2nd frame)
    half_voiced = voiced_frames[::2]
    freqs = np.array([120, 180, 260, 350, 500, 700, 900, 1100, 1400, 1800, 2300, 3000, 3800, 5000, 6500])
    valid_mask = freqs < audio.sample_rate / 2
    valid_freqs = freqs[valid_mask]
    
    powers = _dft_powers(half_voiced, audio.sample_rate, valid_freqs)
    total_power = np.sum(powers, axis=1) + 1e-12
    
    centroid_values = np.sum(valid_freqs * powers, axis=1) / total_power
    high_ratios = np.sum(powers[:, valid_freqs >= 1800], axis=1) / total_power
    consonant_ratios = np.sum(powers[:, valid_freqs >= 2300], axis=1) / total_power
    music_band_ratios = np.sum(powers[:, valid_freqs >= 1400], axis=1) / total_power
    vowel_band_ratios = np.sum(powers[:, (valid_freqs >= 500) & (valid_freqs <= 1100)], axis=1) / total_power
    
    flatness_values = np.exp(np.sum(np.log(powers + 1e-12), axis=1) / len(valid_freqs)) / (total_power / len(valid_freqs))
    ratios_matrix = powers / total_power[:, None]
    entropy_values = -np.sum(ratios_matrix * np.log(ratios_matrix + 1e-12), axis=1) / math.log(len(valid_freqs))

    centroid_median = _percentile_exact(centroid_values, 0.5)
    centroid_cv = float(np.std(centroid_values, ddof=0) / max(centroid_median, 1.0))
    high_ratio_p90 = _percentile_exact(high_ratios, 0.9)
    consonant_ratio_p90 = _percentile_exact(consonant_ratios, 0.9)
    music_band_ratio_p90 = _percentile_exact(music_band_ratios, 0.9)
    vowel_band_ratio_median = _percentile_exact(vowel_band_ratios, 0.5)
    flatness_median = _percentile_exact(flatness_values, 0.5)
    entropy_median = _percentile_exact(entropy_values, 0.5)
    entropy_p90 = _percentile_exact(entropy_values, 0.9)

    speech_like_mask = (
        (zcr_values[::2] > 0.13) | (high_ratios > 0.38) | 
        (consonant_ratios > 0.24) | (music_band_ratios > 0.42) | 
        (entropy_values > 0.72) | (centroid_values > 1900)
    )
    speech_like_ratio = float(np.sum(speech_like_mask)) / max(len(centroid_values), 1)

    # MFCC Vectorization
    bin_freqs = _log_frequency_bins(audio.sample_rate)
    mfcc_powers = _dft_powers(half_voiced, audio.sample_rate, bin_freqs)
    mel_filters = _mel_filter_weights(bin_freqs, audio.sample_rate)
    mel_energies = np.dot(mfcc_powers, mel_filters.T) + 1e-12
    log_mels = np.log(mel_energies)
    
    coeff_index = np.arange(1, 14)
    mel_index = np.arange(24)
    dct_matrix = np.cos(np.pi * coeff_index[:, None] * (mel_index[None, :] + 0.5) / 24.0) / 24.0
    mfcc_vectors = np.dot(log_mels, dct_matrix.T)

    # Euclidean distance on consecutive MFCC vectors
    if len(mfcc_vectors) > 1:
        mfcc_deltas = np.sqrt(np.mean((mfcc_vectors[:-1] - mfcc_vectors[1:])**2, axis=1))
        mfcc_delta_mean = float(np.mean(mfcc_deltas))
        mfcc_delta_p90 = _percentile_exact(mfcc_deltas, 0.9)
        mfcc_unstable_ratio = float(np.sum(mfcc_deltas > 0.58)) / max(len(mfcc_deltas), 1)
    else:
        mfcc_deltas = np.array([])
        mfcc_delta_mean = mfcc_delta_p90 = mfcc_unstable_ratio = 0.0

    mfcc_std_values = np.std(mfcc_vectors[:, :10], axis=0, ddof=0) if len(mfcc_vectors) > 0 else np.zeros(10)
    mfcc_std_mean = float(np.mean(mfcc_std_values))

    centroid_jumps = int(np.sum(np.abs(centroid_values[1:] - centroid_values[:-1]) > 180))

    # Pitch Analysis
    pitches_raw = _autocorrelation_pitch_np(half_voiced, audio.sample_rate)
    pitch_values = np.array([p for p in pitches_raw if p is not None], dtype=float)
    pitch_coverage = len(pitch_values) / max(len(half_voiced), 1)
    pitch_stability = 0.0
    if len(pitch_values) > 0:
        pitch_median = _percentile_exact(pitch_values, 0.5)
        pitch_stability = float(np.std(pitch_values, ddof=0) / max(pitch_median, 1.0))

    # Event Counters Vectorization
    onset_count = int(np.sum(rms_values[1:] > np.maximum(rms_values[:-1] * 1.45, voice_threshold * 1.25)))

    prevs = rms_values[:-2]
    currs = rms_values[1:-1]
    nexts = rms_values[2:]
    local_floors = np.maximum(np.maximum(prevs, nexts), voice_threshold)
    envelope_peak_count = int(np.sum((currs > local_floors * 1.45) & (currs > voice_threshold * 1.3)))

    is_gap = rms_values < voice_threshold
    gap_count = int(np.sum(~is_gap[:-1] & is_gap[1:]))

    duration_sec = len(audio.samples) / audio.sample_rate

    # Rule validations
    reasons: list[str] = []
    if duration_sec < 3.0:
        reasons.append("Audio is too short.")
    if voiced_ratio < 0.8:
        reasons.append("The voiced part is not continuous enough.")
    if voiced_duration_sec < 2.8:
        reasons.append("Voiced duration is too short.")
    if onset_count > 3:
        reasons.append("Repeated syllable-like attacks were detected.")
    if envelope_peak_count > 7 or envelope_modulation > 0.75:
        reasons.append("Amplitude changes look like running speech rather than one held Ah.")
    if gap_count > 5:
        reasons.append("The voice has too many gaps.")
    if zcr_median > 0.18 or zcr_std > 0.07:
        reasons.append("The sound changes too much, like speech rather than a held vowel.")
    if speech_like_ratio > 0.12:
        reasons.append("Spectral changes look like consonants or changing vowels, not sustained Ah.")
    elif centroid_cv > 0.8 and mfcc_unstable_ratio > 0.2:
        reasons.append("Spectral changes look too unstable for one sustained vowel.")
    if high_ratio_p90 > 0.55 or consonant_ratio_p90 > 0.35:
        reasons.append("Too much high-frequency consonant-like energy was detected.")
    if music_band_ratio_p90 > 0.48 or entropy_p90 > 0.78:
        reasons.append("Broadband background audio was detected behind the voice.")
    if mfcc_delta_mean > 0.28 or mfcc_delta_p90 > 0.72 or mfcc_unstable_ratio > 0.22:
        reasons.append("MFCC changes are too large for one sustained Ah vowel.")
    if mfcc_std_mean > 1.1 and entropy_median > 0.52:
        reasons.append("MFCC texture looks like mixed speech/music instead of a single vowel.")
    if vowel_band_ratio_median < 0.03 and centroid_median > 1200:
        reasons.append("The vowel band is too weak for an Ah-like sample.")
    if pitch_coverage < 0.35:
        reasons.append("Not enough voiced pitch was detected.")
    if voiced_rms_median < 0.015:
        reasons.append("Voice level is too weak.")
    if vowel_band_ratio_median < 0.015:
        reasons.append("The vowel resonance is too weak for a sustained Ah.")
    if centroid_median < 220 and vowel_band_ratio_median < 0.025 and pitch_stability < 0.03:
        reasons.append("The sound is too muffled or humming-like for an Ah vowel.")
    if centroid_jumps > 7 and centroid_cv > 0.35:
        reasons.append("Too many vowel shape changes were detected.")

    accepted = not reasons
    
    # Cast all numpy types to native Python types for clean JSON response
    return {
        "accepted": accepted,
        "reasons": reasons,
        "duration_sec": round(float(duration_sec), 2),
        "voiced_ratio": round(float(voiced_ratio), 3),
        "voiced_duration_sec": round(float(voiced_duration_sec), 2),
        "onset_count": int(onset_count),
        "envelope_peak_count": int(envelope_peak_count),
        "gap_count": int(gap_count),
        "zcr_median": round(float(zcr_median), 4),
        "zcr_std": round(float(zcr_std), 4),
        "envelope_modulation": round(float(envelope_modulation), 3),
        "speech_like_ratio": round(float(speech_like_ratio), 3),
        "spectral_centroid_median": round(float(centroid_median), 2),
        "spectral_centroid_cv": round(float(centroid_cv), 3),
        "high_ratio_p90": round(float(high_ratio_p90), 3),
        "consonant_ratio_p90": round(float(consonant_ratio_p90), 3),
        "music_band_ratio_p90": round(float(music_band_ratio_p90), 3),
        "vowel_band_ratio_median": round(float(vowel_band_ratio_median), 3),
        "spectral_flatness_median": round(float(flatness_median), 3),
        "spectral_entropy_median": round(float(entropy_median), 3),
        "spectral_entropy_p90": round(float(entropy_p90), 3),
        "mfcc_delta_mean": round(float(mfcc_delta_mean), 3),
        "mfcc_delta_p90": round(float(mfcc_delta_p90), 3),
        "mfcc_std_mean": round(float(mfcc_std_mean), 3),
        "mfcc_unstable_ratio": round(float(mfcc_unstable_ratio), 3),
        "pitch_coverage": round(float(pitch_coverage), 3),
        "pitch_stability": round(float(pitch_stability), 3),
        "centroid_jumps": int(centroid_jumps),
        "voiced_rms_median": round(float(voiced_rms_median), 6),
    }


def analyze_voice_sample(content: bytes) -> dict:
    audio = read_wav_mono(content)
    snr = analyze_snr(audio)
    ah = validate_sustained_ah(audio)
    
    min_required_snr = 12
    if ah["voiced_rms_median"] < 0.03:
        min_required_snr = 8

    reasons = list(ah["reasons"])
    if snr["reliable"] and snr["snr_db"] < min_required_snr:
        reasons.append("SNR is too low; background noise is too high.")

    accepted = ah["accepted"] and (not snr["reliable"] or snr["snr_db"] >= min_required_snr)
    
    return {
        "accepted": accepted,
        "snr": snr,
        "ah_validation": {**ah, "accepted": accepted, "reasons": reasons},
    }