"""
DENSIDAD ESPACIAL // DBSCAN, HDBSCAN, OPTICS
Métrica Haversine esférica sobre coordenadas latitud/longitud en radianes.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, OPTICS

try:
    from sklearn.cluster import HDBSCAN
    HAS_HDBSCAN = True
except ImportError:
    HAS_HDBSCAN = False

RADIO_TIERRA_KM = 6371.0088

def run_spatial_density(df_points, radio_km=2.5, min_pts=2):
    """
    Ejecuta DBSCAN, HDBSCAN y OPTICS sobre un DataFrame con columnas 'lat' y 'lon'.
    Retorna el DataFrame con columnas ['dbscan', 'hdbscan', 'optics'].
    """
    p = df_points.dropna(subset=['lat', 'lon']).copy()
    if len(p) == 0:
        return p

    # Puntos únicos agrupados para evitar degeneración en duplicados exactos
    u = p.groupby(['lat', 'lon']).size().reset_index(name='n')
    xu = np.radians(u[['lat', 'lon']].to_numpy())

    # 1. DBSCAN con Haversine
    eps_rad = radio_km / RADIO_TIERRA_KM
    db = DBSCAN(eps=eps_rad, min_samples=min_pts, metric='haversine')
    u['dbscan'] = db.fit(xu, sample_weight=u['n'].to_numpy()).labels_

    # 2. HDBSCAN
    if HAS_HDBSCAN:
        hdb = HDBSCAN(min_cluster_size=min_pts, metric='haversine')
        u['hdbscan'] = hdb.fit(xu).labels_
    else:
        u['hdbscan'] = u['dbscan']

    # 3. OPTICS
    opt = OPTICS(min_samples=min_pts, metric='haversine')
    u['optics'] = opt.fit(xu).labels_

    # Merge de vuelta a los eventos originales
    resultado = p.merge(u[['lat', 'lon', 'dbscan', 'hdbscan', 'optics']], on=['lat', 'lon'], how='left')
    return resultado

