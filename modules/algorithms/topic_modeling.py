"""
MODELADO DE TÓPICOS // LATENT DIRICHLET ALLOCATION (LDA)
Descubrimiento de temáticas no supervisadas en texto periodístico.
"""
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

def train_lda_topics(corpus_textos, n_topics=5, max_features=250, random_state=42):
    """
    Entrena un modelo LDA sobre una lista de textos.
    Retorna (modelo_lda, vectorizador, matriz_topicos, top_words_por_topico).
    """
    vec = CountVectorizer(max_features=max_features, max_df=0.85, min_df=2)
    X = vec.fit_transform(corpus_textos)

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=random_state, max_iter=10, learning_method='online')
    topic_matrix = lda.fit_transform(X)

    vocab = vec.get_feature_names_out()
    top_words = {}
    for tid, comp in enumerate(lda.components_):
        top_idx = comp.argsort()[-10:][::-1]
        top_words[tid] = [vocab[i] for i in top_idx]

    return lda, vec, topic_matrix, top_words

