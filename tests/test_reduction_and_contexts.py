import sys
import os
import json
import pytest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_reduction_files_exist():
    """Verifica que ambos datasets Gold existan y contengan coordenadas válidas."""
    bolivia_fp = os.path.join(base_dir, 'data', 'bolivia_news', 'gold', 'reduction_embeddings.json')
    chicago_fp = os.path.join(base_dir, 'data', 'chicago_benchmark', 'gold', 'reduction_embeddings_chicago.json')

    assert os.path.exists(bolivia_fp), "Falta reduction_embeddings.json de Bolivia"
    assert os.path.exists(chicago_fp), "Falta reduction_embeddings_chicago.json de Chicago"

    with open(bolivia_fp, 'r', encoding='utf-8') as f:
        d_bol = json.load(f)
    with open(chicago_fp, 'r', encoding='utf-8') as f:
        d_chi = json.load(f)

    assert len(d_bol.get('points', [])) == 137
    assert len(d_chi.get('points', [])) == 250

    for algo in ['pca', 'svd', 'ppca', 'tsne', 'umap']:
        assert algo in d_bol, f"{algo} no está en embeddings Bolivia"
        assert len(d_bol[algo]['coords']) == 137
        assert algo in d_chi, f"{algo} no está en embeddings Chicago"
        assert len(d_chi[algo]['coords']) == 250

def test_reduction_routes_bolivia(client):
    """Verifica respuesta 200 y ausencia de bug Jinja (None%) en Bolivia."""
    for algo in ['pca', 'svd', 'ppca', 'tsne', 'umap']:
        res = client.get(f'/reduccion-espacios?algo={algo}&ctx=bolivia')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert 'None%' not in html, f"Bug de porcentaje None detectado en {algo} Bolivia"
        assert 'PRENSA POLICIAL BOLIVIA' in html

def test_reduction_routes_chicago(client):
    """Verifica respuesta 200, contexto Chicago y métricas correctas."""
    for algo in ['pca', 'svd', 'ppca', 'tsne', 'umap']:
        res = client.get(f'/reduccion-espacios?algo={algo}&ctx=chicago')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert 'None%' not in html, f"Bug de porcentaje None detectado en {algo} Chicago"
        assert 'CHICAGO POLICE RMS (BENCHMARK)' in html
        assert '250' in html

