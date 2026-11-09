"""
Suite de Pruebas: Filtros Espaciales y Visor Cartográfico Táctico (Fase 2)
Verifica opciones de filtrado, endpoint /api/v1/spatial_filter en ambos contextos,
muestreo estratificado, caché y renderizado del mapa protagonista.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.factory import create_app
from modules.services.spatial_service import SpatialDensityService

@pytest.fixture
def client():
    app = create_app('dev')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_filter_options_bolivia():
    """Verifica que las opciones de filtrado de Bolivia respeten la falta de franja horaria."""
    opts = SpatialDensityService.get_filter_options(ctx='bolivia')
    assert opts["ctx"] == "bolivia"
    assert opts["franja_available"] is False
    assert "75%" in opts["franja_message"]
    assert opts["default_eps"] == 2500
    assert opts["default_min_pts"] == 2
    assert len(opts["crimes"]) > 1
    assert "Todos los delitos" in opts["crimes"]

def test_get_filter_options_chicago():
    """Verifica que las opciones de filtrado de Chicago habiliten franjas horarias y calibración CPD."""
    opts = SpatialDensityService.get_filter_options(ctx='chicago')
    assert opts["ctx"] == "chicago"
    assert opts["franja_available"] is True
    assert opts["franja_message"] is None
    assert opts["default_eps"] in [102, 300]
    assert opts["default_min_pts"] == 25
    assert len(opts["franjas"]) == 3
    assert "THEFT" in opts["crimes"]

def test_spatial_filter_api_bolivia_default(client):
    """Verifica respuesta por defecto de /api/v1/spatial_filter para Bolivia."""
    resp = client.get('/api/v1/spatial_filter?ctx=bolivia')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["ctx"] == "bolivia"
    assert data["eps_meters"] == 2500
    assert data["min_pts"] == 2
    assert data["sampling"]["sampled"] is False
    assert "137" in data["sampling"]["label"]
    assert "layers_data" in data
    assert len(data["layers_data"]["hotspots"]) > 0

def test_spatial_filter_api_chicago_stratified_sampling(client):
    """Verifica muestreo estratificado en /api/v1/spatial_filter para Chicago."""
    resp = client.get('/api/v1/spatial_filter?ctx=chicago')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["ctx"] == "chicago"
    assert data["eps_meters"] == 300
    assert data["min_pts"] == 25
    assert data["sampling"]["sampled"] is True
    assert "5.000" in data["sampling"]["label"] or "5,000" in data["sampling"]["label"]
    assert ("292.171" in data["sampling"]["label"] or "292,171" in data["sampling"]["label"] or
            "1.199.160" in data["sampling"]["label"] or "1,199,160" in data["sampling"]["label"])

def test_spatial_filter_api_with_custom_filters(client):
    """Verifica que los filtros de delito y franja modifiquen el resultado y usen caché."""
    resp = client.get('/api/v1/spatial_filter?ctx=chicago&eps=350&min_pts=30&delito=THEFT&franja=noche')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["eps_meters"] == 350
    assert data["min_pts"] == 30
    assert data["delito"] == "THEFT"
    assert data["franja"] == "noche"

    # Segunda llamada para verificar caché
    resp2 = client.get('/api/v1/spatial_filter?ctx=chicago&eps=350&min_pts=30&delito=THEFT&franja=noche')
    assert resp2.status_code == 200
    assert resp2.get_json() == data

def test_spatial_filter_api_invalid_params(client):
    """Verifica manejo de errores ante parámetros inválidos."""
    resp = client.get('/api/v1/spatial_filter?ctx=bolivia&eps=invalido')
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data

def test_view_espacial_densidad_has_phase2_elements(client):
    """Verifica que la plantilla renderice el visor con panel de controles, botones y leyenda."""
    for ctx in ['bolivia', 'chicago']:
        resp = client.get(f'/espacial-densidad?ctx={ctx}')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # Secciones y elementos de layout
        assert 'id="mapa"' in html
        assert 'id="slider-eps"' in html
        assert 'id="btn-apply-spatial-filter"' in html
        assert 'id="btn-reset-spatial-filter"' in html
        assert 'id="filter-crime-type"' in html
        assert 'data-layer-toggle="dbscan"' in html
        assert 'data-layer-toggle="hdbscan"' in html
        assert 'data-layer-toggle="optics"' in html

        # Variables CSS de algoritmos en la vista
        assert '--algo-dbscan' in html
        assert '--algo-hdbscan' in html
        assert '--algo-optics' in html

