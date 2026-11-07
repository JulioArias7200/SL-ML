"""
CLUSTERING CLÁSICO // K-MEANS & CLUSTERING JERÁRQUICO AGLOMERATIVO (WARD)
Métricas de evaluación: Inercia (WSS), Silueta y Dendrograma.
"""
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score

def compute_kmeans_metrics(X_data, k_range=range(2, 11), random_state=42):
    """
    Evalúa múltiples valores de k calculando Inercia (WSS), Silueta y Davies-Bouldin.
    Retorna un diccionario estructurado por cada k.
    """
    metrics = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_data)
        sil = float(silhouette_score(X_data, labels))
        dbi = float(davies_bouldin_score(X_data, labels))
        metrics[k] = {
            'k': k,
            'wss': round(float(km.inertia_), 2),
            'sil': round(sil, 3),
            'dbi': round(dbi, 2)
        }
    return metrics

def run_hierarchical_ward(X_data, n_clusters=3):
    """
    Ejecuta Clustering Jerárquico Aglomerativo con enlace de mínima varianza (Ward).
    """
    agg = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    labels = agg.fit_predict(X_data)
    return labels, agg

