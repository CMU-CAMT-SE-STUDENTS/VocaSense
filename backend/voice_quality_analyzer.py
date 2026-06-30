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
                "good": 0.0032,
                "moderate": 0.0083,
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
                "good": 0.0032,
                "moderate": 0.008,
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
                "good": 5.0,
                "moderate": 10.21,
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
    # print("----------Hoarseness----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]
        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )
        
        # print(
        #     feature_name,
        #     value,
        #     feature_score
        # )

        score += feature_score * cfg["weight"]

    return round(score * 100, 2)

def calculate_stability(features, config):
    score = 0
    # print("----------Stability----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]
        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )

        score += feature_score * cfg["weight"]
        
        # print(
        #     feature_name,
        #     value,
        #     feature_score
        # )

    return round(score * 100, 2)

def calculate_clarity(features, config):

    score = 0
    # print("----------Clarity----------")
    for feature_name, cfg in config["features"].items():
        value = features[feature_name]

        feature_score = normalize_feature(
            features[feature_name],
            cfg["good"],
            cfg["moderate"],
            cfg["reverse"]
        )

        score += feature_score * cfg["weight"]
        
        # print(
        #     feature_name,
        #     value,
        #     feature_score
        # )

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
    
     # overall condition
    if voice_quality >= 70:
      overall_condition = "healthy"
    elif voice_quality < 70 and voice_quality >= 50:
      overall_condition = "moderate"
    else:
      overall_condition = "warning"
      
    # hoarseness condition
    if hoarseness_risk < 50:
      hoarseness_condition = "low"
    elif hoarseness_risk < 70 and hoarseness_risk >= 50:
      hoarseness_condition = "moderate"
    else:
      hoarseness_condition = "high"
      
    # stability condition
    if stability >=70:
      stability_condition = "stable"
    elif stability < 70 and stability >= 50:
      stability_condition = "slightly_unstable"
    else:
      stability_condition = "unstable"
      
    # clarity condition
    if clarity >=70:
      clarity_condition = "clear"
    elif clarity < 70 and clarity >= 50:
      clarity_condition = "slightly_unclear"
    else:
      clarity_condition = "unclear"
      
    return {
        "voice_quality": {
          "voice_quality_score": round(voice_quality, 2),
          "voice_condition": overall_condition
        },
        "hoarseness_risk":{
          "hoarseness_risk_score": round(hoarseness_risk, 2),
          "hoarseness_condition": hoarseness_condition,
        },
        "stability": {
          "stability_score": round(stability, 2),
          "stability_condition": stability_condition,
        },
        "clarity": {
          "clarity_score": round(clarity, 2),
          "clarity_condition": clarity_condition,
        }
    }
    