import sys
import os
import pytest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from app import create_app
from modules.services.bolivia_service import BoliviaService
from modules.services.chicago_service import ChicagoService

@pytest.fixture
def client():
    app = create_app('dev')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_bolivia_anomalies_service():
    """Valida la detección de anomalías del Autoencoder sobre noticias de Bolivia."""
    data = BoliviaService.get_anomalies_analysis()
    assert data["total_analizados"] == 137
    assert data["total_anomalias"] == 14
    assert 0.0060 <= data["umbral_corte"] <= 0.0062
    assert data["error_max"] > data["error_medio"] > data["error_min"]
    assert len(data["anomalias"]) == 14
    first = data["anomalias"][0]
    assert "error" in first
    assert "titulo" in first
    assert "delito" in first
    assert "ciudad" in first

def test_chicago_anomalies_service():
    """Valida la detección de anomalías del Autoencoder sobre el benchmark de Chicago RMS."""
    data = ChicagoService.get_anomalies_analysis()
    assert data["total_analizados"] == 250
    assert data["total_anomalias"] >= 25
    assert 0.0070 <= data["umbral_corte"] <= 0.0076
    assert data["error_max"] > data["error_medio"] > data["error_min"]
    assert len(data["anomalias"]) >= 25
    first = data["anomalias"][0]
    assert "error" in first
    assert "titulo" in first
    assert "delito" in first
    assert "ciudad" in first

def test_anomalies_view_bolivia(client):
    """Verifica que la vista responda 200 y renderice el corpus boliviano."""
    res = client.get('/anomalias-probabilistico?ctx=bolivia')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'PRENSA POLICIAL BOLIVIA' in html
    assert 'Noticias Anómalas Detectadas (Bolivia)' in html
    assert '137' in html
    assert 'Santa Cruz' in html

def test_anomalies_view_chicago(client):
    """Verifica que la vista responda 200 y renderice el benchmark de Chicago."""
    res = client.get('/anomalias-probabilistico?ctx=chicago')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'CHICAGO POLICE RMS (BENCHMARK)' in html
    assert 'Incidentes Anómalos Detectados (Chicago RMS)' in html
    assert '250' in html
    assert 'The Loop' in html

def test_gmm_simulation_api(client):
    """Verifica la simulación de riesgo estocástico GMM en ambos contextos."""
    # Bolivia
    res_bo = client.post('/api/gmm_simulate', json={
        "lat": -17.7833,
        "lon": -63.1821,
        "ctx": "bolivia"
    })
    assert res_bo.status_code == 200
    data_bo = res_bo.get_json()
    assert "risk_score_pct" in data_bo
    assert "min_mahalanobis" in data_bo
    assert "component_probs" in data_bo

    # Chicago
    res_chi = client.post('/api/gmm_simulate', json={
        "lat": 41.8818,
        "lon": -87.6231,
        "ctx": "chicago"
    })
    assert res_chi.status_code == 200
    data_chi = res_chi.get_json()
    assert "risk_score_pct" in data_chi
    assert "min_mahalanobis" in data_chi
    assert "component_probs" in data_chi

