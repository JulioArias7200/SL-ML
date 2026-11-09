import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

df = pd.read_csv('data/web_scraping_news/dashboard_eventos_clusters_bolivia.csv')
p = df.dropna(subset=['lat', 'lon']).copy()
RT = 6371.0088

# 1. Version Ponderada por n (la del notebook v5: eps=2.5km, min_samples=2)
u = p.groupby(['lat', 'lon']).size().reset_index(name='n')
Xu = np.radians(u[['lat', 'lon']].to_numpy())
db_weighted = DBSCAN(eps=2.5 / RT, min_samples=2, metric='haversine').fit(Xu, sample_weight=u['n'].to_numpy())
u['cluster_weighted'] = db_weighted.labels_
p_w = p.merge(u[['lat', 'lon', 'cluster_weighted']], on=['lat', 'lon'], how='left')

# 2. Version Sin Pesos sobre puntos unicos (eps=2.5km, min_samples=2)
db_unweighted_u = DBSCAN(eps=2.5 / RT, min_samples=2, metric='haversine').fit(Xu)
u['cluster_unweighted'] = db_unweighted_u.labels_
p_unw = p.merge(u[['lat', 'lon', 'cluster_unweighted']], on=['lat', 'lon'], how='left')

# 3. Version Sin Pesos directamente sobre los 60 puntos (eps=2.5km, min_samples=2)
X60 = np.radians(p[['lat', 'lon']].to_numpy())
db_direct60 = DBSCAN(eps=2.5 / RT, min_samples=2, metric='haversine').fit(X60)
p['cluster_direct60'] = db_direct60.labels_

print('=' * 80)
print('RECALCULO PUNTO 4B: DEPENDENCIAS DE DUPLICADOS Y COMPARACION PONDERADA VS SIN PESOS')
print('=' * 80)

print('\n--- 1. MODELO PONDERADO (Notebook v5: eps=2.5km, min_samples=2, sample_weight=n) ---')
total_assigned_w = 0
for c_id in sorted(p_w['cluster_weighted'].unique()):
    grp = p_w[p_w['cluster_weighted'] == c_id]
    n_pts = len(grp)
    n_unique = len(grp[['lat', 'lon']].drop_duplicates())
    if c_id != -1:
        total_assigned_w += n_pts
    pct_dup = ((n_pts - n_unique) / n_pts * 100) if n_pts > 0 else 0
    ciudades = grp['ciudad'].unique().tolist()
    print(f'Cluster {c_id:>2}: {n_pts:>2} puntos totales | {n_unique:>2} coords unicas | Dep. duplicados: {pct_dup:>5.1f}% | Ciudades: {ciudades}')
print(f'Suma puntos asignados a clusters: {total_assigned_w} | Ruido (-1): {(p_w["cluster_weighted"] == -1).sum()} | Total: {len(p_w)}')

print('\n--- 2. MODELO SIN PESOS SOBRE COORDENADAS UNICAS (25 ubicaciones unicas, sin ponderar) ---')
total_assigned_unw = 0
for c_id in sorted(u['cluster_unweighted'].unique()):
    grp_u = u[u['cluster_unweighted'] == c_id]
    n_unique = len(grp_u)
    represented_pts = int(grp_u['n'].sum())
    if c_id != -1:
        total_assigned_unw += represented_pts
    print(f'Cluster {c_id:>2}: {n_unique:>2} coords unicas | {represented_pts:>2} eventos representados')
noise_rep = int(u[u['cluster_unweighted'] == -1]['n'].sum())
print(f'Suma eventos representados en clusters: {total_assigned_unw} | Ruido representados: {noise_rep} | Total: {total_assigned_unw + noise_rep}')

print('\n--- 3. MODELO DIRECTO SOBRE 60 PUNTOS (eps=2.5km, min_samples=2 sin colapsar coords) ---')
total_direct = 0
for c_id in sorted(p['cluster_direct60'].unique()):
    grp = p[p['cluster_direct60'] == c_id]
    n_pts = len(grp)
    n_unique = len(grp[['lat', 'lon']].drop_duplicates())
    if c_id != -1:
        total_direct += n_pts
    pct_dup = ((n_pts - n_unique) / n_pts * 100) if n_pts > 0 else 0
    ciudades = grp['ciudad'].unique().tolist()
    print(f'Cluster {c_id:>2}: {n_pts:>2} puntos | {n_unique:>2} coords unicas | Dep. duplicados: {pct_dup:>5.1f}% | Ciudades: {ciudades}')
print(f'Suma puntos asignados a clusters: {total_direct} | Ruido (-1): {(p["cluster_direct60"] == -1).sum()} | Total: {len(p)}')

