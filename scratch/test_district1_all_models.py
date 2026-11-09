import time
import os
import psutil
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, OPTICS
from sklearn.metrics import silhouette_score, adjusted_rand_score
try:
    from sklearn.cluster import HDBSCAN
    has_hdb = True
except ImportError:
    has_hdb = False

parquet_path = "data/chicago_benchmark/silver/chicago_crimes_curated.parquet"
df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude", "Year", "Primary Type"])
df = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()

# Complete geographic subset: District 1 (The Loop) - 2024 to 2025 (recent complete period)
df_sub = df[(df["District"] == 1) & (df["Year"] >= 2024)].copy()
n_pts = len(df_sub)
print(f"Option B: District 1 (The Loop) 2024-2025: {n_pts:,} events (100% complete in sector)", flush=True)

r_earth = 6371008.8
eps_rad = 300.0 / r_earth

coords_rad = np.radians(df_sub[["Latitude", "Longitude"]].to_numpy())

# 1. DBSCAN (eps=300m, MinPts=25)
t0 = time.perf_counter()
db = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
l_db = db.fit_predict(coords_rad)
t_db = time.perf_counter() - t0
clusters_db = len(set(l_db) - {-1})
noise_db = (l_db == -1).sum()
pct_db = (l_db == -1).mean() * 100
print(f"DBSCAN: {t_db*1000:.1f} ms ({t_db:.2f} s) | Clusters: {clusters_db} | Noise: {noise_db} ({pct_db:.2f}%)", flush=True)

# 2. HDBSCAN (min_cluster_size=25, min_samples=15)
if has_hdb:
    t0 = time.perf_counter()
    hdb = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine", copy=True)
    l_hdb = hdb.fit_predict(coords_rad)
    t_hdb = time.perf_counter() - t0
    clusters_hdb = len(set(l_hdb) - {-1})
    noise_hdb = (l_hdb == -1).sum()
    pct_hdb = (l_hdb == -1).mean() * 100
    print(f"HDBSCAN: {t_hdb*1000:.1f} ms ({t_hdb:.2f} s) | Clusters: {clusters_hdb} | Noise: {noise_hdb} ({pct_hdb:.2f}%)", flush=True)

# 3. OPTICS (xi=0.05, min_samples=25)
t0 = time.perf_counter()
opt = OPTICS(min_samples=25, xi=0.05, metric="haversine", algorithm="ball_tree")
l_opt = opt.fit_predict(coords_rad)
t_opt = time.perf_counter() - t0
clusters_opt = len(set(l_opt) - {-1})
noise_opt = (l_opt == -1).sum()
pct_opt = (l_opt == -1).mean() * 100
print(f"OPTICS: {t_opt*1000:.1f} ms ({t_opt:.2f} s) | Clusters: {clusters_opt} | Noise: {noise_opt} ({pct_opt:.2f}%)", flush=True)

