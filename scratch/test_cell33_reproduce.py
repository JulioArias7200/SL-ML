import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS

RT = 6371.0088
df = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')
p = df.dropna(subset=["lat", "lon"]).copy()

X = np.radians(p[["lat", "lon"]].to_numpy())
hdb = HDBSCAN(min_cluster_size=2, metric="haversine", copy=True)
labels_hdb_live = hdb.fit_predict(X)

print("Live HDBSCAN labels with min_cluster_size=2 on X:")
print(pd.Series(labels_hdb_live).value_counts().to_dict())

print("\nRow 48 in live HDBSCAN:")
print("Live label:", labels_hdb_live[48])
print("CSV label: ", df.loc[48, 'hdbscan'])

print("\nCochabamba live labels (row 2, 10, etc):")
print(labels_hdb_live[[2, 10, 13, 15, 17, 34, 48, 51, 52, 57]])

# What if HDBSCAN was run on something else?
# Let's check if HDBSCAN was run on euclidean coordinates, or if it was run on TF-IDF, or if it was run on standardized features!
from sklearn.cluster import HDBSCAN
hdb_euc = HDBSCAN(min_cluster_size=2).fit_predict(p[["lat", "lon"]].to_numpy())
print("\nEuclidean HDBSCAN on lat/lon:", hdb_euc[48], "vs Cochabamba:", hdb_euc[2])

# What if it was run on ppca_x, ppca_y or embeddings or NLP?
if 'ppca_x' in df.columns:
    print("ppca_x exists")

