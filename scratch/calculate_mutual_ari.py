import json
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

# Test mutual ARI for Bolivia
df_bo = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')

def compute_aris(l1, l2):
    l1 = np.asarray(l1)
    l2 = np.asarray(l2)
    # Global ARI (including -1)
    ari_global = round(float(adjusted_rand_score(l1, l2)), 3)
    # Mutual clustered ARI (excluding points where either is -1)
    mask = (l1 != -1) & (l2 != -1)
    if mask.sum() > 2 and len(set(l1[mask])) > 1 and len(set(l2[mask])) > 1:
        ari_mutual = round(float(adjusted_rand_score(l1[mask], l2[mask])), 3)
    else:
        ari_mutual = None
    return ari_global, ari_mutual, int(mask.sum())

print("="*80)
print("BOLIVIA ARI: GLOBAL VS MUTUO (EXCLUYENDO RUIDO)")
print("="*80)
db_hdb_g, db_hdb_m, n_dh = compute_aris(df_bo['dbscan'], df_bo['hdbscan'])
db_opt_g, db_opt_m, n_do = compute_aris(df_bo['dbscan'], df_bo['optics'])
hdb_opt_g, hdb_opt_m, n_ho = compute_aris(df_bo['hdbscan'], df_bo['optics'])

print(f"DBSCAN vs HDBSCAN: Global = {db_hdb_g} | Mutuo ({n_dh} pts asignados por ambos) = {db_hdb_m}")
print(f"DBSCAN vs OPTICS:  Global = {db_opt_g} | Mutuo ({n_do} pts asignados por ambos) = {db_opt_m}")
print(f"HDBSCAN vs OPTICS: Global = {hdb_opt_g} | Mutuo ({n_ho} pts asignados por ambos) = {hdb_opt_m}")

