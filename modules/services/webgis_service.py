import os
import pandas as pd

class WebGISService:
    _df_cache = None
    _metadata_cache = None

    @classmethod
    def _load_data(cls):
        if cls._df_cache is not None:
            return cls._df_cache

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Intentar cargar dataset clusterizado enriquecido de Bolivia
        csv_clusters = os.path.join(base_dir, 'data', 'web_scraping_news', 'dashboard_eventos_clusters_bolivia.csv')
        csv_eventos = os.path.join(base_dir, 'data', 'web_scraping_news', 'eventos_bolivia.csv')

        df = None
        if os.path.exists(csv_clusters):
            try:
                df = pd.read_csv(csv_clusters)
            except Exception as e:
                print(f"[WebGISService] Error leyendo clusters: {e}")

        if df is None or len(df) == 0:
            if os.path.exists(csv_eventos):
                try:
                    df = pd.read_csv(csv_eventos)
                except Exception as e:
                    print(f"[WebGISService] Error leyendo eventos: {e}")

        if df is None:
            # Respaldo vacío si no encuentra archivos
            df = pd.DataFrame(columns=['lat', 'lon', 'titulo', 'delito_principal', 'fecha', 'ciudad', 'url', 'fuente'])

        # Limpieza básica: filtrar nulos en coordenadas
        df = df.dropna(subset=['lat', 'lon']).copy()
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon']).copy()

        # Completar nulos en campos descriptivos
        df['titulo'] = df['titulo'].fillna('Reporte policial no especificado')
        df['delito_principal'] = df['delito_principal'].fillna('Sin categoría')
        df['ciudad'] = df['ciudad'].fillna('Nacional / No especificada')
        df['zona_principal'] = df.get('zona_principal', pd.Series()).fillna(df['ciudad'])
        df['fuente'] = df.get('fuente', pd.Series()).fillna('Prensa')
        df['url'] = df.get('url', pd.Series()).fillna('#')
        df['fecha'] = df.get('fecha', pd.Series()).fillna('')
        df['dbscan'] = df.get('dbscan', pd.Series(0)).fillna(0).astype(int)

        cls._df_cache = df
        return cls._df_cache

    @classmethod
    def get_geojson(cls, bbox=None, categoria=None, ciudad=None):
        df = cls._load_data().copy()

        # 1. Filtro espacial por Bounding Box (min_lon, min_lat, max_lon, max_lat)
        if bbox:
            try:
                coords = [float(x.strip()) for x in bbox.split(',')]
                if len(coords) == 4:
                    min_lon, min_lat, max_lon, max_lat = coords
                    df = df[(df['lon'] >= min_lon) & (df['lon'] <= max_lon) &
                            (df['lat'] >= min_lat) & (df['lat'] <= max_lat)]
            except (ValueError, AttributeError):
                pass

        # 2. Filtro por categoría de delito
        if categoria and categoria.lower() != 'todos':
            df = df[df['delito_principal'].str.lower() == categoria.lower()]

        # 3. Filtro por ciudad
        if ciudad and ciudad.lower() != 'todas':
            df = df[df['ciudad'].str.lower() == ciudad.lower()]

        # Construcción rápida de GeoJSON FeatureCollection
        features = []
        for row in df.itertuples():
            feat = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row.lon), float(row.lat)]
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
                    "cluster": int(getattr(row, 'dbscan', 0))
                }
            }
            features.append(feat)

        return {
            "type": "FeatureCollection",
            "features": features,
            "total": len(features)
        }

    @classmethod
    def get_metadata(cls):
        df = cls._load_data()
        
        # Categorías y conteos
        categorias = df['delito_principal'].value_counts().to_dict()
        
        # Ciudades y centros aproximados
        ciudades_counts = df['ciudad'].value_counts().to_dict()
        ciudades_list = []
        for c, count in ciudades_counts.items():
            sub = df[df['ciudad'] == c]
            ciudades_list.append({
                "nombre": c,
                "count": int(count),
                "lat": float(sub['lat'].mean()),
                "lon": float(sub['lon'].mean())
            })

        return {
            "total_eventos": len(df),
            "ciudades": ciudades_list,
            "categorias": [{"nombre": k, "count": int(v)} for k, v in categorias.items()],
            "centros_urbanos": {
                "Bolivia": {"lat": -16.5, "lon": -64.9, "zoom": 5.2},
                "Santa Cruz": {"lat": -17.7833, "lon": -63.1821, "zoom": 12},
                "La Paz": {"lat": -16.5000, "lon": -68.1300, "zoom": 12},
                "Cochabamba": {"lat": -17.3935, "lon": -66.1570, "zoom": 12},
                "El Alto": {"lat": -16.5050, "lon": -68.1850, "zoom": 12}
            }
        }

