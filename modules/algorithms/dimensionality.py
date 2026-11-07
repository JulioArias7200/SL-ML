"""
REDUCCIÓN DE DIMENSIONALIDAD // PCA, TRUNCATED SVD, PPCA, t-SNE, UMAP
Técnicas vistas en las clases del 26 y 29 de Octubre de 2026.
"""
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD, FactorAnalysis
from sklearn.manifold import TSNE

try:
    import umap
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

def compute_embeddings_2d(X_matrix, random_state=42):
    """
    Calcula las proyecciones 2D para una matriz densa o dispersa de características TF-IDF.
    Retorna un diccionario con las coordenadas de cada técnica y varianzas explicadas.
    """
    if hasattr(X_matrix, "toarray"):
        X_dense = X_matrix.toarray()
    else:
        X_dense = np.asarray(X_matrix)

    n_samples, n_features = X_dense.shape
    results = {}

    # 1. PCA (Lineal / Ortogonal)
    pca = PCA(n_components=2, random_state=random_state)
    coords_pca = pca.fit_transform(X_dense)
    results['pca'] = {
        'coords': np.round(coords_pca, 4).tolist(),
        'variance_explained': np.round(pca.explained_variance_ratio_ * 100, 2).tolist()
    }

    # 2. TruncatedSVD (Descomposición en Valores Singulares)
    svd = TruncatedSVD(n_components=2, random_state=random_state)
    coords_svd = svd.fit_transform(X_dense)
    results['svd'] = {
        'coords': np.round(coords_svd, 4).tolist(),
        'variance_explained': np.round(svd.explained_variance_ratio_ * 100, 2).tolist()
    }

    # 3. PPCA (Probabilistic PCA vía FactorAnalysis)
    fa = FactorAnalysis(n_components=2, random_state=random_state)
    coords_ppca = fa.fit_transform(X_dense)
    results['ppca'] = {
        'coords': np.round(coords_ppca, 4).tolist(),
        'variance_explained': [None, None]
    }

    # 4. t-SNE (No Lineal / Distribución t de Student)
    perp = max(5, min(30, n_samples // 4))
    tsne = TSNE(n_components=2, perplexity=perp, random_state=random_state, init='pca')
    coords_tsne = tsne.fit_transform(X_dense)
    results['tsne'] = {
        'coords': np.round(coords_tsne, 4).tolist(),
        'variance_explained': [None, None]
    }

    # 5. UMAP (Aproximación Múltiple Uniforme)
    if HAS_UMAP:
        um = umap.UMAP(n_components=2, n_neighbors=min(15, n_samples - 1), random_state=random_state)
        coords_umap = um.fit_transform(X_dense)
    else:
        from sklearn.manifold import SpectralEmbedding
        se = SpectralEmbedding(n_components=2, random_state=random_state)
        coords_umap = se.fit_transform(X_dense)

    results['umap'] = {
        'coords': np.round(coords_umap, 4).tolist(),
        'variance_explained': [None, None]
    }

    return results

