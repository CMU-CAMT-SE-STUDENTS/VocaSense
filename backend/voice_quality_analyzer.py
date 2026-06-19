from feature_extractor import get_feature_names
from typing import Dict

VOICE_QUALITY_CONFIG = {
    "hoarseness": {
        "features": {

            "hnr_db": {
                "weight": 0.35,
                "good": 24.02,
                "moderate": 16.01,
                "reverse": False,
            },
            "jitter_local": {
                "weight": 0.25,
                "good": 0.032,
                "moderate": 0.083,
                "reverse": True,
            },
            "shimmer_local": {
                "weight": 0.20,
                "good": 0.02,
                "moderate": 0.07,
                "reverse": True,
            },
            "cpps_db": {
                "weight": 0.20,
                "good": 10.20,
                "moderate": 6.35,
                "reverse": False,
            }
        }
    },
    
    "stability": {
        "features": {
            "f0_std_hz": {
                "weight": 0.26,
                "good": 2.10,
                "moderate": 10.44,
                "reverse": True,
            },
            "jitter_local": {
                "weight": 0.34,
                "good": 0.0037,
                "moderate": 0.007,
                "reverse": True,
            },
            "spectral_entropy": {
                "weight": 0.40,
                "good": 5.0,
                "moderate": 10.21,
                "reverse": True,
            },
        }
    },
    "clarity": {
        "features": {
            "cpps_db": {
                "weight": 0.45,
                "good": 10.20,
                "moderate": 7.35,
                "reverse": False,
            },
            "hnr_db": {
                "weight": 0.35,
                "good": 17.02,
                "moderate": 10.00,
                "reverse": False,
            },
            "spectral_entropy": {
                "weight": 0.20,
                "good": 4.0,
                "moderate": 7.8,
                "reverse": True,
            },
        }
    }
}

FEATURE_NAMES = (
    get_feature_names
)

def normalize_feature(
    value: float,
    good: float,
    moderate: float,
    reverse: bool = False
) -> float:

    if reverse:
        score = (moderate - value) / (moderate - good)
    else:
        score = (value - moderate) / (good - moderate)

    return max(0.0, min(1.0, score))

def calculate_hoarseness(features, config):

    score = 0
    print("----------Hoarseness----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]
        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )
        
        print(
            feature_name,
            value,
            feature_score
        )

        score += feature_score * cfg["weight"]

    return round(score * 100, 2)

def calculate_stability(features, config):
    score = 0
    print("----------Stability----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]
        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )

        score += feature_score * cfg["weight"]
        
        print(
            feature_name,
            value,
            feature_score
        )

    return round(score * 100, 2)

def calculate_clarity(features, config):

    score = 0
    print("----------Clarity----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]

        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )

        score += feature_score * cfg["weight"]
        
        print(
            feature_name,
            value,
            feature_score
        )

    return round(score * 100, 2)

def calculate_voice_quality(
    hoarseness_score,
    stability_score,
    clarity_score
):

    voice_quality = (
        0.40 * clarity_score +
        0.30 * stability_score +
        0.30 * hoarseness_score
    )

    return round(voice_quality, 2)

def analyze_voice_quality(features: Dict[str, float]) -> Dict:
    
    config = VOICE_QUALITY_CONFIG
    hoarseness = calculate_hoarseness(
        features,
        config["hoarseness"]
    )

    stability = calculate_stability(
        features,
        config["stability"]
    )

    clarity = calculate_clarity(
        features,
        config["clarity"]
    )
    
    hoarseness_risk = 100-hoarseness
    
    voice_quality = calculate_voice_quality(hoarseness, stability, clarity)
    return {
        "voice_quality": round(voice_quality, 2),
        "hoarseness_risk": round(hoarseness_risk, 2),
        "stability": round(stability, 2),
        "clarity": round(clarity, 2),
    }
    