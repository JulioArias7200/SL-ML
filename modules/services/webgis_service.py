import os
import pandas as pd


class WebGISService:
    _df_cache = None
    _chicago_cache = None

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
                    "cluster": int(getattr(row, "dbscan", 0)),
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
                    "cluster": dist_val,
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
        }
