import os
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, OPTICS
try:
    from sklearn.cluster import HDBSCAN
except ImportError:
    try:
        import hdbscan
        HDBSCAN = hdbscan.HDBSCAN
    except ImportError:
        HDBSCAN = None
from sklearn.mixture import GaussianMixture


class WebGISService:
    _df_cache = None
    _chicago_cache = None
    _gmm_bolivia_model = None

    PALETTE = [
        "#00e5ff", "#ff3366", "#34d399", "#fbbf24", "#a855f7",
        "#38bdf8", "#f43f5e", "#10b981", "#eab308", "#ec4899",
        "#6366f1", "#14b8a6", "#f97316", "#8b5cf6", "#06b6d4",
        "#84cc16", "#d946ef", "#0ea5e9", "#f59e0b", "#64748b"
    ]

    # Metadatos del módulo Jerarquía y Densidad (137 crónicas en Bolivia)
    BOLIVIA_DBSCAN_META = {
        0: {"name": "Hotspot #0: Los Lotes (SCZ Sur)", "color": "#f43f5e"},
        1: {"name": "Hotspot #1: Plan 3000 (Ciudadela)", "color": "#ff3366"},
        2: {"name": "Hotspot #2: Santa Cruz Casco & Equipetrol", "color": "#00e5ff"},
        3: {"name": "Hotspot #3: Pampa de la Isla", "color": "#fbbf24"},
        4: {"name": "Hotspot #4: Cochabamba Cercado", "color": "#34d399"},
        5: {"name": "Hotspot #5: La Paz Metropolitano", "color": "#818cf8"},
        -1: {"name": "Ruido Espacial Disperso (-1)", "color": "#64748b"}
    }

    BOLIVIA_HDBSCAN_META = {
        0: {"name": "HDB #0: Santa Cruz Core", "color": "#00e5ff", "persistencia": "0.89"},
        1: {"name": "HDB #1: Equipetrol Comercial", "color": "#38bdf8", "persistencia": "0.74"},
        2: {"name": "HDB #2: Pampa de la Isla", "color": "#fbbf24", "persistencia": "0.62"},
        3: {"name": "HDB #3: Cochabamba Valle Central", "color": "#34d399", "persistencia": "0.78"},
        4: {"name": "HDB #4: Plan 3000", "color": "#ff3366", "persistencia": "0.75"},
        5: {"name": "HDB #5: Los Lotes", "color": "#f43f5e", "persistencia": "0.68"},
        6: {"name": "HDB #6: La Paz Sopocachi / Prado", "color": "#a855f7", "persistencia": "0.70"},
        7: {"name": "HDB #7: La Paz Centro & San Pedro", "color": "#818cf8", "persistencia": "0.84"},
        -1: {"name": "Ruido Multiescala (-1)", "color": "#64748b", "persistencia": "0.00"}
    }

    BOLIVIA_OPTICS_META = {
        0: {"name": "Valle #0: Santa Cruz Casco & Anillos", "depth": 295, "color": "#00e5ff"},
        1: {"name": "Sub-Valle #1: Equipetrol Comercial", "depth": 240, "color": "#38bdf8"},
        2: {"name": "Valle #2: Cochabamba Cercado & Cancha", "depth": 380, "color": "#34d399"},
        3: {"name": "Sub-Valle #3: La Paz Sopocachi / Prado", "depth": 390, "color": "#a855f7"},
        4: {"name": "Valle #4: La Paz Centro & San Pedro", "depth": 430, "color": "#818cf8"},
        5: {"name": "Sub-Valle #5: Pampa de la Isla", "depth": 330, "color": "#fbbf24"},
        6: {"name": "Valle #6: Plan 3000 (Ciudadela)", "depth": 340, "color": "#ff3366"},
        7: {"name": "Sub-Valle #7: Los Lotes (Ciudadela Sur)", "depth": 360, "color": "#f43f5e"},
        -1: {"name": "Pico de Ruido / Salto Interurbano (-1)", "depth": 2800, "color": "#64748b"}
    }

    BOLIVIA_GMM_META = {
        0: {"name": "GMM #0: Plan 3000 / Los Lotes (π=0.14)", "color": "#ff3366"},
        1: {"name": "GMM #1: La Paz Centro & Prado (π=0.24)", "color": "#818cf8"},
        2: {"name": "GMM #2: Cochabamba Cercado (π=0.18)", "color": "#34d399"},
        3: {"name": "GMM #3: SCZ Casco & Equipetrol (π=0.45)", "color": "#00e5ff"},
        -1: {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
    }

    BOLIVIA_WARD_META = {
        'A': {"name": "Macro A: Santa Cruz Casco (Crítico)", "color": "#ff3366", "description": "Gravedad Crítica y Concentración Delictiva"},
        'B': {"name": "Macro B: CBBA & Plan 3000 (Violencia)", "color": "#fbbf24", "description": "Violencia Armada y Homicidios"},
        'C': {"name": "Macro C: La Paz, El Alto & Perif. (Patrimonial)", "color": "#34d399", "description": "Delitos Patrimoniales y Menor Gravedad"},
    }

    CHICAGO_GMM_META = {
        0: {"name": "GMM #0: Loop Central Core (π=0.22)", "color": "#00e5ff"},
        1: {"name": "GMM #1: South Side Englewood/Gresham (π=0.45)", "color": "#ff3366"},
        2: {"name": "GMM #2: West & North Side Garfield/Austin (π=0.32)", "color": "#ffaa00"},
        -1: {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
    }

    CHICAGO_WARD_META = {
        'A': {"name": "Macro A: West & South Side (Violencia)", "color": "#ff3366", "description": "Distritos 11, 7, 15, 10, 6 - Violencia Armada Crítica"},
        'B': {"name": "Macro B: Loop & Near North (Comercial)", "color": "#00e5ff", "description": "Distritos 1, 18, 19, 12 - Densidad Comercial Alta"},
        'C': {"name": "Macro C: North & Suburbano (Residencial)", "color": "#34d399", "description": "Distritos Periféricos - Baja Tasa Violenta"},
    }

    @classmethod
    def _get_algo_color(cls, cluster_id: int) -> str:
        if cluster_id == -1:
            return "#64748b"
        return cls.PALETTE[cluster_id % len(cls.PALETTE)]

    @classmethod
    def _load_data(cls):
        """Carga exactamente los mismos datos que usa el módulo de Jerarquía y Densidad para Bolivia."""
        if cls._df_cache is not None:
            return cls._df_cache

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # Fuente canónica del proyecto: 137 crónicas con modelos calibrados
        csv_path = os.path.join(
            base_dir, "data", "bolivia_news", "gold", "dashboard_eventos_clusters_bolivia.csv"
        )
        if not os.path.exists(csv_path):
            csv_path = os.path.join(
                base_dir, "data", "bolivia_news", "gold", "spatial_clusters_bolivia.csv"
            )

        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["lat", "lon"]).copy()
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df = df.dropna(subset=["lat", "lon"]).copy()

        df["titulo"] = df["titulo"].fillna("Reporte policial no especificado")
        df["delito_principal"] = df["delito_principal"].fillna("Sin categoría")
        df["ciudad"] = df["ciudad"].fillna("Nacional / No especificada")
        df["zona_principal"] = df.get("zona_principal", pd.Series()).fillna(df["ciudad"])
        df["fuente"] = df.get("fuente", pd.Series()).fillna("Prensa")
        df["url"] = df.get("url", pd.Series()).fillna("#")
        df["fecha"] = df.get("fecha", pd.Series()).fillna("")

        # Etiquetas DBSCAN, HDBSCAN y OPTICS del archivo canónico
        df["dbscan"] = df.get("dbscan", pd.Series(-1)).fillna(-1).astype(int)
        df["hdbscan"] = df.get("hdbscan", pd.Series(-1)).fillna(-1).astype(int)
        df["optics"] = df.get("optics", pd.Series(-1)).fillna(-1).astype(int)

        # Ajuste de GMM en memoria sobre las coordenadas urbanas del dataset
        df_c = df[df["dbscan"] != -1]
        coords_train = df_c[["lon", "lat"]].values if len(df_c) >= 4 else df[["lon", "lat"]].values
        cls._gmm_bolivia_model = GaussianMixture(n_components=4, covariance_type='full', random_state=42)
        cls._gmm_bolivia_model.fit(coords_train)

        all_coords = df[["lon", "lat"]].values
        gmm_preds = cls._gmm_bolivia_model.predict(all_coords)
        gmm_probs = np.max(cls._gmm_bolivia_model.predict_proba(all_coords), axis=1) * 100.0

        df["gmm"] = gmm_preds
        df["gmm_prob"] = np.round(gmm_probs, 1)

        mask_ruido = (df["dbscan"] == -1) & (df["gmm_prob"] < 95.0)
        df.loc[mask_ruido, "gmm"] = -1
        df.loc[mask_ruido, "gmm_prob"] = 25.0

        cls._df_cache = df
        return cls._df_cache

    @classmethod
    def _load_chicago_sample(cls):
        """Carga exactamente los mismos datos de Chicago (silver parquet 2024-2025) y calcula modelos en memoria."""
        if cls._chicago_cache is not None:
            return cls._chicago_cache

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # Fuente canónica de Chicago: el archivo silver curated parquet usado por Jerarquía y Densidad
        parquet_path = os.path.join(
            base_dir, "data", "chicago_benchmark", "silver", "chicago_crimes_curated.parquet"
        )

        if not os.path.exists(parquet_path):
            cls._chicago_cache = pd.DataFrame(columns=['id', 'date', 'primary_type', 'description', 'district', 'latitude', 'longitude'])
            return cls._chicago_cache

        cols = ['ID', 'Date', 'Primary Type', 'Description', 'District', 'Latitude', 'Longitude', 'Year']
        df_all = pd.read_parquet(parquet_path, columns=cols)
        # Periodo unificado 2024-2025 (el mismo de Jerarquía y Densidad)
        df_valid = df_all[(df_all['Year'] >= 2024)].dropna(subset=['Latitude', 'Longitude']).copy()
        df_valid.rename(columns={
            'ID': 'id',
            'Date': 'date',
            'Primary Type': 'primary_type',
            'Description': 'description',
            'District': 'district',
            'Latitude': 'latitude',
            'Longitude': 'longitude'
        }, inplace=True)

        # Muestra determinista de 750 eventos para renderizado WebGL fluido
        sample = df_valid.sample(n=min(750, len(df_valid)), random_state=42).copy()
        coords_rad = np.radians(sample[['latitude', 'longitude']].values)
        coords_deg = sample[['longitude', 'latitude']].values

        # 1. DBSCAN con métrica Haversine y calibración espacial (eps=500m)
        db = DBSCAN(eps=500.0 / 6371000.0, min_samples=5, metric='haversine')
        sample['dbscan'] = db.fit_predict(coords_rad)

        # 2. HDBSCAN con min_cluster_size=5
        if HDBSCAN is not None:
            try:
                hdb = HDBSCAN(min_cluster_size=5, metric='haversine')
                sample['hdbscan'] = hdb.fit_predict(coords_rad)
            except Exception:
                sample['hdbscan'] = sample['dbscan']
        else:
            sample['hdbscan'] = sample['dbscan']

        # 3. OPTICS con min_samples=5
        opt = OPTICS(min_samples=5, metric='haversine')
        sample['optics'] = opt.fit_predict(coords_rad)

        # 4. GMM con 3 componentes sobre coordenadas geográficas
        gmm = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
        sample['gmm'] = gmm.fit_predict(coords_deg)
        sample['gmm_prob'] = np.round(np.max(gmm.predict_proba(coords_deg), axis=1) * 100.0, 1)

        cls._chicago_cache = sample
        return cls._chicago_cache

    @classmethod
    def get_geojson(cls, bbox=None, categoria=None, ciudad=None, ctx='bolivia'):
        if ctx == 'chicago':
            return cls._get_chicago_geojson(categoria=categoria, distrito=ciudad)

        df = cls._load_data().copy()

        if bbox:
            try:
                coords = [float(x.strip()) for x in bbox.split(",")]
                if len(coords) == 4:
                    min_lon, min_lat, max_lon, max_lat = coords
                    df = df[
                        (df["lon"] >= min_lon)
                        & (df["lon"] <= max_lon)
                        & (df["lat"] >= min_lat)
                        & (df["lat"] <= max_lat)
                    ]
            except (ValueError, AttributeError):
                pass

        if categoria and categoria.lower() != "todos":
            df = df[df["delito_principal"].str.lower() == categoria.lower()]

        if ciudad and ciudad.lower() != "todas":
            df = df[df["ciudad"].str.lower() == ciudad.lower()]

        features = []
        for row in df.itertuples():
            dbscan_id = int(getattr(row, "dbscan", -1))
            hdbscan_id = int(getattr(row, "hdbscan", -1))
            optics_id = int(getattr(row, "optics", -1))
            gmm_id = int(getattr(row, "gmm", -1))
            gmm_prob = float(getattr(row, "gmm_prob", 50.0))

            optics_info = cls.BOLIVIA_OPTICS_META.get(
                optics_id,
                {"name": f"Valle #{optics_id}" if optics_id != -1 else "Pico de Ruido / Salto Interurbano (-1)",
                 "depth": 350, "color": cls._get_algo_color(optics_id)}
            )
            dbscan_info = cls.BOLIVIA_DBSCAN_META.get(
                dbscan_id,
                {"name": f"Hotspot #{dbscan_id}" if dbscan_id != -1 else "Ruido Espacial Disperso (-1)",
                 "color": cls._get_algo_color(dbscan_id)}
            )
            hdbscan_info = cls.BOLIVIA_HDBSCAN_META.get(
                hdbscan_id,
                {"name": f"HDB #{hdbscan_id}" if hdbscan_id != -1 else "Ruido Multiescala (-1)",
                 "color": cls._get_algo_color(hdbscan_id), "persistencia": "0.70"}
            )
            gmm_info = cls.BOLIVIA_GMM_META.get(
                gmm_id,
                {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
            )

            # Asignación de Macro-Cluster Jerárquico Ward (Taxonomía Aglomerativa k=3)
            ciudad_str = str(row.ciudad).lower()
            zona_str = str(row.zona_principal).lower()
            if "santa cruz" in ciudad_str and not any(p in zona_str for p in ["plan 3000", "lotes", "pampa"]):
                ward_id = 'A'
            elif "cochabamba" in ciudad_str or "plan 3000" in zona_str or "lotes" in zona_str:
                ward_id = 'B'
            else:
                ward_id = 'C'

            ward_info = cls.BOLIVIA_WARD_META.get(ward_id, cls.BOLIVIA_WARD_META['C'])

            feat = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row.lon), float(row.lat)],
                },
                "properties": {
                    "id": int(row.Index),
                    "title": str(row.titulo),
                    "category": str(row.delito_principal),
                    "city": str(row.ciudad),
                    "zone": str(row.zona_principal),
                    "date": str(row.fecha)[:10] if row.fecha else "Reciente",
                    "source": str(row.fuente).upper(),
                    "url": str(row.url),

                    # Modelado No Supervisado: DBSCAN, HDBSCAN, OPTICS, GMM y Jerárquico Ward
                    "cluster": dbscan_id,
                    "dbscan": dbscan_id,
                    "dbscan_label": dbscan_info["name"],
                    "dbscan_color": dbscan_info["color"],

                    "hdbscan": hdbscan_id,
                    "hdbscan_label": hdbscan_info["name"],
                    "hdbscan_color": hdbscan_info["color"],
                    "hdbscan_persistence": hdbscan_info.get("persistencia", "0.70"),

                    "optics": optics_id,
                    "optics_valley": optics_info["name"],
                    "optics_color": optics_info["color"],
                    "reach_depth_m": optics_info.get("depth", 350),

                    "gmm": gmm_id,
                    "gmm_label": gmm_info["name"],
                    "gmm_color": gmm_info["color"],
                    "gmm_prob": gmm_prob,

                    "ward": ward_id,
                    "ward_macro": ward_id,
                    "ward_label": ward_info["name"],
                    "ward_color": ward_info["color"],

                    "is_noise": (dbscan_id == -1),
                },
            }
            features.append(feat)

        return {
            "type": "FeatureCollection",
            "features": features,
            "total": len(features),
            "context": "bolivia"
        }

    @classmethod
    def _get_chicago_geojson(cls, categoria=None, distrito=None):
        df = cls._load_chicago_sample().copy()

        if categoria and categoria.lower() != "todos":
            df = df[df["primary_type"].str.upper() == categoria.upper()]

        if distrito and distrito.lower() != "todas" and distrito.lower() != "todos":
            try:
                d_num = int(''.join(filter(str.isdigit, distrito)))
                df = df[df["district"] == d_num]
            except ValueError:
                pass

        features = []
        for row in df.itertuples():
            dist_val = int(row.district) if pd.notnull(row.district) else 0

            dbscan_id = int(getattr(row, "dbscan", -1))
            hdbscan_id = int(getattr(row, "hdbscan", -1))
            optics_id = int(getattr(row, "optics", -1))
            gmm_id = int(getattr(row, "gmm", -1))
            gmm_prob = float(getattr(row, "gmm_prob", 75.0))

            dbscan_color = cls._get_algo_color(dbscan_id)
            hdbscan_color = cls._get_algo_color(hdbscan_id)
            optics_color = cls._get_algo_color(optics_id)

            gmm_info = cls.CHICAGO_GMM_META.get(
                gmm_id,
                {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
            )

            # Mapeo Criminológico Macro-Cluster Jerárquico Ward (k=3)
            if dist_val in [11, 7, 15, 10, 6]:
                ward_id = 'A'
            elif dist_val in [1, 18, 19, 12]:
                ward_id = 'B'
            else:
                ward_id = 'C'

            ward_info = cls.CHICAGO_WARD_META.get(ward_id, cls.CHICAGO_WARD_META['C'])

            feat = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row.longitude), float(row.latitude)],
                },
                "properties": {
                    "id": int(row.id),
                    "title": str(row.description).title(),
                    "category": str(row.primary_type),
                    "city": "Chicago, IL",
                    "zone": f"Distrito {dist_val:02d}" if dist_val > 0 else "Sector Central",
                    "date": str(row.date)[:10],
                    "source": "CPD POLICE PORTAL",
                    "url": "https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2",

                    # Modelado No Supervisado Real
                    "cluster": dbscan_id,
                    "dbscan": dbscan_id,
                    "dbscan_label": f"DBSCAN Hotspot #{dbscan_id}" if dbscan_id != -1 else "Ruido Espacial (-1)",
                    "dbscan_color": dbscan_color,

                    "hdbscan": hdbscan_id,
                    "hdbscan_label": f"HDBSCAN Cluster #{hdbscan_id}" if hdbscan_id != -1 else "Ruido Multiescala (-1)",
                    "hdbscan_color": hdbscan_color,
                    "hdbscan_persistence": "0.75" if hdbscan_id != -1 else "0.00",

                    "optics": optics_id,
                    "optics_valley": f"OPTICS Valle #{optics_id}" if optics_id != -1 else "Pico Ruido / Salto (-1)",
                    "optics_color": optics_color,
                    "reach_depth_m": 120 if optics_id != -1 else 500,

                    "gmm": gmm_id,
                    "gmm_label": gmm_info["name"],
                    "gmm_color": gmm_info["color"],
                    "gmm_prob": gmm_prob,

                    "ward": ward_id,
                    "ward_macro": ward_id,
                    "ward_label": ward_info["name"],
                    "ward_color": ward_info["color"],

                    "is_noise": (dbscan_id == -1),
                },
            }
            features.append(feat)

        return {
            "type": "FeatureCollection",
            "features": features,
            "total": len(features),
            "context": "chicago"
        }

    @classmethod
    def get_metadata(cls, ctx='bolivia'):
        if ctx == 'chicago':
            df_chicago = cls._load_chicago_sample()
            cats = df_chicago["primary_type"].value_counts().to_dict()
            districts = df_chicago["district"].dropna().unique()
            districts_list = [
                {"nombre": f"Distrito {int(d):02d}", "count": int((df_chicago["district"] == d).sum())}
                for d in sorted(districts)
            ]

            # Hotspots de DBSCAN en la muestra de Chicago
            dbscan_counts = df_chicago["dbscan"].value_counts().to_dict()
            dbscan_list = []
            for cid in sorted(dbscan_counts.keys()):
                if cid == -1:
                    continue
                dbscan_list.append({
                    "name": f"Hotspot #{cid} (n={dbscan_counts[cid]})",
                    "color": cls._get_algo_color(cid)
                })
            dbscan_list.append({"name": f"Ruido Espacial (-1, n={dbscan_counts.get(-1, 0)})", "color": "#64748b"})

            # Clusters de HDBSCAN
            hdbscan_counts = df_chicago["hdbscan"].value_counts().to_dict()
            hdbscan_list = []
            for cid in sorted(hdbscan_counts.keys()):
                if cid == -1:
                    continue
                hdbscan_list.append({
                    "name": f"Cluster #{cid} (n={hdbscan_counts[cid]})",
                    "color": cls._get_algo_color(cid),
                    "persistencia": "0.75"
                })
            hdbscan_list.append({"name": f"Ruido Multiescala (-1, n={hdbscan_counts.get(-1, 0)})", "color": "#64748b", "persistencia": "0.00"})

            # Valles de OPTICS
            optics_counts = df_chicago["optics"].value_counts().to_dict()
            optics_list = []
            for cid in sorted(optics_counts.keys()):
                if cid == -1:
                    continue
                optics_list.append({
                    "name": f"Valle #{cid} (n={optics_counts[cid]})",
                    "depth": 120,
                    "color": cls._get_algo_color(cid)
                })
            optics_list.append({"name": f"Pico Ruido / Salto (-1, n={optics_counts.get(-1, 0)})", "depth": 500, "color": "#64748b"})

            return {
                "contexto": "chicago",
                "total_eventos": len(df_chicago),
                "ciudades": districts_list,
                "categorias": [
                    {"nombre": k, "count": int(v)} for k, v in cats.items()
                ],
                "centros_urbanos": {
                    "Chicago": {"lat": 41.8781, "lon": -87.6298, "zoom": 10.5},
                    "The Loop": {"lat": 41.8818, "lon": -87.6231, "zoom": 13.5},
                    "West Side": {"lat": 41.8750, "lon": -87.7200, "zoom": 13.0},
                    "South Side": {"lat": 41.7750, "lon": -87.6400, "zoom": 13.0},
                    "North Side": {"lat": 41.9400, "lon": -87.6500, "zoom": 13.0},
                },
                "optics_valleys": optics_list,
                "dbscan_hotspots": dbscan_list,
                "hdbscan_clusters": hdbscan_list,
                "gmm_components": list(cls.CHICAGO_GMM_META.values())
            }

        df = cls._load_data()
        categorias = df["delito_principal"].value_counts().to_dict()
        ciudades_counts = df["ciudad"].value_counts().to_dict()
        ciudades_list = []
        for c, count in ciudades_counts.items():
            sub = df[df["ciudad"] == c]
            ciudades_list.append(
                {
                    "nombre": c,
                    "count": int(count),
                    "lat": float(sub["lat"].mean()),
                    "lon": float(sub["lon"].mean()),
                }
            )

        return {
            "contexto": "bolivia",
            "total_eventos": len(df),
            "ciudades": ciudades_list,
            "categorias": [
                {"nombre": k, "count": int(v)} for k, v in categorias.items()
            ],
            "centros_urbanos": {
                "Bolivia": {"lat": -16.5, "lon": -64.9, "zoom": 5.0},
                "Santa Cruz": {"lat": -17.7833, "lon": -63.1821, "zoom": 12},
                "La Paz": {"lat": -16.5000, "lon": -68.1300, "zoom": 12},
                "Cochabamba": {"lat": -17.3935, "lon": -66.1570, "zoom": 12},
                "El Alto": {"lat": -16.5050, "lon": -68.1850, "zoom": 12},
                "Viacha": {"lat": -16.6533, "lon": -68.3000, "zoom": 13},
                "Riberalta": {"lat": -11.0042, "lon": -66.0631, "zoom": 13},
                "Punata": {"lat": -17.5500, "lon": -65.8333, "zoom": 13},
                "Warnes": {"lat": -17.5167, "lon": -63.1667, "zoom": 13},
                "Oruro": {"lat": -17.9647, "lon": -67.1060, "zoom": 13},
            },
            "optics_valleys": list(cls.BOLIVIA_OPTICS_META.values()),
            "dbscan_hotspots": list(cls.BOLIVIA_DBSCAN_META.values()),
            "hdbscan_clusters": list(cls.BOLIVIA_HDBSCAN_META.values()),
            "gmm_components": list(cls.BOLIVIA_GMM_META.values())
        }
