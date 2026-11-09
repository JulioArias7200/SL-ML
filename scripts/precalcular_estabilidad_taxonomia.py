#!/usr/bin/env python3
"""
Precalculador de Estabilidad de Taxonomía Jerárquica mediante Bootstrap Remuestreado.

Realiza B=200 iteraciones de bootstrap remuestreando eventos con reemplazo dentro de
cada unidad territorial (distritos en Chicago, zonas con n >= 3 en Bolivia).
Evalúa la estabilidad de las asignaciones de clústeres mediante el Índice de Rand
Ajustado (ARI) y la tasa de consistencia por unidad.

Salida:
- data/chicago_benchmark/gold/chicago_taxonomy_stability.json
- data/bolivia_news/gold/bolivia_taxonomy_stability.json
"""

import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

SCRIPT_VERSION = "1.0.0"

# Mapeo oficial de categorías de delitos para Chicago
CHICAGO_CRIME_CATEGORIES = {
    "HOMICIDE": "Violencia armada y homicidio",
    "WEAPONS VIOLATION": "Violencia armada y homicidio",
    "BATTERY": "Agresión y violencia personal",
    "ASSAULT": "Agresión y violencia personal",
    "CRIM SEXUAL ASSAULT": "Agresión y violencia personal",
    "OFFENSE INVOLVING CHILDREN": "Agresión y violencia personal",
    "ROBBERY": "Robo con fuerza y allanamiento",
    "BURGLARY": "Robo con fuerza y allanamiento",
    "THEFT": "Hurto y sustracción patrimonial",
    "MOTOR VEHICLE THEFT": "Hurto y sustracción patrimonial",
    "DECEPTIVE PRACTICE": "Fraude y engaño financiero",
    "NARCOTICS": "Narcóticos y orden público",
    "CRIMINAL DAMAGE": "Narcóticos y orden público",
    "CRIMINAL TRESPASS": "Narcóticos y orden público",
    "PUBLIC PEACE VIOLATION": "Narcóticos y orden público",
    "OTHER OFFENSE": "Narcóticos y orden público"
}

# Categorías estándar para Bolivia
BOLIVIA_CRIME_CATEGORIES = [
    "Robo agravado y asalto",
    "Agresión física y lesiones",
    "Homicidio y asesinato",
    "Hurto y descuidismo",
    "Narcotráfico y sustancias",
    "Delitos financieros y estafas"
]


def align_clusters(ref_labels, cand_labels):
    """Alinea las etiquetas del clúster candidato con las de referencia mediante el algoritmo húngaro."""
    unique_ref = np.unique(ref_labels)
    unique_cand = np.unique(cand_labels)
    n_clusters = max(len(unique_ref), len(unique_cand))
    
    contingency = np.zeros((n_clusters, n_clusters), dtype=int)
    for r, c in zip(ref_labels, cand_labels):
        contingency[r - 1, c - 1] += 1
        
    row_ind, col_ind = linear_sum_assignment(-contingency)
    mapping = {col + 1: row + 1 for row, col in zip(row_ind, col_ind)}
    aligned = np.array([mapping.get(c, c) for c in cand_labels])
    return aligned


def bootstrap_chicago_taxonomy(df_chi, B=200, k=3, seed=42):
    """Ejecuta bootstrap remuestreando eventos dentro de cada uno de los 22 distritos policiales de Chicago."""
    rng = np.random.RandomState(seed)
    districts = sorted([d for d in df_chi["District"].unique() if d != 31 and d in range(1, 26)])
    categories = sorted(list(set(CHICAGO_CRIME_CATEGORIES.values())))

    # 1. Perfiles base de referencia
    df_chi_valid = df_chi[df_chi["District"].isin(districts)].copy()
    df_chi_valid["cat"] = df_chi_valid["Primary Type"].map(CHICAGO_CRIME_CATEGORIES).fillna("Narcóticos y orden público")
    
    base_ct = pd.crosstab(df_chi_valid["District"], df_chi_valid["cat"])
    # Reindexar columnas para orden determinista
    base_ct = base_ct.reindex(columns=categories, fill_value=0)
    base_prop = base_ct.div(base_ct.sum(axis=1), axis=0).values

    # Hellinger
    base_hel = np.sqrt(base_prop)
    Z_base = linkage(pdist(base_hel, metric="euclidean"), method="ward")
    ref_labels = fcluster(Z_base, t=k, criterion="maxclust")

    # Guardar eventos discretos por distrito para muestreo multinomial
    district_counts = base_ct.values
    district_totals = base_ct.sum(axis=1).values

    ari_list = []
    unit_consistent_counts = np.zeros(len(districts), dtype=int)

    for b in range(B):
        boot_props = np.zeros_like(base_prop)
        for i in range(len(districts)):
            p_i = base_prop[i]
            n_i = district_totals[i]
            # Muestreo multinomial con reemplazo
            sampled_counts = rng.multinomial(n_i, p_i)
            boot_props[i] = sampled_counts / n_i

        boot_hel = np.sqrt(boot_props)
        Z_boot = linkage(pdist(boot_hel, metric="euclidean"), method="ward")
        boot_labels = fcluster(Z_boot, t=k, criterion="maxclust")

        ari = adjusted_rand_score(ref_labels, boot_labels)
        ari_list.append(round(float(ari), 4))

        aligned_boot = align_clusters(ref_labels, boot_labels)
        for i in range(len(districts)):
            if aligned_boot[i] == ref_labels[i]:
                unit_consistent_counts[i] += 1

    mean_ari = round(float(np.mean(ari_list)), 3)
    ci_lower = round(float(np.percentile(ari_list, 2.5)), 3)
    ci_upper = round(float(np.percentile(ari_list, 97.5)), 3)

    unit_stability = {}
    for i, dist in enumerate(districts):
        pct = round((unit_consistent_counts[i] / B) * 100.0, 1)
        unit_stability[str(dist)] = {
            "district_id": int(dist),
            "district_name": f"Distrito {dist}",
            "ref_cluster": int(ref_labels[i]),
            "stability_pct": pct,
            "total_events": int(district_totals[i])
        }

    return {
        "ctx": "chicago",
        "units_count": len(districts),
        "total_events": int(df_chi_valid.shape[0]),
        "years_range": "2024-2025",
        "optimal_k": k,
        "linkage": "ward",
        "transformation": "hellinger_sqrt",
        "mean_ari": mean_ari,
        "ci_95": [ci_lower, ci_upper],
        "units": unit_stability,
        "categories": categories
    }


def bootstrap_bolivia_taxonomy(df_bo, B=200, k=3, seed=42):
    """Ejecuta bootstrap para Bolivia sobre las zonas con n >= 3 crónicas de prensa."""
    rng = np.random.RandomState(seed)
    zona_counts = df_bo["zona_principal"].value_counts()
    valid_zonas = sorted(zona_counts[zona_counts >= 3].index.tolist())
    df_sub = df_bo[df_bo["zona_principal"].isin(valid_zonas)].copy()

    # Mapeo a categorías estándar
    def map_bo_delito(d):
        d_lower = str(d).lower()
        if "robo" in d_lower or "asalto" in d_lower or "atraco" in d_lower:
            return "Robo agravado y asalto"
        if "agresi" in d_lower or "lesion" in d_lower or "riña" in d_lower:
            return "Agresión física y lesiones"
        if "homicid" in d_lower or "asesinat" in d_lower:
            return "Homicidio y asesinato"
        if "hurto" in d_lower or "descuid" in d_lower:
            return "Hurto y descuidismo"
        if "narcot" in d_lower or "droga" in d_lower:
            return "Narcotráfico y sustancias"
        return "Delitos financieros y estafas"

    df_sub["cat"] = df_sub["delito_principal"].apply(map_bo_delito)
    categories = BOLIVIA_CRIME_CATEGORIES

    base_ct = pd.crosstab(df_sub["zona_principal"], df_sub["cat"])
    base_ct = base_ct.reindex(columns=categories, fill_value=0)
    base_prop = base_ct.div(base_ct.sum(axis=1), axis=0).values

    base_hel = np.sqrt(base_prop)
    Z_base = linkage(pdist(base_hel, metric="euclidean"), method="ward")
    ref_labels = fcluster(Z_base, t=k, criterion="maxclust")

    zone_totals = base_ct.sum(axis=1).values
    ari_list = []
    unit_consistent_counts = np.zeros(len(valid_zonas), dtype=int)

    for b in range(B):
        boot_props = np.zeros_like(base_prop)
        for i in range(len(valid_zonas)):
            p_i = base_prop[i]
            n_i = zone_totals[i]
            sampled_counts = rng.multinomial(n_i, p_i)
            boot_props[i] = sampled_counts / n_i

        boot_hel = np.sqrt(boot_props)
        Z_boot = linkage(pdist(boot_hel, metric="euclidean"), method="ward")
        boot_labels = fcluster(Z_boot, t=k, criterion="maxclust")

        ari = adjusted_rand_score(ref_labels, boot_labels)
        ari_list.append(round(float(ari), 4))

        aligned_boot = align_clusters(ref_labels, boot_labels)
        for i in range(len(valid_zonas)):
            if aligned_boot[i] == ref_labels[i]:
                unit_consistent_counts[i] += 1

    mean_ari = round(float(np.mean(ari_list)), 3)
    ci_lower = round(float(np.percentile(ari_list, 2.5)), 3)
    ci_upper = round(float(np.percentile(ari_list, 97.5)), 3)

    unit_stability = {}
    for i, z in enumerate(valid_zonas):
        pct = round((unit_consistent_counts[i] / B) * 100.0, 1)
        unit_stability[z] = {
            "zone_name": z,
            "ref_cluster": int(ref_labels[i]),
            "stability_pct": pct,
            "total_crónicas": int(zone_totals[i])
        }

    excluded_zonas = zona_counts[zona_counts < 3].to_dict()

    return {
        "ctx": "bolivia",
        "units_count": len(valid_zonas),
        "total_events": int(df_sub.shape[0]),
        "total_corpus_crónicas": int(len(df_bo)),
        "optimal_k": k,
        "linkage": "ward",
        "transformation": "hellinger_sqrt",
        "mean_ari": mean_ari,
        "ci_95": [ci_lower, ci_upper],
        "units": unit_stability,
        "excluded_units": excluded_zonas,
        "categories": categories
    }


def main():
    parser = argparse.ArgumentParser(description="Precalcular estabilidad bootstrap para taxonomía jerárquica.")
    parser.add_argument("--chi-input", default="data/chicago_benchmark/silver/chicago_crimes_curated.parquet")
    parser.add_argument("--bo-input", default="data/bolivia_news/gold/dashboard_eventos_clusters_bolivia.csv")
    parser.add_argument("--chi-output", default="data/chicago_benchmark/gold/chicago_taxonomy_stability.json")
    parser.add_argument("--bo-output", default="data/bolivia_news/gold/bolivia_taxonomy_stability.json")
    parser.add_argument("--B", type=int, default=200, help="Número de réplicas bootstrap")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria fija")
    args = parser.parse_args()

    with open(__file__, "rb") as f:
        script_sha256 = hashlib.sha256(f.read()).hexdigest()

    print("=" * 80)
    print("PRECÁLCULO DE ESTABILIDAD BOOTSTRAP DE TAXONOMÍA (B=200)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Script SHA-256: {script_sha256}")
    print(f"Versión: {SCRIPT_VERSION}")
    print(f"Semilla aleatoria: {args.seed}")
    print(f"Réplicas B: {args.B}")
    print("-" * 80)

    # 1. Chicago
    if os.path.exists(args.chi_input):
        print("\n1. Procesando Chicago CPD (2024-2025)...")
        df_chi = pd.read_parquet(args.chi_input, columns=["District", "Primary Type", "Year"])
        df_chi_recent = df_chi[df_chi["Year"] >= 2024]
        res_chi = bootstrap_chicago_taxonomy(df_chi_recent, B=args.B, k=3, seed=args.seed)
        res_chi["script_version"] = SCRIPT_VERSION
        res_chi["script_sha256"] = script_sha256
        res_chi["random_seed"] = args.seed
        res_chi["bootstrap_B"] = args.B
        res_chi["generated_at"] = datetime.now().isoformat()

        os.makedirs(os.path.dirname(args.chi_output), exist_ok=True)
        with open(args.chi_output, "w", encoding="utf-8") as f:
            json.dump(res_chi, f, indent=2, ensure_ascii=False)
        print(f"   [OK] Chicago guardado en {args.chi_output}")
        print(f"   ARI medio: {res_chi['mean_ari']} (IC 95%: {res_chi['ci_95']})")

    # 2. Bolivia
    if os.path.exists(args.bo_input):
        print("\n2. Procesando Bolivia Prensa (zonas n >= 3)...")
        df_bo = pd.read_csv(args.bo_input)
        res_bo = bootstrap_bolivia_taxonomy(df_bo, B=args.B, k=3, seed=args.seed)
        res_bo["script_version"] = SCRIPT_VERSION
        res_bo["script_sha256"] = script_sha256
        res_bo["random_seed"] = args.seed
        res_bo["bootstrap_B"] = args.B
        res_bo["generated_at"] = datetime.now().isoformat()

        os.makedirs(os.path.dirname(args.bo_output), exist_ok=True)
        with open(args.bo_output, "w", encoding="utf-8") as f:
            json.dump(res_bo, f, indent=2, ensure_ascii=False)
        print(f"   [OK] Bolivia guardado en {args.bo_output}")
        print(f"   ARI medio: {res_bo['mean_ari']} (IC 95%: {res_bo['ci_95']})")

    print("\n" + "=" * 80)
    print("ESTABILIDAD DE TAXONOMÍA PRECALCULADA EXITOSAMENTE.")
    print("=" * 80)


if __name__ == "__main__":
    main()

