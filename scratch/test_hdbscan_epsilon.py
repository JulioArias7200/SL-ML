import pandas as pd
import numpy as np
from sklearn.cluster import HDBSCAN

df = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')
X = np.radians(df[["lat", "lon"]].to_numpy())
r_earth = 6371008.8

# Test cluster_selection_epsilon = 1500m (or 2500m)
eps_rad = 2500.0 / r_earth
hdb_constrained = HDBSCAN(min_cluster_size=2, cluster_selection_epsilon=eps_rad, metric="haversine", copy=True)
labels_c = hdb_constrained.fit_predict(X)

print("HDBSCAN with cluster_selection_epsilon = 2.5 km:")
print("Row 48 (Oruro) label:", labels_c[48])
print("Cochabamba label:", labels_c[2])
print("Is Oruro noise now?:", labels_c[48] == -1)

# Check all labels
print("Label counts with cluster_selection_epsilon=2.5km:")
print(pd.Series(labels_c).value_counts().to_dict())

