import pandas as pd
import numpy as np
from sklearn.cluster import HDBSCAN

df = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')
X = np.radians(df[["lat", "lon"]].to_numpy())

# With min_cluster_size=2, min_samples=2 (the default in Cell 33 of notebook)
hdb2 = HDBSCAN(min_cluster_size=2, metric="haversine", copy=True)
labels2 = hdb2.fit_predict(X)
print("--- With min_cluster_size=2 ---")
print("Row 48 label:", labels2[48])
print("Cochabamba labels:", labels2[2])
print("Are they in the same cluster?:", labels2[48] == labels2[2])

# Now with min_cluster_size=5 (or min_samples=5)
hdb5 = HDBSCAN(min_cluster_size=5, metric="haversine", copy=True)
labels5 = hdb5.fit_predict(X)
print("\n--- With min_cluster_size=5 ---")
print("Row 48 label:", labels5[48])
print("Cochabamba labels:", labels5[2])
print("Is Row 48 noise with min_cluster_size=5?:", labels5[48] == -1)

# Now what if min_samples=2 but min_cluster_size=3?
hdb3 = HDBSCAN(min_cluster_size=3, min_samples=2, metric="haversine", copy=True)
labels3 = hdb3.fit_predict(X)
print("\n--- With min_cluster_size=3, min_samples=2 ---")
print("Row 48 label:", labels3[48])
print("Cochabamba labels:", labels3[2])
print("Is Row 48 noise?:", labels3[48] == -1)

