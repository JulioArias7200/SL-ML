import os
import json
import pytest
from app import app
from modules.services.spatial_service import SpatialDensityService


class TestDistrictTable:
    """Pruebas rigurosas de la Fase 5: Tabla de Zonas, Taxonomía Composicional y Densidad Auditada."""

    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def setup_method(self):
        SpatialDensityService._TABLA_ZONAS_CACHE.clear()
        SpatialDensityService._TAXONOMIA_CACHE.clear()

    def test_tabla_zonas_chicago_matches_benchmark_and_taxonomy(self):
        """Verifica que la tabla de Chicago contenga los 22 distritos oficiales, coincida exactamente con el benchmark y la taxonomía."""
        tz = SpatialDensityService.tabla_zonas(ctx="chicago")
        assert tz["status"] == "ok"
        assert tz["total_units"] == 22
        assert len(tz["units"]) == 22
        assert tz["total_events"] == 292171, "El volumen total evaluado en los 22 distritos debe ser exactamente 292.171 eventos"
        assert tz["period"] == "2024-2025"

        # Verificar Distrito 1 (The Loop)
        d1 = next((u for u in tz["units"] if u["district_id"] == 1), None)
        assert d1 is not None, "Distrito 1 debe estar presente"
        assert d1["code"] == "D-001"
        assert "Central" in d1["name"]
        assert d1["events_count"] == 16771
        assert d1["hotspots_count"] == 33
        assert d1["single_coord_clusters"] == 1
        assert d1["eps_calibrated_m"] == 102
        assert d1["stability_pct"] == 100.0
        assert d1["night_pct"] == 29.8
        assert d1["night_str"] == "29.8%"

        # Exclusión de D-31
        assert "D-31" in tz["excluded_units"]
        assert "19 eventos" in tz["excluded_units"]["D-31"]

    def test_tabla_zonas_bolivia_exploratory(self):
        """Verifica que la tabla de Bolivia muestre las macro-zonas con n >= 3, sin alertas preventivas ni franja horaria."""
        tz = SpatialDensityService.tabla_zonas(ctx="bolivia")
        assert tz["status"] == "ok"
        assert tz["total_units"] == 7
        assert len(tz["units"]) == 7
        assert tz["total_events"] == 85, "Suma de crónicas en las 7 zonas (35+21+15+5+3+3+3) debe ser exactamente 85"
        assert tz["period"] == "2024-2026"

        # Validar ausencia de franja horaria y estado sin clasificar
        for u in tz["units"]:
            assert u["alert_status"] == "Sin clasificar", f"Zona {u['name']} debe estar 'Sin clasificar'"
            assert u["alert_color"] == "slate"
            assert u["night_pct"] is None, f"Zona {u['name']} no debe tener % nocturno numérico"
            assert u["night_str"] == "No disponible"
            assert u["eps_calibrated_m"] == 2500

    def test_density_omitted_honestly_when_no_polygon_exists(self):
        """Verifica que la densidad delictiva en km² se omita explícitamente y se justifique en la procedencia."""
        for ctx in ["chicago", "bolivia"]:
            tz = SpatialDensityService.tabla_zonas(ctx=ctx)
            for u in tz["units"]:
                assert u["density_val"] is None, "El valor numérico de densidad debe ser None"
                assert "No disponible" in u["density_str"]
                assert "sin polígono oficial" in u["density_str"].lower()

            assert "densidad" in tz["provenance"]
            assert "shapefile" in tz["provenance"]["densidad"].lower() or "poligonal" in tz["provenance"]["densidad"].lower()

    def test_alert_classification_relative_ranking_chicago(self):
        """Verifica que en Chicago los niveles de alerta sigan una regla relativa de terciles sobre delitos violentos."""
        tz = SpatialDensityService.tabla_zonas(ctx="chicago")
        units = tz["units"]

        alerts = [u["alert_status"] for u in units]
        assert "ALERTA ROJA" in alerts
        assert "VIGILANCIA ALTA" in alerts
        assert "PATRULLAJE DINÁMICO" in alerts

        # Comprobar que Alerta Roja tenga en promedio mayor violencia que Patrullaje Dinámico
        red_viols = [u["violent_pct"] for u in units if u["alert_status"] == "ALERTA ROJA"]
        green_viols = [u["violent_pct"] for u in units if u["alert_status"] == "PATRULLAJE DINÁMICO"]

        assert min(red_viols) >= max(green_viols), "Las unidades en Alerta Roja deben tener mayor o igual % violento que Patrullaje Dinámico"

    def test_api_v1_zones_table_endpoint(self, client):
        """Verifica el endpoint GET /api/v1/zones_table para ambos contextos."""
        # Chicago
        resp_chi = client.get("/api/v1/zones_table?ctx=chicago")
        assert resp_chi.status_code == 200
        data_chi = resp_chi.get_json()
        assert data_chi["status"] == "ok"
        assert data_chi["total_units"] == 22
        assert len(data_chi["units"]) == 22

        # Bolivia
        resp_bo = client.get("/api/v1/zones_table?ctx=bolivia")
        assert resp_bo.status_code == 200
        data_bo = resp_bo.get_json()
        assert data_bo["status"] == "ok"
        assert data_bo["total_units"] == 7
        assert len(data_bo["units"]) == 7

    def test_rendered_view_includes_zones_table(self, client):
        """Verifica que la vista HTML renderice la tabla consolidada de zonas sin errores."""
        resp = client.get("/espacial-densidad?ctx=chicago")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "zonas-table-container" in html
        assert "D-001" in html
        assert "Central (The Loop)" in html
        assert "btn-export-zones-csv" in html
        assert "btn-export-map-png" in html

