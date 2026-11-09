import time
import os
import psutil
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
try:
    from sklearn.cluster import HDBSCAN
    has_hdb = True
except ImportError:
    has_hdb = False

def get_mem_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

print(f"Initial Memory: {get_mem_mb():.1f} MB")

parquet_path = "data/chicago_benchmark/silver/chicago_crimes_curated.parquet"
df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude"])
df = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()
total_n = len(df)
print(f"Total valid events in Parquet: {total_n:,}")
print(f"Memory after loading: {get_mem_mb():.1f} MB")

r_earth = 6371008.8
eps_rad = 300.0 / r_earth

# -------------------------------------------------------------
# TEST OPTION A: Full dataset DBSCAN (1,199,160 points)
# -------------------------------------------------------------
print("\n--- Testing Option A: DBSCAN on FULL dataset (1,199,160 points) ---")
coords_rad_full = np.radians(df[["Latitude", "Longitude"]].to_numpy())
t0 = time.perf_counter()
mem_start = get_mem_mb()
try:
    db_full = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree", leaf_size=50)
    labels_full = db_full.fit_predict(coords_rad_full)
    t_full = time.perf_counter() - t0
    mem_peak = get_mem_mb()
    
    clusters_full = len(set(labels_full) - {-1})
    noise_count_full = int((labels_full == -1).sum())
    noise_pct_full = round((noise_count_full / total_n) * 100.0, 2)
    print(f"SUCCESS Option A:")
    print(f"  Time: {t_full:.2f} s ({t_full*1000:.1f} ms)")
    print(f"  Memory delta: {mem_peak - mem_start:.1f} MB (Peak: {mem_peak:.1f} MB)")
    print(f"  Active clusters: {clusters_full}")
    print(f"  Noise count: {noise_count_full:,} ({noise_pct_full}%)")
    print(f"  Coverage: {100.0 - noise_pct_full:.2f}%")
except Exception as e:
    print(f"FAILED Option A: {e}")

# -------------------------------------------------------------
# TEST OPTION B: Full spatial contiguous subset (e.g. Districts 1, 18, 12: Downtown / Near North / Near West)
# -------------------------------------------------------------
print("\n--- Testing Option B: DBSCAN & HDBSCAN on Complete Contiguous Districts ---")
# District 1: Central (The Loop), District 18: Near North, District 12: Near West
sel_districts = [1, 18, 12]
df_subset = df[df["District"].isin(sel_districts)].copy()
n_subset = len(df_subset)
print(f"Subset districts {sel_districts}: {n_subset:,} points (100% of their events, preserving physical density)")
coords_rad_sub = np.radians(df_subset[["Latitude", "Longitude"]].to_numpy())

t0 = time.perf_counter()
db_sub = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
labels_db_sub = db_sub.fit_predict(coords_rad_sub)
t_db_sub = time.perf_counter() - t0
clusters_db_sub = len(set(labels_db_sub) - {-1})
noise_db_sub = (labels_db_sub == -1).sum()
noise_pct_db_sub = round((noise_db_sub / n_subset) * 100.0, 2)
print(f"DBSCAN on Districts {sel_districts}:")
print(f"  Time: {t_db_sub:.2f} s, Clusters: {clusters_db_sub}, Noise: {noise_db_sub:,} ({noise_pct_db_sub}%)")

# Also test single district: District 1 (The Loop, 54k events)
df_d1 = df[df["District"] == 1].copy()
n_d1 = len(df_d1)
coords_rad_d1 = np.radians(df_d1[["Latitude", "Longitude"]].to_numpy())
t0 = time.perf_counter()
db_d1 = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
labels_db_d1 = db_d1.fit_predict(coords_rad_d1)
t_db_d1 = time.perf_counter() - t0
print(f"DBSCAN on District 1 (The Loop, {n_d1:,} pts):")
print(f"  Time: {t_db_d1:.2f} s, Clusters: {len(set(labels_db_d1)-{-1})}, Noise: {(labels_db_d1==-1).sum():,} ({((labels_db_d1==-1).mean()*100):.2f}%)")

# -------------------------------------------------------------
# TEST OPTION C: Scaled MinPts on random sample
# -------------------------------------------------------------
print("\n--- Testing Option C: Scaled MinPts on Sample ---")
for sample_n in [25000, 50000]:
    sub = df.sample(n=sample_n, random_state=42)
    fraction = sample_n / total_n
    scaled_min_pts = max(2, int(round(25 * fraction)))
    coords_s = np.radians(sub[["Latitude", "Longitude"]].to_numpy())
    t0 = time.perf_counter()
    db_s = DBSCAN(eps=eps_rad, min_samples=scaled_min_pts, metric="haversine", algorithm="ball_tree")
    l_s = db_s.fit_predict(coords_s)
    print(f"Sample N={sample_n:,} (f={fraction:.3f}) with scaled MinPts={scaled_min_pts}:")
    print(f"  Noise: {(l_s == -1).sum():,} ({((l_s == -1).mean()*100):.2f}%), Clusters: {len(set(l_s)-{-1})}")

