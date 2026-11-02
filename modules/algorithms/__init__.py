"""
CPD ANALYTICS CORE // MÓDULO DE ALGORITMOS NO SUPERVISADOS
Estandarización de técnicas del curso de Machine Learning No Supervisado (Octubre 2026).
"""

from .spatial_density import run_spatial_density
from .dimensionality import compute_embeddings_2d
from .topic_modeling import train_lda_topics
from .anomaly_autoencoder import detect_anomalies_autoencoder
from .clustering_classic import compute_kmeans_metrics, run_hierarchical_ward

__all__ = [
    'run_spatial_density',
    'compute_embeddings_2d',
    'train_lda_topics',
    'detect_anomalies_autoencoder',
    'compute_kmeans_metrics',
    'run_hierarchical_ward'
]

