import pytest
import json
from modules.factory import create_app
from modules.services.spatial_service import SpatialDensityService

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestValidationSection:

    def test_validation_data_chicago_service(self):
        """Valida que get_validation_data para Chicago (D-1) retorne la estructura matemática esperada."""
        data = SpatialDensityService.get_validation_data(ctx="chicago", district=1)
        assert data["status"] == "ok"
        assert data["ctx"] == "chicago"
        assert data["district"] == 1
        assert "Distrito 1" in data["scope_label"]

        # 1. k-distance
        k_dist = data["k_distance"]
        assert k_dist["k"] == 25
        assert k_dist["calibrated_eps_m"] == 102
        assert k_dist["elbow_pct"] >= 80.0
        assert len(k_dist["points"]) > 10
        assert "polyline_points" in k_dist
        assert "secant_line" in k_dist
        assert "elbow_marker" in k_dist
        assert k_dist["elbow_marker"]["eps_m"] == 102

        # 2. Sensibilidad
        sens = data["sensitivity"]
        assert sens["base_eps"] == 102
        assert sens["base_min_pts"] == 25
        assert len(sens["by_eps"]) >= 4
        assert any(pt["is_calibrated"] and pt["eps_m"] == 102 for pt in sens["by_eps"])
        assert any(pt["is_calibrated"] and pt["min_pts"] == 25 for pt in sens["by_min_pts"])

        # 3. Horas circadianas
        hourly = data["hourly"]
        assert hourly["available"] is True
        assert len(hourly["hours"]) == 24
        assert any(h["hour"] == 12 and h["count"] > 1000 for h in hourly["hours"])

    def test_validation_data_bolivia_service(self):
        """Valida que get_validation_data para Bolivia use k=2, eps=2500m y reporte franjas honestas sin horas falsas."""
        data = SpatialDensityService.get_validation_data(ctx="bolivia")
        assert data["status"] == "ok"
        assert data["ctx"] == "bolivia"
        assert "137 crónicas georreferenciadas" in data["scope_label"]

        # 1. k-distance
        k_dist = data["k_distance"]
        assert k_dist["k"] == 2
        assert k_dist["calibrated_eps_m"] == 2500
        assert k_dist["elbow_pct"] >= 70.0

        # 2. Sensibilidad
        sens = data["sensitivity"]
        assert sens["base_eps"] == 2500
        assert sens["base_min_pts"] == 2

        # 3. Horas: sin horas inventadas, franjas reportadas
        hourly = data["hourly"]
        assert hourly["available"] is False
        assert len(hourly["bolivia_franjas"]) == 5
        desconocida = next(f for f in hourly["bolivia_franjas"] if "Desconocida" in f["franja"])
        assert desconocida["count"] == 45
        assert desconocida["pct"] == 75.0

    def test_validation_cache_reuse(self):
        """Verifica que llamadas sucesivas devuelvan la respuesta cacheadas instantáneamente."""
        data1 = SpatialDensityService.get_validation_data(ctx="chicago", district=1)
        data2 = SpatialDensityService.get_validation_data(ctx="chicago", district=1)
        assert data1 is data2

    def test_api_validation_data_endpoint(self, client):
        """Verifica el endpoint GET /api/v1/validation_data para Chicago y Bolivia."""
        # Chicago
        resp_chi = client.get("/api/v1/validation_data?ctx=chicago&district=1")
        assert resp_chi.status_code == 200
        d_chi = json.loads(resp_chi.data)
        assert d_chi["status"] == "ok"
        assert d_chi["ctx"] == "chicago"
        assert d_chi["k_distance"]["calibrated_eps_m"] == 102

        # Bolivia
        resp_bol = client.get("/api/v1/validation_data?ctx=bolivia")
        assert resp_bol.status_code == 200
        d_bol = json.loads(resp_bol.data)
        assert d_bol["status"] == "ok"
        assert d_bol["ctx"] == "bolivia"
        assert d_bol["k_distance"]["calibrated_eps_m"] == 2500

    def test_rendered_view_contains_validation_section(self, client):
        """Verifica que la plantilla renderice el acordeón de validación y elementos SVG."""
        # Chicago
        resp = client.get("/espacial-densidad?ctx=chicago")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert 'id="validation-section"' in html
        assert 'id="validation-details"' in html
        assert 'id="svg-kdistance"' in html
        assert 'href="#validacion"' in html
        assert 'Codo ε = 102 m' in html or 'Codo: ε=102 m' in html
        assert 'Histograma de 24 horas' in html

        # Bolivia
        resp_bol = client.get("/espacial-densidad?ctx=bolivia")
        assert resp_bol.status_code == 200
        html_bol = resp_bol.data.decode("utf-8")
        assert 'id="validation-section"' in html_bol
        assert '75% de las crónicas' in html_bol
        assert 'Desconocida' in html_bol

