"""
Suite de Pruebas de Continuidad y Calidad de Frontend (CPD Analytics Core)
Verifica que todas las rutas analíticas respondan HTTP 200 en ambos contextos
(Bolivia y Chicago) y audita las plantillas para asegurar cumplimiento de contraste.
"""
import sys
import os
import re
import pytest

# Asegurar que el directorio 'proyecto' esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.factory import create_app

@pytest.fixture
def client():
    app = create_app('dev')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_routes_status_bolivia(client):
    """Verifica que todas las vistas carguen correctamente con contexto Bolivia."""
    endpoints = [
        '/',
        '/globo-3d',
        '/reduccion-espacios',
        '/nlp-topicos',
        '/anomalias-probabilistico',
        '/jerarquico-densidad',
        '/kmeans-nlp'
    ]
    for ep in endpoints:
        resp = client.get(f"{ep}?ctx=bolivia")
        assert resp.status_code == 200, f"Fallo al cargar {ep}?ctx=bolivia"

def test_routes_status_chicago(client):
    """Verifica que todas las vistas carguen correctamente con contexto Chicago."""
    endpoints = [
        '/',
        '/globo-3d',
        '/reduccion-espacios',
        '/nlp-topicos',
        '/anomalias-probabilistico',
        '/jerarquico-densidad',
        '/kmeans-nlp'
    ]
    for ep in endpoints:
        resp = client.get(f"{ep}?ctx=chicago")
        assert resp.status_code == 200, f"Fallo al cargar {ep}?ctx=chicago"

def test_sidebar_nav_links_have_tactical_class(client):
    """Verifica que la barra lateral utilice la clase semántica .nav-link-tactical."""
    resp = client.get('/?ctx=bolivia')
    html = resp.get_data(as_text=True)
    assert 'nav-link-tactical' in html, "No se encontró la clase .nav-link-tactical en la barra lateral"
    assert 'nav-section-title' in html, "No se encontró la clase .nav-section-title en la barra lateral"

def test_dashboard_kpi_has_no_raw_text_white(client):
    """Verifica que los números de KPIs no usen text-white rígido sin calificador dark:."""
    resp = client.get('/?ctx=bolivia')
    html = resp.get_data(as_text=True)
    # Validar que los KPIs numéricos usen text-slate-950 dark:text-white
    assert 'text-slate-950 dark:text-white' in html, "Los KPIs deben incluir text-slate-950 dark:text-white"

def test_css_design_tokens_present():
    """Verifica que style.css contenga los tokens semánticos requeridos."""
    css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'style.css'))
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert '--nav-active-bg' in content
    assert '--nav-active-text' in content
    assert '.nav-link-tactical' in content
    assert '.badge-status-cyan' in content
    assert '--text-muted: #334155;' in content

def test_globo_3d_dock_dropdown_contrast(client):
    """Verifica que el menú desplegable de ciudades en Globo 3D tenga clases adaptativas claro/oscuro."""
    resp = client.get('/globo-3d?ctx=bolivia')
    html = resp.get_data(as_text=True)
    assert 'bg-white/95 dark:bg-slate-900/95' in html, "El menú desplegable debe ser bg-white/95 en modo día"
    
    css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'globo_3d.css'))
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
    assert '#dock-dropdown-menu' in css
    assert 'var(--hud-glass-bg)' in css
    assert '.hud-dock-menu-btn.active' in css

def test_spatial_density_math_and_inspector(client):
    """Verifica que la vista jerarquico-densidad contenga la fundamentación matemática adaptativa y el inspector lateral."""
    for ctx, sample in [('bolivia', '137 reportes curados'), ('chicago', '50,000 incidentes')]:
        resp = client.get(f'/jerarquico-densidad?ctx={ctx}')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # 1. Fundamentación matemática formal presente con KaTeX adaptativo (sin cajas negras forzadas)
        assert 'FUNDAMENTACIÓN MATEMÁTICA // MODELOS DE DENSIDAD' in html
        assert 'bg-slate-100/90 dark:bg-slate-800/70' in html
        assert 'Métrica Haversine' in html
        assert 'Densidad DBSCAN' in html
        assert 'Topología OPTICS' in html
        assert 'HDBSCAN &amp; Ward' in html

        # 2. Inspector lateral táctico
        assert 'id="spatial-inspector-panel"' in html
        assert 'INSPECTOR GEOESPACIAL' in html
        assert 'side-inspector-zone' in html
        assert 'side-inspector-vol' in html

        # 3. Datos correctos del contexto
        assert sample in html

        # 4. Controles tácticos superpuestos al mapa oscuro con contraste garantizado (sin text-on-surface ciego)
        assert 'id="spatial-hud-box"' in html
        assert 'id="tactical-legend-dock"' in html
        assert 'id="tactical-zoom-dock"' in html
        assert 'text-slate-100 font-semibold' in html
        assert 'bg-[#0b1320]/95' in html

def test_kmeans_nlp_math_cross_concordance_and_api(client):
    """Verifica que /kmeans-nlp presente la fundamentación matemática adaptativa, la concordancia cruzada ARI/NMI y la inferencia bicontexto."""
    # 1. Contexto Bolivia
    resp_bo = client.get('/kmeans-nlp?ctx=bolivia')
    assert resp_bo.status_code == 200
    html_bo = resp_bo.get_data(as_text=True)

    assert 'BOLIVIA DATA: 137 REPORTES CLASIFICADOS' in html_bo
    assert 'bg-slate-100/90 dark:bg-slate-800/70' in html_bo
    assert 'Inercia WSS (Elbow)' in html_bo
    assert 'Silhouette Score' in html_bo
    assert 'Davies-Bouldin (DBI)' in html_bo
    assert 'Calinski-Harabasz' in html_bo
    assert 'ARI = 1.000' in html_bo
    assert 'NMI = 1.000' in html_bo
    assert 'Consistencia: 100.0%' in html_bo
    assert 'Santa Cruz Casco' in html_bo
    assert 'Cochabamba Cercado' in html_bo
    assert 'id="k-metrics-json"' in html_bo

    # 2. Contexto Chicago
    resp_chi = client.get('/kmeans-nlp?ctx=chicago')
    assert resp_chi.status_code == 200
    html_chi = resp_chi.get_data(as_text=True)

    assert 'CHICAGO DATA: 800,000+ INCIDENT RECORDS' in html_chi
    assert 'ARI = 0.742' in html_chi
    assert 'NMI = 0.789' in html_chi
    assert 'D-011 / Harrison West' in html_chi

    # 3. Inferencia NLP API con español (Bolivia)
    res_es = client.post('/api/v1/predict_nlp', json={
        "text": "ASALTO A MANO ARMADA EN EL SEXTO ANILLO DE LA DOBLE VIA A LA GUARDIA DOS MOTOLADRONES CON PISTOLA Y DISPARO",
        "algo": "kmeans"
    })
    assert res_es.status_code == 200
    data_es = res_es.get_json()
    assert data_es['success'] is True
    assert data_es['cluster_id'] == 2
    assert data_es['confidence'] >= 75.0
    assert any(k in ["ASALTO", "ARMA", "PISTOLA", "DISPARO", "MOTOLADRONES"] for k in data_es['matched_keywords'])

    # 4. Inferencia NLP API con inglés (Chicago)
    res_en = client.post('/api/v1/predict_nlp', json={
        "text": "RETAIL THEFT AT TARGET DEPARTMENT STORE CASH REGISTER CONCEALED MERCHANDISE",
        "algo": "kmeans"
    })
    assert res_en.status_code == 200
    data_en = res_en.get_json()
    assert data_en['success'] is True
    assert data_en['cluster_id'] == 1
    assert data_en['confidence'] >= 75.0
    assert any(k in ["THEFT", "RETAIL", "STORE", "CASH", "REGISTER"] for k in data_en['matched_keywords'])





