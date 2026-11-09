import os
import json
import pandas as pd

class ReductionService:
    _embeddings_cache = None
    _eventos_cache = None
    _mtime_embeddings = 0

    # Metadatos teóricos, pedagógicos y matemáticos exactos por algoritmo
    ALGORITHMS_THEORY = {
        'pca': {
            'name': 'PCA (Análisis de Componentes Principales)',
            'type': 'Lineal / Ortogonal',
            'description': 'Maximiza la varianza proyectada en componentes ortogonales no correlacionados.',
            'formula_latex': r'X = U \Sigma V^T \implies Z = X V_k',
            'formula_display': 'X = U · Σ · V^T   →   Z = X · V_k'
        },
        'svd': {
            'name': 'TruncatedSVD (LSA - Latent Semantic Analysis)',
            'type': 'Factorización Matricial',
            'description': 'Factorización directa sobre la matriz dispersa término-documento preservando el espacio semántico latente.',
            'formula_latex': r'X \approx U_k \Sigma_k V_k^T',
            'formula_display': 'X ≈ U_k · Σ_k · V_k^T'
        },
        'ppca': {
            'name': 'PPCA (PCA Probabilístico / Factor Analysis)',
            'type': 'Generativo Probabilístico',
            'description': 'Modelo latente gaussiano que tolera valores faltantes y estima incertidumbre asociada a la proyección.',
            'formula_latex': r'x = W z + \mu + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \sigma^2 I)',
            'formula_display': 'x = W·z + μ + ε,    ε ~ N(0, σ²·I)'
        },
        'tsne': {
            'name': 't-SNE (t-Distributed Stochastic Neighbor Embedding)',
            'type': 'No Lineal / Estocástico',
            'description': 'Convierte distancias euclidianas en probabilidades y minimiza la divergencia Kullback-Leibler, separando nítidamente clusters locales.',
            'formula_latex': r'p_{j|i} = \frac{\exp(-\|x_i-x_j\|^2 / 2\sigma_i^2)}{\sum_{k \neq i} \exp(-\|x_i-x_k\|^2 / 2\sigma_i^2)}, \quad q_{ij} = \frac{(1+\|y_i-y_j\|^2)^{-1}}{\sum_k \sum_{l \neq k} (1+\|y_k-y_l\|^2)^{-1}}',
            'formula_display': 'p_{j|i} = exp(-||x_i - x_j||² / 2σ²) / Σ exp,    q_ij = (1 + ||y_i - y_j||²)⁻¹ / Σ (1 + ||y_k - y_l||²)⁻¹'
        },
        'umap': {
            'name': 'UMAP (Uniform Manifold Approximation and Projection)',
            'type': 'Topológico No Lineal',
            'description': 'Aproximación de variedades Riemannianas y conjuntos simpliciales difusos. Preserva tanto la estructura local como la global con alta velocidad.',
            'formula_latex': r'\mathcal{L} = \sum_{i \neq j} \left( \mu_{ij} \log \frac{\mu_{ij}}{\nu_{ij}} + (1 - \mu_{ij}) \log \frac{1 - \mu_{ij}}{1 - \nu_{ij}} \right)',
            'formula_display': 'L = Σ [ μ_ij · log(μ_ij / ν_ij) + (1 - μ_ij) · log((1 - μ_ij) / (1 - ν_ij)) ]'
        }
    }

    BOLIVIA_WARD_META = {
        'Santa Cruz': {'macro': 'Macro A', 'label': 'Macro A: Casco SCZ (Crítico)', 'color': '#ff3366'},
        'Cochabamba': {'macro': 'Macro B', 'label': 'Macro B: CBBA & Plan 3000 (Violencia)', 'color': '#fbbf24'},
        'Plan 3000': {'macro': 'Macro B', 'label': 'Macro B: CBBA & Plan 3000 (Violencia)', 'color': '#fbbf24'},
        'Equipetrol': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'La Paz': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'Los Lotes': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
        'Pampa de la Isla': {'macro': 'Macro C', 'label': 'Macro C: La Paz & Perif. (Patrimonial)', 'color': '#34d399'},
    }

    CHICAGO_WARD_META = {
        'Macro A': {'macro': 'Macro A', 'label': 'Macro A: Casco Central & Turístico (The Loop / Hurtos)', 'color': '#00e5ff'},
        'Macro B': {'macro': 'Macro B', 'label': 'Macro B: Sector Oeste & Sur (Violencia Armada Crítica)', 'color': '#ff3366'},
        'Macro C': {'macro': 'Macro C', 'label': 'Macro C: Periferias Residenciales (Baja Incidencia)', 'color': '#34d399'}
    }

    LDA_TOPICS_META = {
        0: {"label": "Tópico #0: Agresiones y Conflictos", "color": "#ff3366"},
        1: {"label": "Tópico #1: Litigios y Estafas", "color": "#9d4edd"},
        2: {"label": "Tópico #2: Narcotráfico e Incautaciones", "color": "#34d399"},
        3: {"label": "Tópico #3: Atracos y Motochorros", "color": "#fbbf24"},
        4: {"label": "Tópico #4: Hurtos y Descuidismo", "color": "#00e5ff"}
    }

    CHICAGO_LDA_TOPICS_META = {
        0: {"label": "Tópico #0: Robbery & Armed Handgun", "color": "#ff3366"},
        1: {"label": "Tópico #1: Battery & Domestic Assault", "color": "#fbbf24"},
        2: {"label": "Tópico #2: Theft & Property Loss", "color": "#00e5ff"},
        3: {"label": "Tópico #3: Narcotics & Street Crime", "color": "#34d399"},
        4: {"label": "Tópico #4: Deceptive Practice & Fraud", "color": "#9d4edd"}
    }

    @classmethod
    def _load(cls, ctx="bolivia"):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if ctx == "chicago":
            fp = os.path.join(base_dir, 'data', 'chicago_benchmark', 'gold', 'reduction_embeddings_chicago.json')
        else:
            gold_fp = os.path.join(base_dir, 'data', 'bolivia_news', 'gold', 'reduction_embeddings.json')
            legacy_fp = os.path.join(base_dir, 'data', 'web_scraping_news', 'reduction_embeddings.json')
            fp = gold_fp if os.path.exists(gold_fp) else legacy_fp
        
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"points": [], "pca": {}, "svd": {}, "ppca": {}, "tsne": {}, "umap": {}}

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
    def get_algorithm_data(cls, algo_name="pca", ctx="bolivia"):
        data = cls._load(ctx=ctx)
        algo_name = algo_name.lower()
        if algo_name not in ["pca", "svd", "ppca", "tsne", "umap"]:
            algo_name = "pca"

        algo_info = data.get(algo_name, {})
        coords = algo_info.get("coords", [])
        points = data.get("points", [])
        df_eventos = cls._load_eventos() if ctx == "bolivia" else None

        # Enriquecer meta con la teoría pedagógica solicitada
        theory = cls.ALGORITHMS_THEORY.get(algo_name, cls.ALGORITHMS_THEORY['pca'])
        meta = {**algo_info, **theory}
        meta['n_features'] = data.get('n_features', 250)
        meta['context'] = ctx

        topic_meta_dict = cls.CHICAGO_LDA_TOPICS_META if ctx == "chicago" else cls.LDA_TOPICS_META
        ward_meta_dict = cls.CHICAGO_WARD_META if ctx == "chicago" else cls.BOLIVIA_WARD_META

        # Combinar coordenadas 2D con metadatos del punto y clustering jerárquico Ward
        series = []
        for i, pt in enumerate(points):
            c = coords[i] if i < len(coords) else [0, 0]
            zona = pt.get("zone", "")
            if not zona and df_eventos is not None and i < len(df_eventos):
                row = df_eventos.iloc[i]
                zona = str(row['zona_principal']) if pd.notnull(row.get('zona_principal')) else ""
            
            ciudad = str(pt.get("city", "Chicago" if ctx == "chicago" else "Bolivia"))
            
            # Determinación de Macro-Cluster Jerárquico Ward (k=3) dinámico o fallback
            if "ward_macro" in pt and pt.get("ward_macro"):
                ward_macro = pt["ward_macro"]
                ward_label = pt.get("ward_label", ward_macro)
                ward_color = pt.get("ward_color", "#38bdf8")
            elif ctx == "chicago":
                w_info = ward_meta_dict.get(pt.get("ward_macro", "Macro A"), ward_meta_dict["Macro A"])
                ward_macro = w_info["macro"]
                ward_label = w_info["label"]
                ward_color = w_info["color"]
            elif zona in cls.BOLIVIA_WARD_META:
                ward_info = cls.BOLIVIA_WARD_META[zona]
                ward_macro = ward_info["macro"]
                ward_label = ward_info["label"]
                ward_color = ward_info["color"]
            elif "santa cruz" in ciudad.lower():
                ward_info = cls.BOLIVIA_WARD_META['Santa Cruz']
                ward_macro = ward_info["macro"]
                ward_label = ward_info["label"]
                ward_color = ward_info["color"]
            elif "cochabamba" in ciudad.lower():
                ward_info = cls.BOLIVIA_WARD_META['Cochabamba']
                ward_macro = ward_info["macro"]
                ward_label = ward_info["label"]
                ward_color = ward_info["color"]
            else:
                ward_info = cls.BOLIVIA_WARD_META['La Paz']
                ward_macro = ward_info["macro"]
                ward_label = ward_info["label"]
                ward_color = ward_info["color"]

            topic_id = int(pt.get("topic", 0))
            topic_info = topic_meta_dict.get(topic_id, {"label": f"Tópico #{topic_id}", "color": "#00e5ff"})

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
                "ward_macro": ward_macro,
                "ward_label": ward_label,
                "ward_color": ward_color
            })

        return {
            "algorithm": algo_name,
            "context": ctx,
            "dataset_name": data.get("dataset_name", "Chicago Police Department (RMS)" if ctx == "chicago" else "Seguridad Ciudadana Bolivia"),
            "meta": meta,
            "series": series,
            "available_algorithms": [
                {"id": "pca", "label": "PCA (Componentes Principales)", "class_date": "26-Oct"},
                {"id": "svd", "label": "TruncatedSVD (LSA Texto)", "class_date": "26-Oct"},
                {"id": "ppca", "label": "PPCA (Probabilistic PCA)", "class_date": "29-Oct"},
                {"id": "tsne", "label": "t-SNE (Variedad No Lineal)", "class_date": "29-Oct"},
                {"id": "umap", "label": "UMAP (Topología Simplicial)", "class_date": "29-Oct"}
            ]
        }
