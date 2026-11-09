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

parquet_path = "data/chicago_benchmark/silver/chicago_crimes_curated.parquet"
df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude"])
df = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()
total_n = len(df)
r_earth = 6371008.8
eps_rad = 300.0 / r_earth

print("="*80, flush=True)
print("EXPERIMENTO OPCIÓN B: SUB-CONJUNTO ESPACIAL COMPLETO (PRESERVA DENSIDAD REAL)", flush=True)
print("="*80, flush=True)

# Distritos contiguos del Core Urbano:
# Distrito 1: Central / The Loop
# Distrito 18: Near North (River North, Magnificent Mile)
# Distrito 12: Near West (West Loop, UIC, Pilsen)
core_districts = [1, 18, 12]
df_core = df[df["District"].isin(core_districts)].copy()
n_core = len(df_core)
print(f"Distritos seleccionados {core_districts} (Downtown & Eje Central):", flush=True)
print(f"  Eventos totales: {n_core:,} (100% de sus incidentes, densidad física intacta)", flush=True)

coords_core = np.radians(df_core[["Latitude", "Longitude"]].to_numpy())
t0 = time.perf_counter()
mem_start = get_mem_mb()
db_core = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
labels_db_core = db_core.fit_predict(coords_core)
t_db_core = time.perf_counter() - t0
mem_peak = get_mem_mb()

clusters_core = len(set(labels_db_core) - {-1})
noise_core = int((labels_db_core == -1).sum())
noise_pct_core = round((noise_core / n_core) * 100.0, 2)
coverage_core = round(100.0 - noise_pct_core, 2)

print(f"DBSCAN en Distritos {core_districts} (ε=300m, MinPts=25):", flush=True)
print(f"  Tiempo ejecución: {t_db_core:.2f} s ({t_db_core*1000:.1f} ms)", flush=True)
print(f"  Memoria: {mem_peak - mem_start:.1f} MB (Total: {mem_peak:.1f} MB)", flush=True)
print(f"  Clústeres activos: {clusters_core}", flush=True)
print(f"  Ruido real: {noise_core:,} de {n_core:,} eventos ({noise_pct_core}%)", flush=True)
print(f"  Cobertura real: {coverage_core}%", flush=True)

# Distrito 1 individual (The Loop)
df_d1 = df[df["District"] == 1].copy()
coords_d1 = np.radians(df_d1[["Latitude", "Longitude"]].to_numpy())
t0 = time.perf_counter()
db_d1 = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
l_d1 = db_d1.fit_predict(coords_d1)
t_d1 = time.perf_counter() - t0
print(f"\nDBSCAN Distrito 1 solo (The Loop, {len(df_d1):,} eventos):", flush=True)
print(f"  Tiempo: {t_d1:.2f} s, Clústeres: {len(set(l_d1)-{-1})}, Ruido: {(l_d1==-1).sum():,} ({((l_d1==-1).mean()*100):.2f}%)", flush=True)

# Distritos 11 y 15 (West Side: Garfield Park / Austin, zona crítica de armas)
df_west = df[df["District"].isin([11, 15])].copy()
coords_west = np.radians(df_west[["Latitude", "Longitude"]].to_numpy())
t0 = time.perf_counter()
db_west = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
l_west = db_west.fit_predict(coords_west)
t_west = time.perf_counter() - t0
print(f"\nDBSCAN Distritos 11 y 15 (West Side, {len(df_west):,} eventos):", flush=True)
print(f"  Tiempo: {t_west:.2f} s, Clústeres: {len(set(l_west)-{-1})}, Ruido: {(l_west==-1).sum():,} ({((l_west==-1).mean()*100):.2f}%)", flush=True)

print("\n" + "="*80, flush=True)
print("EXPERIMENTO OPCIÓN C: ESCALADO DE MINPTS SEGÚN FRACCIÓN MUESTRAL", flush=True)
print("="*80, flush=True)
for s_size in [10000, 25000, 50000, 100000]:
    sample = df.sample(n=s_size, random_state=42)
    fraction = s_size / total_n
    # Si N se reduce en factor (1/f), el número de vecinos esperados en un radio fijo se reduce por f.
    # Por lo tanto, si la densidad real requería MinPts=25 en el conjunto completo,
    # ¿cómo escala?
    # MinPts_scaled = max(2, int(round(25 * fraction)))
    pts_scaled = max(2, int(round(25 * fraction)))
    coords_s = np.radians(sample[["Latitude", "Longitude"]].to_numpy())
    db_c = DBSCAN(eps=eps_rad, min_samples=pts_scaled, metric="haversine", algorithm="ball_tree")
    l_c = db_c.fit_predict(coords_s)
    pct_noise = (l_c == -1).mean() * 100
    print(f"Sample N={s_size:>6,} (f={fraction:.3f}) | MinPts={pts_scaled:>2} | Ruido: {pct_noise:5.2f}% | Clústeres: {len(set(l_c)-{-1}):>3}", flush=True)

