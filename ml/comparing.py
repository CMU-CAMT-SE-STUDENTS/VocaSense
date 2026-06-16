from typing import Counter

import pandas as pd
import numpy as np
from itertools import combinations
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics.pairwise import cosine_similarity

# =====================
# Load Data
# =====================
df = pd.read_csv("./outputs/comparing/unlabeled_audio_features.csv")

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# mean feature
centroids = (
    df.groupby("acoustic_label")[numeric_cols]
      .mean()
)

#normalizer
scaler = StandardScaler()
centroids_scaled = pd.DataFrame(
    scaler.fit_transform(centroids),
    index=centroids.index,
    columns=centroids.columns
)

distance_matrix = pd.DataFrame(
    squareform(
        pdist(centroids_scaled, metric="euclidean")
    ),
    index=centroids.index,
    columns=centroids.index
)

# Similarity Matrix
similarity = pd.DataFrame(
    cosine_similarity(centroids_scaled),
    index=centroids.index,
    columns=centroids.index
)

# Hierarchical Clustering
Z = linkage(
    centroids_scaled,
    method="ward"
)

plt.figure(figsize=(8,5))

dendrogram(
    Z,
    labels=centroids_scaled.index.tolist()
)

plt.title(
    "Acoustic Label Similarity"
)

plt.ylabel("Distance")
plt.savefig(
    "../ml/outputs/comparing/acoustic_label_dendrogram.png"
)

# Cohen's d
def cohens_d(group1, group2):
    n1 = len(group1)
    n2 = len(group2)

    if n1 < 2 or n2 < 2:
        return np.nan

    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)

    pooled_std = np.sqrt(
        ((n1 - 1) * var1 + (n2 - 1) * var2)
        / (n1 + n2 - 2)
    )

    if pooled_std == 0:
        return 0

    return (np.mean(group1) - np.mean(group2)) / pooled_std

# Pairwise Comparison
results = []

labels = sorted(df["acoustic_label"].dropna().unique())

for label_a, label_b in combinations(labels, 2):

    df_a = df[df["acoustic_label"] == label_a]
    df_b = df[df["acoustic_label"] == label_b]

    for feature in numeric_cols:

        mean_a = df_a[feature].mean()
        mean_b = df_b[feature].mean()

        std_a = df_a[feature].std()
        std_b = df_b[feature].std()

        diff = mean_a - mean_b
        abs_diff = abs(diff)

        d = cohens_d(
            df_a[feature].dropna(),
            df_b[feature].dropna()
        )

        results.append({
            "label_a": label_a,
            "label_b": label_b,
            "feature": feature,

            "mean_a": mean_a,
            "mean_b": mean_b,

            "std_a": std_a,
            "std_b": std_b,

            "difference": diff,
            "abs_difference": abs_diff,

            "cohens_d": d,
            "abs_cohens_d": abs(d) if pd.notna(d) else np.nan
        })

pairwise_df = pd.DataFrame(results)

pair_feature_results = []

counter = Counter()

for label_a, label_b in combinations(centroids_scaled.index, 2):

    diff = (
        centroids_scaled.loc[label_a]
        - centroids_scaled.loc[label_b]
    ).abs()
    print(f"\n{'='*50}") 
    print(f"{label_a} vs {label_b}")
    
    print("\nMost Similar Features") 
    print( diff.sort_values() .head(5) ) 
    print("\nMost Different Features") 
    print( diff.sort_values( ascending=False ).head(5) )
    
    top_diff = diff.sort_values(
        ascending=False
    ).head(5)

    counter.update(top_diff.index)
    
    print(
    pd.DataFrame(
        counter.items(),
        columns=["feature","count"]
    )
    .sort_values(
        "count",
        ascending=False
    )
)
    
    abs_diff = diff.abs()

    pair_df = pd.DataFrame({
        "feature": diff.index,
        "difference": diff.values,
        "abs_difference": abs_diff.values
    })

    pair_df = pair_df.sort_values(
        "abs_difference",
        ascending=True
    )

    # feature ที่คล้ายกันที่สุด
    most_similar = pair_df.head(10).copy()
    most_similar["relation"] = "similar"

    # feature ที่ต่างกันที่สุด
    most_different = pair_df.sort_values(
        "abs_difference",
        ascending=False
    ).head(10).copy()

    most_different["relation"] = "different"

    result = pd.concat([
        most_similar,
        most_different
    ])

    result["label_a"] = label_a
    result["label_b"] = label_b

    pair_feature_results.append(result)

pair_feature_results = pd.concat(
    pair_feature_results,
    ignore_index=True
)

pair_feature_results.to_csv(
    "../ml/outputs/comparing/pair_feature_contribution.csv",
    index=False
)

print(pair_feature_results.head())

# Top Features per Pair
top_features = (
    pairwise_df
    .sort_values(
        ["label_a", "label_b", "abs_cohens_d"],
        ascending=[True, True, False]
    )
    .groupby(["label_a", "label_b"])
    .head(10)
)

pairwise_df.to_csv(
    "../ml/outputs/comparing/pairwise_feature_comparison.csv",
    index=False
)

top_features.to_csv(
    "../ml/outputs/comparing/top10_features_per_pair.csv",
    index=False
)
target_pair = pairwise_df[
    ((pairwise_df["label_a"] == "cold") &
     (pairwise_df["label_b"] == "normal"))
]

target_pair.sort_values(
    "abs_cohens_d",
    ascending=False
).head(5)

print(top_features[
    [
        "label_a",
        "label_b",
        "feature",
        "mean_a",
        "mean_b",
        "cohens_d"
    ]
].head(5))


# print distance and similarity matrices
print("Distance Matrix:")
print(distance_matrix)

distance_matrix.to_csv(
    "../ml/outputs/comparing/acoustic_label_distance.csv"
)

print("Similarity Matrix:")
print(similarity)

similarity.to_csv(
    "../ml/outputs/comparing/acoustic_label_similarity.csv"
)


# Importance features
important_features = [
    "mfcc_5_mean",
    "mfcc_9_mean",
    "mfcc_4_std",
    "mfcc_13_mean",
    "spectral_flux_std",
    "mfcc_2_std",
    "f0_std_hz",
    "mfcc_8_mean",
    "mfcc_11_std",
    "mfcc_10_std",
]

summary = (
    df.groupby("acoustic_label")[important_features]
      .agg(["mean","std"])
)

summary.to_csv(
    "../ml/outputs/comparing/summary.csv",
    index=False
)

print(summary)