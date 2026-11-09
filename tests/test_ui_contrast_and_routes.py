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


