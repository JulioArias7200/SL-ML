import os
import json
import pytest
import numpy as np
from modules.services.spatial_service import SpatialDensityService


class TestModelComparisonIntegrity:
    """Suite de pruebas para garantizar la honestidad técnica y procedencia de las métricas de clustering."""

    def setup_method(self):
        # Limpiar caché estático antes de cada prueba
        SpatialDensityService._COMPARAR_MODELOS_CACHE.clear()

    def test_chicago_benchmark_exists_and_valid(self):
        """Verifica que el archivo gold de Chicago existe, es JSON válido y contiene metadatos de reproducibilidad."""
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "chicago_benchmark", "gold", "chicago_model_benchmark.json"
        )
        assert os.path.exists(json_path), f"El archivo {json_path} debe existir tras el precálculo."

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "models" in data
        assert "ari_matrix" in data
        assert "rescued_events" in data
        assert data["metadata"]["n_sampled_points"] >= 10000
        assert data["metadata"]["random_seed"] == 42
        assert "version" in data["metadata"]

    def test_execution_time_not_implausible(self):
        """Falla si el tiempo de ejecución para conjuntos grandes (> 10.000 puntos) es menor a 1 ms (constante fija)."""
        comp = SpatialDensityService.comparar_modelos("chicago")
        assert comp["precalculated"] is True

        models = comp["models"]
        for model_id, m in models.items():
            t_ms = m.get("execution_time_ms")
            assert t_ms is not None, f"El tiempo de ejecución para {model_id} no debe ser None."
            # Para más de 10.000 puntos, cualquier algoritmo real tarda al menos 10 ms
            assert t_ms >= 10.0, (
                f"Tiempo inverosímil para {model_id} en Chicago ({t_ms} ms). "
                "Un tiempo < 10 ms para > 10.000 puntos evidencia una constante inventada."
            )

    def test_different_models_identical_metrics_must_have_justification(self):
        """Falla si dos modelos distintos devuelven métricas idénticas sin una justificación matemática explícita."""
        for ctx in ["bolivia", "chicago"]:
            comp = SpatialDensityService.comparar_modelos(ctx)
            if not comp.get("precalculated"):
                continue

            models = comp["models"]
            model_keys = list(models.keys())

            for i in range(len(model_keys)):
                for j in range(i + 1, len(model_keys)):
                    m1 = models[model_keys[i]]
                    m2 = models[model_keys[j]]

                    # Verificar si tienen métricas idénticas
                    identical_clusters = (m1.get("clusters") == m2.get("clusters"))
                    identical_noise = (m1.get("noise_pct") == m2.get("noise_pct"))
                    identical_sil = (m1.get("silhouette_spatial") == m2.get("silhouette_spatial"))

                    if identical_clusters and identical_noise and identical_sil:
                        # Si son idénticos, DEBE existir justificación matemática en ari_matrix.explanation
                        explanation = comp.get("ari_matrix", {}).get("explanation", "").lower()
                        justified = any(term in explanation for term in ["isomórfica", "permutación", "biyectiva", "partición"])
                        assert justified, (
                            f"En contexto {ctx}, los modelos {m1['name']} y {m2['name']} tienen métricas idénticas "
                            f"(clusters={m1.get('clusters')}, noise={m1.get('noise_pct')}%, sil={m1.get('silhouette_spatial')}) "
                            "sin una justificación matemática explícita (e.g. permutación biyectiva de etiquetas)."
                        )

    def test_all_non_null_metrics_have_registered_provenance(self):
        """Falla si cualquier modelo con métricas válidas carece de procedencia registrada."""
        for ctx in ["bolivia", "chicago"]:
            comp = SpatialDensityService.comparar_modelos(ctx)
            if not comp.get("precalculated"):
                continue

            for model_id, m in comp["models"].items():
                provenance = m.get("provenance")
                assert provenance and isinstance(provenance, str) and len(provenance.strip()) > 10, (
                    f"El modelo {model_id} en contexto {ctx} no tiene un registro de procedencia válido ('{provenance}')."
                )

    def test_rescued_events_definition_and_consistency(self):
        """Verifica la definición formal de eventos rescatados y su coherencia entre comparar_modelos y generar_hallazgos."""
        # Prueba unitaria de la función formal
        base = np.array([-1, -1, 0, 1, -1, 0])
        cand = np.array([0, -1, 0, 1, 2, -1])
        # Puntos donde base == -1 y cand != -1: índice 0 y 4 (total 2)
        assert SpatialDensityService._calcular_eventos_rescatados(base, cand) == 2

        # Prueba de consistencia en Bolivia
        comp_bo = SpatialDensityService.comparar_modelos("bolivia")
        rescued_bo = comp_bo["rescued_events"]["hdbscan_from_dbscan"]
        hallazgos_bo = SpatialDensityService.generar_hallazgos("bolivia")
        if rescued_bo == 0:
            assert any("no asigna a ningún clúster eventos que dbscan marcó como ruido" in h.lower() for h in hallazgos_bo), (
                "Cuando rescued_events == 0, los hallazgos deben indicar textualmente que HDBSCAN no asigna eventos marcados como ruido por DBSCAN."
            )
        else:
            hallazgo_rescate_bo = next((h for h in hallazgos_bo if "rescata" in h.lower()), None)
            assert hallazgo_rescate_bo is not None
            assert f"rescata {rescued_bo}" in hallazgo_rescate_bo

        # Prueba de consistencia en Chicago
        comp_chi = SpatialDensityService.comparar_modelos("chicago")
        if comp_chi.get("precalculated"):
            rescued_chi = comp_chi["rescued_events"]["hdbscan_from_dbscan"]
            hallazgos_chi = SpatialDensityService.generar_hallazgos("chicago")
            if rescued_chi == 0:
                assert any("no asigna a ningún clúster eventos que dbscan marcó como ruido" in h.lower() for h in hallazgos_chi), (
                    "Cuando rescued_events == 0, los hallazgos deben indicar textualmente que HDBSCAN no asigna eventos marcados como ruido por DBSCAN."
                )
            else:
                hallazgo_rescate_chi = next((h for h in hallazgos_chi if "rescata" in h.lower()), None)
                assert hallazgo_rescate_chi is not None
                assert f"{rescued_chi:,}" in hallazgo_rescate_chi

    def test_missing_benchmark_returns_null_gracefully(self, monkeypatch):
        """Verifica que si el archivo de benchmark no existe, comparar_modelos devuelve null y precalculated=False."""
        import os.path
        original_exists = os.path.exists

        def mock_exists(path):
            if "chicago_model_benchmark.json" in str(path):
                return False
            return original_exists(path)

        monkeypatch.setattr(os.path, "exists", mock_exists)
        SpatialDensityService._COMPARAR_MODELOS_CACHE.clear()

        comp = SpatialDensityService.comparar_modelos("chicago")
        assert comp["precalculated"] is False
        assert comp["models"] is None
        assert comp["models_list"] == []
        assert comp["ari_matrix"] is None
        assert "no disponible" in comp["unavailable_reason"]
