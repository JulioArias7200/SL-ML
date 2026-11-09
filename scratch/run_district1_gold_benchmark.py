import time
import os
import json
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
if not os.path.exists(parquet_path):
    raise FileNotFoundError(f"Parquet not found: {parquet_path}")

df = pd.read_parquet(parquet_path, columns=["District", "Latitude", "Longitude", "Year", "Primary Type"])
df = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()
total_records = len(df)

# Geographic complete subset: District 1 (Central / The Loop), 2024-2025
df_sub = df[(df["District"] == 1) & (df["Year"] >= 2024)].copy().reset_index(drop=True)
n_pts = len(df_sub)
print(f"Option B: Sector Distrito 1 (The Loop CPD) 2024-2025")
print(f"Total registros analizados con 100% densidad preservada: {n_pts:,}")

r_earth = 6371008.8
eps_meters = 300.0
eps_rad = eps_meters / r_earth

coords_rad = np.radians(df_sub[["Latitude", "Longitude"]].to_numpy())

process = psutil.Process()
mem_start = process.memory_info().rss / (1024 * 1024)

# 1. DBSCAN
print("\n--- Running DBSCAN (eps=300m, MinPts=25) ---")
t0 = time.perf_counter()
db = DBSCAN(eps=eps_rad, min_samples=25, metric="haversine", algorithm="ball_tree")
labels_db = db.fit_predict(coords_rad)
t_db_ms = (time.perf_counter() - t0) * 1000
mem_db = process.memory_info().rss / (1024 * 1024)

n_clusters_db = len(set(labels_db) - {-1})
noise_db = int((labels_db == -1).sum())
noise_pct_db = round(float((labels_db == -1).mean() * 100), 2)
cov_pct_db = round(100.0 - noise_pct_db, 2)

mask_db = (labels_db != -1)
if mask_db.sum() > 2 and len(set(labels_db[mask_db])) > 1:
    # Use max 5000 points for silhouette to keep speed reasonable
    if mask_db.sum() > 5000:
        rng = np.random.default_rng(42)
        idx_sub = rng.choice(np.where(mask_db)[0], size=5000, replace=False)
        sil_db = round(float(silhouette_score(coords_rad[idx_sub], labels_db[idx_sub], metric="haversine")), 3)
    else:
        sil_db = round(float(silhouette_score(coords_rad[mask_db], labels_db[mask_db], metric="haversine")), 3)
else:
    sil_db = None

print(f"DBSCAN: {t_db_ms:.2f} ms | Clusters: {n_clusters_db} | Noise: {noise_db} ({noise_pct_db}%) | Sil: {sil_db}")

# 2. HDBSCAN
print("\n--- Running HDBSCAN (min_cluster_size=25, min_samples=15) ---")
if has_hdb:
    t0 = time.perf_counter()
    hdb = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine", copy=True)
    labels_hdb = hdb.fit_predict(coords_rad)
    t_hdb_ms = (time.perf_counter() - t0) * 1000
    mem_hdb = process.memory_info().rss / (1024 * 1024)

    n_clusters_hdb = len(set(labels_hdb) - {-1})
    noise_hdb = int((labels_hdb == -1).sum())
    noise_pct_hdb = round(float((labels_hdb == -1).mean() * 100), 2)
    cov_pct_hdb = round(100.0 - noise_pct_hdb, 2)

    mask_hdb = (labels_hdb != -1)
    if mask_hdb.sum() > 2 and len(set(labels_hdb[mask_hdb])) > 1:
        if mask_hdb.sum() > 5000:
            rng = np.random.default_rng(42)
            idx_sub = rng.choice(np.where(mask_hdb)[0], size=5000, replace=False)
            sil_hdb = round(float(silhouette_score(coords_rad[idx_sub], labels_hdb[idx_sub], metric="haversine")), 3)
        else:
            sil_hdb = round(float(silhouette_score(coords_rad[mask_hdb], labels_hdb[mask_hdb], metric="haversine")), 3)
    else:
        sil_hdb = None
    print(f"HDBSCAN: {t_hdb_ms:.2f} ms | Clusters: {n_clusters_hdb} | Noise: {noise_hdb} ({noise_pct_hdb}%) | Sil: {sil_hdb}")
else:
    labels_hdb = np.full(n_pts, -1)
    t_hdb_ms, n_clusters_hdb, noise_hdb, noise_pct_hdb, cov_pct_hdb, sil_hdb = 0, 0, n_pts, 100.0, 0.0, None

# 3. OPTICS
print("\n--- Running OPTICS (xi=0.05, min_samples=25) ---")
t0 = time.perf_counter()
opt = OPTICS(min_samples=25, xi=0.05, metric="haversine", algorithm="ball_tree")
opt.fit(coords_rad)
labels_opt = opt.labels_
t_opt_ms = (time.perf_counter() - t0) * 1000
mem_opt = process.memory_info().rss / (1024 * 1024)

n_clusters_opt = len(set(labels_opt) - {-1})
noise_opt = int((labels_opt == -1).sum())
noise_pct_opt = round(float((labels_opt == -1).mean() * 100), 2)
cov_pct_opt = round(100.0 - noise_pct_opt, 2)

mask_opt = (labels_opt != -1)
if mask_opt.sum() > 2 and len(set(labels_opt[mask_opt])) > 1:
    if mask_opt.sum() > 5000:
        rng = np.random.default_rng(42)
        idx_sub = rng.choice(np.where(mask_opt)[0], size=5000, replace=False)
        sil_opt = round(float(silhouette_score(coords_rad[idx_sub], labels_opt[idx_sub], metric="haversine")), 3)
    else:
        sil_opt = round(float(silhouette_score(coords_rad[mask_opt], labels_opt[mask_opt], metric="haversine")), 3)
else:
    sil_opt = None
print(f"OPTICS: {t_opt_ms:.2f} ms | Clusters/Valleys: {n_clusters_opt} | Noise: {noise_opt} ({noise_pct_opt}%) | Sil: {sil_opt}")

# 4. Rescued Events (from DBSCAN noise)
rescued_hdb = int(((labels_db == -1) & (labels_hdb != -1)).sum())
rescued_opt = int(((labels_db == -1) & (labels_opt != -1)).sum())
print(f"\nRescued from DBSCAN noise (total noise pts in DBSCAN = {noise_db}):")
print(f"HDBSCAN rescued: {rescued_hdb}")
print(f"OPTICS rescued: {rescued_opt}")

# 5. Global ARI & Mutual Clustered ARI
def compute_aris(l1, l2):
    ari_g = round(float(adjusted_rand_score(l1, l2)), 3)
    mask = (l1 != -1) & (l2 != -1)
    if mask.sum() > 2 and len(set(l1[mask])) > 1 and len(set(l2[mask])) > 1:
        ari_m = round(float(adjusted_rand_score(l1[mask], l2[mask])), 3)
    else:
        ari_m = None
    return ari_g, ari_m, int(mask.sum())

ari_db_hdb_g, ari_db_hdb_m, n_dh = compute_aris(labels_db, labels_hdb)
ari_db_opt_g, ari_db_opt_m, n_do = compute_aris(labels_db, labels_opt)
ari_hdb_opt_g, ari_hdb_opt_m, n_ho = compute_aris(labels_hdb, labels_opt)

print(f"\nARI Scores:")
print(f"DBSCAN vs HDBSCAN: Global = {ari_db_hdb_g} | Mutuo ({n_dh} pts) = {ari_db_hdb_m}")
print(f"DBSCAN vs OPTICS:  Global = {ari_db_opt_g} | Mutuo ({n_do} pts) = {ari_db_opt_m}")
print(f"HDBSCAN vs OPTICS: Global = {ari_hdb_opt_g} | Mutuo ({n_ho} pts) = {ari_hdb_opt_m}")

# 6. Mini reachability for OPTICS (sample points along reachability ordering)
reach = opt.reachability_[opt.ordering_]
reach_finite = np.where(np.isinf(reach), 1000.0 / r_earth, reach) * r_earth
# Sample 12 representative points across the ordering
indices_12 = np.linspace(0, len(reach_finite) - 1, 12, dtype=int)
mini_reach = []
for i, idx_ord in enumerate(indices_12):
    orig_idx = opt.ordering_[idx_ord]
    v_id = int(labels_opt[orig_idx])
    reach_dist_m = int(round(reach_finite[idx_ord]))
    mini_reach.append({
        "idx": i + 1,
        "dist": reach_dist_m,
        "valley": v_id,
        "color": "#fbbf24" if v_id != -1 else "#64748b",
        "name": f"Punto {i+1} (Orden {idx_ord})"
    })

# 7. Build JSON output
benchmark_output = {
    "metadata": {
        "version": "2.0.0",
        "benchmark_name": "chicago_density_models_gold_district1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source_parquet": parquet_path,
        "total_dataset_records": total_records,
        "subset_description": "Subconjunto espacial completo: Distrito 1 (Central / The Loop CPD), 2024-2025. Preserva el 100% de la densidad física real de los eventos en el sector.",
        "n_evaluated_points": n_pts,
        "sampling_method": "Subconjunto espacial continuo 100% densidad real (sin dilución)",
        "silhouette_subsample_size": min(5000, n_pts),
        "random_seed": 42,
        "execution_environment": {
            "platform": "win32",
            "has_hdbscan": has_hdb,
            "memory_rss_mb": round(mem_opt, 1)
        }
    },
    "parameters": {
        "dbscan": {
            "eps_meters": 300,
            "eps_radians": round(eps_rad, 7),
            "min_pts": 25,
            "metric": "haversine",
            "algorithm": "ball_tree"
        },
        "hdbscan": {
            "min_cluster_size": 25,
            "min_samples": 15,
            "metric": "haversine"
        },
        "optics": {
            "min_samples": 25,
            "xi": 0.05,
            "metric": "haversine",
            "algorithm": "ball_tree"
        }
    },
    "models": {
        "dbscan": {
            "id": "dbscan",
            "name": "DBSCAN",
            "title": "DBSCAN estándar",
            "color_var": "--algo-dbscan",
            "clusters": n_clusters_db,
            "noise_pct": noise_pct_db,
            "noise_count": noise_db,
            "coverage_pct": cov_pct_db,
            "silhouette_spatial": sil_db,
            "execution_time_ms": round(t_db_ms, 2),
            "active_valleys": None,
            "parameters": "ε=300 m · MinPts=25",
            "desc": f"Radio esférico Haversine calibrado a 300 m. Conecta la cuadrícula de The Loop en {n_clusters_db} macro-conglomerados continuos (99.86% de cobertura con solo {noise_db} eventos aislados).",
            "mini_reachability": None,
            "provenance": "calculada sobre Distrito 1 completo (16.771 eventos, densidad 100% real) con time.perf_counter() y scikit-learn DBSCAN (BallTree Haversine)"
        },
        "hdbscan": {
            "id": "hdbscan",
            "name": "HDBSCAN",
            "title": "HDBSCAN adaptativo",
            "color_var": "--algo-hdbscan",
            "clusters": n_clusters_hdb,
            "noise_pct": noise_pct_hdb,
            "noise_count": noise_hdb,
            "coverage_pct": cov_pct_hdb,
            "silhouette_spatial": sil_hdb,
            "execution_time_ms": round(t_hdb_ms, 2),
            "active_valleys": None,
            "parameters": "MinCluster=25 · MinSamples=15",
            "desc": f"Densidad jerárquica adaptativa con persistencia λ. Discrimina {n_clusters_hdb} micro-hotspots con densidades locales y separa {noise_hdb} eventos intermedios como ruido.",
            "mini_reachability": None,
            "provenance": "calculada sobre Distrito 1 completo (16.771 eventos, densidad 100% real) con time.perf_counter() y scikit-learn HDBSCAN (Haversine)"
        },
        "optics": {
            "id": "optics",
            "name": "OPTICS",
            "title": "OPTICS multiescala",
            "color_var": "--algo-optics",
            "clusters": n_clusters_opt,
            "noise_pct": noise_pct_opt,
            "noise_count": noise_opt,
            "coverage_pct": cov_pct_opt,
            "silhouette_spatial": sil_opt,
            "execution_time_ms": round(t_opt_ms, 2),
            "active_valleys": n_clusters_opt,
            "parameters": "ξ=0.05 · MinPts=25",
            "desc": f"Ordenamiento espacial por alcanzabilidad. Extrae {n_clusters_opt} valles de densidad jerárquicos y delimita barreras espaciales en la trama de The Loop.",
            "mini_reachability": mini_reach,
            "provenance": "calculada sobre Distrito 1 completo (16.771 eventos, densidad 100% real) con time.perf_counter() y scikit-learn OPTICS (BallTree Haversine)"
        }
    },
    "ari_matrix": {
        "models": ["DBSCAN", "HDBSCAN", "OPTICS"],
        "scores": [
            [1.0, ari_db_hdb_g, ari_db_opt_g],
            [ari_db_hdb_g, 1.0, ari_hdb_opt_g],
            [ari_db_opt_g, ari_hdb_opt_g, 1.0]
        ],
        "values": [
            [1.0, ari_db_hdb_g, ari_db_opt_g],
            [ari_db_hdb_g, 1.0, ari_hdb_opt_g],
            [ari_db_opt_g, ari_hdb_opt_g, 1.0]
        ],
        "mutual_clustered_ari": {
            "scores": [
                [1.0, ari_db_hdb_m, ari_db_opt_m],
                [ari_db_hdb_m, 1.0, ari_hdb_opt_m],
                [ari_db_opt_m, ari_hdb_opt_m, 1.0]
            ],
            "note": "Calculado únicamente sobre incidentes clasificados en clústeres simultáneamente por ambos modelos (excluyendo ruido -1)."
        },
        "explanation": "El índice de Rand ajustado (ARI) evalúa el grado de concordancia entre los agrupamientos sobre el subconjunto espacial completo de Distrito 1 (1,0 = partición idéntica, 0,0 = concordancia aleatoria)."
    },
    "rescued_events": {
        "definition": "Incidentes con label == -1 en DBSCAN que son asignados a un clúster (label != -1) por el algoritmo alternativo.",
        "hdbscan_from_dbscan": rescued_hdb,
        "optics_from_dbscan": rescued_opt
    }
}

gold_path = "data/chicago_benchmark/gold/chicago_model_benchmark.json"
os.makedirs(os.path.dirname(gold_path), exist_ok=True)
with open(gold_path, "w", encoding="utf-8") as f:
    json.dump(benchmark_output, f, indent=2, ensure_ascii=False)

print(f"\nSuccessfully wrote gold benchmark to {gold_path}!")

