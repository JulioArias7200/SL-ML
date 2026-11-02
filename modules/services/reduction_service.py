import os
import json
import pandas as pd

class ReductionService:
    _embeddings_cache = None
    _eventos_cache = None

    BOLIVIA_WARD_META = {
        'Santa Cruz': {'macro': 'Macro A', 'label': 'Macro A: Casco SCZ (Crítico)', 'color': '#ff3366'},
        'Cochabamba': {'macro': 'Macro B', 'label': 'Macro B: CBBA & Plan 3000 (Violencia)', 'color': '#fbbf24'},
        'Plan 3000': {'macro': 'Macro B', 'label': 'Macro B: CBBA & Plan 3000 (Violencia)', 'color': '#fbbf24'},
        'Equipetrol': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'La Paz': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'Los Lotes': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'Pampa de la Isla': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
    }

    LDA_TOPICS_META = {
        0: {"label": "Tópico #0: Agresiones y Conflictos", "color": "#ff3366"},
        1: {"label": "Tópico #1: Litigios y Estafas", "color": "#9d4edd"},
        2: {"label": "Tópico #2: Narcotráfico e Incautaciones", "color": "#34d399"},
        3: {"label": "Tópico #3: Atracos y Motochorros", "color": "#fbbf24"},
        4: {"label": "Tópico #4: Hurtos y Descuidismo", "color": "#00e5ff"}
    }

    @classmethod
    def _load(cls):
        if cls._embeddings_cache is not None:
            return cls._embeddings_cache
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        gold_fp = os.path.join(base_dir, 'data', 'bolivia_news', 'gold', 'reduction_embeddings.json')
        legacy_fp = os.path.join(base_dir, 'data', 'web_scraping_news', 'reduction_embeddings.json')
        fp = gold_fp if os.path.exists(gold_fp) else legacy_fp
        
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                cls._embeddings_cache = json.load(f)
        else:
            cls._embeddings_cache = {"points": [], "pca": {}, "svd": {}, "ppca": {}, "tsne": {}, "umap": {}}
        return cls._embeddings_cache

    @classmethod
    def _load_eventos(cls):
        if cls._eventos_cache is not None:
            return cls._eventos_cache
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        for p in [
            os.path.join(base_dir, 'data', 'bolivia_news', 'bronze', 'eventos_bolivia_raw.csv'),
            os.path.join(base_dir, 'data', 'web_scraping_news', 'eventos_bolivia.csv'),
        ]:
            if os.path.exists(p):
                try:
                    cls._eventos_cache = pd.read_csv(p)
                    return cls._eventos_cache
                except Exception:
                    pass
        return None

    @classmethod
    def get_algorithm_data(cls, algo_name="pca"):
        data = cls._load()
        algo_name = algo_name.lower()
        if algo_name not in ["pca", "svd", "ppca", "tsne", "umap"]:
            algo_name = "pca"

        algo_info = data.get(algo_name, {})
        coords = algo_info.get("coords", [])
        points = data.get("points", [])
        df_eventos = cls._load_eventos()

        # Combinar coordenadas 2D con metadatos del punto y clustering jerárquico Ward
        series = []
        for i, pt in enumerate(points):
            c = coords[i] if i < len(coords) else [0, 0]
            zona = ""
            if df_eventos is not None and i < len(df_eventos):
                row = df_eventos.iloc[i]
                zona = str(row['zona_principal']) if pd.notnull(row.get('zona_principal')) else ""
            
            ciudad = str(pt.get("city", ""))
            
            # Determinación de Macro-Cluster Jerárquico Ward (k=3)
            if zona in cls.BOLIVIA_WARD_META:
                ward_info = cls.BOLIVIA_WARD_META[zona]
            elif "santa cruz" in ciudad.lower():
                ward_info = cls.BOLIVIA_WARD_META['Santa Cruz']
            elif "cochabamba" in ciudad.lower():
                ward_info = cls.BOLIVIA_WARD_META['Cochabamba']
            else:
                ward_info = cls.BOLIVIA_WARD_META['La Paz']

            topic_id = int(pt.get("topic", 0))
            topic_info = cls.LDA_TOPICS_META.get(topic_id, {"label": f"Tópico #{topic_id}", "color": "#00e5ff"})

            series.append({
                "x": c[0],
                "y": c[1],
                "id": pt["id"],
                "title": pt["title"],
                "category": pt["category"],
                "city": ciudad,
                "zone": zona if zona else ciudad,
                "topic": topic_id,
                "topic_label": topic_info["label"],
                "topic_color": topic_info["color"],
                "is_anomaly": pt["is_anomaly"],
                "reconstruction_error": pt["reconstruction_error"],
                "ward_macro": ward_info["macro"],
                "ward_label": ward_info["label"],
                "ward_color": ward_info["color"]
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
