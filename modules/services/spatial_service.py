class SpatialDensityService:
    DISTRICTS = [
        {"id": "011", "name": "Harrison (Garfield Park)", "macro": "A", "macro_name": "Violencia Armada Crítica", "badge_color": "rose", "total_5y": 58412, "density_km2": 184.2, "cluster": "DBSCAN #2", "noise_pct": 3.2, "status": "ALERTA ROJA"},
        {"id": "007", "name": "Englewood", "macro": "A", "macro_name": "Violencia Armada Crítica", "badge_color": "rose", "total_5y": 51204, "density_km2": 172.5, "cluster": "DBSCAN #3", "noise_pct": 3.6, "status": "ALERTA ROJA"},
        {"id": "015", "name": "Austin", "macro": "A", "macro_name": "Violencia Armada Crítica", "badge_color": "rose", "total_5y": 48920, "density_km2": 165.1, "cluster": "DBSCAN #2", "noise_pct": 4.1, "status": "ALERTA ROJA"},
        {"id": "010", "name": "Ogden (Lawndale)", "macro": "A", "macro_name": "Violencia Armada Crítica", "badge_color": "rose", "total_5y": 42100, "density_km2": 152.0, "cluster": "DBSCAN #2", "noise_pct": 3.8, "status": "ALERTA ROJA"},
        {"id": "006", "name": "Gresham", "macro": "A", "macro_name": "Violencia Armada Crítica", "badge_color": "rose", "total_5y": 39800, "density_km2": 141.8, "cluster": "DBSCAN #3", "noise_pct": 4.0, "status": "ALERTA ROJA"},

        {"id": "001", "name": "Central (The Loop)", "macro": "B", "macro_name": "Comercial, Hurto & Turístico", "badge_color": "cyan", "total_5y": 62450, "density_km2": 196.4, "cluster": "DBSCAN #1", "noise_pct": 2.1, "status": "VIGILANCIA ALTA"},
        {"id": "018", "name": "Near North (Mag Mile)", "macro": "B", "macro_name": "Comercial, Hurto & Turístico", "badge_color": "cyan", "total_5y": 55300, "density_km2": 188.0, "cluster": "DBSCAN #1", "noise_pct": 2.4, "status": "VIGILANCIA ALTA"},
        {"id": "012", "name": "Near West (UIC / West Loop)", "macro": "B", "macro_name": "Comercial, Hurto & Turístico", "badge_color": "cyan", "total_5y": 41200, "density_km2": 138.5, "cluster": "DBSCAN #4", "noise_pct": 3.5, "status": "PATRULLAJE DINÁMICO"},
        {"id": "019", "name": "Town Hall (Lakeview)", "macro": "B", "macro_name": "Comercial, Hurto & Turístico", "badge_color": "cyan", "total_5y": 36700, "density_km2": 115.2, "cluster": "DBSCAN #1", "noise_pct": 3.9, "status": "PATRULLAJE DINÁMICO"},

        {"id": "016", "name": "Jefferson Park", "macro": "C", "macro_name": "Residencial de Baja Incidencia", "badge_color": "emerald", "total_5y": 21400, "density_km2": 62.4, "cluster": "DBSCAN #5", "noise_pct": 6.8, "status": "ESTABLE"},
        {"id": "017", "name": "Albany Park", "macro": "C", "macro_name": "Residencial de Baja Incidencia", "badge_color": "emerald", "total_5y": 24100, "density_km2": 74.8, "cluster": "DBSCAN #5", "noise_pct": 5.9, "status": "ESTABLE"},
        {"id": "008", "name": "Chicago Lawn", "macro": "C", "macro_name": "Residencial de Baja Incidencia", "badge_color": "emerald", "total_5y": 32800, "density_km2": 95.0, "cluster": "DBSCAN #3", "noise_pct": 5.2, "status": "ESTABLE"},
        {"id": "004", "name": "South Chicago", "macro": "C", "macro_name": "Residencial de Baja Incidencia", "badge_color": "emerald", "total_5y": 28900, "density_km2": 88.5, "cluster": "DBSCAN #3", "noise_pct": 5.5, "status": "ESTABLE"},
        {"id": "020", "name": "Lincoln", "macro": "C", "macro_name": "Residencial de Baja Incidencia", "badge_color": "emerald", "total_5y": 22100, "density_km2": 68.2, "cluster": "DBSCAN #5", "noise_pct": 6.2, "status": "ESTABLE"}
    ]

    @classmethod
    def calculate_haversine_hud(cls, eps_meters: int = 300, min_pts: int = 25):
        # Conversión a radianes: eps / R_tierra (6371008 m)
        eps_rad = eps_meters / 6371008.8
        
        # Modelo heurístico de respuesta del clustering ante variación de radio
        # A mayor eps -> se agrupan más puntos, menos ruido, clusters más grandes y consolidados
        base_hotspots = 148
        hotspot_delta = int((300 - eps_meters) * 0.15 + (min_pts - 25) * -1.2)
        active_hotspots = max(45, min(230, base_hotspots + hotspot_delta))

        noise_base = 4200
        noise_delta = int((300 - eps_meters) * 8.5 + (min_pts - 25) * 45)
        noise_count = max(1800, min(8500, noise_base + noise_delta))
        noise_pct = round((noise_count / 50000) * 100, 1)

        return {
            "eps_meters": eps_meters,
            "eps_radians": f"{eps_rad:.6f}",
            "min_pts": min_pts,
            "active_hotspots": active_hotspots,
            "noise_count": noise_count,
            "noise_pct": noise_pct,
            "cophenetic_r": 0.812,
            "silhouette_spatial": 0.612,
            "sample_size": "50,000 folium"
        }
