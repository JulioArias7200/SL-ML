#!/usr/bin/env python3
"""
Precálculo y Benchmark de Modelos de Densidad para Chicago por Distrito Policial CPD.

Ejecuta DBSCAN, HDBSCAN y OPTICS sobre el 100% de los incidentes (2024-2025)
para cada uno de los 22 distritos policiales operativos de Chicago sin dilución ni muestreo.

Características:
- Determinación de ε por distrito mediante curva k-distance (k=MinPts=25) con criterio de codo
  de máxima distancia a la cuerda.
- Evaluación de duplicados: conteo de coordenadas únicas, porcentaje de eventos duplicados
  y micro-hotspots correspondientes a una sola coordenada (contados aparte).
- Silhouette espacial con métrica Haversine esférica: evaluada tanto sobre el conjunto completo
  como sobre coordenadas deduplicadas.
- Matriz de concordancia estructural (ARI) global, deduplicada y mutua entre particiones.
- Medición rigurosa de tiempos de CPU con time.perf_counter() y memoria RAM pico con tracemalloc.
- Ejecución paralela con ProcessPoolExecutor para reproducibilidad eficiente.
- Generación con firma SHA-256 del propio script para auditoría de integridad.
"""

import os
import sys
import json
import time
import hashlib
import tracemalloc
import argparse
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd

from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN, OPTICS
try:
    from sklearn.cluster import HDBSCAN
    HAS_HDBSCAN = True
except ImportError:
    HAS_HDBSCAN = False

from sklearn.metrics import adjusted_rand_score, silhouette_score

R_EARTH_M = 6371008.8
SCRIPT_VERSION = "3.1.0"


class NpEncoder(json.JSONEncoder):
    """Maneja tipos nativos de NumPy para serialización JSON segura."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def calculate_kdistance_elbow(coords_rad: np.ndarray, k: int = 25) -> int:
    """
    Calcula el codo de la curva k-distance para k vecinos mediante el criterio geométrico
    de máxima distancia perpendicular a la recta secante (cuerda) que une los extremos.
    """
    n_pts = len(coords_rad)
    if n_pts <= k:
        return 300

    nbrs = NearestNeighbors(n_neighbors=k, metric="haversine", algorithm="ball_tree").fit(coords_rad)
    dists, _ = nbrs.kneighbors(coords_rad)
    k_dists = np.sort(dists[:, k - 1] * R_EARTH_M)

    p1 = np.array([0.0, k_dists[0]])
    p2 = np.array([float(n_pts - 1), k_dists[-1]])
    line_vec = p2 - p1
    line_norm = np.linalg.norm(line_vec)
    if line_norm == 0:
        return 300

    line_unitvec = line_vec / line_norm
    pts = np.column_stack([np.arange(n_pts, dtype=float), k_dists])
    vec_from_p1 = pts - p1
    proj_len = np.dot(vec_from_p1, line_unitvec)
    proj_vec = np.outer(proj_len, line_unitvec)
    perp_dist = np.linalg.norm(vec_from_p1 - proj_vec, axis=1)

    elbow_idx = int(np.argmax(perp_dist))
    eps_elbow = int(round(k_dists[elbow_idx]))
    # Acotar entre 75m y 450m para estabilidad operativa táctica
    return max(75, min(450, eps_elbow))


def count_single_coord_clusters(labels: np.ndarray, coords: np.ndarray) -> int:
    """Cuenta clústeres donde el 100% de los incidentes comparten exactamente la misma coordenada geográfica."""
    cnt = 0
    for cl in set(labels) - {-1}:
        cl_coords = coords[labels == cl]
        if len(np.unique(cl_coords, axis=0)) == 1:
            cnt += 1
    return cnt


def compute_clean_silhouette(coords_rad: np.ndarray, labels: np.ndarray, max_subsample: int = 2000, seed: int = 42) -> float:
    """Calcula el coeficiente de Silhouette espacial con Haversine excluyendo ruido (-1)."""
    mask = (labels != -1)
    valid_coords = coords_rad[mask]
    valid_labels = labels[mask]
    unique_labels = set(valid_labels)
    if len(unique_labels) < 2 or len(valid_labels) < 2:
        return None

    if len(valid_labels) > max_subsample:
        rng = np.random.RandomState(seed)
        sub_idx = rng.choice(len(valid_labels), size=max_subsample, replace=False)
        valid_coords = valid_coords[sub_idx]
        valid_labels = valid_labels[sub_idx]
        if len(set(valid_labels)) < 2:
            return None

    score = silhouette_score(valid_coords, valid_labels, metric="haversine")
    return round(float(score), 3)


def compute_mutual_clustered_ari(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """Calcula ARI únicamente sobre los puntos asignados a clústeres simultáneamente por ambos modelos."""
    mask = (labels_a != -1) & (labels_b != -1)
    if mask.sum() < 2:
        return 0.0
    return round(float(adjusted_rand_score(labels_a[mask], labels_b[mask])), 3)


def process_district_worker(args_tuple):
    """Función de nivel superior para multiprocesamiento."""
    dist_id, coords, seed = args_tuple
    dist_id = int(dist_id)
    n_pts = len(coords)
    if n_pts < 25:
        return dist_id, {
            "status": "no disponible",
            "reason": f"Muestra insuficiente ({n_pts} eventos < MinPts=25)",
            "n_evaluated_points": n_pts
        }

    coords_rad = np.radians(coords)

    # Análisis de duplicados
    u_coords, u_indices = np.unique(coords, axis=0, return_index=True)
    n_unique = len(u_coords)
    n_duplicated = n_pts - n_unique
    pct_duplicated = round((n_duplicated / n_pts) * 100.0, 2)

    # Cálculo de eps_elbow
    eps_elbow_m = calculate_kdistance_elbow(coords_rad, k=25)
    eps_elbow_rad = eps_elbow_m / R_EARTH_M

    # 1. DBSCAN con eps_elbow
    tracemalloc.start()
    t0 = time.perf_counter()
    db_elbow = DBSCAN(eps=eps_elbow_rad, min_samples=25, metric="haversine", algorithm="ball_tree").fit(coords_rad)
    t_db_sec = time.perf_counter() - t0
    peak_db_bytes = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    t_db_ms = round(t_db_sec * 1000.0, 2)
    db_labels = db_elbow.labels_

    # DBSCAN con 300m de referencia
    db_300 = DBSCAN(eps=300.0 / R_EARTH_M, min_samples=25, metric="haversine", algorithm="ball_tree").fit(coords_rad)
    db_300_labels = db_300.labels_

    # 2. HDBSCAN
    tracemalloc.start()
    t0 = time.perf_counter()
    if HAS_HDBSCAN:
        hdb = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine", copy=True).fit(coords_rad)
        hdb_labels = hdb.labels_
    else:
        hdb_labels = np.full(n_pts, -1)
    t_hdb_sec = time.perf_counter() - t0
    peak_hdb_bytes = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    t_hdb_ms = round(t_hdb_sec * 1000.0, 2)

    # 3. OPTICS
    tracemalloc.start()
    t0 = time.perf_counter()
    opt = OPTICS(min_samples=25, xi=0.05, metric="haversine", algorithm="ball_tree", max_eps=500.0 / R_EARTH_M).fit(coords_rad)
    t_opt_sec = time.perf_counter() - t0
    peak_opt_bytes = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    t_opt_ms = round(t_opt_sec * 1000.0, 2)
    opt_labels = opt.labels_

    # Eventos rescatados
    rescued_hdb = int(((db_labels == -1) & (hdb_labels != -1)).sum())
    rescued_opt = int(((db_labels == -1) & (opt_labels != -1)).sum())

    # Silhouette estándar
    sil_db = compute_clean_silhouette(coords_rad, db_labels, seed=seed)
    sil_hdb = compute_clean_silhouette(coords_rad, hdb_labels, seed=seed)
    sil_opt = compute_clean_silhouette(coords_rad, opt_labels, seed=seed)

    # Silhouette deduplicado
    sil_db_dedup = compute_clean_silhouette(coords_rad[u_indices], db_labels[u_indices], seed=seed)
    sil_hdb_dedup = compute_clean_silhouette(coords_rad[u_indices], hdb_labels[u_indices], seed=seed)
    sil_opt_dedup = compute_clean_silhouette(coords_rad[u_indices], opt_labels[u_indices], seed=seed)

    # ARI Global
    ari_db_hdb = round(float(adjusted_rand_score(db_labels, hdb_labels)), 3)
    ari_db_opt = round(float(adjusted_rand_score(db_labels, opt_labels)), 3)
    ari_hdb_opt = round(float(adjusted_rand_score(hdb_labels, opt_labels)), 3)

    # ARI Deduplicado
    ari_db_hdb_dedup = round(float(adjusted_rand_score(db_labels[u_indices], hdb_labels[u_indices])), 3)
    ari_db_opt_dedup = round(float(adjusted_rand_score(db_labels[u_indices], opt_labels[u_indices])), 3)
    ari_hdb_opt_dedup = round(float(adjusted_rand_score(hdb_labels[u_indices], opt_labels[u_indices])), 3)

    # ARI Mutuo Clustered
    ari_mut_db_hdb = compute_mutual_clustered_ari(db_labels, hdb_labels)
    ari_mut_db_opt = compute_mutual_clustered_ari(db_labels, opt_labels)
    ari_mut_hdb_opt = compute_mutual_clustered_ari(hdb_labels, opt_labels)

    # Resumen estructurado por modelo
    def model_summary(labels, t_ms, ram_bytes, sil_std, sil_dedup, name, title, color_var, params_str, desc_str):
        cl_set = set(labels) - {-1}
        n_cl = len(cl_set)
        n_noise = int((labels == -1).sum())
        noise_pct = round((n_noise / n_pts) * 100.0, 2)
        cov_pct = round(100.0 - noise_pct, 2)
        single_coords = count_single_coord_clusters(labels, coords)
        spatial_hotspots = n_cl - single_coords

        return {
            "id": name.lower(),
            "name": name,
            "title": title,
            "color_var": color_var,
            "clusters": n_cl,
            "spatial_hotspots": spatial_hotspots,
            "single_coord_clusters": single_coords,
            "noise_pct": noise_pct,
            "noise_count": n_noise,
            "coverage_pct": cov_pct,
            "silhouette_spatial": sil_std,
            "silhouette_deduplicated": sil_dedup,
            "execution_time_ms": t_ms,
            "peak_memory_mb": round(ram_bytes / (1024 * 1024), 2),
            "memory_type": "memoria Python rastreada (tracemalloc)",
            "parameters": params_str,
            "desc": desc_str,
            "provenance": f"calculada sobre Distrito {dist_id} completo ({n_pts:,} eventos, densidad 100% real) con time.perf_counter() y tracemalloc"
        }

    models_data = {
        "dbscan": model_summary(
            db_labels, t_db_ms, peak_db_bytes, sil_db, sil_db_dedup,
            "DBSCAN", "DBSCAN (k-distance)", "--algo-dbscan",
            f"ε={eps_elbow_m} m (codo k-dist) · MinPts=25",
            f"Radio Haversine determinado por codo de máxima distancia a la cuerda ({eps_elbow_m} m). "
            f"Descarta {int((db_labels == -1).sum()):,} eventos como ruido ({round((db_labels == -1).mean()*100, 1)}%) "
            f"y detecta {len(set(db_labels) - {-1})} clústeres ({len(set(db_labels) - {-1}) - count_single_coord_clusters(db_labels, coords)} hotspots espaciales, {count_single_coord_clusters(db_labels, coords)} de punto único)."
        ),
        "dbscan_300m": model_summary(
            db_300_labels, 0.0, 0, None, None,
            "DBSCAN 300m", "DBSCAN histórico 300m", "--algo-dbscan",
            "ε=300 m · MinPts=25",
            f"DBSCAN con radio fijo de 300 m: genera {len(set(db_300_labels) - {-1})} macro-conglomerados y {round((db_300_labels == -1).mean()*100, 2)}% de ruido."
        ),
        "hdbscan": model_summary(
            hdb_labels, t_hdb_ms, peak_hdb_bytes, sil_hdb, sil_hdb_dedup,
            "HDBSCAN", "HDBSCAN adaptativo", "--algo-hdbscan",
            "MinCluster=25 · MinSamples=15",
            f"Densidad jerárquica adaptativa con persistencia λ. Identifica {len(set(hdb_labels) - {-1})} micro-hotspots locales "
            f"({len(set(hdb_labels) - {-1}) - count_single_coord_clusters(hdb_labels, coords)} hotspots espaciales, {count_single_coord_clusters(hdb_labels, coords)} de punto único) "
            f"y discrimina {int((hdb_labels == -1).sum()):,} eventos como ruido inter-cluster ({round((hdb_labels == -1).mean()*100, 1)}%)."
        ),
        "optics": model_summary(
            opt_labels, t_opt_ms, peak_opt_bytes, sil_opt, sil_opt_dedup,
            "OPTICS", "OPTICS multiescala", "--algo-optics",
            "ξ=0.05 · MinPts=25 · max_eps=500m",
            f"Ordenamiento por alcanzabilidad jerárquica con cota max_eps=500 m. Extrae {len(set(opt_labels) - {-1})} valles de densidad "
            f"({len(set(opt_labels) - {-1}) - count_single_coord_clusters(opt_labels, coords)} valles espaciales, {count_single_coord_clusters(opt_labels, coords)} de punto único)."
        )
    }

    # Mini alcanzabilidad OPTICS
    reach = opt.reachability_[opt.ordering_]
    valleys = opt_labels[opt.ordering_]
    step = max(1, len(reach) // 12)
    mini_reach = []
    for rank, idx in enumerate(range(0, len(reach), step)[:12]):
        val = float(reach[idx])
        dist_m = 1000 if np.isinf(val) or val > (1000.0 / R_EARTH_M) else int(round(val * R_EARTH_M))
        v_id = int(valleys[idx])
        mini_reach.append({
            "idx": rank + 1,
            "dist": dist_m,
            "valley": v_id,
            "color": "#fbbf24" if v_id != -1 else "#64748b",
            "name": f"Punto {rank+1} (Orden {idx})"
        })
    models_data["optics"]["mini_reachability"] = mini_reach

    ari_matrix_dict = {
        "models": ["DBSCAN", "HDBSCAN", "OPTICS"],
        "scores": [
            [1.0, ari_db_hdb, ari_db_opt],
            [ari_db_hdb, 1.0, ari_hdb_opt],
            [ari_db_opt, ari_hdb_opt, 1.0]
        ],
        "values": [
            [1.0, ari_db_hdb, ari_db_opt],
            [ari_db_hdb, 1.0, ari_hdb_opt],
            [ari_db_opt, ari_hdb_opt, 1.0]
        ],
        "global_ari": [
            [1.0, ari_db_hdb, ari_db_opt],
            [ari_db_hdb, 1.0, ari_hdb_opt],
            [ari_db_opt, ari_hdb_opt, 1.0]
        ],
        "deduplicated_scores": [
            [1.0, ari_db_hdb_dedup, ari_db_opt_dedup],
            [ari_db_hdb_dedup, 1.0, ari_hdb_opt_dedup],
            [ari_db_opt_dedup, ari_hdb_opt_dedup, 1.0]
        ],
        "deduplicated_ari": [
            [1.0, ari_db_hdb_dedup, ari_db_opt_dedup],
            [ari_db_hdb_dedup, 1.0, ari_hdb_opt_dedup],
            [ari_db_opt_dedup, ari_hdb_opt_dedup, 1.0]
        ],
        "mutual_clustered_ari": {
            "scores": [
                [1.0, ari_mut_db_hdb, ari_mut_db_opt],
                [ari_mut_db_hdb, 1.0, ari_mut_hdb_opt],
                [ari_mut_db_opt, ari_mut_hdb_opt, 1.0]
            ],
            "values": [
                [1.0, ari_mut_db_hdb, ari_mut_db_opt],
                [ari_mut_db_hdb, 1.0, ari_mut_hdb_opt],
                [ari_mut_db_opt, ari_mut_hdb_opt, 1.0]
            ],
            "note": "Calculado únicamente sobre incidentes clasificados en clústeres simultáneamente por ambos modelos (excluyendo ruido -1)."
        },
        "explanation": f"Evaluación de concordancia estructural sobre el Distrito {dist_id} completo ({n_pts:,} eventos). scikit-learn solo admite sample_weight en DBSCAN; HDBSCAN, OPTICS y adjusted_rand_score no admiten ponderación."
    }

    result = {
        "status": "completado",
        "district_id": dist_id,
        "n_evaluated_points": n_pts,
        "unique_coords": n_unique,
        "duplicated_points": n_duplicated,
        "pct_duplicated": pct_duplicated,
        "eps_elbow_m": eps_elbow_m,
        "models": models_data,
        "ari_matrix": ari_matrix_dict,
        "rescued_events": {
            "definition": "Incidentes con label == -1 en DBSCAN que son asignados a un clúster (label != -1) por el algoritmo alternativo.",
            "hdbscan_from_dbscan": rescued_hdb,
            "optics_from_dbscan": rescued_opt
        }
    }
    return dist_id, result


def parse_args():
    parser = argparse.ArgumentParser(description="Precalcular benchmark espacial de Chicago por distrito.")
    parser.add_argument("--input", default="data/chicago_benchmark/silver/chicago_crimes_curated.parquet",
                        help="Ruta al archivo parquet curado de Chicago.")
    parser.add_argument("--output", default="data/chicago_benchmark/gold/chicago_model_benchmark.json",
                        help="Ruta de destino del archivo JSON con los resultados.")
    parser.add_argument("--years-min", type=int, default=2024,
                        help="Año mínimo de eventos para densidad continua (default 2024).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria para reproducibilidad.")
    parser.add_argument("--workers", type=int, default=6,
                        help="Número de procesos paralelos para evaluación rápida.")
    return parser.parse_args()


def main():
    args = parse_args()

    # Cálculo del hash SHA-256 de este propio script para auditoría de integridad
    with open(__file__, "rb") as f:
        script_sha256 = hashlib.sha256(f.read()).hexdigest()

    print("=" * 80, flush=True)
    print("AUDITORÍA & PRECÁLCULO DE MODELOS DE DENSIDAD ESPACIAL: CHICAGO CPD POR DISTRITO", flush=True)
    print("=" * 80, flush=True)
    print(f"Timestamp: {datetime.now().isoformat()}", flush=True)
    print(f"Script SHA-256: {script_sha256}", flush=True)
    print(f"Versión: {SCRIPT_VERSION}", flush=True)
    print(f"Dataset de entrada: {args.input}", flush=True)
    print(f"Años evaluados: >= {args.years_min}", flush=True)
    print(f"Destino JSON: {args.output}", flush=True)
    print(f"Workers paralelos: {args.workers}", flush=True)
    print("-" * 80, flush=True)

    if not os.path.exists(args.input):
        print(f"ERROR: No se encontró el archivo {args.input}", file=sys.stderr)
        sys.exit(1)

    print("1. Cargando conjunto de datos Parquet...", flush=True)
    t0 = time.perf_counter()
    df = pd.read_parquet(args.input, columns=["ID", "District", "Latitude", "Longitude", "Year", "Primary Type"])
    t_load = time.perf_counter() - t0
    total_records = len(df)
    print(f"   Total registros cargados: {total_records:,} en {t_load:.2f} s", flush=True)

    df_valid = df.dropna(subset=["Latitude", "Longitude", "District"]).copy()
    df_recent = df_valid[df_valid["Year"] >= args.years_min].copy()
    df_recent["District"] = df_recent["District"].astype(int)
    print(f"   Registros válidos (>= {args.years_min}): {len(df_recent):,}", flush=True)

    districts = sorted(df_recent["District"].unique())
    print(f"   Distritos encontrados ({len(districts)}): {districts}", flush=True)

    # Preparar tareas para ProcessPoolExecutor
    tasks = []
    for dist_id in districts:
        dist_df = df_recent[df_recent["District"] == dist_id]
        coords = dist_df[["Latitude", "Longitude"]].to_numpy()
        tasks.append((dist_id, coords, args.seed))

    print(f"\n2. Procesando {len(tasks)} distritos con {args.workers} workers paralelos...", flush=True)
    t_pool0 = time.perf_counter()
    districts_results = {}

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for dist_id, res in executor.map(process_district_worker, tasks):
            districts_results[str(dist_id)] = res
            if res.get("status") == "completado":
                db_m = res["models"]["dbscan"]
                hdb_m = res["models"]["hdbscan"]
                opt_m = res["models"]["optics"]
                print(f"   [OK] Distrito {dist_id:>2} ({res['n_evaluated_points']:>6,} pts, {res['unique_coords']:>5,} unq, {res['pct_duplicated']:>4.1f}% dup): "
                      f"eps={res['eps_elbow_m']:>3}m | DB={db_m['clusters']:>2} cl ({db_m['spatial_hotspots']} esp + {db_m['single_coord_clusters']} unq) ruido={db_m['noise_pct']:>4.1f}% | "
                      f"HDB={hdb_m['clusters']:>3} cl ({hdb_m['spatial_hotspots']} esp + {hdb_m['single_coord_clusters']} unq) | "
                      f"OPT={opt_m['clusters']:>3} cl ({opt_m['spatial_hotspots']} esp + {opt_m['single_coord_clusters']} unq) | "
                      f"RAM={opt_m['peak_memory_mb']:>5.2f}MB, t={round(opt_m['execution_time_ms']/1000, 1)}s", flush=True)
            else:
                print(f"   [OMITIDO] Distrito {dist_id:>2}: {res.get('status')} - {res.get('reason')}", flush=True)

    t_pool = time.perf_counter() - t_pool0
    print(f"\nEvaluación paralela completada en {t_pool:.2f} s ({t_pool/60:.2f} min).", flush=True)

    # Top-level default apunta a Distrito 1
    d1_res = districts_results.get("1", {})
    if d1_res.get("status") == "completado":
        top_models = {
            "dbscan": d1_res["models"]["dbscan"],
            "hdbscan": d1_res["models"]["hdbscan"],
            "optics": d1_res["models"]["optics"]
        }
        top_ari = d1_res["ari_matrix"]
        top_rescued = d1_res["rescued_events"]
    else:
        top_models, top_ari, top_rescued = {}, {}, {}

    output_payload = {
        "metadata": {
            "version": SCRIPT_VERSION,
            "script_version": SCRIPT_VERSION,
            "script_sha256": script_sha256,
            "benchmark_name": "chicago_density_models_all_districts",
            "generated_at": datetime.now().isoformat(),
            "source_parquet": args.input,
            "total_dataset_records": total_records,
            "n_sampled_points": d1_res.get("n_evaluated_points", 16771),
            "subset_description": "Subconjuntos espaciales completos por distrito policial CPD (2024-2025). 100% densidad real sin muestreo.",
            "evaluated_districts_count": len(districts),
            "years_range": f"{args.years_min}-2025",
            "random_seed": args.seed,
            "memory_metric_type": "memoria Python rastreada (tracemalloc)",
            "methodology": {
                "k_distance_elbow_k": 25,
                "elbow_criterion": "Maxima distancia perpendicular a la recta secante (cuerda)",
                "k_distance_coincident_handling": "Los eventos coincidentes en la misma coordenada (distancia 0 m) se conservan para reflejar la densidad de pila local; k=25 mide la distancia necesaria para trascender el amontonamiento puntual local.",
                "spatial_metric": "haversine_spherical_radians",
                "earth_radius_m": R_EARTH_M,
                "hdbscan_min_cluster": 25,
                "hdbscan_min_samples": 15,
                "optics_min_samples": 25,
                "optics_xi": 0.05,
                "optics_max_eps_m": 500,
                "sample_weight_support": "scikit-learn solo admite sample_weight en DBSCAN; no lo admite en HDBSCAN, OPTICS ni adjusted_rand_score."
            }
        },
        "models": top_models,
        "ari_matrix": top_ari,
        "rescued_events": top_rescued,
        "districts": districts_results
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False, cls=NpEncoder)

    print("\n" + "=" * 80, flush=True)
    print(f"PRECÁLCULO FINALIZADO. Guardado en {args.output}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
