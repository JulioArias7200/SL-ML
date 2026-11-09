import sys
import os
import pytest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from app import create_app
from modules.services.nlp_topics_service import NLPTopicsService

@pytest.fixture
def client():
    app = create_app('dev')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_nlp_summary_bolivia():
    """Valida la agregación estadística del corpus de Bolivia (137 notas)."""
    summary = NLPTopicsService.get_corpus_summary('bolivia')
    assert summary['context'] == 'bolivia'
    assert summary['total_notes'] == 137
    assert len(summary['topics']) == 5
    assert len(summary['topic_distribution']) == 5
    assert len(summary['sample_notes']) == 137

    # Verificar que los porcentajes sumen aproximadamente 100%
    total_pct = sum(d['pct'] for d in summary['topic_distribution'])
    assert 99.0 <= total_pct <= 101.0

def test_nlp_summary_chicago():
    """Valida la agregación estadística del benchmark de Chicago (250 incidentes curados)."""
    summary = NLPTopicsService.get_corpus_summary('chicago')
    assert summary['context'] == 'chicago'
    assert summary['total_notes'] == 250
    assert len(summary['topics']) == 5
    assert len(summary['topic_distribution']) == 5
    assert len(summary['sample_notes']) == 250

    total_pct = sum(d['pct'] for d in summary['topic_distribution'])
    assert 99.0 <= total_pct <= 101.0

def test_nlp_view_bolivia(client):
    """Verifica que /nlp-topicos?ctx=bolivia responda 200 y renderice el corpus boliviano."""
    res = client.get('/nlp-topicos?ctx=bolivia')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Contexto: Bolivia' in html
    assert '137 registros analizados' in html
    assert 'undefined' not in html
    assert 'Atracos' in html
    assert 'Narcotráfico' in html

def test_nlp_view_chicago(client):
    """Verifica que /nlp-topicos?ctx=chicago responda 200 y renderice el benchmark de Chicago."""
    res = client.get('/nlp-topicos?ctx=chicago')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Contexto: Chicago' in html
    assert '250 registros analizados' in html
    assert 'undefined' not in html
    assert 'Retail Shoplifting' in html
    assert 'Weapons Violations' in html

def test_nlp_api_predict_bolivia(client):
    """Verifica la inferencia LDA en vivo con texto boliviano en español."""
    payload = {
        "text": "Dos sujetos a bordo de una motocicleta amenazaron a una mujer con arma de fuego en el segundo anillo para robar su cartera.",
        "ctx": "bolivia"
    }
    res = client.post('/api/v1/predict_nlp', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['title'] is not None
    assert 'undefined' not in data['title']
    assert '%' in data['confidence']
    assert len(data['probabilities']) == 5
    assert data['topic_id'] == 3  # Atracos Motochorros
    assert 'arma' in data['matched_keywords']

def test_nlp_api_predict_chicago(client):
    """Verifica la inferencia LDA en vivo con texto de Chicago en inglés."""
    payload = {
        "text": "Two armed suspects displayed a handgun on the sidewalk and demanded cash from the victim.",
        "ctx": "chicago"
    }
    res = client.post('/api/v1/predict_nlp', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['title'] is not None
    assert len(data['probabilities']) == 5
    assert data['topic_id'] == 2  # Weapons & Armed Robbery
    assert 'handgun' in data['matched_keywords'] or 'sidewalk' in data['matched_keywords']

