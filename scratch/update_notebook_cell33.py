import json

nb_path = "data/notebooks_pipeline/01_scraping_unsupervised_v5.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

cell_source = '''if ZONAS_OK:
    from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS
    from sklearn.neighbors import NearestNeighbors
    RT = 6371.0088

    def clusters_espaciales(df, radio_km=2.5, min_pts=2):
        p = df.dropna(subset=["lat", "lon"]).copy()
        
        # 1. DBSCAN sobre ubicaciones únicas ponderadas por número de crónicas locales
        u = p.groupby(["lat", "lon"]).size().reset_index(name="n")
        Xu = np.radians(u[["lat", "lon"]].to_numpy())
        u["dbscan"] = DBSCAN(eps=radio_km / RT, min_samples=min_pts, metric="haversine").fit(Xu, sample_weight=u["n"].to_numpy()).labels_
        p = p.drop(columns=["dbscan"], errors="ignore").merge(u[["lat", "lon", "dbscan"]], on=["lat", "lon"], how="left")
        
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
        p["optics"] = OPTICS(min_samples=max(2, min_pts), metric="haversine", xi=0.05, max_eps=radio_km / RT).fit_predict(X)
        return p

    esp = clusters_espaciales(df, radio_km=2.5, min_pts=2)
    for c in ["dbscan", "hdbscan", "optics"]:
        n_clusters = len(set(esp[c])) - (1 if -1 in set(esp[c]) else 0)
        n_ruido = int((esp[c] == -1).sum())
        print(f"{c:8s} clusters={n_clusters}  ruido={n_ruido}")
    display(esp[["ciudad", "zona_principal", "delito_principal", "dbscan", "hdbscan", "optics"]].head(15))
else:
    print("Sección omitida: faltan eventos georreferenciados.")'''

nb["cells"][33]["source"] = [line + "\n" for line in cell_source.split("\n")]
if nb["cells"][33]["source"]:
    nb["cells"][33]["source"][-1] = nb["cells"][33]["source"][-1].rstrip("\n")

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Updated cell 33 successfully in notebook.")

