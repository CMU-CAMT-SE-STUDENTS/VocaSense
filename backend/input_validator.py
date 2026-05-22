import io
import math
import statistics
import struct
import wave
from dataclasses import dataclass


@dataclass
class AudioData:
    samples: list[float]
    sample_rate: int


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * ratio)))
    return sorted_values[index]


def _rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)

# Read WAV audio bytes and convert to mono float samples in the range -1..1
def read_wav_mono(content: bytes) -> AudioData:
    """Read PCM WAV bytes into mono float samples in the range -1..1."""
    try:
        with wave.open(io.BytesIO(content), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            frame_count = wav.getnframes()
            raw = wav.readframes(frame_count)
    except wave.Error as exc:
        raise ValueError("Only WAV audio can be analyzed by this helper.") from exc

    if channels < 1:
        raise ValueError("Audio must contain at least one channel.")

    samples: list[float] = []
    if sample_width == 1:
        for frame in range(0, len(raw), channels):
            values = [(raw[frame + channel] - 128) / 128 for channel in range(channels)]
            samples.append(sum(values) / channels)
    elif sample_width == 2:
        step = channels * 2
        for frame in range(0, len(raw), step):
            values = [
                struct.unpack_from("<h", raw, frame + channel * 2)[0] / 32768
                for channel in range(channels)
            ]
            samples.append(sum(values) / channels)
    elif sample_width == 3:
        step = channels * 3
        for frame in range(0, len(raw), step):
            values = []
            for channel in range(channels):
                offset = frame + channel * 3
                value = int.from_bytes(raw[offset : offset + 3], "little", signed=True)
                values.append(value / 8388608)
            samples.append(sum(values) / channels)
    elif sample_width == 4:
        step = channels * 4
        for frame in range(0, len(raw), step):
            values = [
                struct.unpack_from("<i", raw, frame + channel * 4)[0] / 2147483648
                for channel in range(channels)
            ]
            samples.append(sum(values) / channels)
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes.")

    samples = [max(-1.0, min(1.0, sample)) for sample in samples]
    if not samples:
        raise ValueError("Audio file is empty.")
    return AudioData(samples=samples, sample_rate=sample_rate)

# split audio to frames of given length and hop, return list of frames (each frame is a list of samples)
def _frame_audio(audio: AudioData, frame_ms: int = 40, hop_ms: int = 20) -> list[list[float]]:
    frame_size = max(1, round(audio.sample_rate * frame_ms / 1000))
    hop_size = max(1, round(audio.sample_rate * hop_ms / 1000))
    if len(audio.samples) < frame_size:
        return [audio.samples]
    return [
        audio.samples[start : start + frame_size]
        for start in range(0, len(audio.samples) - frame_size + 1, hop_size)
    ]


def _zero_crossing_rate(frame: list[float]) -> float:
    if len(frame) < 2:
        return 0.0
    crossings = 0
    previous = frame[0]
    for sample in frame[1:]:
        if (previous >= 0 > sample) or (previous < 0 <= sample):
            crossings += 1
        previous = sample
    return crossings / (len(frame) - 1)

# Estimate pitch using autocorrelation method, return frequency in Hz or None if no clear pitch is detected
def _autocorrelation_pitch(frame: list[float], sample_rate: int) -> float | None:
    min_hz = 70
    max_hz = 450
    min_lag = max(1, sample_rate // max_hz)
    max_lag = min(len(frame) // 2, sample_rate // min_hz)
    if max_lag <= min_lag:
        return None

    energy = sum(sample * sample for sample in frame)
    if energy <= 1e-8:
        return None

    best_lag = None
    best_corr = 0.0
    for lag in range(min_lag, max_lag + 1):
        corr = 0.0
        for index in range(0, len(frame) - lag, 2):
            corr += frame[index] * frame[index + lag]
        normalized = corr / energy
        if normalized > best_corr:
            best_corr = normalized
            best_lag = lag

    if best_lag is None or best_corr < 0.18:
        return None
    return sample_rate / best_lag

# Goertzel algorithm to estimate power at a specific frequency in a frame
def _goertzel_power(frame: list[float], sample_rate: int, frequency: float) -> float:
    if not frame:
        return 0.0
    normalized = frequency / sample_rate
    coefficient = 2.0 * math.cos(2.0 * math.pi * normalized)
    previous = 0.0
    previous2 = 0.0
    for index, sample in enumerate(frame):
        window = 0.5 - 0.5 * math.cos((2.0 * math.pi * index) / max(len(frame) - 1, 1))
        value = sample * window + coefficient * previous - previous2
        previous2 = previous
        previous = value
    return previous2 * previous2 + previous * previous - coefficient * previous * previous2

# Analyze spectral profile of a frame, return dict with centroid and energy ratios in specific bands
def _spectral_profile(frame: list[float], sample_rate: int) -> dict:
    freqs = (120, 180, 260, 350, 500, 700, 900, 1100, 1400, 1800, 2300, 3000, 3800, 5000, 6500)
    powers = [(freq, _goertzel_power(frame, sample_rate, freq)) for freq in freqs if freq < sample_rate / 2]
    total = sum(power for _, power in powers) + 1e-12
    centroid = sum(freq * power for freq, power in powers) / total
    high_power = sum(power for freq, power in powers if freq >= 1800)
    consonant_power = sum(power for freq, power in powers if freq >= 2300)
    music_band_power = sum(power for freq, power in powers if freq >= 1400)
    vowel_band_power = sum(power for freq, power in powers if 500 <= freq <= 1100)
    flatness = math.exp(sum(math.log(power + 1e-12) for _, power in powers) / len(powers)) / (total / len(powers))
    entropy = 0.0
    for _, power in powers:
        ratio = power / total
        entropy -= ratio * math.log(ratio + 1e-12)
    entropy /= math.log(len(powers))
    return {
        "centroid": centroid,
        "high_ratio": high_power / total,
        "consonant_ratio": consonant_power / total,
        "music_band_ratio": music_band_power / total,
        "vowel_band_ratio": vowel_band_power / total,
        "flatness": flatness,
        "entropy": entropy,
    }


def _mel_scale(freq: float) -> float:
    return 2595.0 * math.log10(1.0 + freq / 700.0)


def _inverse_mel_scale(mel: float) -> float:
    return 700.0 * (10 ** (mel / 2595.0) - 1.0)


def _log_frequency_bins(sample_rate: int, count: int = 72) -> list[float]:
    min_freq = 80.0
    max_freq = min(7800.0, sample_rate / 2 - 80.0)
    if max_freq <= min_freq:
        return [min_freq]
    ratio = max_freq / min_freq
    return [min_freq * (ratio ** (index / (count - 1))) for index in range(count)]


def _mel_filter_weights(bin_freqs: list[float], sample_rate: int, filter_count: int = 24) -> list[list[float]]:
    min_freq = 80.0
    max_freq = min(7800.0, sample_rate / 2 - 80.0)
    mel_min = _mel_scale(min_freq)
    mel_max = _mel_scale(max_freq)
    edges = [
        _inverse_mel_scale(mel_min + (mel_max - mel_min) * index / (filter_count + 1))
        for index in range(filter_count + 2)
    ]
    filters: list[list[float]] = []
    for index in range(1, filter_count + 1):
        left = edges[index - 1]
        center = edges[index]
        right = edges[index + 1]
        weights = []
        for freq in bin_freqs:
            if freq <= left or freq >= right:
                weights.append(0.0)
            elif freq <= center:
                weights.append((freq - left) / max(center - left, 1e-6))
            else:
                weights.append((right - freq) / max(right - center, 1e-6))
        filters.append(weights)
    return filters


def _mfcc_profile(frame: list[float], sample_rate: int, coeff_count: int = 13) -> dict:
    bin_freqs = _log_frequency_bins(sample_rate)
    powers = [_goertzel_power(frame, sample_rate, freq) for freq in bin_freqs]
    filters = _mel_filter_weights(bin_freqs, sample_rate)
    mel_energies = [
        sum(power * weight for power, weight in zip(powers, weights)) + 1e-12
        for weights in filters
    ]
    log_mels = [math.log(energy) for energy in mel_energies]
    coeffs = []
    for coeff_index in range(1, coeff_count + 1):
        coeff = 0.0
        for mel_index, value in enumerate(log_mels):
            coeff += value * math.cos(math.pi * coeff_index * (mel_index + 0.5) / len(log_mels))
        coeffs.append(coeff / len(log_mels))
    return {"coeffs": coeffs, "log_mels": log_mels}


def _euclidean_distance(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)) / min(len(left), len(right)))


def analyze_snr(audio: AudioData) -> dict:
    frames = _frame_audio(audio)
    rms_values = [_rms(frame) for frame in frames]
    noise_floor = max(_percentile(rms_values, 0.1), 1e-5)
    signal_level = max(_percentile(rms_values, 0.9), noise_floor)
    reliable = noise_floor < signal_level * 0.55
    snr_db = 20 * math.log10(signal_level / noise_floor) if reliable else None
    return {
        "snr_db": round(snr_db, 2) if snr_db is not None else None,
        "reliable": reliable,
        "noise_floor": round(noise_floor, 6),
        "signal_level": round(signal_level, 6),
    }


def validate_sustained_ah(audio: AudioData) -> dict:
    frames = _frame_audio(audio)
    rms_values = [_rms(frame) for frame in frames]
    noise_floor = max(_percentile(rms_values, 0.1), 1e-5)
    voice_threshold = max(_percentile(rms_values, 0.55) * 0.55, 0.008)

    voiced_indexes = [index for index, value in enumerate(rms_values) if value >= voice_threshold]
    voiced_frames = [frames[index] for index in voiced_indexes]
    voiced_ratio = len(voiced_frames) / max(len(frames), 1)
    voiced_duration_sec = len(voiced_frames) * 0.02

    zcr_values = [_zero_crossing_rate(frame) for frame in voiced_frames]
    zcr_median = _percentile(zcr_values, 0.5)
    zcr_std = _std(zcr_values)
    voiced_rms_values = [rms_values[index] for index in voiced_indexes]
    envelope_modulation = _std(voiced_rms_values) / max(_percentile(voiced_rms_values, 0.5), 1e-5)

    profiles = [_spectral_profile(frame, audio.sample_rate) for frame in voiced_frames[::2]]
    centroid_values = [profile["centroid"] for profile in profiles]
    high_ratios = [profile["high_ratio"] for profile in profiles]
    consonant_ratios = [profile["consonant_ratio"] for profile in profiles]
    music_band_ratios = [profile["music_band_ratio"] for profile in profiles]
    vowel_band_ratios = [profile["vowel_band_ratio"] for profile in profiles]
    flatness_values = [profile["flatness"] for profile in profiles]
    entropy_values = [profile["entropy"] for profile in profiles]
    centroid_median = _percentile(centroid_values, 0.5)
    centroid_cv = _std(centroid_values) / max(centroid_median, 1.0)
    high_ratio_p90 = _percentile(high_ratios, 0.9)
    consonant_ratio_p90 = _percentile(consonant_ratios, 0.9)
    music_band_ratio_p90 = _percentile(music_band_ratios, 0.9)
    vowel_band_ratio_median = _percentile(vowel_band_ratios, 0.5)
    flatness_median = _percentile(flatness_values, 0.5)
    entropy_median = _percentile(entropy_values, 0.5)
    entropy_p90 = _percentile(entropy_values, 0.9)
    speech_like_frames = sum(
        1
        for zcr, profile in zip(zcr_values[::2], profiles)
        if zcr > 0.13
        or profile["high_ratio"] > 0.38
        or profile["consonant_ratio"] > 0.24
        or profile["music_band_ratio"] > 0.42
        or profile["entropy"] > 0.72
        or profile["centroid"] > 1900
    )
    speech_like_ratio = speech_like_frames / max(len(profiles), 1)

    mfcc_profiles = [_mfcc_profile(frame, audio.sample_rate) for frame in voiced_frames[::2]]
    mfcc_vectors = [profile["coeffs"] for profile in mfcc_profiles]
    mfcc_deltas = [
        _euclidean_distance(previous, current)
        for previous, current in zip(mfcc_vectors, mfcc_vectors[1:])
    ]
    mfcc_delta_mean = sum(mfcc_deltas) / max(len(mfcc_deltas), 1)
    mfcc_delta_p90 = _percentile(mfcc_deltas, 0.9)
    mfcc_std_values = []
    if mfcc_vectors:
        for coeff_index in range(min(10, len(mfcc_vectors[0]))):
            mfcc_std_values.append(_std([vector[coeff_index] for vector in mfcc_vectors]))
    mfcc_std_mean = sum(mfcc_std_values) / max(len(mfcc_std_values), 1)
    mfcc_unstable_ratio = sum(delta > 0.58 for delta in mfcc_deltas) / max(len(mfcc_deltas), 1)
    centroid_jumps = 0
    for previous, current in zip(centroid_values, centroid_values[1:]):
        if abs(current - previous) > 180:
            centroid_jumps += 1
    
    pitch_values = [
        pitch
        for frame in voiced_frames[::2]
        if (pitch := _autocorrelation_pitch(frame, audio.sample_rate)) is not None
    ]
    pitch_coverage = len(pitch_values) / max(len(voiced_frames[::2]), 1)
    pitch_stability = 0.0
    if pitch_values:
        pitch_median = _percentile(pitch_values, 0.5)
        pitch_stability = _std(pitch_values) / max(pitch_median, 1.0)

    onset_count = 0
    for previous, current in zip(rms_values, rms_values[1:]):
        if current > max(previous * 1.45, voice_threshold * 1.25):
            onset_count += 1

    envelope_peak_count = 0
    for previous, current, next_value in zip(rms_values, rms_values[1:], rms_values[2:]):
        local_floor = max(previous, next_value, voice_threshold)
        if current > local_floor * 1.45 and current > voice_threshold * 1.3:
            envelope_peak_count += 1

    gaps = 0
    in_gap = False
    for value in rms_values:
        is_gap = value < voice_threshold
        if is_gap and not in_gap:
            gaps += 1
        in_gap = is_gap

    duration_sec = len(audio.samples) / audio.sample_rate
    voiced_rms_median = _percentile(voiced_rms_values, 0.5)
    voiced_rms_values = [rms_values[index] for index in voiced_indexes]

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
    if gaps > 5:
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
    if (
    centroid_median < 220 and vowel_band_ratio_median < 0.025 and pitch_stability < 0.03):
        reasons.append("The sound is too muffled or humming-like for an Ah vowel.")
    if centroid_jumps > 7 and centroid_cv > 0.35:
        reasons.append("Too many vowel shape changes were detected.")
    # Keep abnormal voice quality: high jitter/tremor/hoarseness/pitch wobble should not fail by itself.
    accepted = not reasons
    return {
        "accepted": accepted,
        "reasons": reasons,
        "duration_sec": round(duration_sec, 2),
        "voiced_ratio": round(voiced_ratio, 3),
        "voiced_duration_sec": round(voiced_duration_sec, 2),
        "onset_count": onset_count,
        "envelope_peak_count": envelope_peak_count,
        "gap_count": gaps,
        "zcr_median": round(zcr_median, 4),
        "zcr_std": round(zcr_std, 4),
        "envelope_modulation": round(envelope_modulation, 3),
        "speech_like_ratio": round(speech_like_ratio, 3),
        "spectral_centroid_median": round(centroid_median, 2),
        "spectral_centroid_cv": round(centroid_cv, 3),
        "high_ratio_p90": round(high_ratio_p90, 3),
        "consonant_ratio_p90": round(consonant_ratio_p90, 3),
        "music_band_ratio_p90": round(music_band_ratio_p90, 3),
        "vowel_band_ratio_median": round(vowel_band_ratio_median, 3),
        "spectral_flatness_median": round(flatness_median, 3),
        "spectral_entropy_median": round(entropy_median, 3),
        "spectral_entropy_p90": round(entropy_p90, 3),
        "mfcc_delta_mean": round(mfcc_delta_mean, 3),
        "mfcc_delta_p90": round(mfcc_delta_p90, 3),
        "mfcc_std_mean": round(mfcc_std_mean, 3),
        "mfcc_unstable_ratio": round(mfcc_unstable_ratio, 3),
        "pitch_coverage": round(pitch_coverage, 3),
        "pitch_stability": round(pitch_stability, 3),
        "centroid_jumps": centroid_jumps,
        "voiced_rms_median": round(voiced_rms_median, 6),
    }

# Analyze voice sample bytes, return dict with acceptance and detailed analysis
def analyze_voice_sample(content: bytes) -> dict:
    audio = read_wav_mono(content)
    snr = analyze_snr(audio)
    ah = validate_sustained_ah(audio)
    min_required_snr = 12
    voiced_rms_median = ah["voiced_rms_median"]
    if voiced_rms_median < 0.03:
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
