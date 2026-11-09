import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN
from modules.services.spatial_service import SpatialDensityService

def compute_validation(ctx='chicago', district=1):
    is_chicago = (ctx.lower() == 'chicago')
    district_int = int(district or 1) if is_chicago else None
    R = 6371008.8

    if is_chicago:
        coords_rad = SpatialDensityService._get_chicago_district_coords_rad(district_int)
        if coords_rad is None or len(coords_rad) == 0:
            coords_rad = SpatialDensityService._get_chicago_district_coords_rad(1)
        k_val = 25
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bench_path = os.path.join(base_dir, 'data', 'chicago_benchmark', 'gold', 'chicago_model_benchmark.json')
        with open(bench_path, 'r', encoding='utf-8') as f:
            bench_d = json.load(f)
        d_info = bench_d.get('districts', {}).get(str(district_int), {})
        calibrated_eps = d_info.get('eps_elbow_m', 102)
    else:
        coords_rad = SpatialDensityService._get_bolivia_coords_rad()
        k_val = 2
        calibrated_eps = 2500

    n_pts = len(coords_rad)

    # 1. k-distance calculation
    nn = NearestNeighbors(n_neighbors=k_val, metric='haversine').fit(coords_rad)
    dists, _ = nn.kneighbors(coords_rad)
    k_dists = np.sort(dists[:, k_val - 1] * R)

    # Subsample 60 points for SVG polyline
    sample_indices = np.linspace(0, n_pts - 1, 60, dtype=int)
    sampled_dists = k_dists[sample_indices]
    max_d = float(sampled_dists[-1]) if sampled_dists[-1] > 0 else 1.0

    k_points = []
    for i, idx in enumerate(sample_indices):
        pct = round(float(idx / (n_pts - 1) * 100.0), 1)
        d_m = round(float(k_dists[idx]), 1)
        # Map to SVG box 0..500 x 0..220 (padding: left 45, right 20, top 20, bottom 35 -> width 435, height 165)
        svg_x = round(45 + (pct / 100.0) * 435, 1)
        svg_y = round(185 - (min(d_m, max_d) / max_d) * 165, 1)
        k_points.append({"pct": pct, "dist_m": d_m, "svg_x": svg_x, "svg_y": svg_y})

    # Elbow position
    elbow_idx = int(np.searchsorted(k_dists, calibrated_eps))
    elbow_pct = round(float(elbow_idx / n_pts * 100.0), 1)
    elbow_svg_x = round(45 + (elbow_pct / 100.0) * 435, 1)
    elbow_svg_y = round(185 - (min(calibrated_eps, max_d) / max_d) * 165, 1)

    # 2. Sensitivity variation
    if is_chicago:
        eps_multipliers = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5]
        eps_test_vals = [max(25, int(round(calibrated_eps * m))) for m in eps_multipliers]
        min_pts_vals = [10, 15, 20, 25, 30, 40]
    else:
        eps_test_vals = [1000, 1500, 2000, 2500, 3500, 5000]
        min_pts_vals = [2, 3, 4, 5, 8, 10]

    sens_eps = []
    for eps_m in eps_test_vals:
        db = DBSCAN(eps=eps_m / R, min_samples=k_val, metric='haversine', algorithm='ball_tree').fit(coords_rad)
        lbls = db.labels_
        n_cl = len(set(lbls) - {-1})
        p_noise = round(float((lbls == -1).mean() * 100), 1)
        sens_eps.append({
            "eps_m": eps_m,
            "clusters": n_cl,
            "noise_pct": p_noise,
            "is_calibrated": (eps_m == calibrated_eps)
        })

    sens_min_pts = []
    for mp in min_pts_vals:
        db = DBSCAN(eps=calibrated_eps / R, min_samples=mp, metric='haversine', algorithm='ball_tree').fit(coords_rad)
        lbls = db.labels_
        n_cl = len(set(lbls) - {-1})
        p_noise = round(float((lbls == -1).mean() * 100), 1)
        sens_min_pts.append({
            "min_pts": mp,
            "clusters": n_cl,
            "noise_pct": p_noise,
            "is_calibrated": (mp == k_val)
        })

    # 3. Hourly distribution
    hourly_bars = []
    if is_chicago:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        import pyarrow.parquet as pq
        table = pq.read_table(os.path.join(base_dir, 'data', 'chicago_benchmark', 'silver', 'chicago_crimes_curated.parquet'),
                              columns=['District', 'Date', 'Year'])
        df_p = table.to_pandas()
        df_d = df_p[(df_p['Year'] >= 2024) & (df_p['District'] == float(district_int))].copy()
        dt = pd.to_datetime(df_d['Date'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
        hour_counts = dt.dt.hour.value_counts().to_dict()
        max_h_count = max(hour_counts.values()) if hour_counts else 1
        total_d_events = len(df_d)

        for h in range(24):
            cnt = int(hour_counts.get(h, 0))
            pct = round(float(cnt / total_d_events * 100.0), 1) if total_d_events > 0 else 0.0
            h_bar = round((cnt / max_h_count) * 140, 1) if max_h_count > 0 else 0.0
            is_night = (h >= 20) or (h < 6)
            hourly_bars.append({
                "hour": h,
                "hour_label": f"{h:02d}:00",
                "count": cnt,
                "pct": pct,
                "bar_height": h_bar,
                "is_night": is_night,
                "color": "#7c3aed" if is_night else "#0ea5e9"
            })
    
    print(f"[{ctx.upper()}] Validation computed: k={k_val}, elbow={calibrated_eps}m ({elbow_pct}%), sens_eps={len(sens_eps)}, sens_mp={len(sens_min_pts)}, hourly={len(hourly_bars)}")
    return {
        "k_points": k_points[:3],
        "elbow": {"pct": elbow_pct, "eps_m": calibrated_eps, "svg_x": elbow_svg_x, "svg_y": elbow_svg_y},
        "sens_eps": sens_eps,
        "sens_min_pts": sens_min_pts,
        "hourly_bars": hourly_bars[:3]
    }

compute_validation('chicago', 1)
compute_validation('bolivia')

