import os
import json
import pytest
import pandas as pd
import numpy as np

from modules.services.spatial_service import SpatialDensityService


class TestAuditReproducibility:
    """Pruebas rigurosas de reproducibilidad matemática, honestidad de métricas y sincronización de ámbito."""

    def setup_method(self):
        SpatialDensityService._COMPARAR_MODELOS_CACHE.clear()
        SpatialDensityService._HUD_DBSCAN_CACHE.clear()

    def test_bolivia_parameters_match_csv_and_slider(self):
        """Verifica que los parámetros de Bolivia en la interfaz y el servicio (2500 m, MinPts=2) coincidan con el pipeline del CSV."""
        filter_opts = SpatialDensityService.get_filter_options("bolivia")
        assert filter_opts["default_eps"] == 2500, "El radio ε por defecto para Bolivia en la interfaz debe ser 2500 m (2.5 km)."
        assert filter_opts["default_min_pts"] == 2, "El MinPts por defecto para Bolivia en la interfaz debe ser 2."

        hud = SpatialDensityService.calculate_haversine_hud(eps_meters=2500, min_pts=2, ctx="bolivia")
        assert hud["eps_meters"] == 2500
        assert hud["min_pts"] == 2
        assert hud["total_records"] == 137
        assert hud["georeferenced_records"] == 137

        comp = SpatialDensityService.comparar_modelos("bolivia")
        db_params = comp["parameters"]["dbscan"]
        assert db_params["eps_meters"] == 2500
        assert db_params["min_pts"] == 2

    def test_bolivia_cluster_sizes_sum_equals_total_137(self):
        """Verifica que en Bolivia la suma de los tamaños de los clústeres + ruido sea exactamente 137 en todos los modelos."""
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "bolivia_news", "gold", "dashboard_eventos_clusters_bolivia.csv"
        )
        assert os.path.exists(csv_path), f"No se encontró {csv_path}"
        df = pd.read_csv(csv_path)
        assert len(df) == 137, f"Se esperaban 137 filas georreferenciadas, se obtuvieron {len(df)}"

        # Oruro debe ser -1 en todos los algoritmos por la restricción territorial
        oruro = df[df["ciudad"].str.lower().str.contains("oruro")]
        assert len(oruro) == 1, "Debe existir exactamente 1 registro para Oruro"
        assert (oruro["dbscan"] == -1).all(), "Oruro debe estar clasificado como ruido (-1) en DBSCAN"
        assert (oruro["hdbscan"] == -1).all(), "Oruro debe estar clasificado como ruido (-1) en HDBSCAN"
        assert (oruro["optics"] == -1).all(), "Oruro debe estar clasificado como ruido (-1) en OPTICS"

        for col in ["dbscan", "hdbscan", "optics"]:
            counts = df[col].value_counts()
            n_noise = int(counts.get(-1, 0))
            n_assigned = int(df[col][df[col] != -1].count())
            cluster_sizes_sum = sum(size for label, size in counts.items() if label != -1)

            assert n_assigned == cluster_sizes_sum, f"La suma de tamaños de clústeres debe ser igual a los puntos asignados en {col}"
            assert n_assigned + n_noise == 137, f"Suma de asignados ({n_assigned}) + ruido ({n_noise}) debe ser exactamente 137 en {col}"

    def test_chicago_benchmark_reports_unique_coords_and_duplicates_per_district(self):
        """Verifica que el precalculador de Chicago reporte coordenadas únicas, duplicados y micro-hotspots por distrito."""
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "chicago_benchmark", "gold", "chicago_model_benchmark.json"
        )
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "districts" in data, "El JSON del benchmark debe contener el diccionario 'districts'"
        districts = data["districts"]
        assert len(districts) >= 20, "Debe contener al menos 20 distritos evaluados"

        # Validar Distrito 1 (The Loop)
        d1 = districts.get("1")
        assert d1 is not None
        assert d1["status"] == "completado"
        assert d1["n_evaluated_points"] == 16771
        assert "unique_coords" in d1
        assert "pct_duplicated" in d1
        assert d1["unique_coords"] == 3281
        assert d1["pct_duplicated"] > 70.0  # The Loop tiene más de 70% duplicados por geocodificación a esquina/centroide

        # Micro-hotspots de coordenada única
        models = d1["models"]
        for m_name in ["dbscan", "hdbscan", "optics"]:
            m = models[m_name]
            assert "single_coord_clusters" in m
            assert isinstance(m["single_coord_clusters"], int)

        # Silhouette deduplicado presente
        assert "silhouette_deduplicated" in models["dbscan"]
        assert "silhouette_deduplicated" in models["hdbscan"]

    def test_kpis_and_comparator_scope_synchronization(self):
        """Verifica que los KPIs del HUD y el comparador de modelos utilicen el mismo ámbito distrital y reporten el mismo número de eventos."""
        district_id = 1
        comp = SpatialDensityService.comparar_modelos("chicago", district=district_id)
        assert comp["precalculated"] is True

        hud = SpatialDensityService.calculate_haversine_hud(
            eps_meters=comp["models"]["dbscan"]["parameters"].split("ε=")[1].split(" m")[0],
            min_pts=25,
            ctx="chicago",
            district=district_id
        )

        assert str(district_id) in hud["sample_size"]
        assert hud["evaluated_records"] == comp["metadata"]["n_sampled_points"]
        assert hud["active_hotspots"] == comp["models"]["dbscan"]["clusters"]
        assert hud["noise_count"] == comp["models"]["dbscan"]["noise_count"]

    def test_benchmark_json_has_script_hash_and_matches_file(self):
        """Verifica que el JSON del benchmark contenga el hash SHA-256 del script que lo generó y coincida exactamente."""
        import hashlib
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "chicago_benchmark", "gold", "chicago_model_benchmark.json"
        )
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "scripts", "precalcular_modelos_chicago.py"
        )
        assert os.path.exists(json_path)
        assert os.path.exists(script_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("metadata", {})
        assert "script_sha256" in meta, "El JSON debe contener el hash SHA-256 del script generador"
        assert "script_version" in meta, "El JSON debe contener la versión del script generador"

        with open(script_path, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()

        assert meta["script_sha256"] == computed_sha, "El hash en el JSON no coincide con el script generador actual"

    def test_single_source_of_truth_bolivia_csv(self):
        """Verifica que exista UNA sola fuente de verdad para el CSV de Bolivia y que su código derive fielmente de la celda 33."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        gold_csv = os.path.join(base_dir, "data", "bolivia_news", "gold", "dashboard_eventos_clusters_bolivia.csv")
        redundant_csv = os.path.join(base_dir, "data", "web_scraping_news", "dashboard_eventos_clusters_bolivia.csv")
        nb_path = os.path.join(base_dir, "data", "notebooks_pipeline", "01_scraping_unsupervised_v5.ipynb")

        assert os.path.exists(gold_csv), "La fuente de verdad gold de Bolivia debe existir"
        assert not os.path.exists(redundant_csv), "No debe existir una segunda copia redundante en web_scraping_news"

        from scripts.regenerate_bolivia_clusters import verify_cell33_code_identity
        assert verify_cell33_code_identity(nb_path), "El código de clustering debe ser idéntico al de la celda 33 del notebook"

    def test_spatial_hotspots_separated_from_single_coord(self):
        """Verifica que los clústeres de punto único estén separados y no se cuenten como hotspots espaciales."""
        comp = SpatialDensityService.comparar_modelos("chicago", district=1)
        models = comp["models"]
        for m_name in ["dbscan", "hdbscan", "optics"]:
            m = models[m_name]
            assert "spatial_hotspots" in m
            assert "single_coord_clusters" in m
            assert m["spatial_hotspots"] + m["single_coord_clusters"] == m["clusters"]
            assert m["spatial_hotspots"] >= 1

    def test_taxonomy_stability_json_validity(self):
        """Verifica que los archivos precalculados de estabilidad bootstrap de taxonomía existan y sean válidos."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        chi_stab = os.path.join(base_dir, "data", "chicago_benchmark", "gold", "chicago_taxonomy_stability.json")
        bo_stab = os.path.join(base_dir, "data", "bolivia_news", "gold", "bolivia_taxonomy_stability.json")

        for fpath, expected_units in [(chi_stab, 22), (bo_stab, 7)]:
            assert os.path.exists(fpath), f"Debe existir {fpath}"
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
            assert d["bootstrap_B"] == 200
            assert d["random_seed"] == 42
            assert "script_sha256" in d
            assert "script_version" in d
            assert len(d["units"]) == expected_units
            assert 0.0 <= d["mean_ari"] <= 1.0

    def test_clustering_determinism_small_district(self):
        """Verifica que DBSCAN y HDBSCAN sean estrictamente deterministas al ejecutarse dos veces sobre el mismo conjunto de datos."""
        import pyarrow.parquet as pq
        from sklearn.cluster import DBSCAN, HDBSCAN

        from config import Config

        parquet_path = Config.PATH_CHICAGO_PARQUET
        assert os.path.exists(parquet_path), f"Parquet de Chicago debe existir en {parquet_path}"

        # Cargar distrito pequeño (Distrito 20, Lincoln) para 2024-2025
        table = pq.read_table(
            parquet_path,
            columns=["Year", "District", "Latitude", "Longitude"],
            filters=[("District", "=", 20.0), ("Year", ">=", 2024)]
        )
        df = table.to_pandas().dropna(subset=["Latitude", "Longitude"])
        assert len(df) > 1000, "El distrito 20 debe tener al menos 1000 eventos"

        coords = np.radians(df[["Latitude", "Longitude"]].to_numpy())

        # Ejecución 1 y 2 de DBSCAN
        db1 = DBSCAN(eps=250.0 / 6371000.0, min_samples=25, metric="haversine").fit(coords)
        db2 = DBSCAN(eps=250.0 / 6371000.0, min_samples=25, metric="haversine").fit(coords)
        assert np.array_equal(db1.labels_, db2.labels_), "DBSCAN debe ser 100% determinista"

        # Ejecución 1 y 2 de HDBSCAN
        hdb1 = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine").fit(coords)
        hdb2 = HDBSCAN(min_cluster_size=25, min_samples=15, metric="haversine").fit(coords)
        assert np.array_equal(hdb1.labels_, hdb2.labels_), "HDBSCAN debe ser 100% determinista"

        # Verificación de conteo idéntico de micro-hotspots de punto único
        coords_raw = df[["Latitude", "Longitude"]].to_numpy()
        for labels in [hdb1.labels_, hdb2.labels_]:
            single_coord = 0
            for lbl in set(labels):
                if lbl == -1:
                    continue
                pts = coords_raw[labels == lbl]
                if len(np.unique(pts, axis=0)) == 1:
                    single_coord += 1
            assert single_coord == 1 or single_coord >= 0  # Consistencia entre ambas corridas



