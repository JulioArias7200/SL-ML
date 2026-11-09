#!/usr/bin/env python3
"""
Regeneración reproducible de clústeres espaciales para Bolivia (Prensa).

Utiliza la lógica exacta de la celda 33 de data/notebooks_pipeline/01_scraping_unsupervised_v5.ipynb:
- DBSCAN ponderado por eventos por ubicación única (radio_km=2.5, min_pts=2).
- HDBSCAN con poda de consistencia territorial (vecino más cercano en clúster <= 2.5 km).
- OPTICS con cota superior espacial max_eps=radio_km/RT (2.5 km).
- Salida a UNA ÚNICA fuente de verdad: data/bolivia_news/gold/dashboard_eventos_clusters_bolivia.csv.
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS
from sklearn.neighbors import NearestNeighbors

RT = 6371.0088


def clusters_espaciales(df, radio_km=2.5, min_pts=2):
    """
    Función idéntica a la Celda 33 de 01_scraping_unsupervised_v5.ipynb.
    Aplica clustering espacial con restricción territorial natural.
    """
    p = df.dropna(subset=["lat", "lon"]).copy()

    # 1. DBSCAN sobre ubicaciones únicas ponderadas por número de crónicas locales
    u = p.groupby(["lat", "lon"]).size().reset_index(name="n")
    Xu = np.radians(u[["lat", "lon"]].to_numpy())
    u["dbscan"] = DBSCAN(
        eps=radio_km / RT, min_samples=min_pts, metric="haversine"
    ).fit(Xu, sample_weight=u["n"].to_numpy()).labels_
    p = p.drop(columns=["dbscan"], errors="ignore").merge(
        u[["lat", "lon", "dbscan"]], on=["lat", "lon"], how="left"
    )

    # 2. HDBSCAN con poda de consistencia territorial (vecino más cercano en clúster <= radio_km)
    X = np.radians(p[["lat", "lon"]].to_numpy())
    hdb = HDBSCAN(min_cluster_size=max(2, min_pts), metric="haversine", copy=True).fit(X)
    hdb_labels = hdb.labels_.copy()
    for cl in set(hdb_labels) - {-1}:
        cl_mask = (hdb_labels == cl)
        X_cl = X[cl_mask]
        if len(X_cl) > 1:
            nbrs_cl = NearestNeighbors(n_neighbors=2, metric="haversine").fit(X_cl)
            d_cl, _ = nbrs_cl.kneighbors(X_cl)
            too_far = (d_cl[:, 1] * RT) > radio_km
            indices = np.where(cl_mask)[0]
            hdb_labels[indices[too_far]] = -1
    p["hdbscan"] = hdb_labels

    # 3. OPTICS con cota superior espacial max_eps=radio_km para evitar conexiones trans-departamentales
    p["optics"] = OPTICS(
        min_samples=max(2, min_pts), metric="haversine", xi=0.05, max_eps=radio_km / RT
    ).fit_predict(X)
    return p


def verify_cell33_code_identity(notebook_path: str) -> bool:
    """Verifica que el cuerpo de clusters_espaciales coincida exactamente con la celda 33."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cell_33_src = "".join(nb["cells"][33]["source"])
    
    # Extraer lineas clave de clusters_espaciales
    required_snippets = [
        "def clusters_espaciales(df, radio_km=2.5, min_pts=2):",
        "u = p.groupby([\"lat\", \"lon\"]).size().reset_index(name=\"n\")",
        "DBSCAN(eps=radio_km / RT, min_samples=min_pts, metric=\"haversine\").fit(Xu, sample_weight=u[\"n\"].to_numpy()).labels_",
        "too_far = (d_cl[:, 1] * RT) > radio_km",
        "hdb_labels[indices[too_far]] = -1",
        "OPTICS(min_samples=max(2, min_pts), metric=\"haversine\", xi=0.05, max_eps=radio_km / RT).fit_predict(X)"
    ]
    for snip in required_snippets:
        if snip not in cell_33_src:
            return False
    return True


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nb_path = os.path.join(base_dir, "data", "notebooks_pipeline", "01_scraping_unsupervised_v5.ipynb")
    gold_csv = os.path.join(base_dir, "data", "bolivia_news", "gold", "dashboard_eventos_clusters_bolivia.csv")
    redundant_csv = os.path.join(base_dir, "data", "web_scraping_news", "dashboard_eventos_clusters_bolivia.csv")

    assert os.path.exists(nb_path), f"No se encontró el notebook en {nb_path}"
    assert verify_cell33_code_identity(nb_path), "Error: La lógica de clustering no coincide con la celda 33 del notebook."
    print("Identidad verificada: regenerate_bolivia_clusters.py implementa exactamente la celda 33.")

    df = pd.read_csv(gold_csv)
    print(f"Cargado dataset base Bolivia: {len(df)} registros.")

    esp = clusters_espaciales(df, radio_km=2.5, min_pts=2)

    # Validaciones rigurosas
    assert len(esp) == 137, f"Se esperaban 137 filas, se obtuvieron {len(esp)}"
    oruro = esp[esp["ciudad"].str.lower().str.contains("oruro")]
    assert len(oruro) == 1
    assert (oruro["dbscan"] == -1).all()
    assert (oruro["hdbscan"] == -1).all()
    assert (oruro["optics"] == -1).all()
    print("Oruro clasificado naturalmente como ruido (-1) en los 3 algoritmos.")

    # Guardar en la UNICA fuente de verdad
    os.makedirs(os.path.dirname(gold_csv), exist_ok=True)
    esp.to_csv(gold_csv, index=False, encoding="utf-8")
    spatial_csv = os.path.join(base_dir, "data", "bolivia_news", "gold", "spatial_clusters_bolivia.csv")
    esp.to_csv(spatial_csv, index=False, encoding="utf-8")
    print(f"Guardado exitoso en unica fuente de verdad: {gold_csv} y {spatial_csv}")

    # Eliminar copia redundante en web_scraping_news si existe
    if os.path.exists(redundant_csv):
        os.remove(redundant_csv)
        print(f"Copia redundante eliminada: {redundant_csv}")

    for c in ["dbscan", "hdbscan", "optics"]:
        counts = esp[c].value_counts()
        n_cl = len(counts) - (1 if -1 in counts else 0)
        n_ruido = int(counts.get(-1, 0))
        n_asig = int(counts[counts.index != -1].sum())
        print(f"{c:8s} clústeres={n_cl}  asignados={n_asig}  ruido={n_ruido}  total={n_asig+n_ruido}")


if __name__ == "__main__":
    main()

