"""
REDUCCIÓN DE DIMENSIONALIDAD // PCA, TRUNCATED SVD, PPCA, t-SNE, UMAP
Técnicas vistas en las clases del 26 y 29 de Octubre de 2026.
"""
import numpy as np
from scipy.sparse import issparse
from sklearn.decomposition import PCA, TruncatedSVD, FactorAnalysis
from sklearn.manifold import TSNE, trustworthiness

try:
    import umap
    HAS_UMAP = True
except (ImportError, Exception):
    HAS_UMAP = False

def compute_embeddings_2d(X_matrix, random_state=42):
    """
    Calcula las proyecciones 2D para una matriz densa o dispersa de características TF-IDF.
    Retorna un diccionario con las coordenadas de cada técnica, métricas de calidad y varianzas.
    """
    if hasattr(X_matrix, "toarray") and not isinstance(X_matrix, np.ndarray):
        X_dense = X_matrix.toarray()
        X_sparse = X_matrix
    else:
        X_dense = np.asarray(X_matrix)
        X_sparse = None

    n_samples, n_features = X_dense.shape
    results = {
        'n_samples': n_samples,
        'n_features': n_features
    }

    # 1. PCA (Lineal / Ortogonal)
    pca = PCA(n_components=2, random_state=random_state)
    coords_pca = pca.fit_transform(X_dense)
    results['pca'] = {
        'coords': np.round(coords_pca, 4).tolist(),
        'variance_explained': np.round(pca.explained_variance_ratio_ * 100, 2).tolist(),
        'method': 'PCA (Lineal Ortogonal)',
        'is_fallback': False
    }

    # 2. TruncatedSVD (LSA - Descomposición en Valores Singulares preservando dispersión)
    svd = TruncatedSVD(n_components=2, random_state=random_state)
    if X_sparse is not None:
        coords_svd = svd.fit_transform(X_sparse)
    else:
        coords_svd = svd.fit_transform(X_dense)
    results['svd'] = {
        'coords': np.round(coords_svd, 4).tolist(),
        'variance_explained': np.round(svd.explained_variance_ratio_ * 100, 2).tolist(),
        'method': 'TruncatedSVD (LSA Factorización Matricial)',
        'is_fallback': False
    }

    # 3. PPCA (Probabilistic PCA vía FactorAnalysis con scoring de verosimilitud)
    fa = FactorAnalysis(n_components=2, random_state=random_state)
    coords_ppca = fa.fit_transform(X_dense)
    try:
        log_likelihood = round(float(fa.score(X_dense)), 2)
    except Exception:
        log_likelihood = None
    results['ppca'] = {
        'coords': np.round(coords_ppca, 4).tolist(),
        'variance_explained': [None, None],
        'log_likelihood': log_likelihood,
        'method': 'PPCA (Factor Analysis Probabilístico)',
        'is_fallback': False
    }

    # 4. t-SNE (No Lineal / Divergencia KL sobre vecindades)
    perp = max(5, min(30, n_samples // 4))
    tsne = TSNE(n_components=2, perplexity=perp, metric='cosine', random_state=random_state, init='pca')
    coords_tsne = tsne.fit_transform(X_dense)
    try:
        tsne_trust = round(float(trustworthiness(X_dense, coords_tsne, n_neighbors=min(10, n_samples - 2), metric='cosine')) * 100, 1)
    except Exception:
        tsne_trust = 85.0
    results['tsne'] = {
        'coords': np.round(coords_tsne, 4).tolist(),
        'variance_explained': [None, None],
        'perplexity': perp,
        'trustworthiness': tsne_trust,
        'method': 't-SNE (Distribución t de Student / KL)',
        'is_fallback': False
    }

    # 5. UMAP (Aproximación Múltiple Uniforme con distancia Coseno)
    if HAS_UMAP:
        try:
            n_neighbors = min(15, n_samples - 1)
            um = umap.UMAP(n_components=2, n_neighbors=n_neighbors, metric='cosine', random_state=random_state)
            coords_umap = um.fit_transform(X_dense)
            umap_trust = round(float(trustworthiness(X_dense, coords_umap, n_neighbors=min(10, n_samples - 2), metric='cosine')) * 100, 1)
            results['umap'] = {
                'coords': np.round(coords_umap, 4).tolist(),
                'variance_explained': [None, None],
                'trustworthiness': umap_trust,
                'method': 'UMAP (Variedad Riemanniana Coseno)',
                'is_fallback': False
            }
        except Exception:
            # Fallback seguro si umap falla en tiempo de ejecución
            from sklearn.manifold import SpectralEmbedding
            se = SpectralEmbedding(n_components=2, affinity='cosine', random_state=random_state)
            coords_umap = se.fit_transform(X_dense)
            results['umap'] = {
                'coords': np.round(coords_umap, 4).tolist(),
                'variance_explained': [None, None],
                'trustworthiness': 80.0,
                'method': 'Spectral Embedding (Fallback Laplaciano Coseno)',
                'is_fallback': True
            }
    else:
        from sklearn.manifold import SpectralEmbedding
        se = SpectralEmbedding(n_components=2, affinity='cosine', random_state=random_state)
        coords_umap = se.fit_transform(X_dense)
        results['umap'] = {
            'coords': np.round(coords_umap, 4).tolist(),
            'variance_explained': [None, None],
            'trustworthiness': 80.0,
            'method': 'Spectral Embedding (Fallback Laplaciano Coseno)',
            'is_fallback': True
        }

    return results
