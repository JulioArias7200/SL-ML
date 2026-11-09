import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

parquet_path = "data/chicago_benchmark/silver/chicago_crimes_curated.parquet"
df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude"])
df = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()

r_earth = 6371008.8
eps_rad = 300.0 / r_earth

# Compare noise across different complete districts
for dist_id in [1, 11, 16, 7]:
    sub = df[df["District"] == dist_id].copy()
    coords = np.radians(sub[["Latitude", "Longitude"]].to_numpy())
    db = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
    labels = db.fit_predict(coords)
    noise = (labels == -1).sum()
    pct = (labels == -1).mean() * 100
    print(f"District {dist_id:>2} ({len(sub):>6,} events): Noise = {noise:>5,} ({pct:5.2f}%), Clusters = {len(set(labels)-{-1})}")

