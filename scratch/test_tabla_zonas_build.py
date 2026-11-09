import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import math
import numpy as np
import pandas as pd
from modules.services.spatial_service import SpatialDensityService

def prototype_tabla_zonas(ctx='chicago'):
    tax = SpatialDensityService.calcular_taxonomia(ctx=ctx)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    is_chicago = (ctx.lower() == 'chicago')

    if is_chicago:
        bench_path = os.path.join(base_dir, 'data', 'chicago_benchmark', 'gold', 'chicago_model_benchmark.json')
        with open(bench_path, 'r', encoding='utf-8') as f:
            bench_data = json.load(f)
        districts_bench = bench_data.get('districts', {})

        # Compute violent crimes percentiles across units for relative alert ranking
        categories = tax['columns']
        violent_cats = [c for c in categories if c in [
            "Violencia armada y homicidio", "Agresión y violencia personal", "Robo con fuerza y allanamiento"
        ]]
        
        # Calculate unit violent percentage
        unit_viols = []
        for r in tax['rows']:
            # r['vals'] corresponds to tax['columns']
            v_pct = sum(val for c_name, val in zip(tax['columns'], r['vals']) if c_name in violent_cats)
            unit_viols.append(v_pct)
        
        p33 = float(np.percentile(unit_viols, 33.3))
        p67 = float(np.percentile(unit_viols, 66.7))

        units = []
        letters = SpatialDensityService.TAXONOMY_LETTERS
        for i, r in enumerate(tax['rows']):
            u_id = r['unit_id']
            d_bench = districts_bench.get(str(int(u_id)), {})
            db_m = d_bench.get('models', {}).get('dbscan', {})
            
            # Predominant crime: crime with highest ratio vs global
            # r['vals'] is in %
            ratios = []
            for c_idx, c_name in enumerate(tax['columns']):
                val = r['vals'][c_idx]
                # find global val from tax groups or mean
                ratios.append((c_name, val))
            
            top_c = max(ratios, key=lambda x: x[1])
            v_pct = unit_viols[i]
            
            if v_pct >= p67:
                alert_status = "ALERTA ROJA"
                alert_color = "rose"
            elif v_pct >= p33:
                alert_status = "VIGILANCIA ALTA"
                alert_color = "amber"
            else:
                alert_status = "PATRULLAJE DINÁMICO"
                alert_color = "emerald"

            g_id = r['group_id']
            g_letter = letters[(g_id - 1) % len(letters)]
            night_pct = SpatialDensityService.CHICAGO_NIGHT_PCT.get(int(u_id), 37.0)

            units.append({
                "code": f"D-{int(u_id):03d}",
                "name": SpatialDensityService.CHICAGO_DISTRICT_NAMES.get(int(u_id), f"Distrito {u_id}"),
                "district_id": int(u_id),
                "group_id": g_id,
                "group_letter": g_letter,
                "group_label": f"[Grupo {g_letter}]",
                "group_color": r['color'],
                "predominant_crime": top_c[0],
                "predominant_pct": top_c[1],
                "events_count": r['total_events'],
                "period": "2024–2025",
                "density_str": "No disponible (sin polígono oficial)",
                "night_pct": night_pct,
                "night_str": f"{night_pct:.1f}%",
                "hotspots_count": db_m.get("spatial_hotspots", 0),
                "single_coord_clusters": db_m.get("single_coord_clusters", 0),
                "coverage_pct": db_m.get("coverage_pct", 0.0),
                "eps_calibrated_m": d_bench.get("eps_elbow_m", 102),
                "stability_pct": r['stability_pct'],
                "alert_status": alert_status,
                "alert_color": alert_color,
                "violent_pct": round(v_pct, 1)
            })
        print(f"Chicago units generated: {len(units)}")
        print("Sample unit 1:", units[0])
    else:
        letters = SpatialDensityService.TAXONOMY_LETTERS
        units = []
        code_map = {
            "Cochabamba": "BO-CBBA",
            "Equipetrol": "BO-EQP",
            "La Paz": "BO-LPZ",
            "Los Lotes": "BO-LOT",
            "Plan 3000": "BO-P3K",
            "Santa Cruz": "BO-SCZ"
        }
        for r in tax['rows']:
            u_name = r['name']
            g_id = r['group_id']
            g_letter = letters[(g_id - 1) % len(letters)]
            
            ratios = [(c_name, r['vals'][c_idx]) for c_idx, c_name in enumerate(tax['columns'])]
            top_c = max(ratios, key=lambda x: x[1])

            units.append({
                "code": code_map.get(u_name, f"BO-{u_name[:3].upper()}"),
                "name": u_name,
                "district_id": None,
                "group_id": g_id,
                "group_letter": g_letter,
                "group_label": f"[Grupo {g_letter}]",
                "group_color": r['color'],
                "predominant_crime": top_c[0],
                "predominant_pct": top_c[1],
                "events_count": r['total_events'],
                "period": "2024–2026",
                "density_str": "No disponible (sin polígono oficial)",
                "night_pct": None,
                "night_str": "No disponible",
                "hotspots_count": 1,
                "single_coord_clusters": 1,
                "coverage_pct": 100.0,
                "eps_calibrated_m": 2500,
                "stability_pct": r['stability_pct'],
                "alert_status": "Sin clasificar",
                "alert_color": "slate",
                "violent_pct": 0.0
            })
        print(f"Bolivia units generated: {len(units)}")
        print("Sample unit 1:", units[0])

prototype_tabla_zonas('chicago')
prototype_tabla_zonas('bolivia')
