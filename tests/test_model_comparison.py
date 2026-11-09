"""
Suite de Pruebas: Comparador de Modelos de Densidad (Fase 3)
Valida la estructura homogénea de métricas, valores null/no disponible,
cálculo de ARI (matriz 3x3), caché por contexto y el endpoint GET /api/v1/model_comparison.
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

def test_comparar_modelos_bolivia_structure():
    """Verifica que comparar_modelos devuelva las 6 métricas idénticas y nulls consistentes en Bolivia."""
    data = SpatialDensityService.comparar_modelos('bolivia')
    assert data["status"] == "ok"
    assert data["ctx"] == "bolivia"
    assert data["total_events"] == 137
    assert "models" in data
    assert "ari_matrix" in data
    assert "methodology_note" in data

    models = data["models"]
    for key in ["dbscan", "hdbscan", "optics"]:
        assert key in models
        m = models[key]
        assert "clusters" in m
        assert "noise_pct" in m
        assert "coverage_pct" in m
        assert "silhouette_spatial" in m
        assert "execution_time_ms" in m
        assert "parameters" in m

    # Honestidad de métricas: active_valleys solo aplica a OPTICS, null en DBSCAN y HDBSCAN
    assert models["dbscan"]["active_valleys"] is None
    assert models["hdbscan"]["active_valleys"] is None
    assert models["optics"]["active_valleys"] == 4
    assert len(models["optics"]["mini_reachability"]) > 0

    # Coherencia matemática de cobertura + ruido
    for m in models.values():
        total_pct = m["coverage_pct"] + m["noise_pct"]
        assert 99.0 <= total_pct <= 101.0, f"Suma de cobertura y ruido ({total_pct}) fuera de rango"

def test_comparar_modelos_chicago_structure():
    """Verifica que comparar_modelos devuelva métricas auditadas desde el archivo gold de Chicago."""
    data = SpatialDensityService.comparar_modelos('chicago')
    assert data["status"] == "ok"
    assert data["ctx"] == "chicago"
    assert data["total_events"] == 1199160
    assert data["precalculated"] is True

    models = data["models"]
    assert models["dbscan"]["clusters"] in [2, 34]
    assert models["dbscan"]["noise_pct"] in [0.14, 3.97]
    assert models["hdbscan"]["clusters"] == 240
    assert models["optics"]["clusters"] >= 200

def test_ari_matrix_properties():
    """Verifica que la matriz de Rand ajustado sea 3x3, simétrica y con diagonal unitaria."""
    for ctx in ["bolivia", "chicago"]:
        data = SpatialDensityService.comparar_modelos(ctx)
        ari = data["ari_matrix"]
        assert len(ari["models"]) == 3
        assert len(ari["values"]) == 3

        matrix = ari["values"]
        # Diagonal en 1.0 (concordancia consigo mismo)
        for i in range(3):
            assert matrix[i][i] == 1.0

        # Simetría matrix[i][j] == matrix[j][i]
        for i in range(3):
            for j in range(3):
                assert matrix[i][j] == matrix[j][i]
                assert -0.2 <= matrix[i][j] <= 1.0

def test_comparar_modelos_cache():
    """Verifica que la caché retorne la misma instancia sin recalcular."""
    first = SpatialDensityService.comparar_modelos('bolivia')
    second = SpatialDensityService.comparar_modelos('bolivia')
    assert first is second

def test_api_model_comparison_endpoint(client):
    """Verifica el endpoint GET /api/v1/model_comparison para ambos contextos."""
    for ctx in ['bolivia', 'chicago']:
        resp = client.get(f'/api/v1/model_comparison?ctx={ctx}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["ctx"] == ctx
        assert "models" in data
        assert "ari_matrix" in data

def test_view_model_comparison_dom_rendering(client):
    """Verifica el renderizado HTML de las 3 tarjetas, acordeones y la matriz ARI en la vista."""
    for ctx in ['bolivia', 'chicago']:
        resp = client.get(f'/espacial-densidad?ctx={ctx}')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # Sección modelos presente
        assert 'id="modelos"' in html
        assert 'Comparador de modelos de densidad' in html

        # Variables de los 3 algoritmos en las tarjetas
        assert '--algo-dbscan' in html
        assert '--algo-hdbscan' in html
        assert '--algo-optics' in html

        # Las mismas métricas en el mismo orden
        assert 'N.º de clústeres:' in html
        assert '% de ruido:' in html
        assert 'Cobertura espacial:' in html
        assert 'Silhouette espacial:' in html
        assert 'Tiempo de ejecución:' in html

        # Nota metodológica de honestidad presente
        assert 'Silhouette calculado sin ruido' in html
        assert 'cobertura espacial' in html

        # Acordeón "Ver detalle técnico" presente
        assert 'Ver detalle técnico' in html

        # Mini matriz ARI presente
        assert 'Coincidencia entre modelos de densidad' in html
        assert 'índice de Rand ajustado' in html

        # Clarificación A: coherencia de conteos de Bolivia
        if ctx == 'bolivia':
            assert '137 crónicas analizadas · 137 georreferenciadas' in html

