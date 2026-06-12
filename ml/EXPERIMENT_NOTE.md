In this experiment
- Change PCA value
    Result: change pca to 41 from 30, the matric barely change. but reducing to 20 is still work 
- Add RPDE and PPE to feature_extractor.py
    Result: cannot extract both because pyrem crash. Decided to change to sample entropy and spectral entropy
- Add sample entropy and spectral entropy to feature_extractor.py
    Result: effect on self audio. It also help clustering healthy, unhealthy, pretended. rather than 5 classes(cold, hoarsed, wind, normal, fatigue). thet only work on health classification
- Change self audio label to healthy, unhealthy, pretended
    Result: ari score went up (0.103->0.240), NMI down (0.397->0.308), purity up (0.561->0.659).
        I think we in the right way for using 3 classes for this dataset.
- Use 3 types of label: acoustic(cold, hoarsed, wind, normal, fatigue), health(healthy, unhealthy, pretended), and device(logitech, maono)
    Result: 
        - Acoustic: cannot separate acoustic state clearly. this related to many papers that jitter and shimmer are sensitived to vocal instability more than MFCC
        - Health: the best set for now. entropy significantly useful in this clustering. this result can said that sample entropy and spectral entropy help separating health status.
        - Device: the score are 1 in many feature set. this result shows that this feature set captures mic characteristics more strongly than vocal health characteristic

About pd_speech: remove from primary clustering experiment
    Reason: Most results show that this dataset get ARI near or < 0

Summary:
    replicated_acoustic suit with current the most
    remove pd_speech
    entropy worked on health classification only
    current feature group got ari = 1 and nmi = 1 for device label
    pertubation is the main feature group
    the main problem is feature bias to device quality

What should be done next round:
- try another feature combinations to solve the feature bias
- or do some normalization