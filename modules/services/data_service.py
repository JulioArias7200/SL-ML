import os

class DataService:
    @staticmethod
    def get_dashboard_summary():
        return {
            "total_records": 842119,
            "period": "2020 - 2025",
            "active_hotspots": 148,
            "noise_records": 4200,
            "noise_pct": 3.2,
            "arrest_rate": 18.4,
            "domestic_pct": 14.8,
            "districts_count": 22,
            "top_crimes": [
                {"name": "THEFT (Hurto)", "count": 218450, "pct": 25.9, "color": "#00e5ff"},
                {"name": "BATTERY (Agresión simple)", "count": 164210, "pct": 19.5, "color": "#ff3366"},
                {"name": "CRIMINAL DAMAGE (Daño a propiedad)", "count": 98400, "pct": 11.7, "color": "#fbbf24"},
                {"name": "ASSAULT (Asalto agravado)", "count": 78900, "pct": 9.4, "color": "#ff5c8a"},
                {"name": "DECEPTIVE PRACTICE (Fraude)", "count": 64300, "pct": 7.6, "color": "#9d4edd"},
                {"name": "ROBBERY (Robo agravado)", "count": 48200, "pct": 5.7, "color": "#f97316"},
                {"name": "MOTOR VEHICLE THEFT (Robo vehículo)", "count": 42800, "pct": 5.1, "color": "#38bdf8"},
                {"name": "OTROS DELITOS", "count": 126859, "pct": 15.1, "color": "#64748b"}
            ],
            "hardware_telemetry": {
                "gpu": "NVIDIA T4 16GB",
                "vram_used": "6.7 GB",
                "vram_total": "16.0 GB",
                "vram_pct": 41.8,
                "status": "ONLINE (GPU T4)",
                "latency_ms": 16.8
            }
        }
