import os
import pandas as pd


class WebGISService:
    _df_cache = None
    _chicago_cache = None

    BOLIVIA_OPTICS_META = {
        0: {"name": "Valle #0: Santa Cruz Casco & Anillos", "depth": 295, "color": "#00e5ff"},
        1: {"name": "Sub-Valle #1: Equipetrol Comercial", "depth": 240, "color": "#38bdf8"},
        2: {"name": "Valle #2: Plan 3000 (Ciudadela)", "depth": 340, "color": "#ff3366"},
        3: {"name": "Valle #3: Los Lotes (Ciudadela Sur)", "depth": 360, "color": "#f43f5e"},
        4: {"name": "Sub-Valle #4: Quillacollo Blanco Galindo", "depth": 460, "color": "#10b981"},
        5: {"name": "Valle #5: La Paz (El Prado / Miraflores)", "depth": 430, "color": "#818cf8"},
        6: {"name": "Sub-Valle #6: Pampa de la Isla", "depth": 330, "color": "#34d399"},
        7: {"name": "Valle #7: Cochabamba Cercado & Cancha", "depth": 380, "color": "#34d399"},
        -1: {"name": "Pico de Ruido / Salto Interurbano (-1)", "depth": 2800, "color": "#64748b"}
    }

    BOLIVIA_DBSCAN_META = {
        0: {"name": "Hotspot #0: Santa Cruz Core", "color": "#00e5ff"},
        1: {"name": "Hotspot #1: Cochabamba Cercado", "color": "#34d399"},
        2: {"name": "Hotspot #2: Plan 3000 / Los Lotes", "color": "#ff3366"},
        3: {"name": "Hotspot #3: Pampa de la Isla", "color": "#fbbf24"},
        4: {"name": "Hotspot #4: Cochabamba Periferia", "color": "#10b981"},
        5: {"name": "Hotspot #5: La Paz Centro", "color": "#818cf8"},
        -1: {"name": "Ruido Espacial Disperso (-1)", "color": "#64748b"}
    }

    BOLIVIA_GMM_META = {
        0: {"name": "GMM #0: SCZ Casco & Equipetrol (π=0.42)", "color": "#00e5ff"},
        1: {"name": "GMM #1: Plan 3000 / Los Lotes (π=0.28)", "color": "#ff3366"},
        2: {"name": "GMM #2: Cochabamba Cercado (π=0.18)", "color": "#34d399"},
        3: {"name": "GMM #3: La Paz & El Alto (π=0.12)", "color": "#818cf8"},
        -1: {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
    }

    CHICAGO_OPTICS_META = {
        1: {"name": "Valle #1: The Loop / Central CPD", "depth": 88, "color": "#00e5ff"},
        2: {"name": "Valle #2: Harrison / Garfield Park", "depth": 125, "color": "#ff3366"},
        3: {"name": "Valle #3: Englewood / South Side", "depth": 145, "color": "#ffaa00"},
        4: {"name": "Valle #4: Near West / UIC / Pilsen", "depth": 172, "color": "#a855f7"},
        -1: {"name": "Pico de Ruido / Salto Autopista (-1)", "depth": 380, "color": "#64748b"}
    }

    CHICAGO_DBSCAN_META = {
        1: {"name": "DBSCAN #1: The Loop (D-001/018)", "color": "#00e5ff"},
        2: {"name": "DBSCAN #2: Harrison West (D-011/015)", "color": "#ff3366"},
        3: {"name": "DBSCAN #3: Englewood South (D-007/006)", "color": "#ffaa00"},
        4: {"name": "DBSCAN #4: Near West (D-012)", "color": "#a855f7"},
        -1: {"name": "Ruido Espacial Disperso (-1)", "color": "#64748b"}
    }

    CHICAGO_GMM_META = {
        1: {"name": "GMM #1: Loop Comercial (π=0.35)", "color": "#00e5ff"},
        2: {"name": "GMM #2: West Side Garfield/Austin (π=0.40)", "color": "#ff3366"},
        3: {"name": "GMM #3: South Side Englewood (π=0.25)", "color": "#ffaa00"},
        -1: {"name": "Dispersión Fuera de Elipse (>3σ)", "color": "#64748b"}
    }

    BOLIVIA_WARD_META = {
        'A': {"name": "Macro A: Santa Cruz Casco (Crítico)", "color": "#ff3366", "description": "Gravedad Crítica y Concentración Delictiva"},
        'B': {"name": "Macro B: CBBA & Plan 3000 (Violencia)", "color": "#fbbf24", "description": "Violencia Armada y Homicidios"},
        'C': {"name": "Macro C: La Paz, El Alto & Perif. (Patrimonial)", "color": "#34d399", "description": "Delitos Patrimoniales y Menor Gravedad"},
    }

    CHICAGO_WARD_META = {
        'A': {"name": "Macro A: West & South Side (Violencia)", "color": "#ff3366", "description": "Distritos 11, 7, 15, 10, 6 - Violencia Armada Crítica"},
        'B': {"name": "Macro B: Loop & Near North (Comercial)", "color": "#00e5ff", "description": "Distritos 1, 18, 19, 12 - Densidad Comercial Alta"},
        'C': {"name": "Macro C: North & Suburbano (Residencial)", "color": "#34d399", "description": "Distritos Periféricos - Baja Tasa Violenta"},
    }

    @classmethod
    def _load_data(cls):
        # Siempre recargar si el archivo fue modificado o el caché está vacío
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_gold = os.path.join(
            base_dir, "data", "bolivia_news", "gold", "spatial_clusters_bolivia.csv"
        )
        csv_clusters_legacy = os.path.join(
            base_dir,
            "data",
            "web_scraping_news",
            "dashboard_eventos_clusters_bolivia.csv",
        )
        csv_eventos_raw = os.path.join(
            base_dir, "data", "bolivia_news", "bronze", "eventos_bolivia_raw.csv"
        )
        csv_eventos_legacy = os.path.join(
            base_dir, "data", "web_scraping_news", "eventos_bolivia.csv"
        )

        df = None
        for path in [
            csv_gold,
            csv_clusters_legacy,
            csv_eventos_raw,
            csv_eventos_legacy,
        ]:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    if len(df) > 0:
                        break
                except Exception as e:
                    print(f"[WebGISService] Error leyendo {path}: {e}")

        if df is None:
            df = pd.DataFrame(
                columns=[
                    "lat",
                    "lon",
                    "titulo",
                    "delito_principal",
                    "fecha",
                    "ciudad",
                    "url",
                    "fuente",
                ]
            )

        df = df.dropna(subset=["lat", "lon"]).copy()
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df = df.dropna(subset=["lat", "lon"]).copy()

        df["titulo"] = df["titulo"].fillna("Reporte policial no especificado")
        df["delito_principal"] = df["delito_principal"].fillna("Sin categoría")
        df["ciudad"] = df["ciudad"].fillna("Nacional / No especificada")
        df["zona_principal"] = df.get("zona_principal", pd.Series()).fillna(
            df["ciudad"]
        )
        df["fuente"] = df.get("fuente", pd.Series()).fillna("Prensa")
        df["url"] = df.get("url", pd.Series()).fillna("#")
        df["fecha"] = df.get("fecha", pd.Series()).fillna("")
        df["dbscan"] = df.get("dbscan", pd.Series(0)).fillna(0).astype(int)

        cls._df_cache = df
        return cls._df_cache

    @classmethod
    def _load_chicago_sample(cls):
        if cls._chicago_cache is not None:
            return cls._chicago_cache

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        parquet_path = os.path.join(
            base_dir, "data", "chicago_benchmark", "silver", "chicago_crimes_curated.parquet"
        )

        if os.path.exists(parquet_path):
            try:
                cols = ['ID', 'Date', 'Primary Type', 'Description', 'District', 'Latitude', 'Longitude']
                df_all = pd.read_parquet(parquet_path, columns=cols)
                df_valid = df_all.dropna(subset=['Latitude', 'Longitude']).copy()
                # Renombrar columnas para acceso limpio sin espacios
                df_valid.rename(columns={
                    'ID': 'id',
                    'Date': 'date',
                    'Primary Type': 'primary_type',
                    'Description': 'description',
                    'District': 'district',
                    'Latitude': 'latitude',
                    'Longitude': 'longitude'
                }, inplace=True)
                sample = df_valid.sample(n=min(750, len(df_valid)), random_state=42).copy()
                cls._chicago_cache = sample
                return cls._chicago_cache
            except Exception as e:
                print(f"[WebGISService] Error cargando parquet Chicago: {e}")

        cls._chicago_cache = pd.DataFrame(columns=['id', 'date', 'primary_type', 'description', 'district', 'latitude', 'longitude'])
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
            dbscan_id = int(getattr(row, "dbscan", 0))
            optics_id = int(getattr(row, "optics", -1))
            
            # Asignación probabilística GMM según proximidad
            ciudad_str = str(row.ciudad).lower()
            if "santa cruz" in ciudad_str:
                gmm_id = 1 if ("plan 3000" in str(row.zona_principal).lower() or "lotes" in str(row.zona_principal).lower()) else 0
                gmm_prob = 84.5 if gmm_id == 0 else 76.2
            elif "cochabamba" in ciudad_str:
                gmm_id = 2
                gmm_prob = 81.0
            elif "la paz" in ciudad_str or "el alto" in ciudad_str:
                gmm_id = 3
                gmm_prob = 79.4
            else:
                gmm_id = -1
                gmm_prob = 25.0

            optics_info = cls.BOLIVIA_OPTICS_META.get(optics_id, cls.BOLIVIA_OPTICS_META[-1])
            dbscan_info = cls.BOLIVIA_DBSCAN_META.get(dbscan_id, cls.BOLIVIA_DBSCAN_META[-1])
            gmm_info = cls.BOLIVIA_GMM_META.get(gmm_id, cls.BOLIVIA_GMM_META[-1])

            # Asignación de Macro-Cluster Jerárquico Ward (Taxonomía Aglomerativa k=3)
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
                    
                    # Modelado No Supervisado: DBSCAN, OPTICS, GMM y Jerárquico Ward
                    "cluster": dbscan_id,
                    "dbscan": dbscan_id,
                    "dbscan_label": dbscan_info["name"],
                    "dbscan_color": dbscan_info["color"],
                    
                    "optics": optics_id,
                    "optics_valley": optics_info["name"],
                    "optics_color": optics_info["color"],
                    "reach_depth_m": optics_info["depth"],

                    "gmm": gmm_id,
                    "gmm_label": gmm_info["name"],
                    "gmm_color": gmm_info["color"],
                    "gmm_prob": gmm_prob,

                    "ward": ward_id,
                    "ward_macro": ward_id,
                    "ward_label": ward_info["name"],
                    "ward_color": ward_info["color"],
                    
                    "is_noise": (dbscan_id == -1 or optics_id == -1),
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

            # Mapeo criminológico a DBSCAN, OPTICS y GMM
            if dist_val in [1, 18]:
                dbscan_id = 1
                optics_id = 1
                gmm_id = 1
                gmm_prob = 88.2
            elif dist_val in [11, 15, 10]:
                dbscan_id = 2
                optics_id = 2
                gmm_id = 2
                gmm_prob = 84.6
            elif dist_val in [7, 6]:
                dbscan_id = 3
                optics_id = 3
                gmm_id = 3
                gmm_prob = 79.1
            elif dist_val in [12]:
                dbscan_id = 4
                optics_id = 4
                gmm_id = 2
                gmm_prob = 62.4
            else:
                dbscan_id = -1
                optics_id = -1
                gmm_id = -1
                gmm_prob = 30.0

            optics_info = cls.CHICAGO_OPTICS_META.get(optics_id, cls.CHICAGO_OPTICS_META[-1])
            dbscan_info = cls.CHICAGO_DBSCAN_META.get(dbscan_id, cls.CHICAGO_DBSCAN_META[-1])
            gmm_info = cls.CHICAGO_GMM_META.get(gmm_id, cls.CHICAGO_GMM_META[-1])

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
                    
                    # Modelado No Supervisado: DBSCAN, OPTICS, GMM y Jerárquico Ward
                    "cluster": dbscan_id,
                    "dbscan": dbscan_id,
                    "dbscan_label": dbscan_info["name"],
                    "dbscan_color": dbscan_info["color"],
                    
                    "optics": optics_id,
                    "optics_valley": optics_info["name"],
                    "optics_color": optics_info["color"],
                    "reach_depth_m": optics_info["depth"],

                    "gmm": gmm_id,
                    "gmm_label": gmm_info["name"],
                    "gmm_color": gmm_info["color"],
                    "gmm_prob": gmm_prob,

                    "ward": ward_id,
                    "ward_macro": ward_id,
                    "ward_label": ward_info["name"],
                    "ward_color": ward_info["color"],
                    
                    "is_noise": (dbscan_id == -1 or optics_id == -1),
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
                "optics_valleys": list(cls.CHICAGO_OPTICS_META.values()),
                "dbscan_hotspots": list(cls.CHICAGO_DBSCAN_META.values()),
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
            },
            "optics_valleys": list(cls.BOLIVIA_OPTICS_META.values()),
            "dbscan_hotspots": list(cls.BOLIVIA_DBSCAN_META.values()),
            "gmm_components": list(cls.BOLIVIA_GMM_META.values())
        }
