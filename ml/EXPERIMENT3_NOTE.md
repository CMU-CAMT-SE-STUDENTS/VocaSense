experiment round 3

from last experiment, i found that feature set kinda bias to device. 
features that have the most difference between 2 devices are:
- mfcc_2_mean
- mfcc_3_mean
- mfcc_4_mean
- mfcc_6_mean
- mfcc_7_mean
- alpha_ratio_db
- spectral_centroid_mean_hz
- many MFCC std
even perform normalization(StandardScaler)

so now, i'll drop normalization and scaler

Analyzing device bias for audio_folder_device_label_clustering
Top device-sensitive features
                      feature  importance
22                mfcc_6_mean    0.157292
23                mfcc_7_mean    0.102026
20                mfcc_4_mean    0.098831
36                 mfcc_7_std    0.083051
34                 mfcc_5_std    0.071977
18                mfcc_2_mean    0.057917
19                mfcc_3_mean    0.054819
39                mfcc_10_std    0.049943
42                mfcc_13_std    0.047391
16   spectral_centroid_std_hz    0.042959
15  spectral_centroid_mean_hz    0.024859
37                 mfcc_8_std    0.024151
30                 mfcc_1_std    0.022772
25                mfcc_9_mean    0.016599
13          spectral_flux_std    0.016545
11             alpha_ratio_db    0.015750
41                mfcc_12_std    0.012912
33                 mfcc_4_std    0.008707
38                 mfcc_9_std    0.008419
27               mfcc_11_mean    0.007431

finding
1 cepstral features(MFCC) are highly sensitive to recording devices and can perfectly separate Maono and Logitech recordings

2 removing mfcc mean improved health label clustering performance (ARI 0.240->0.275)

3 voice quality features (jitter, shimmer, HNR, CPPS, entropy, F0)

4 device bias exists primary on cepstral features, but clustering on the complete feature set is not dominated by device labels