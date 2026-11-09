import time
import os
import psutil
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, OPTICS
try:
    from sklearn.cluster import HDBSCAN
    has_hdb = True
except ImportError:
    has_hdb = False

parquet_path = "data/chicago_benchmark/silver/chicago_crimes_curated.parquet"
df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude", "Year"])
df_d1 = df[df["District"] == 1].dropna(subset=["Latitude", "Longitude"]).copy()
n_d1 = len(df_d1)
print(f"District 1 (The Loop): {n_d1:,} total events (2020-2025)", flush=True)

# Let's test if HDBSCAN and OPTICS can run on 30,000 points of District 1 (e.g. 2023-2025)
df_d1_recent = df_d1[df_d1["Year"] >= 2023].copy()
n_recent = len(df_d1_recent)
print(f"District 1 (The Loop, 2023-2025): {n_recent:,} events", flush=True)

r_earth = 6371008.8
eps_rad = 300.0 / r_earth

coords_rad = np.radians(df_d1_recent[["Latitude", "Longitude"]].to_numpy())

# DBSCAN
t0 = time.perf_counter()
db = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
l_db = db.fit_predict(coords_rad)
t_db = time.perf_counter() - t0
print(f"DBSCAN: {t_db:.2f} s | Clusters: {len(set(l_db)-{-1})} | Noise: {(l_db==-1).sum()} ({(l_db==-1).mean()*100:.2f}%)", flush=True)

# HDBSCAN on 27k points
if has_hdb:
    t0 = time.perf_counter()
    hdb = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine", copy=True)
    l_hdb = hdb.fit_predict(coords_rad)
    t_hdb = time.perf_counter() - t0
    print(f"HDBSCAN: {t_hdb:.2f} s | Clusters: {len(set(l_hdb)-{-1})} | Noise: {(l_hdb==-1).sum()} ({(l_hdb==-1).mean()*100:.2f}%)", flush=True)

