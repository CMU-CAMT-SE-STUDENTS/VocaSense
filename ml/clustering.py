from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

from sklearn.preprocessing import StandardScaler

from feature_extractor import extract_feature_dict, get_feature_names


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"
OUTPUT_DIR = ROOT / "outputs" / "clustering"
AUDIO_DIR = AUDIO_DIR = ROOT / "dataset" / "acoustic"
AUDIO_CACHE = OUTPUT_DIR / "unlabeled_audio_features.csv"
VOICE_ICAR_DIR = DATASET_DIR / "voice-icar-federico-ii-database-1.0.0"
VOICE_ICAR_CACHE = OUTPUT_DIR / "voice_icar_features.csv"
VOICE_ICAR_WAV_DIR = OUTPUT_DIR / "voice_icar_wav"
RANDOM_STATE = 42


PARKINSON_SPEECH_FEATURES = [
    "jitter_local",
    "jitter_local_abs",
    "jitter_rap",
    "jitter_ppq5",
    "jitter_ddp",
    "shimmer_local",
    "shimmer_local_db",
    "shimmer_apq3",
    "shimmer_apq5",
    "shimmer_apq11",
    "shimmer_dda",
    "autocorrelation",
    "noise_to_harmonics",
    "harmonics_to_noise",
    "median_pitch_hz",
    "mean_pitch_hz",
    "pitch_std_hz",
    "min_pitch_hz",
    "max_pitch_hz",
    "num_pulses",
    "num_periods",
    "mean_period",
    "period_std",
    "unvoiced_frame_fraction",
    "num_voice_breaks",
    "degree_voice_breaks",
]


REPLICATED_TO_AUDIO = {
    "Jitter_rel": "jitter_local",
    "Shim_loc": "shimmer_local",
    "HNR05": "hnr_db",
    "MFCC0": "mfcc_1_mean",
    "MFCC1": "mfcc_2_mean",
    "MFCC2": "mfcc_3_mean",
    "MFCC3": "mfcc_4_mean",
    "MFCC4": "mfcc_5_mean",
    "MFCC5": "mfcc_6_mean",
    "MFCC6": "mfcc_7_mean",
    "MFCC7": "mfcc_8_mean",
    "MFCC8": "mfcc_9_mean",
    "MFCC9": "mfcc_10_mean",
    "MFCC10": "mfcc_11_mean",
    "MFCC11": "mfcc_12_mean",
    "MFCC12": "mfcc_13_mean",
}


# PD_SPEECH_TO_AUDIO = {
#     "locPctJitter": "jitter_local",
#     "locShimmer": "shimmer_local",
#     "meanHarmToNoiseHarmonicity": "hnr_db",
#     "mean_MFCC_0th_coef": "mfcc_1_mean",
#     "mean_MFCC_1st_coef": "mfcc_2_mean",
#     "mean_MFCC_2nd_coef": "mfcc_3_mean",
#     "mean_MFCC_3rd_coef": "mfcc_4_mean",
#     "mean_MFCC_4th_coef": "mfcc_5_mean",
#     "mean_MFCC_5th_coef": "mfcc_6_mean",
#     "mean_MFCC_6th_coef": "mfcc_7_mean",
#     "mean_MFCC_7th_coef": "mfcc_8_mean",
#     "mean_MFCC_8th_coef": "mfcc_9_mean",
#     "mean_MFCC_9th_coef": "mfcc_10_mean",
#     "mean_MFCC_10th_coef": "mfcc_11_mean",
#     "mean_MFCC_11th_coef": "mfcc_12_mean",
#     "mean_MFCC_12th_coef": "mfcc_13_mean",
# }


@dataclass
class LabeledDataset:
    name: str
    ids: list[str]
    feature_names: list[str]
    x: np.ndarray
    y: np.ndarray
    source: list[str]


@dataclass
class ExperimentResult:
    experiment: str
    feature_set: str
    n_samples: int
    n_features: int
    silhouette: float | None
    ari: float | None
    nmi: float | None
    cluster_purity: float | None
    original_features: int
    pca_features: int
    pca_explained_variance: float

def _safe_float(value: str | float | int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return np.nan
    if np.isfinite(parsed):
        return parsed
    return np.nan


def _read_csv_rows(path: Path, header_row: int = 0) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    header = rows[header_row]
    records = [dict(zip(header, row)) for row in rows[header_row + 1 :] if row]
    return header, records


def _numeric_matrix(records: list[dict[str, str]], feature_names: list[str]) -> np.ndarray:
    matrix = [[_safe_float(record.get(name, "")) for name in feature_names] for record in records]
    return np.asarray(matrix, dtype=float)


def _drop_bad_columns(x: np.ndarray, feature_names: list[str]) -> tuple[np.ndarray, list[str]]:
    finite_ratio = np.mean(np.isfinite(x), axis=0)
    variance = np.nanvar(x, axis=0)
    keep = (finite_ratio >= 0.95) & np.isfinite(variance) & (variance > 0)
    if not np.any(keep):
        raise ValueError("No usable numeric feature columns after filtering.")

    x = x[:, keep]
    names = [name for name, keep_col in zip(feature_names, keep) if keep_col]
    medians = np.nanmedian(x, axis=0)
    row_idx, col_idx = np.where(~np.isfinite(x))
    x[row_idx, col_idx] = medians[col_idx]
    return x, names


def _standardize(x: np.ndarray) -> np.ndarray:
    return StandardScaler().fit_transform(x)


def _kmeans(x_scaled: np.ndarray, n_clusters: int = 2) -> np.ndarray:
    model = KMeans(n_clusters=n_clusters, n_init=50, random_state=RANDOM_STATE)
    return model.fit_predict(x_scaled)


def _cluster_purity(y_true: np.ndarray, clusters: np.ndarray) -> float:
    total = 0
    for cluster_id in np.unique(clusters):
        labels = y_true[clusters == cluster_id]
        if labels.size:
            _, counts = np.unique(labels, return_counts=True)
            total += int(np.max(counts))
    return total / max(1, y_true.size)

def _determine_clusters(y: np.ndarray | None) -> int:
    if y is None:
        return 2

    unique = np.unique(y)
    if len(unique) < 2:
        return 2

    return len(unique)

def _reduce_dimensions(
    x_scaled: np.ndarray,
    max_components: int = 20,
) -> tuple[np.ndarray, dict]:
    if x_scaled.shape[1] <= max_components:
        return x_scaled, {
            "original_features": x_scaled.shape[1],
            "pca_features": x_scaled.shape[1],
            "pca_explained_variance": 1.0,
        }
    pca = PCA(
        n_components=min(
            max_components,
            x_scaled.shape[0] - 1,
            x_scaled.shape[1]
        ),
        random_state=RANDOM_STATE,
    )
    reduced = pca.fit_transform(x_scaled)
    metadata = {
        "original_features": x_scaled.shape[1],
        "pca_features": reduced.shape[1],
        "pca_explained_variance": float(
            pca.explained_variance_ratio_.sum()
        ),
    }
    # print(
    #     f"PCA: {x_scaled.shape[1]} -> "
    #     f"{reduced.shape[1]} features "
    #     f"(explained variance "
    #     f"{pca.explained_variance_ratio_.sum():.3f})"
    # )
    return reduced, metadata

def _evaluate(
    experiment: str,
    feature_set: str,
    x: np.ndarray,
    y: np.ndarray | None,
) -> tuple[ExperimentResult, np.ndarray, np.ndarray]:
    x_scaled = _standardize(x)
    x_cluster, pca_info = _reduce_dimensions(x_scaled)
    n_clusters = _determine_clusters(y)
    clusters = _kmeans(
        x_cluster,
        n_clusters=n_clusters,
    )
    silhouette = None
    if (
        len(np.unique(clusters)) > 1
        and x_cluster.shape[0] > len(np.unique(clusters))
    ):
        silhouette = float(
            silhouette_score(
                x_cluster,
                clusters,
            )
        )
    ari = nmi = purity = None
    if y is not None:
        ari = float(adjusted_rand_score(y, clusters))
        nmi = float(normalized_mutual_info_score(y, clusters))
        purity = float(_cluster_purity(y, clusters))
    return (
        ExperimentResult(
            experiment=experiment,
            feature_set=feature_set,
            n_samples=x.shape[0],
            n_features=x.shape[1],
            original_features=pca_info["original_features"],
            pca_features=pca_info["pca_features"],
            pca_explained_variance=pca_info["pca_explained_variance"],
            silhouette=silhouette,
            ari=ari,
            nmi=nmi,
            cluster_purity=purity,
        ),
        x_scaled,
        clusters,
    )


def _labels_to_plot_text(labels: np.ndarray) -> np.ndarray:
    return np.asarray([str(label) for label in labels], dtype=object)


def _save_projection(
    output_path: Path,
    title: str,
    x_scaled: np.ndarray,
    clusters: np.ndarray,
    labels: np.ndarray | None = None,
    source: list[str] | None = None,
) -> None:
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    points = pca.fit_transform(x_scaled)

    plt.figure(figsize=(10, 7))
    markers = {"labeled": "o", "unlabeled_audio": "X"}
    source = source or ["labeled"] * len(points)
    for src in sorted(set(source)):
        mask = np.asarray(source) == src
        scatter = plt.scatter(
            points[mask, 0],
            points[mask, 1],
            c=clusters[mask],
            cmap="tab10",
            marker=markers.get(src, "o"),
            edgecolor="black" if src == "unlabeled_audio" else "none",
            linewidth=0.7,
            alpha=0.82,
            label=src,
        )

    if labels is not None:
        plot_labels = _labels_to_plot_text(labels)
        for label_value in np.unique(plot_labels):
            mask = plot_labels == label_value
            centroid = np.mean(points[mask], axis=0)
            plt.text(
                centroid[0],
                centroid[1],
                f"class {label_value}",
                fontsize=10,
                weight="bold",
                bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "alpha": 0.75},
            )

    plt.title(title)
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% var)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}% var)")
    plt.legend(handles=scatter.legend_elements()[0], title="cluster", loc="best")
    if len(set(source)) > 1:
        plt.gca().legend(loc="best")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def _write_rows(
    path: Path,
    rows: Iterable[dict[str, object]]
) -> None:
    rows = list(rows)
    if not rows:
        return
    fieldnames = []
    
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def load_parkinson_speech() -> LabeledDataset:
    ids: list[str] = []
    rows: list[list[float]] = []
    labels: list[int] = []
    sources: list[str] = []

    for filename, label_index in [("train_data.txt", 28), ("test_data.txt", 27)]:
        path = DATASET_DIR / "parkinson-speech" / filename
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if not row:
                    continue
                ids.append(row[0])
                rows.append([_safe_float(value) for value in row[1:27]])
                labels.append(int(_safe_float(row[label_index])))
                sources.append(filename)

    x, names = _drop_bad_columns(np.asarray(rows, dtype=float), PARKINSON_SPEECH_FEATURES)
    return LabeledDataset("parkinson_speech_26", ids, names, x, np.asarray(labels), sources)


def load_replicated() -> LabeledDataset:
    _, records = _read_csv_rows(DATASET_DIR / "ReplicatedAcousticFeatures-ParkinsonDatabase.csv")
    excluded = {"ID", "Recording", "Status", "Gender"}
    feature_names = [name for name in records[0] if name not in excluded]
    x, names = _drop_bad_columns(_numeric_matrix(records, feature_names), feature_names)
    ids = [f"{record['ID']}_rec{record['Recording']}" for record in records]
    y = np.asarray([int(_safe_float(record["Status"])) for record in records])
    return LabeledDataset("replicated_acoustic", ids, names, x, y, ["replicated"] * len(ids))


# def load_pd_speech() -> LabeledDataset:
#     _, records = _read_csv_rows(DATASET_DIR / "pd_speech_features.csv", header_row=1)
#     excluded = {"id", "class"}
#     feature_names = [name for name in records[0] if name not in excluded]
#     x, names = _drop_bad_columns(_numeric_matrix(records, feature_names), feature_names)
#     ids = [record["id"] for record in records]
#     y = np.asarray([int(_safe_float(record["class"])) for record in records])
#     return LabeledDataset("pd_speech_features", ids, names, x, y, ["pd_speech"] * len(ids))


def _iter_audio_files() -> list[Path]:
    extensions = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
    print(AUDIO_DIR)
    print(AUDIO_DIR.exists())
    return sorted(path for path in AUDIO_DIR.rglob("*") if path.suffix.lower() in extensions)

# label for self audio

def _build_label_map(root: Path) -> dict[str, str]:
    mapping = {}

    for label_dir in root.iterdir():
        if not label_dir.is_dir():
            continue

        label = label_dir.name

        for file in label_dir.rglob("*"):
            if file.is_file():
                mapping[file.stem.lower()] = label

    return mapping

HEALTH_MAP = _build_label_map(
    ROOT / "dataset" / "health"
)

DEVICE_MAP = _build_label_map(
    ROOT / "dataset" / "device"
)

ACOUSTIC_MAP = _build_label_map(
    ROOT / "dataset" / "acoustic"
)

def _get_acoustic_label(path: Path) -> str:
    return ACOUSTIC_MAP.get(
        path.stem.lower(),
        "unknown",
    )

def _get_health_label(path: Path) -> str:
    return HEALTH_MAP.get(
        path.stem.lower(),
        "unknown",
    )

def _get_device_label(path: Path) -> str:
   return DEVICE_MAP.get(
        path.stem.lower(),
        "unknown",
    )
   
def extract_unlabeled_audio(limit: int | None = None, refresh_cache: bool = False) -> list[dict[str, str]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_names = get_feature_names()
    audio_files = _iter_audio_files()
    print(
    "found audio files:",
    len(audio_files)
    )
    if limit is not None:
        audio_files = audio_files[:limit]

    if AUDIO_CACHE.exists() and not refresh_cache:
        _, records = _read_csv_rows(AUDIO_CACHE)
        cached_paths = {record["path"] for record in records}
        wanted_paths = {str(path.relative_to(ROOT)) for path in audio_files}
        if wanted_paths.issubset(cached_paths):
            return [record for record in records if record["path"] in wanted_paths]

    rows: list[dict[str, str]] = []
    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[audio] extracting {index}/{len(audio_files)} {audio_path.relative_to(ROOT)}")
        features = extract_feature_dict(audio_path)
        acoustic_label = _get_acoustic_label(audio_path)
        health_label = _get_health_label(audio_path)
        device_label = _get_device_label(audio_path)

        row = {
            "id": audio_path.stem,
            "path": str(audio_path.relative_to(ROOT)),
            "acoustic_label": acoustic_label,
            "health_label": health_label,
            "device_label": device_label,
        }
        row.update({name: str(features.get(name, "")) for name in feature_names})
        rows.append(row)

    _write_rows(AUDIO_CACHE, rows)
    return rows

# see device bias problem
def _analyze_device_bias(dataset):

    clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
    )

    clf.fit(
        dataset.x,
        dataset.y,
    )

    importance_df = pd.DataFrame(
        {
            "feature": dataset.feature_names,
            "importance": clf.feature_importances_,
        }
    )

    importance_df = importance_df.sort_values(
        "importance",
        ascending=False,
    )

    print("\nTop device-sensitive features")
    print(importance_df.head(20))

def _feature_rows_to_dataset(
    name: str,
    rows: list[dict[str, str]],
    label_column: str | None = None,
) -> LabeledDataset:
    feature_names = [feature for feature in get_feature_names() if feature in rows[0]]
    x, names = _drop_bad_columns(_numeric_matrix(rows, feature_names), feature_names)
    ids = [row["id"] for row in rows]
    if label_column is None:
        y = np.asarray([row.get("acoustic_label", "unlabeled") for row in rows], dtype=object)
    else:
        y = np.asarray([row[label_column] for row in rows], dtype=object)
    return LabeledDataset(name, ids, names, x, y, [name] * len(ids))


def run_audio_folder_clustering(
    audio_records: list[dict[str, str]],
    results: list[ExperimentResult],
) -> None:
    print(f"audio_records = {len(audio_records)}")
    if len(audio_records) < 3:
        print("[skip] audio_folder_self_clustering: fewer than three audio records")
        return
    
    label_columns = [
    "acoustic_label",
    "health_label",
    "device_label",
    ]

    for label_column in label_columns:

        dataset = _feature_rows_to_dataset(
            f"audio_folder_{label_column}_clustering",
            audio_records,
            label_column=label_column,
        )
        
        if label_column == "device_label":
            print(f"\nAnalyzing device bias for {dataset.name}")
            _analyze_device_bias(dataset)

        feature_sets = build_feature_sets(dataset)

        for feature_set_name, feature_names in feature_sets.items():

            indices = [
                dataset.feature_names.index(f)
                for f in feature_names
            ]

            x_subset = dataset.x[:, indices]

            result, x_scaled, clusters = _evaluate(
                dataset.name,
                feature_set_name,
                x_subset,
                dataset.y,
            )

            results.append(result)
        
    _save_projection(
        OUTPUT_DIR / "audio_folder_self_clustering.png",
        "Unlabeled audio folder clustering",
        x_scaled,
        clusters,
        labels=dataset.y,
        source=["unlabeled_audio"] * len(audio_records),
    )
    _write_rows(
        OUTPUT_DIR / "audio_folder_self_clustering_assignments.csv",
        (
            {
                "id": record["id"],
                "path": record["path"],
                "acoustic_label": record["acoustic_label"],
                "health_label": record["health_label"],
                "device_label": record["device_label"],
                "cluster": int(cluster),
            }
            for record, cluster in zip(audio_records, clusters)
        ),
    )


def _parse_hea(hea_path: Path) -> dict[str, object]:
    lines = hea_path.read_text(encoding="utf-8").splitlines()
    record_parts = lines[0].split()
    signal_parts = lines[1].split()
    gain_baseline = signal_parts[2]
    if "(" in gain_baseline and ")" in gain_baseline:
        gain_text, baseline_text = gain_baseline.split("(", 1)
        baseline_text = baseline_text.split(")", 1)[0]
    else:
        gain_text, baseline_text = gain_baseline, "0"

    diagnosis = ""
    for line in lines:
        if "<diagnoses>:" in line:
            diagnosis = line.split("<diagnoses>:", 1)[1].split("<", 1)[0].strip()
            break

    return {
        "record": record_parts[0],
        "sample_rate": int(float(record_parts[2])),
        "samples": int(float(record_parts[3])),
        "dat_name": signal_parts[0],
        "format": signal_parts[1],
        "gain": float(gain_text),
        "baseline": int(float(baseline_text)),
        "diagnosis": diagnosis,
    }


def _diagnosis_group(diagnosis: str) -> str:
    normalized = diagnosis.strip().lower()
    if normalized == "healthy":
        return "healthy"
    if normalized.startswith("hyperkinetic"):
        return "hyperkinetic"
    if normalized.startswith("hypokinetic"):
        return "hypokinetic"
    if normalized.startswith("reflux"):
        return "reflux"
    return "other"


def _wfdb_dat_to_wav(hea_path: Path, refresh: bool = False) -> tuple[Path, dict[str, object]]:
    meta = _parse_hea(hea_path)
    wav_path = VOICE_ICAR_WAV_DIR / f"{meta['record']}.wav"
    if wav_path.exists() and not refresh:
        return wav_path, meta

    if meta["format"] != "32":
        raise ValueError(f"Unsupported WFDB format {meta['format']} in {hea_path.name}")

    dat_path = hea_path.with_name(str(meta["dat_name"]))
    digital = np.fromfile(dat_path, dtype="<i4", count=int(meta["samples"]))
    if digital.size == 0:
        raise ValueError(f"No samples found in {dat_path}")

    physical = (digital.astype(np.float64) - float(meta["baseline"])) / float(meta["gain"])
    max_abs = float(np.max(np.abs(physical)))
    if max_abs > 0:
        physical = physical / max_abs

    VOICE_ICAR_WAV_DIR.mkdir(parents=True, exist_ok=True)
    wavfile.write(wav_path, int(meta["sample_rate"]), physical.astype(np.float32))
    return wav_path, meta


def extract_voice_icar(
    limit: int | None = None,
    refresh_cache: bool = False,
) -> list[dict[str, str]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_names = get_feature_names()
    hea_files = sorted(VOICE_ICAR_DIR.glob("*.hea"))
    if limit is not None:
        hea_files = hea_files[:limit]

    if VOICE_ICAR_CACHE.exists() and not refresh_cache:
        _, records = _read_csv_rows(VOICE_ICAR_CACHE)
        cached_ids = {record["id"] for record in records}
        wanted_ids = {path.stem for path in hea_files}
        if wanted_ids.issubset(cached_ids):
            return [record for record in records if record["id"] in wanted_ids]

    rows: list[dict[str, str]] = []
    for index, hea_path in enumerate(hea_files, start=1):
        print(f"[voice-icar] converting/extracting {index}/{len(hea_files)} {hea_path.name}")
        wav_path, meta = _wfdb_dat_to_wav(hea_path, refresh=refresh_cache)
        features = extract_feature_dict(wav_path)
        diagnosis = str(meta["diagnosis"])
        row = {
            "id": str(meta["record"]),
            "path": str(hea_path.relative_to(ROOT)),
            "wav_path": str(wav_path.relative_to(ROOT)),
            "diagnosis": diagnosis,
            "diagnosis_group": _diagnosis_group(diagnosis),
            "health_status": "healthy" if diagnosis.strip().lower() == "healthy" else "disordered",
        }
        row.update({name: str(features.get(name, "")) for name in feature_names})
        rows.append(row)

    _write_rows(VOICE_ICAR_CACHE, rows)
    return rows


def run_voice_icar_clustering(
    voice_icar_records: list[dict[str, str]],
    results: list[ExperimentResult],
) -> None:
    if len(voice_icar_records) < 3:
        print("[skip] voice_icar_self_clustering: fewer than three records")
        return

    for label_column in ["health_status"]:
        dataset = _feature_rows_to_dataset(
            f"voice_icar_{label_column}_clustering",
            voice_icar_records,
            label_column=label_column,
        )
        feature_sets = build_feature_sets(dataset)

        for feature_set_name, feature_names in feature_sets.items():

            indices = [
                dataset.feature_names.index(f)
                for f in feature_names
            ]

            x_subset = dataset.x[:, indices]

            result, x_scaled, clusters = _evaluate(
                dataset.name,
                feature_set_name,
                x_subset,
                dataset.y,
            )

            results.append(result)
            
        _save_projection(
            OUTPUT_DIR / f"{dataset.name}.png",
            f"Voice ICAR clustering by {label_column}",
            x_scaled,
            clusters,
            labels=dataset.y,
            source=["voice_icar"] * len(voice_icar_records),
        )
        _write_rows(
            OUTPUT_DIR / f"{dataset.name}_assignments.csv",
            (
                {
                    "id": record["id"],
                    "diagnosis": record["diagnosis"],
                    "diagnosis_group": record["diagnosis_group"],
                    "health_status": record["health_status"],
                    "cluster": int(cluster),
                }
                for record, cluster in zip(voice_icar_records, clusters)
            ),
        )


def run_labeled_experiment(
    dataset: LabeledDataset,
    feature_sets: dict[str, list[str]],
    results: list[ExperimentResult],
) -> None:
    name_to_index = {name: idx for idx, name in enumerate(dataset.feature_names)}
    for feature_set, requested_names in feature_sets.items():
        selected = [name_to_index[name] for name in requested_names if name in name_to_index]
        if len(selected) < 2:
            print(f"[skip] {dataset.name}/{feature_set}: fewer than two usable features")
            continue
        x = dataset.x[:, selected]
        result, x_scaled, clusters = _evaluate(dataset.name, feature_set, x, dataset.y)
        results.append(result)
        _save_projection(
            OUTPUT_DIR / f"{dataset.name}_{feature_set}.png",
            f"{dataset.name}: {feature_set}",
            x_scaled,
            clusters,
            labels=dataset.y,
        )
        _write_rows(
            OUTPUT_DIR / f"{dataset.name}_{feature_set}_assignments.csv",
            (
                {
                    "id": sample_id,
                    "source": source,
                    "true_class": int(label),
                    "cluster": int(cluster),
                }
                for sample_id, source, label, cluster in zip(
                    dataset.ids, dataset.source, dataset.y, clusters
                )
            ),
        )


def run_audio_overlay(
    dataset: LabeledDataset,
    mapping: dict[str, str],
    audio_records: list[dict[str, str]],
    results: list[ExperimentResult],
) -> None:
    labeled_names = [source_name for source_name in mapping if source_name in dataset.feature_names]
    audio_names = [mapping[name] for name in labeled_names]
    if len(labeled_names) < 3 or not audio_records:
        print(f"[skip] {dataset.name}/audio_overlay: insufficient common features or no audio")
        return

    name_to_index = {name: idx for idx, name in enumerate(dataset.feature_names)}
    labeled_x = dataset.x[:, [name_to_index[name] for name in labeled_names]]
    audio_x = np.asarray(
        [[_safe_float(record.get(name, "")) for name in audio_names] for record in audio_records],
        dtype=float,
    )
    combined_x, kept_names = _drop_bad_columns(
        np.vstack([labeled_x, audio_x]),
        [mapping[name] for name in labeled_names],
    )

    result, x_scaled, clusters = _evaluate(
        f"{dataset.name}_plus_unlabeled_audio",
        "audio_compatible_common_features",
        combined_x,
        None,
    )
    results.append(result)

    n_labeled = dataset.x.shape[0]
    labels = np.concatenate([dataset.y, np.full(len(audio_records), -1)])
    source = ["labeled"] * n_labeled + ["unlabeled_audio"] * len(audio_records)
    _save_projection(
        OUTPUT_DIR / f"{dataset.name}_plus_unlabeled_audio.png",
        f"{dataset.name} + unlabeled audio ({len(kept_names)} common features)",
        x_scaled,
        clusters,
        labels=labels,
        source=source,
    )

    assignments = []
    for sample_id, label, cluster in zip(dataset.ids, dataset.y, clusters[:n_labeled]):
        assignments.append(
            {
                "id": sample_id,
                "source": "labeled",
                "true_class": label,
                "cluster": int(cluster),
            }
        )
    for record, cluster in zip(audio_records, clusters[n_labeled:]):
        assignments.append(
            {
                "id": record["id"],
                "source": "unlabeled_audio",
                "acoustic_label": record["acoustic_label"],
                "health_label": record["health_label"],
                "device_label": record["device_label"],
                "cluster": int(cluster),
            }
        )
    _write_rows(OUTPUT_DIR / f"{dataset.name}_plus_unlabeled_audio_assignments.csv", assignments)
    with (OUTPUT_DIR / f"{dataset.name}_plus_unlabeled_audio_features.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump({"features": kept_names}, handle, indent=2)


def build_feature_sets(dataset: LabeledDataset) -> dict[str, list[str]]:
    all_features = dataset.feature_names
    
    without_entropy = [
        f
        for f in all_features
        if f.lower() not in {"sample_entropy", "spectral_entropy"}
    ]
    
    without_mfcc_mean = [
        f
        for f in all_features
        if f.lower() not in {"mfcc_1_mean", "mfcc_2_mean", "mfcc_3_mean", "mfcc_4_mean", "mfcc_5_mean", "mfcc_6_mean", "mfcc_7_mean", "mfcc_8_mean", "mfcc_9_mean", "mfcc_10_mean", "mfcc_11_mean", "mfcc_12_mean", "mfcc_13_mean"}
    ]
    
    without_cepstral = [
        f
        for f in all_features
        if "mfcc" not in f.lower()
    ]
    
    without_top_device_features = [
        f
        for f in all_features
        if f.lower() not in {"mfcc_6_mean", "mfcc_7_mean", "mfcc_4_mean", "mfcc_7_std","mfcc_5_std","mfcc_2_mean"," mfcc_3_mean","mfcc_10_std","mfcc_13_std","spectral_centroid_std_hz"}
    ]
    
    voice_quality_features = [
        f
        for f in all_features
        if any(
            keyword in f.lower()
            for keyword in [
                "hnr",
                "cpps",
                "entropy",
                "jitter",
                "shimmer",
                "f0",
            ]
        )
    ]
    
    cepstral_features = [
        f
        for f in all_features
        if "mfcc" in f.lower()
    ]

    noise_features = [
        f
        for f in all_features
        if any(
            keyword in f.lower()
            for keyword in [
                "hnr",
                "noise",
                "harmonic",
            ]
        )
    ]

    nonlinear_features = [
        f
        for f in all_features
            if f.lower() in {"sample_entropy", "spectral_entropy"}
    ]

    sets = {
        "all_features": all_features,
        # "without_entropy": without_entropy,
        "without_cepstral": without_cepstral,
        "without_mfcc_mean": without_mfcc_mean,
        "without_top_device_features": without_top_device_features,
        "voice_quality_only": voice_quality_features,
    }
    
        
    if cepstral_features and noise_features:
        sets["cepstral_noise"] = (
            cepstral_features
            + noise_features
        )

    if (
        cepstral_features
        and noise_features
        and nonlinear_features
    ):
        sets["cepstral_noise_nonlinear"] = (
            cepstral_features
            + noise_features
            + nonlinear_features
        )

    # -------------------------
    # Clinical feature groups
    # -------------------------

    feature_map = {
        "perturbation": [
            "jitter",
            "jitter_local",
            "shimmer",
            "shimmer_local",
        ],

        "noise": [
            "hnr",
            "hnr_db",
            "noise_to_harmonics",
            "harmonics_to_noise",
        ],

        "pitch": [
            "f0",
            "mean_pitch_hz",
            "pitch_std_hz",
        ],

        "nonlinear": [
            "sample_entropy",
            "spectral_entropy",
        ],
    }

    
    for group_name, candidates in feature_map.items():

        matched = [
            feature
            for feature in all_features
            if any(
                candidate.lower() in feature.lower()
                for candidate in candidates
            )
        ]

        if len(matched) >= 2:
            sets[f"{group_name}_only"] = matched


    mfcc_features = [
        feature
        for feature in all_features
        if "mfcc" in feature.lower()
    ]

    if len(mfcc_features) >= 2:
        sets["cepstral_only"] = mfcc_features

    return sets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Parkinson speech clustering and RPDE/PPE impact experiments."
    )
    parser.add_argument("--skip-audio", action="store_true", help="Skip unlabeled audio extraction.")
    parser.add_argument("--skip-voice-icar", action="store_true", help="Skip voice ICAR dat/hea extraction.")
    parser.add_argument("--refresh-audio-cache", action="store_true", help="Re-extract all audio features.")
    parser.add_argument("--refresh-voice-icar-cache", action="store_true", help="Re-convert and re-extract voice ICAR features.")
    parser.add_argument("--audio-limit", type=int, default=None, help="Limit unlabeled audio files for quick tests.")
    parser.add_argument("--voice-icar-limit", type=int, default=None, help="Limit voice ICAR records for quick tests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[ExperimentResult] = []
    datasets = [load_parkinson_speech(), load_replicated()
                #, load_pd_speech()
                ]

    for dataset in datasets:
        run_labeled_experiment(dataset, build_feature_sets(dataset), results)

    if not args.skip_audio:
        audio_records = extract_unlabeled_audio(
            limit=args.audio_limit,
            refresh_cache=args.refresh_audio_cache,
        )
        run_audio_folder_clustering(audio_records, results)
        run_audio_overlay(load_replicated(), REPLICATED_TO_AUDIO, audio_records, results)
        # run_audio_overlay(load_pd_speech(), PD_SPEECH_TO_AUDIO, audio_records, results)

    if not args.skip_voice_icar:
        voice_icar_records = extract_voice_icar(
            limit=args.voice_icar_limit,
            refresh_cache=args.refresh_voice_icar_cache,
        )
        run_voice_icar_clustering(voice_icar_records, results)

    _write_rows(
        OUTPUT_DIR / "metrics_summary.csv",
        (
            {
                "experiment": result.experiment,
                "feature_set": result.feature_set,
                "n_samples": result.n_samples,
                "n_features": result.n_features,
                "original_features": result.original_features,
                "pca_features": result.pca_features,
                "pca_explained_variance": f"{result.pca_explained_variance:.6f}",
                "silhouette": "" if result.silhouette is None else f"{result.silhouette:.6f}",
                "ari": "" if result.ari is None else f"{result.ari:.6f}",
                "nmi": "" if result.nmi is None else f"{result.nmi:.6f}",
                "cluster_purity": ""
                if result.cluster_purity is None
                else f"{result.cluster_purity:.6f}",
            }
            for result in results
        ),
    )
    print(f"Saved clustering outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
