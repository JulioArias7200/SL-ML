import os
import json

class ReductionService:
    _embeddings_cache = None

    @classmethod
    def _load(cls):
        if cls._embeddings_cache is not None:
            return cls._embeddings_cache
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        fp = os.path.join(base_dir, 'data', 'web_scraping_news', 'reduction_embeddings.json')
        
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                cls._embeddings_cache = json.load(f)
        else:
            cls._embeddings_cache = {"points": [], "pca": {}, "svd": {}, "ppca": {}, "tsne": {}, "umap": {}}
        return cls._embeddings_cache

    @classmethod
    def get_algorithm_data(cls, algo_name="pca"):
        data = cls._load()
        algo_name = algo_name.lower()
        if algo_name not in ["pca", "svd", "ppca", "tsne", "umap"]:
            algo_name = "pca"

        algo_info = data.get(algo_name, {})
        coords = algo_info.get("coords", [])
        points = data.get("points", [])

        # Combinar coordenadas 2D con metadatos del punto
        series = []
        for i, pt in enumerate(points):
            c = coords[i] if i < len(coords) else [0, 0]
            series.append({
                "x": c[0],
                "y": c[1],
                "id": pt["id"],
                "title": pt["title"],
                "category": pt["category"],
                "city": pt["city"],
                "topic": pt["topic"],
                "is_anomaly": pt["is_anomaly"],
                "reconstruction_error": pt["reconstruction_error"]
            })

        return {
            "algorithm": algo_name,
            "meta": algo_info,
            "series": series,
            "available_algorithms": [
                {"id": "pca", "label": "PCA (Componentes Principales)", "class_date": "26-Oct"},
                {"id": "svd", "label": "TruncatedSVD (LSA Texto)", "class_date": "26-Oct"},
                {"id": "ppca", "label": "PPCA (Probabilistic PCA)", "class_date": "29-Oct"},
                {"id": "tsne", "label": "t-SNE (Variedad No Lineal)", "class_date": "29-Oct"},
                {"id": "umap", "label": "UMAP (Topología Simplicial)", "class_date": "29-Oct"}
            ]
        }

