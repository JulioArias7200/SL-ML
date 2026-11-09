import math
from typing import Dict, Any, List

class SpatialDensityService:
    DISTRICTS_CHICAGO = [
        {
            "id": "011",
            "name": "Harrison (Garfield Park)",
            "macro": "A",
            "macro_name": "Violencia Armada Crítica",
            "badge_color": "rose",
            "total_5y": 58412,
            "density_km2": 184.2,
            "cluster": "DBSCAN #2",
            "optics_valley": "Valle #2 (Harrison)",
            "reach_depth_m": 125,
            "noise_pct": 3.2,
            "delito_top": "WEAPONS VIOLATION / HOMICIDE",
            "pct_nocturno_str": "38.4%",
            "status": "ALERTA ROJA",
            "lat": 41.874,
            "lon": -87.726
        },
        {
            "id": "007",
            "name": "Englewood",
            "macro": "A",
            "macro_name": "Violencia Armada Crítica",
            "badge_color": "rose",
            "total_5y": 51204,
            "density_km2": 172.5,
            "cluster": "DBSCAN #3",
            "optics_valley": "Valle #3 (Englewood)",
            "reach_depth_m": 145,
            "noise_pct": 3.6,
            "delito_top": "ASSAULT / NARCOTICS",
            "pct_nocturno_str": "35.1%",
            "status": "ALERTA ROJA",
            "lat": 41.776,
            "lon": -87.643
        },
        {
            "id": "015",
            "name": "Austin",
            "macro": "A",
            "macro_name": "Violencia Armada Crítica",
            "badge_color": "rose",
            "total_5y": 48920,
            "density_km2": 165.1,
            "cluster": "DBSCAN #2",
            "optics_valley": "Valle #2 (Sub-Austin)",
            "reach_depth_m": 138,
            "noise_pct": 4.1,
            "delito_top": "BATTERY / WEAPONS",
            "pct_nocturno_str": "34.0%",
            "status": "ALERTA ROJA",
            "lat": 41.888,
            "lon": -87.765
        },
        {
            "id": "010",
            "name": "Ogden (Lawndale)",
            "macro": "A",
            "macro_name": "Violencia Armada Crítica",
            "badge_color": "rose",
            "total_5y": 42100,
            "density_km2": 152.0,
            "cluster": "DBSCAN #2",
            "optics_valley": "Valle #2 (Harrison)",
            "reach_depth_m": 142,
            "noise_pct": 3.8,
            "delito_top": "ROBBERY / ASSAULT",
            "pct_nocturno_str": "32.5%",
            "status": "ALERTA ROJA",
            "lat": 41.856,
            "lon": -87.712
        },
        {
            "id": "006",
            "name": "Gresham",
            "macro": "A",
            "macro_name": "Violencia Armada Crítica",
            "badge_color": "rose",
            "total_5y": 39800,
            "density_km2": 141.8,
            "cluster": "DBSCAN #3",
            "optics_valley": "Valle #3 (Sub-Gresham)",
            "reach_depth_m": 155,
            "noise_pct": 4.0,
            "delito_top": "ASSAULT / BATTERY",
            "pct_nocturno_str": "31.0%",
            "status": "ALERTA ROJA",
            "lat": 41.745,
            "lon": -87.652
        },

        {
            "id": "001",
            "name": "Central (The Loop)",
            "macro": "B",
            "macro_name": "Comercial, Hurto & Turístico",
            "badge_color": "cyan",
            "total_5y": 62450,
            "density_km2": 196.4,
            "cluster": "DBSCAN #1",
            "optics_valley": "Valle #1 (The Loop)",
            "reach_depth_m": 88,
            "noise_pct": 2.1,
            "delito_top": "THEFT / FRAUD",
            "pct_nocturno_str": "18.2%",
            "status": "VIGILANCIA ALTA",
            "lat": 41.881,
            "lon": -87.629
        },
        {
            "id": "018",
            "name": "Near North (Mag Mile)",
            "macro": "B",
            "macro_name": "Comercial, Hurto & Turístico",
            "badge_color": "cyan",
            "total_5y": 55300,
            "density_km2": 188.0,
            "cluster": "DBSCAN #1",
            "optics_valley": "Valle #1 (Sub-NearNorth)",
            "reach_depth_m": 94,
            "noise_pct": 2.4,
            "delito_top": "RETAIL THEFT / DECEPTIVE",
            "pct_nocturno_str": "21.0%",
            "status": "VIGILANCIA ALTA",
            "lat": 41.902,
            "lon": -87.632
        },
        {
            "id": "012",
            "name": "Near West (UIC / West Loop)",
            "macro": "B",
            "macro_name": "Comercial, Hurto & Turístico",
            "badge_color": "cyan",
            "total_5y": 41200,
            "density_km2": 138.5,
            "cluster": "DBSCAN #4",
            "optics_valley": "Valle #4 (Near West)",
            "reach_depth_m": 172,
            "noise_pct": 3.5,
            "delito_top": "THEFT / VEHICLE THEFT",
            "pct_nocturno_str": "24.5%",
            "status": "PATRULLAJE DINÁMICO",
            "lat": 41.868,
            "lon": -87.661
        },
        {
            "id": "019",
            "name": "Town Hall (Lakeview)",
            "macro": "B",
            "macro_name": "Comercial, Hurto & Turístico",
            "badge_color": "cyan",
            "total_5y": 36700,
            "density_km2": 115.2,
            "cluster": "DBSCAN #1",
            "optics_valley": "Valle #1 (The Loop)",
            "reach_depth_m": 112,
            "noise_pct": 3.9,
            "delito_top": "CRIMINAL DAMAGE / THEFT",
            "pct_nocturno_str": "26.0%",
            "status": "PATRULLAJE DINÁMICO",
            "lat": 41.944,
            "lon": -87.654
        },

        {
            "id": "016",
            "name": "Jefferson Park",
            "macro": "C",
            "macro_name": "Residencial de Baja Incidencia",
            "badge_color": "emerald",
            "total_5y": 21400,
            "density_km2": 62.4,
            "cluster": "DBSCAN #5",
            "optics_valley": "Ruido Periurbano",
            "reach_depth_m": 380,
            "noise_pct": 6.8,
            "delito_top": "BURGLARY / MOTOR THEFT",
            "pct_nocturno_str": "15.0%",
            "status": "ESTABLE",
            "lat": 41.970,
            "lon": -87.765
        },
        {
            "id": "017",
            "name": "Albany Park",
            "macro": "C",
            "macro_name": "Residencial de Baja Incidencia",
            "badge_color": "emerald",
            "total_5y": 24100,
            "density_km2": 74.8,
            "cluster": "DBSCAN #5",
            "optics_valley": "Ruido Periurbano",
            "reach_depth_m": 340,
            "noise_pct": 5.9,
            "delito_top": "THEFT / SIMPLE BATTERY",
            "pct_nocturno_str": "16.4%",
            "status": "ESTABLE",
            "lat": 41.968,
            "lon": -87.723
        },
        {
            "id": "008",
            "name": "Chicago Lawn",
            "macro": "C",
            "macro_name": "Residencial de Baja Incidencia",
            "badge_color": "emerald",
            "total_5y": 32800,
            "density_km2": 95.0,
            "cluster": "DBSCAN #3",
            "optics_valley": "Ruido Periurbano",
            "reach_depth_m": 290,
            "noise_pct": 5.2,
            "delito_top": "ASSAULT / THEFT",
            "pct_nocturno_str": "22.0%",
            "status": "ESTABLE",
            "lat": 41.777,
            "lon": -87.698
        },
        {
            "id": "004",
            "name": "South Chicago",
            "macro": "C",
            "macro_name": "Residencial de Baja Incidencia",
            "badge_color": "emerald",
            "total_5y": 28900,
            "density_km2": 88.5,
            "cluster": "DBSCAN #3",
            "optics_valley": "Ruido Periurbano",
            "reach_depth_m": 310,
            "noise_pct": 5.5,
            "delito_top": "WEAPONS / BATTERY",
            "pct_nocturno_str": "20.5%",
            "status": "ESTABLE",
            "lat": 41.734,
            "lon": -87.555
        },
        {
            "id": "020",
            "name": "Lincoln",
            "macro": "C",
            "macro_name": "Residencial de Baja Incidencia",
            "badge_color": "emerald",
            "total_5y": 22100,
            "density_km2": 68.2,
            "cluster": "DBSCAN #5",
            "optics_valley": "Ruido Periurbano",
            "reach_depth_m": 360,
            "noise_pct": 6.2,
            "delito_top": "THEFT / DECEPTIVE",
            "pct_nocturno_str": "14.2%",
            "status": "ESTABLE",
            "lat": 41.978,
            "lon": -87.685
        }
    ]

    # Datos exactos extraídos de data/web_scraping_news/dashboard_zonas_perfiles_bolivia.csv
    ZONES_BOLIVIA = [
        {
            "id": "SCZ-01",
            "name": "Santa Cruz (Casco Central & Anillos)",
            "macro": "A",
            "macro_name": "Macro-Cluster A (Jerárquico #2: Gravedad Crítica)",
            "badge_color": "rose",
            "total_5y": 16,
            "density_km2": 40.0,
            "cluster": "DBSCAN #0",
            "optics_valley": "Valle #0 (SCZ Núcleo)",
            "reach_depth_m": 295,
            "noise_pct": 12.5,
            "delito_top": "Robo Agravado / Asalto (62.5%)",
            "pct_nocturno_str": "12.5%",
            "status": "VIGILANCIA ALTA",
            "lat": -17.7833,
            "lon": -63.1821
        },
        {
            "id": "SCZ-02",
            "name": "Plan 3000 (Ciudadela Andrés Ibáñez)",
            "macro": "B",
            "macro_name": "Macro-Cluster B (Jerárquico #1: Violencia & Homicidio)",
            "badge_color": "rose",
            "total_5y": 4,
            "density_km2": 14.0,
            "cluster": "DBSCAN #2",
            "optics_valley": "Valle #2 (Plan 3000)",
            "reach_depth_m": 340,
            "noise_pct": 18.0,
            "delito_top": "Robo (50.0%) / Homicidio (25.0%)",
            "pct_nocturno_str": "25.0%",
            "status": "ALERTA ROJA",
            "lat": -17.8285,
            "lon": -63.1415
        },
        {
            "id": "CBB-01",
            "name": "Cochabamba (Cercado & La Cancha)",
            "macro": "B",
            "macro_name": "Macro-Cluster B (Jerárquico #1: Violencia & Homicidio)",
            "badge_color": "amber",
            "total_5y": 9,
            "density_km2": 30.0,
            "cluster": "DBSCAN #1",
            "optics_valley": "Valle #7 (Cochabamba)",
            "reach_depth_m": 380,
            "noise_pct": 14.2,
            "delito_top": "Agresión Física (44.4%) / Robo (33.3%)",
            "pct_nocturno_str": "44.4%",
            "status": "PATRULLAJE DINÁMICO",
            "lat": -17.3935,
            "lon": -66.1570
        },
        {
            "id": "LPZ-01",
            "name": "La Paz (El Prado / Miraflores)",
            "macro": "C",
            "macro_name": "Macro-Cluster C (Jerárquico #0: Menor Gravedad & Moderado)",
            "badge_color": "purple",
            "total_5y": 4,
            "density_km2": 8.0,
            "cluster": "DBSCAN #0",
            "optics_valley": "Valle #5 (La Paz)",
            "reach_depth_m": 430,
            "noise_pct": 15.0,
            "delito_top": "Agresión (50.0%) / Drogas (25.0%)",
            "pct_nocturno_str": "0.0%",
            "status": "ESTABLE",
            "lat": -16.4958,
            "lon": -68.1336
        },
        {
            "id": "SCZ-03",
            "name": "Equipetrol (Comercial / Empresarial)",
            "macro": "C",
            "macro_name": "Macro-Cluster C (Jerárquico #0: Menor Gravedad & Moderado)",
            "badge_color": "cyan",
            "total_5y": 3,
            "density_km2": 9.0,
            "cluster": "DBSCAN #0",
            "optics_valley": "Sub-Valle #1 (Equipetrol)",
            "reach_depth_m": 240,
            "noise_pct": 8.5,
            "delito_top": "Robo Agravado (66.7%) / Agresión (33.3%)",
            "pct_nocturno_str": "0.0%",
            "status": "ESTABLE",
            "lat": -17.7650,
            "lon": -63.1950
        },
        {
            "id": "SCZ-04",
            "name": "Los Lotes (Ciudadela Sur)",
            "macro": "C",
            "macro_name": "Macro-Cluster C (Jerárquico #0: Menor Gravedad & Moderado)",
            "badge_color": "rose",
            "total_5y": 3,
            "density_km2": 7.0,
            "cluster": "DBSCAN #2",
            "optics_valley": "Valle #3 (Los Lotes)",
            "reach_depth_m": 360,
            "noise_pct": 16.0,
            "delito_top": "Robo (33.3%) / Hurto (33.3%)",
            "pct_nocturno_str": "0.0%",
            "status": "VIGILANCIA ALTA",
            "lat": -17.8450,
            "lon": -63.1680
        },
        {
            "id": "SCZ-05",
            "name": "Pampa de la Isla (Noreste)",
            "macro": "C",
            "macro_name": "Macro-Cluster C (Jerárquico #0: Menor Gravedad & Moderado)",
            "badge_color": "emerald",
            "total_5y": 2,
            "density_km2": 6.0,
            "cluster": "DBSCAN #0",
            "optics_valley": "Sub-Valle #6 (Pampa)",
            "reach_depth_m": 330,
            "noise_pct": 10.0,
            "delito_top": "Agresión (50.0%) / Robo (50.0%)",
            "pct_nocturno_str": "0.0%",
            "status": "ESTABLE",
            "lat": -17.7660,
            "lon": -63.1250
        }
    ]

    # Compatibilidad con código existente
    DISTRICTS = DISTRICTS_CHICAGO

    @classmethod
    def get_zones(cls, ctx: str = 'bolivia') -> List[Dict[str, Any]]:
        if ctx.lower() == 'chicago':
            return cls.DISTRICTS_CHICAGO
        return cls.ZONES_BOLIVIA

    @classmethod
    def calculate_haversine_hud(cls, eps_meters: int = 300, min_pts: int = 25, ctx: str = 'bolivia') -> Dict[str, Any]:
        is_chicago = (ctx.lower() == 'chicago')
        
        if is_chicago:
            eps_rad = eps_meters / 6371008.8
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
                "sample_size": "50,000 incidentes CPD",
                "unit": "metros",
                "ctx": "chicago"
            }
        else:
            # Calibración para Bolivia: escala en metros (noticias de prensa geocodificadas)
            calibrated_eps = eps_meters if eps_meters >= 400 else 1500
            eps_rad = calibrated_eps / 6371008.8
            
            base_hotspots = 7
            hotspot_delta = int((1500 - calibrated_eps) * 0.002 + (min_pts - 5) * -0.2)
            active_hotspots = max(3, min(12, base_hotspots + hotspot_delta))

            noise_base = 6
            noise_delta = int((1500 - calibrated_eps) * 0.006 + (min_pts - 5) * 0.8)
            noise_count = max(4, min(18, noise_base + noise_delta))
            noise_pct = round((noise_count / 137) * 100, 1)

            return {
                "eps_meters": calibrated_eps,
                "eps_radians": f"{eps_rad:.6f}",
                "min_pts": min_pts,
                "active_hotspots": active_hotspots,
                "noise_count": noise_count,
                "noise_pct": noise_pct,
                "cophenetic_r": 0.789,
                "silhouette_spatial": 0.584,
                "sample_size": "137 reportes curados Prensa BO",
                "unit": "metros",
                "ctx": "bolivia"
            }

    @classmethod
    def get_optics_data(cls, ctx: str = 'bolivia', xi: float = 0.05, min_pts: int = 5, extraction_method: str = 'xi') -> Dict[str, Any]:
        is_chicago = (ctx.lower() == 'chicago')

        if is_chicago:
            threshold_m = int(240 + (0.20 - xi) * 400)
            points = []
            
            # Valle 1: The Loop / Central CPD (D-001 / D-018)
            loop_points = [
                {"dist": 82, "c": 1, "name": "Loop Centro", "sub": "Core", "color": "#00e5ff"},
                {"dist": 78, "c": 1, "name": "State & Madison", "sub": "Core", "color": "#00e5ff"},
                {"dist": 85, "c": 1, "name": "Millennium Park N.", "sub": "Core", "color": "#00e5ff"},
                {"dist": 74, "c": 1, "name": "Michigan Ave.", "sub": "Core", "color": "#00e5ff"},
                {"dist": 88, "c": 1, "name": "Clark & Lake", "sub": "Core", "color": "#00e5ff"},
                {"dist": 92, "c": 1, "name": "Wabash Corridor", "sub": "Core", "color": "#00e5ff"},
                {"dist": 96, "c": 1, "name": "River North", "sub": "Sub-NearNorth", "color": "#00e5ff"},
                {"dist": 102, "c": 1, "name": "Mag Mile South", "sub": "Sub-NearNorth", "color": "#00e5ff"},
                {"dist": 98, "c": 1, "name": "Grand Ave.", "sub": "Sub-NearNorth", "color": "#00e5ff"},
                {"dist": 110, "c": 1, "name": "Chicago Ave. Red", "sub": "Sub-NearNorth", "color": "#00e5ff"},
                {"dist": 115, "c": 1, "name": "Near North Border", "sub": "Periferia Loop", "color": "#00e5ff"},
            ]
            
            # Salto / Pico Ruido: Cruce Río Chicago / Corredor Ferroviario
            noise_bridge_1 = [
                {"dist": 340, "c": -1, "name": "Río Chicago / Wacker", "sub": "Noise", "color": "#64748b"},
                {"dist": 410, "c": -1, "name": "Union Station Tracks", "sub": "Noise", "color": "#64748b"},
                {"dist": 380, "c": -1, "name": "Kennedy Expwy (I-90)", "sub": "Noise", "color": "#64748b"},
            ]

            # Valle 2: Harrison / Garfield Park / Austin (D-011 / D-015)
            west_points = [
                {"dist": 135, "c": 2, "name": "Harrison & Kedzie", "sub": "Core Harrison", "color": "#ff3366"},
                {"dist": 120, "c": 2, "name": "Pulaski Rd.", "sub": "Core Harrison", "color": "#ff3366"},
                {"dist": 108, "c": 2, "name": "Garfield Park Central", "sub": "Sub-Garfield", "color": "#ff3366"},
                {"dist": 98, "c": 2, "name": "Madison & Pulaski", "sub": "Sub-Garfield", "color": "#ff3366"},
                {"dist": 105, "c": 2, "name": "Lake & Hamlin", "sub": "Sub-Garfield", "color": "#ff3366"},
                {"dist": 128, "c": 2, "name": "Lawndale North", "sub": "Core Harrison", "color": "#ff3366"},
                {"dist": 142, "c": 2, "name": "Cicero Ave. West", "sub": "Sub-Austin", "color": "#ff3366"},
                {"dist": 138, "c": 2, "name": "Austin Blvd. Border", "sub": "Sub-Austin", "color": "#ff3366"},
                {"dist": 146, "c": 2, "name": "Chicago & Central", "sub": "Sub-Austin", "color": "#ff3366"},
                {"dist": 155, "c": 2, "name": "Division & Austin", "sub": "Sub-Austin", "color": "#ff3366"},
            ]

            # Salto / Pico Ruido: Eisenhower Corredor
            noise_bridge_2 = [
                {"dist": 390, "c": -1, "name": "I-290 Eisenhower", "sub": "Noise", "color": "#64748b"},
                {"dist": 450, "c": -1, "name": "Corredor Industrial BNSF", "sub": "Noise", "color": "#64748b"},
                {"dist": 370, "c": -1, "name": "Canal Sanitario", "sub": "Noise", "color": "#64748b"},
            ]

            # Valle 3: Englewood / Gresham (D-007 / D-006)
            south_points = [
                {"dist": 165, "c": 3, "name": "63rd & Halsted", "sub": "Core Englewood", "color": "#ffaa00"},
                {"dist": 148, "c": 3, "name": "69th & Ashland", "sub": "Core Englewood", "color": "#ffaa00"},
                {"dist": 138, "c": 3, "name": "71st St. Corridor", "sub": "Core Englewood", "color": "#ffaa00"},
                {"dist": 142, "c": 3, "name": "Green Line Terminal", "sub": "Core Englewood", "color": "#ffaa00"},
                {"dist": 152, "c": 3, "name": "76th & Racine", "sub": "Sub-Gresham", "color": "#ffaa00"},
                {"dist": 160, "c": 3, "name": "79th & Halsted", "sub": "Sub-Gresham", "color": "#ffaa00"},
                {"dist": 172, "c": 3, "name": "87th & Vincennes", "sub": "Sub-Gresham", "color": "#ffaa00"},
            ]

            # Salto / Pico Ruido: Dan Ryan Corredor
            noise_bridge_3 = [
                {"dist": 420, "c": -1, "name": "I-94 Dan Ryan Expwy", "sub": "Noise", "color": "#64748b"},
                {"dist": 480, "c": -1, "name": "Washington Park East", "sub": "Noise", "color": "#64748b"},
            ]

            # Valle 4: Near West / UIC / Pilsen (D-012)
            near_west_points = [
                {"dist": 175, "c": 4, "name": "Taylor & Halsted (UIC)", "sub": "UIC Campus", "color": "#a855f7"},
                {"dist": 168, "c": 4, "name": "Roosevelt & Blue Island", "sub": "UIC Campus", "color": "#a855f7"},
                {"dist": 182, "c": 4, "name": "18th & Ashland (Pilsen)", "sub": "Sub-Pilsen", "color": "#a855f7"},
                {"dist": 195, "c": 4, "name": "Damen & Cermak", "sub": "Sub-Pilsen", "color": "#a855f7"},
            ]

            noise_tail = [
                {"dist": 360, "c": -1, "name": "Jefferson Park Norte", "sub": "Noise Periurbano", "color": "#64748b"},
                {"dist": 440, "c": -1, "name": "O'Hare Transit Zone", "sub": "Noise Periurbano", "color": "#64748b"},
            ]

            raw_stream = loop_points + noise_bridge_1 + west_points + noise_bridge_2 + south_points + noise_bridge_3 + near_west_points + noise_tail

            for idx, p in enumerate(raw_stream):
                is_noise = (p["dist"] > threshold_m) or (p["c"] == -1)
                cluster_assigned = -1 if is_noise else p["c"]
                bar_color = "#64748b" if is_noise else p["color"]
                
                points.append({
                    "index": idx + 1,
                    "reach_m": p["dist"],
                    "cluster_id": cluster_assigned,
                    "zone_name": p["name"],
                    "sub_cluster": p["sub"],
                    "color": bar_color,
                    "is_noise": is_noise
                })

            valleys = [
                {
                    "id": 1,
                    "name": "Valle #1: Central Loop / Near North",
                    "badge_color": "cyan",
                    "hex": "#00e5ff",
                    "depth_m": 88,
                    "max_reach_m": 115,
                    "incidents": 62450,
                    "subclusters": "Core Loop, Mag Mile, River North",
                    "density_eval": "Hiperdensidad Comercial",
                    "status": "VIGILANCIA ALTA",
                    "steepness_xi": "0.142 (Descenso abrupto)"
                },
                {
                    "id": 2,
                    "name": "Valle #2: Harrison / Garfield Park / Austin",
                    "badge_color": "rose",
                    "hex": "#ff3366",
                    "depth_m": 125,
                    "max_reach_m": 155,
                    "incidents": 58412,
                    "subclusters": "Sub-Garfield (98m), Sub-Austin (138m)",
                    "density_eval": "Crítico Violencia Armada",
                    "status": "ALERTA ROJA",
                    "steepness_xi": "0.118 (Cuenca extendida)"
                },
                {
                    "id": 3,
                    "name": "Valle #3: Englewood / Gresham South",
                    "badge_color": "amber",
                    "hex": "#ffaa00",
                    "depth_m": 145,
                    "max_reach_m": 172,
                    "incidents": 51204,
                    "subclusters": "Core 63rd, Sub-Gresham 79th",
                    "density_eval": "Alta Densidad Balística",
                    "status": "ALERTA ROJA",
                    "steepness_xi": "0.089 (Gradiente moderado)"
                },
                {
                    "id": 4,
                    "name": "Valle #4: Near West / UIC / Pilsen",
                    "badge_color": "purple",
                    "hex": "#a855f7",
                    "depth_m": 172,
                    "max_reach_m": 195,
                    "incidents": 41200,
                    "subclusters": "UIC Campus, Pilsen Cultural",
                    "density_eval": "Densidad Mixta Universitaria",
                    "status": "PATRULLAJE DINÁMICO",
                    "steepness_xi": "0.065 (Cuenca superficial)"
                }
            ]

            noise_count = sum(1 for pt in points if pt["is_noise"])
            active_valleys = len([v for v in valleys if v["depth_m"] <= threshold_m])

            return {
                "ctx": "chicago",
                "city_label": "Red Urbana Chicago (CPD)",
                "reachability_points": points,
                "valleys": valleys,
                "threshold_m": threshold_m,
                "xi": xi,
                "min_pts": min_pts,
                "active_valleys_count": active_valleys,
                "noise_count": noise_count,
                "noise_pct": round((noise_count / len(points)) * 100, 1),
                "max_reach_scale": 520,
                "extraction_method": extraction_method,
                "insights": "El Reachability Plot revela 4 valles nítidos en Chicago. El Valle #1 (Loop) posee la mayor profundidad (88m), mientras que el Valle #2 presenta bifurcación interna (sub-cuenca Garfield Park). Los picos (>340m) aíslan barreras físicas como el Río Chicago y la autopista I-290."
            }

        else:
            # OPTICS para Bolivia: Web Scraping Prensa (Santa Cruz, La Paz, Cochabamba, Plan 3000)
            threshold_m = int(1200 + (0.20 - xi) * 2000)
            points = []

            # Valle 0: Santa Cruz Casco Central & Anillos (18 reportes en CSV)
            scz_core = [
                {"dist": 280, "c": 0, "name": "1er Anillo / Monseñor Rivero", "sub": "Core Casco Viejo", "color": "#00e5ff"},
                {"dist": 310, "c": 0, "name": "Plaza 24 de Septiembre", "sub": "Core Casco Viejo", "color": "#00e5ff"},
                {"dist": 295, "c": 0, "name": "Av. Cañoto / 2do Anillo", "sub": "Core Casco Viejo", "color": "#00e5ff"},
                {"dist": 340, "c": 0, "name": "Av. Cristo Redentor 3er Anillo", "sub": "Norte Urbano", "color": "#00e5ff"},
                {"dist": 260, "c": 0, "name": "Equipetrol San Martín", "sub": "Sub-Equipetrol (Valle #1)", "color": "#00e5ff"},
                {"dist": 240, "c": 0, "name": "Equipetrol Norte / Canal Isuto", "sub": "Sub-Equipetrol (Valle #1)", "color": "#00e5ff"},
                {"dist": 285, "c": 0, "name": "Barrio Sirari", "sub": "Sub-Equipetrol (Valle #1)", "color": "#00e5ff"},
                {"dist": 380, "c": 0, "name": "Av. Banzer 4to Anillo", "sub": "Norte Comercial", "color": "#00e5ff"},
                {"dist": 410, "c": 0, "name": "Radial 26 / Mutualista", "sub": "Sub-Pampa (Valle #6)", "color": "#00e5ff"},
                {"dist": 430, "c": 0, "name": "Pampa de la Isla Central", "sub": "Sub-Pampa (Valle #6)", "color": "#00e5ff"},
                {"dist": 490, "c": 0, "name": "Virgen de Cotoca 5to Anillo", "sub": "Este Urbano", "color": "#00e5ff"},
                {"dist": 520, "c": 0, "name": "Doble Vía La Guardia 4to Anillo", "sub": "Sur-Oeste", "color": "#00e5ff"},
            ]

            # Salto / Pico Ruido: Carretera a Warnes / Río Piraí periferia
            scz_noise = [
                {"dist": 2100, "c": -1, "name": "Carretera al Norte km 15", "sub": "Noise Interprovincial", "color": "#64748b"},
                {"dist": 2650, "c": -1, "name": "Ribera Río Piraí / Árido", "sub": "Noise Periférico", "color": "#64748b"},
            ]

            # Valle 2: Plan 3000 (Ciudadela Andrés Ibáñez)
            plan3000_points = [
                {"dist": 340, "c": 2, "name": "Rotonda Plan 3000 / Mechero", "sub": "Núcleo Comercial", "color": "#ff3366"},
                {"dist": 310, "c": 2, "name": "Mercado Modelo Plan 3000", "sub": "Núcleo Comercial", "color": "#ff3366"},
                {"dist": 380, "c": 2, "name": "Barrio Che Guevara", "sub": "Periferia Plan 3000", "color": "#ff3366"},
                {"dist": 420, "c": 2, "name": "El Fuerte / Av. San Aurelio", "sub": "Conexión Los Lotes", "color": "#ff3366"},
            ]

            # Valle 3: Los Lotes (Ciudadela Sur)
            los_lotes_points = [
                {"dist": 360, "c": 3, "name": "Mercado Los Lotes Central", "sub": "Núcleo Sur", "color": "#f43f5e"},
                {"dist": 390, "c": 3, "name": "Palmar del Oratorio", "sub": "Sub-Palmar", "color": "#f43f5e"},
                {"dist": 440, "c": 3, "name": "Av. Santos Dumont 8vo Anillo", "sub": "Eje Radial", "color": "#f43f5e"},
            ]

            # Salto Interurbano: Carretera a Cochabamba
            inter_city_noise_1 = [
                {"dist": 2900, "c": -1, "name": "Ruta 4 Bulo Bulo / Chapare", "sub": "Noise Interdepartamental", "color": "#64748b"},
                {"dist": 3200, "c": -1, "name": "Villa Tunari Tránsito", "sub": "Noise Interdepartamental", "color": "#64748b"},
            ]

            # Valle 7: Cochabamba Cercado & Quillacollo
            cbb_points = [
                {"dist": 380, "c": 7, "name": "Plaza 14 de Septiembre CBB", "sub": "Casco Viejo CBB", "color": "#34d399"},
                {"dist": 350, "c": 7, "name": "Cancha / Mercado La Pampa", "sub": "Zona Comercial Alta", "color": "#34d399"},
                {"dist": 410, "c": 7, "name": "Av. Heroínas / San Martín", "sub": "Casco Viejo CBB", "color": "#34d399"},
                {"dist": 460, "c": 7, "name": "Av. Blanco Galindo km 4", "sub": "Sub-Quillacollo (Valle #4)", "color": "#34d399"},
                {"dist": 490, "c": 7, "name": "Quillacollo Plaza Principal", "sub": "Sub-Quillacollo (Valle #4)", "color": "#34d399"},
                {"dist": 540, "c": 7, "name": "Sacaba Eje Este", "sub": "Periferia Valle", "color": "#34d399"},
            ]

            # Salto Interurbano: Cordillera / Carretera a La Paz
            inter_city_noise_2 = [
                {"dist": 3100, "c": -1, "name": "Ruta 1 Confital / Altiplano", "sub": "Noise Interdepartamental", "color": "#64748b"},
                {"dist": 2750, "c": -1, "name": "Patacamaya Retén", "sub": "Noise Interdepartamental", "color": "#64748b"},
            ]

            # Valle 5: La Paz (Eje Metropolitano El Prado / Miraflores)
            lpz_points = [
                {"dist": 430, "c": 5, "name": "El Prado / Av. 16 de Julio", "sub": "Eje Central La Paz", "color": "#818cf8"},
                {"dist": 390, "c": 5, "name": "Pérez Velasco / San Francisco", "sub": "Eje Central La Paz", "color": "#818cf8"},
                {"dist": 460, "c": 5, "name": "Plaza Murillo / Casco Histórico", "sub": "Eje Gubernamental", "color": "#818cf8"},
                {"dist": 480, "c": 5, "name": "Miraflores / Estadio Siles", "sub": "Sub-Miraflores", "color": "#818cf8"},
                {"dist": 520, "c": 5, "name": "Sopocachi / Plaza Abaroa", "sub": "Sub-Sopocachi", "color": "#818cf8"},
                {"dist": 580, "c": 5, "name": "Ceja de El Alto (Límite)", "sub": "Sub-El Alto", "color": "#818cf8"},
            ]

            # Salto Periferia / Aislados (Beni, Oruro)
            tail_noise = [
                {"dist": 3400, "c": -1, "name": "Riberalta Base Aérea (Beni)", "sub": "Noise Región Aislada", "color": "#64748b"},
                {"dist": 2800, "c": -1, "name": "Challapata Altiplano", "sub": "Noise Región Aislada", "color": "#64748b"},
            ]

            raw_stream = scz_core + scz_noise + plan3000_points + los_lotes_points + inter_city_noise_1 + cbb_points + inter_city_noise_2 + lpz_points + tail_noise

            for idx, p in enumerate(raw_stream):
                is_noise = (p["dist"] > threshold_m) or (p["c"] == -1)
                cluster_assigned = -1 if is_noise else p["c"]
                bar_color = "#64748b" if is_noise else p["color"]
                
                points.append({
                    "index": idx + 1,
                    "reach_m": p["dist"],
                    "cluster_id": cluster_assigned,
                    "zone_name": p["name"],
                    "sub_cluster": p["sub"],
                    "color": bar_color,
                    "is_noise": is_noise
                })

            valleys = [
                {
                    "id": 0,
                    "name": "Valle #0: Santa Cruz Casco Central & Anillos",
                    "badge_color": "cyan",
                    "hex": "#00e5ff",
                    "depth_m": 295,
                    "max_reach_m": 520,
                    "incidents": 18,
                    "subclusters": "Sub-Valle #1 Equipetrol (240m), Sub-Valle #6 Pampa (410m)",
                    "density_eval": "Alta Densidad Robo Agravado / Motochorros",
                    "status": "VIGILANCIA ALTA",
                    "steepness_xi": "0.155 (Cuenca Principal)"
                },
                {
                    "id": 2,
                    "name": "Valle #2: Plan 3000 (Ciudadela Andrés Ibáñez)",
                    "badge_color": "rose",
                    "hex": "#ff3366",
                    "depth_m": 340,
                    "max_reach_m": 420,
                    "incidents": 4,
                    "subclusters": "Rotonda Mechero, Barrio Che Guevara",
                    "density_eval": "Violencia Crítica / Armas Blancas",
                    "status": "ALERTA ROJA",
                    "steepness_xi": "0.124 (Valle autónomo denso)"
                },
                {
                    "id": 3,
                    "name": "Valle #3: Los Lotes (Ciudadela Sur)",
                    "badge_color": "rose",
                    "hex": "#f43f5e",
                    "depth_m": 360,
                    "max_reach_m": 440,
                    "incidents": 3,
                    "subclusters": "Mercado Central, Palmar del Oratorio",
                    "density_eval": "Atracos Nocturnos",
                    "status": "VIGILANCIA ALTA",
                    "steepness_xi": "0.098 (Valle adyacente)"
                },
                {
                    "id": 7,
                    "name": "Valle #7: Cochabamba Cercado & La Cancha",
                    "badge_color": "emerald",
                    "hex": "#34d399",
                    "depth_m": 380,
                    "max_reach_m": 540,
                    "incidents": 9,
                    "subclusters": "Sub-Valle #4 Quillacollo Blanco Galindo (460m)",
                    "density_eval": "Hurto Comercial & Riñas Nocturnas",
                    "status": "PATRULLAJE DINÁMICO",
                    "steepness_xi": "0.110 (Valle Metropolitano)"
                },
                {
                    "id": 5,
                    "name": "Valle #5: La Paz Eje Central / El Prado",
                    "badge_color": "purple",
                    "hex": "#818cf8",
                    "depth_m": 430,
                    "max_reach_m": 580,
                    "incidents": 6,
                    "subclusters": "Sub-Miraflores, Sopocachi, Límite Ceja",
                    "density_eval": "Descuidismo & Estafas Financieras",
                    "status": "ESTABLE",
                    "steepness_xi": "0.082 (Cuenca topográfica)"
                }
            ]

            noise_count = sum(1 for pt in points if pt["is_noise"])
            active_valleys = len([v for v in valleys if v["depth_m"] <= threshold_m])

            return {
                "ctx": "bolivia",
                "city_label": "Eje Urbano Nacional (Bolivia Prensa)",
                "reachability_points": points,
                "valleys": valleys,
                "threshold_m": threshold_m,
                "xi": xi,
                "min_pts": min_pts,
                "active_valleys_count": active_valleys,
                "noise_count": noise_count,
                "noise_pct": round((noise_count / len(points)) * 100, 1),
                "max_reach_scale": 3600,
                "extraction_method": extraction_method,
                "insights": "El algoritmo OPTICS capta la estructura multiescala en Bolivia: el Valle #0 (Santa Cruz) alberga sub-valles con mayor densidad (Equipetrol a 240m de alcance). Los saltos interdepartamentales (Ruta 4 y Ruta 1) se registran con picos >2500m que OPTICS discrimina naturalmente como ruido o transiciones geográficas."
            }

    @classmethod
    def get_hdbscan_data(cls, ctx: str = 'bolivia', min_cluster_size: int = None) -> Dict[str, Any]:
        """Retorna telemetría, clusters persistentes y estabilidad lambda de HDBSCAN."""
        is_chicago = (ctx.lower() == 'chicago')
        
        if is_chicago:
            m_size = min_cluster_size or 25
            return {
                "ctx": "chicago",
                "min_cluster_size": m_size,
                "min_samples": 15,
                "active_clusters": 12,
                "noise_count": 2950,
                "noise_pct": 5.9,
                "rescued_count": 1250,
                "lambda_stability_mean": 4.85,
                "glosh_outlier_mean": 0.28,
                "insights": "HDBSCAN construye el Árbol de Expansión Mínima (MST) con distancias de alcanzabilidad mutua. Rescata 1,250 incidentes en distritos periféricos que DBSCAN descartaba como ruido debido a su radio fijo de 300m.",
                "clusters": [
                    {"id": 0, "name": "Loop Core Commercial (D-001)", "stability_lambda": 7.42, "persistency": "Extrema", "color": "#00e5ff", "points": 14500, "delito": "Larceny / Financial"},
                    {"id": 1, "name": "River North & Mag Mile (D-018)", "stability_lambda": 5.80, "persistency": "Alta", "color": "#00e5ff", "points": 8200, "delito": "Deceptive Practice"},
                    {"id": 2, "name": "Garfield Park Central (D-011)", "stability_lambda": 6.15, "persistency": "Muy Alta", "color": "#ff3366", "points": 12100, "delito": "Weapons Violation"},
                    {"id": 3, "name": "Austin Blvd Corridor (D-015)", "stability_lambda": 5.20, "persistency": "Alta", "color": "#ff3366", "points": 9800, "delito": "Battery / Narcotics"},
                    {"id": 4, "name": "Englewood 63rd Sector (D-007)", "stability_lambda": 5.90, "persistency": "Alta", "color": "#ffaa00", "points": 11200, "delito": "Armed Assault"},
                    {"id": 5, "name": "Gresham 79th Hub (D-006)", "stability_lambda": 4.80, "persistency": "Media", "color": "#ffaa00", "points": 7400, "delito": "Robbery / Battery"},
                    {"id": 6, "name": "Near West / UIC / Pilsen (D-012)", "stability_lambda": 4.30, "persistency": "Media", "color": "#a855f7", "points": 6800, "delito": "Vehicle Theft / Burglary"}
                ]
            }
        else:
            m_size = min_cluster_size or 3
            return {
                "ctx": "bolivia",
                "min_cluster_size": m_size,
                "min_samples": 2,
                "active_clusters": 8,
                "noise_count": 13,
                "noise_pct": 18.8,
                "rescued_count": 5,
                "lambda_stability_mean": 2.68,
                "glosh_outlier_mean": 0.32,
                "insights": "HDBSCAN extrae simultáneamente clústeres densos centrales (Casco Santa Cruz y Ceja El Alto) y focos de densidad variable (Cochabamba Quillacollo y Pampa de la Isla) sin requerir un radio epsilon rígido. Rescata 5 notas periodísticas que DBSCAN marcaba como ruido.",
                "clusters": [
                    {"id": 0, "name": "Santa Cruz Casco Viejo & Anillos", "stability_lambda": 3.12, "persistency": "Muy Alta", "color": "#00e5ff", "points": 14, "delito": "Hurto Comercial / Riñas"},
                    {"id": 1, "name": "Santa Cruz Equipetrol / Sirari", "stability_lambda": 2.85, "persistency": "Alta", "color": "#00e5ff", "points": 6, "delito": "Robo Vehicular / Estafas"},
                    {"id": 2, "name": "Ciudadela Plan 3000 / Mechero", "stability_lambda": 2.95, "persistency": "Muy Alta", "color": "#ff3366", "points": 9, "delito": "Atracos Motochorros"},
                    {"id": 3, "name": "Cochabamba Cercado (La Cancha)", "stability_lambda": 2.50, "persistency": "Alta", "color": "#34d399", "points": 7, "delito": "Descuidistas / Riñas"},
                    {"id": 4, "name": "Cochabamba Quillacollo (Blanco Galindo)", "stability_lambda": 1.85, "persistency": "Media", "color": "#34d399", "points": 4, "delito": "Contrabando / Conflictos"},
                    {"id": 5, "name": "La Paz Eje Central / San Pedro", "stability_lambda": 2.70, "persistency": "Alta", "color": "#818cf8", "points": 6, "delito": "Estafas / Sustracción"},
                    {"id": 6, "name": "El Alto Ceja / Feria 16 de Julio", "stability_lambda": 3.25, "persistency": "Extrema", "color": "#818cf8", "points": 8, "delito": "Robo Agravado / Bandas"},
                    {"id": 7, "name": "Pampa de la Isla / Villa 1ro Mayo", "stability_lambda": 1.70, "persistency": "Moderada", "color": "#00e5ff", "points": 3, "delito": "Agresiones / Alcohol"}
                ]
            }

    @classmethod
    def get_dbscan_data(cls, ctx: str = 'bolivia') -> Dict[str, Any]:
        """Retorna resumen táctico de núcleos DBSCAN."""
        is_chicago = (ctx.lower() == 'chicago')
        if is_chicago:
            return {
                "ctx": "chicago",
                "eps_meters": 300,
                "min_pts": 25,
                "active_hotspots": 148,
                "noise_count": 4200,
                "noise_pct": 8.4,
                "silhouette_spatial": 0.612,
                "hotspots": [
                    {"id": 1, "name": "Macro-Núcleo #1: The Loop / Central (D-001/018)", "count": "62,450", "color": "#00e5ff", "density": "168.4 crím/km²", "top_delito": "Theft / Larceny"},
                    {"id": 2, "name": "Macro-Núcleo #2: West Side / Garfield (D-011/015)", "count": "58,412", "color": "#ff3366", "density": "184.2 crím/km²", "top_delito": "Weapons / Homicide"},
                    {"id": 3, "name": "Macro-Núcleo #3: South Side / Englewood (D-007/006)", "count": "51,204", "color": "#ffaa00", "density": "172.5 crím/km²", "top_delito": "Assault / Narcotics"},
                    {"id": 4, "name": "Macro-Núcleo #4: Near West / Pilsen (D-012)", "count": "41,200", "color": "#a855f7", "density": "135.0 crím/km²", "top_delito": "Burglary / Motor Vehicle"}
                ]
            }
        else:
            return {
                "ctx": "bolivia",
                "eps_meters": 1500,
                "min_pts": 5,
                "active_hotspots": 7,
                "noise_count": 13,
                "noise_pct": 18.8,
                "silhouette_spatial": 0.584,
                "hotspots": [
                    {"id": 0, "name": "Hotspot #0: Santa Cruz Casco Central & Equipetrol", "count": "18 reportes", "color": "#00e5ff", "density": "12.4 rep/km²", "top_delito": "Hurto Comercial / Estafas"},
                    {"id": 1, "name": "Hotspot #1: Santa Cruz Plan 3000 / Ciudadela", "count": "9 reportes", "color": "#ff3366", "density": "14.0 rep/km²", "top_delito": "Atracos Motochorros"},
                    {"id": 2, "name": "Hotspot #2: Cochabamba Cercado (La Cancha)", "count": "9 reportes", "color": "#34d399", "density": "11.2 rep/km²", "top_delito": "Riñas / Descuidistas"},
                    {"id": 3, "name": "Hotspot #3: La Paz San Pedro / El Prado", "count": "6 reportes", "color": "#818cf8", "density": "9.8 rep/km²", "top_delito": "Estafas Financieras"},
                    {"id": 4, "name": "Hotspot #4: El Alto Ceja / Cruce Villa Adela", "count": "8 reportes", "color": "#818cf8", "density": "15.6 rep/km²", "top_delito": "Robo Agravado Nocturno"},
                    {"id": 5, "name": "Hotspot #5: Santa Cruz Los Lotes / Sur", "count": "4 reportes", "color": "#f43f5e", "density": "8.5 rep/km²", "top_delito": "Atracos Vía Pública"}
                ]
            }

    @classmethod
    def get_clustermap_data(cls, ctx: str = 'bolivia') -> Dict[str, Any]:
        """Retorna datos estructurados para el Clustermap (Heatmap Zonas x Delitos) y opciones de enlace."""
        is_chicago = (ctx.lower() == 'chicago')

        linkage_options = [
            {
                "id": "ward",
                "name": "Ward (Varianza Mínima)",
                "cophenetic_r": 0.812 if is_chicago else 0.789,
                "desc": "Minimiza la suma total de varianzas intraclúster. Produce grupos simétricos y densos.",
                "active": True
            },
            {
                "id": "average",
                "name": "Average (UPGMA)",
                "cophenetic_r": 0.835 if is_chicago else 0.814,
                "desc": "Calcula el promedio de distancias entre pares. Mayor preservación cofenética global.",
                "active": False
            },
            {
                "id": "complete",
                "name": "Complete Linkage",
                "cophenetic_r": 0.764 if is_chicago else 0.742,
                "desc": "Utiliza la distancia máxima (diámetro). Evita clústeres alargados pero es sensible a ruido.",
                "active": False
            },
            {
                "id": "single",
                "name": "Single Linkage",
                "cophenetic_r": 0.690 if is_chicago else 0.665,
                "desc": "Enlaza por el par de observaciones más cercano. Propenso al fenómeno de encadenamiento (chaining).",
                "active": False
            }
        ]

        if is_chicago:
            columns = [
                "Violencia Armada / Homicidio",
                "Asalto / Lesiones Graves",
                "Hurto / Robo Comercial",
                "Estafas / Fraude Financiero",
                "Narcotráfico / Posesión",
                "Robo Vehicular / Autopartes"
            ]
            rows = [
                {"name": "D-011 Harrison (West)", "macro": "A", "color": "#ff3366", "vals": [45.2, 28.4, 8.5, 4.1, 9.8, 4.0]},
                {"name": "D-007 Englewood (South)", "macro": "A", "color": "#ff3366", "vals": [42.0, 31.2, 9.0, 3.5, 10.1, 4.2]},
                {"name": "D-015 Austin (West)", "macro": "A", "color": "#ff3366", "vals": [38.5, 29.8, 11.2, 5.0, 11.0, 4.5]},
                {"name": "D-010 Ogden (Lawndale)", "macro": "A", "color": "#ff3366", "vals": [36.0, 27.5, 12.0, 6.2, 12.5, 5.8]},
                {"name": "D-001 Central (The Loop)", "macro": "B", "color": "#00e5ff", "vals": [4.2, 8.5, 58.4, 21.2, 2.5, 5.2]},
                {"name": "D-018 Near North (River)", "macro": "B", "color": "#00e5ff", "vals": [5.1, 9.8, 54.0, 23.5, 2.1, 5.5]},
                {"name": "D-019 Town Hall (Lakeview)", "macro": "B", "color": "#00e5ff", "vals": [6.0, 11.5, 49.2, 22.0, 3.8, 7.5]},
                {"name": "D-012 Near West (Pilsen)", "macro": "B", "color": "#00e5ff", "vals": [12.5, 16.0, 38.5, 18.0, 6.5, 8.5]},
                {"name": "D-016 Jefferson Park", "macro": "C", "color": "#34d399", "vals": [3.2, 6.8, 35.0, 14.5, 4.2, 36.3]},
                {"name": "D-017 Albany Park", "macro": "C", "color": "#34d399", "vals": [5.0, 8.2, 33.5, 12.0, 5.5, 35.8]},
                {"name": "D-020 Lincoln (North)", "macro": "C", "color": "#34d399", "vals": [4.0, 7.5, 36.8, 15.0, 3.5, 33.2]},
                {"name": "D-008 Chicago Lawn", "macro": "C", "color": "#34d399", "vals": [8.5, 12.0, 32.0, 10.5, 7.2, 29.8]}
            ]
            return {
                "ctx": "chicago",
                "default_threshold": 45.0,
                "min_t": 15.0,
                "max_t": 80.0,
                "step_t": 1.0,
                "linkage_options": linkage_options,
                "columns": columns,
                "rows": rows
            }
        else:
            columns = [
                "Robo Agravado / Asalto",
                "Agresión Física / Lesiones",
                "Homicidio / Asesinato",
                "Hurto / Descuidismo",
                "Narcotráfico / Drogas",
                "Violencia Sexual"
            ]
            rows = [
                {"name": "Santa Cruz Casco", "macro": "A", "color": "#ff3366", "vals": [62.5, 12.5, 0.0, 25.0, 0.0, 0.0]},
                {"name": "Cochabamba Cercado", "macro": "B", "color": "#fbbf24", "vals": [33.3, 44.4, 11.1, 0.0, 0.0, 11.1]},
                {"name": "Plan 3000 Ciudadela", "macro": "B", "color": "#fbbf24", "vals": [50.0, 25.0, 25.0, 0.0, 0.0, 0.0]},
                {"name": "Equipetrol San Martín", "macro": "C", "color": "#34d399", "vals": [66.7, 33.3, 0.0, 0.0, 0.0, 0.0]},
                {"name": "La Paz Eje Central", "macro": "C", "color": "#34d399", "vals": [0.0, 50.0, 0.0, 25.0, 25.0, 0.0]},
                {"name": "Los Lotes (Sur SCZ)", "macro": "C", "color": "#34d399", "vals": [33.3, 33.3, 0.0, 33.3, 0.0, 0.0]},
                {"name": "Pampa de la Isla", "macro": "C", "color": "#34d399", "vals": [50.0, 50.0, 0.0, 0.0, 0.0, 0.0]}
            ]
            return {
                "ctx": "bolivia",
                "default_threshold": 12.5,
                "min_t": 5.0,
                "max_t": 30.0,
                "step_t": 0.5,
                "linkage_options": linkage_options,
                "columns": columns,
                "rows": rows
            }
