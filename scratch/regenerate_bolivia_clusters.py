import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS
from sklearn.neighbors import NearestNeighbors

# Paths
gold_path = "data/bolivia_news/gold/dashboard_eventos_clusters_bolivia.csv"
web_path = "data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv"

df = pd.read_csv(gold_path)
print(f"Cargado dataset original: {df.shape[0]} filas, {df.shape[1]} columnas.")

# Limpiar columnas de clustering previas para un cálculo 100% puro
df_clean = df.drop(columns=["dbscan", "hdbscan", "optics"], errors="ignore").copy()

RT = 6371.0088
radio_km = 2.5
min_pts = 2

# 1. DBSCAN sobre ubicaciones únicas ponderadas por número de crónicas locales
u = df_clean.groupby(["lat", "lon"]).size().reset_index(name="n")
Xu = np.radians(u[["lat", "lon"]].to_numpy())
db = DBSCAN(eps=radio_km / RT, min_samples=min_pts, metric="haversine").fit(Xu, sample_weight=u["n"].to_numpy())
u["dbscan"] = db.labels_

df_result = df_clean.merge(u[["lat", "lon", "dbscan"]], on=["lat", "lon"], how="left")

# 2. HDBSCAN con poda territorial
X = np.radians(df_result[["lat", "lon"]].to_numpy())
hdb = HDBSCAN(min_cluster_size=min_pts, metric="haversine", copy=True).fit(X)
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

df_result["hdbscan"] = hdb_labels

# 3. OPTICS con max_eps = radio_km / RT
opt = OPTICS(min_samples=min_pts, metric="haversine", xi=0.05, max_eps=radio_km / RT).fit(X)
df_result["optics"] = opt.labels_

# Verificación de Oruro (debe ser naturalmente -1 en los 3 algoritmos sin intervención manual)
oruro_row = df_result[df_result["ciudad"].str.lower().str.contains("oruro")]
print("\n--- Verificación Oruro (fila 48) ---")
print(oruro_row[["ciudad", "zona_principal", "lat", "lon", "dbscan", "hdbscan", "optics"]])
assert (oruro_row["dbscan"] == -1).all(), "Oruro debe ser -1 en DBSCAN"
assert (oruro_row["hdbscan"] == -1).all(), "Oruro debe ser -1 en HDBSCAN"
assert (oruro_row["optics"] == -1).all(), "Oruro debe ser -1 en OPTICS"

print("\n--- Conteo de Clústeres y Ruido ---")
for col in ["dbscan", "hdbscan", "optics"]:
    n_cl = len(set(df_result[col]) - {-1})
    n_noise = int((df_result[col] == -1).sum())
    n_assigned = int((df_result[col] != -1).sum())
    print(f"{col:8s}: Clústeres = {n_cl}, Asignados = {n_assigned}, Ruido = {n_noise}, Total = {n_assigned + n_noise}")
    assert n_assigned + n_noise == 60, f"Suma de asignados + ruido debe ser 60 en {col}"

# Guardar en gold y web_scraping_news
df_result.to_csv(gold_path, index=False, encoding="utf-8")
df_result.to_csv(web_path, index=False, encoding="utf-8")
print(f"\nGuardado exitoso en {gold_path} y {web_path}.")

