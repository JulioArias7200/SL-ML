import time
import tracemalloc
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS
import warnings
warnings.filterwarnings('ignore')

df = pd.read_parquet('data/chicago_benchmark/silver/chicago_crimes_curated.parquet', columns=['Latitude', 'Longitude'])
df = df.dropna()
coords_all = np.radians(df[['Latitude', 'Longitude']].to_numpy())
r_earth = 6371008.8

print("=" * 70)
print("EXPERIMENTO DE ESCALABILIDAD MEDIDA (TIEMPO Y MEMORIA PICO VS N)")
print("=" * 70)
print(f"{'N puntos':<10} | {'DBSCAN (s)':<12} | {'HDBSCAN (s)':<12} | {'OPTICS (s)':<12} | {'OPTICS RAM (MB)':<15}")
print("-" * 70)

for n in [1000, 5000, 10000, 20000]:
    sub = coords_all[:n]
    
    # DBSCAN
    t0 = time.perf_counter()
    db = DBSCAN(eps=200/r_earth, min_samples=25, metric='haversine', algorithm='ball_tree').fit(sub)
    t_db = time.perf_counter() - t0
    
    # HDBSCAN
    t0 = time.perf_counter()
    hdb = HDBSCAN(min_cluster_size=25, min_samples=15, metric='haversine', copy=True).fit(sub)
    t_hdb = time.perf_counter() - t0
    
    # OPTICS
    tracemalloc.start()
    t0 = time.perf_counter()
    opt = OPTICS(min_samples=25, max_eps=500/r_earth, xi=0.05, metric='haversine', algorithm='ball_tree').fit(sub)
    t_opt = time.perf_counter() - t0
    _, peak_opt = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"{n:<10,} | {t_db:<12.3f} | {t_hdb:<12.3f} | {t_opt:<12.3f} | {peak_opt/(1024*1024):<15.2f}")

