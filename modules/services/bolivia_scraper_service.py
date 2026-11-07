"""
===============================================================================
BOLIVIA SCRAPER SERVICE  -  Motor de Ingesta Incremental y Sostenible
===============================================================================
Propósito:
    Recolectar noticias policiales de Bolivia de forma incremental:
    - NUNCA borra las noticias que ya se tienen.
    - Preserva la fecha original de publicación de cada noticia.
    - En cada ejecución, suma noticias nuevas al histórico acumulado.
    - Evita duplicados por URL y por similitud semántica.
    - Cubre todos los departamentos de Bolivia (basado en NOTICIAS.md).

Medios cubiertos (basado en investigación NOTICIAS.md):
    Nacional: Red Uno, ATB, Unitel, Bolivisión, Cadena A, Bolivia TV, 
              Erbol, Radio Fides, ANF, ABI, Brújula Digital, Urgente, Eju.tv
    La Paz:   La Razón, El Diario, Visión 360, El Alteño, Éxito Noticias
    Santa Cruz: El Deber, El Día, El Mundo, Asuntos Centrales
    Cochabamba: Los Tiempos, Opinión
    Chuquisaca: Correo del Sur
    Oruro:    La Patria
    Potosí:   El Potosí
    Tarija:   El País, La Voz de Tarija, El Gran Chaco
    Beni:     La Palabra del Beni
    Pando:    Sol de Pando, Perla del Acre

Arquitectura:
    Bronze  → data/bolivia_news/bronze/eventos_bolivia_raw.csv    (acumulado crudo)
    Silver  → data/bolivia_news/silver/eventos_bolivia_cleaned.csv (acumulado limpio)
    Gold    → data/bolivia_news/gold/*.csv                         (modelos aplicados)
===============================================================================
"""

import os
import sys
import re
import time
import json
import html as _html
import gzip
import random
import hashlib
import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin

# Reconfigurar stdout/stderr para evitar fallos de codificacion en Windows (cp1252)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import numpy as np
import pandas as pd

# ─── Importaciones opcionales con degradación elegante ───────────────────────
try:
    import requests
    import requests_cache
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[SCRAPER] AVISO: 'requests' no instalado. Instalar con: pip install requests requests-cache")

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False
    print("[SCRAPER] AVISO: 'trafilatura' no instalado. Instalar con: pip install trafilatura")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# ─── Rutas canónicas del proyecto ────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BRONZE    = os.path.join(_BASE_DIR, 'data', 'bolivia_news', 'bronze', 'eventos_bolivia_raw.csv')
_SILVER    = os.path.join(_BASE_DIR, 'data', 'bolivia_news', 'silver', 'eventos_bolivia_cleaned.csv')
_GOLD_DIR  = os.path.join(_BASE_DIR, 'data', 'bolivia_news', 'gold')
_CACHE_DB  = os.path.join(_BASE_DIR, 'data', 'bolivia_news', 'bronze', 'cache_http.sqlite')

# ─── Parámetros globales de crawl ────────────────────────────────────────────
DESDE_SITEMAP        = "2024-01-01"      # Noticias desde esta fecha en sitemaps
MAX_DESCARGAS_MEDIO  = 300               # Artículos nuevos máx. por medio por corrida
MAX_SITEMAPS_INDICE  = 24               # Profundidad máxima en índices de sitemaps
DELAY_ENTRE_PETICIONES = (1.5, 3.5)     # Rango de espera aleatoria entre peticiones (educado)
TIMEOUT_HTTP         = 15               # Tiempo máximo de espera por petición

# ─── Cabeceras de navegador realistas (rotación) ─────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
]

# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 1: CATÁLOGO DE FUENTES (basado en NOTICIAS.md)
# ═══════════════════════════════════════════════════════════════════════════════

# Canales de YouTube: ID del canal → RSS público (sin API Key)
# El feed RSS oficial de YouTube es público y gratuito para cualquier canal.
CANALES_YT_RSS = {
    # === NACIONALES ===
    "unitel":           "UCBTuUY99I5plMaC_ZcmXIYw",   # Unitel Bolivia
    "reduno":           "UCaIoV23UMZNifJ3G-djMU-Q",   # Red Uno de Bolivia
    "atb":              "UCYZQTHltkIdWPAcM-XfFiIQ",   # ATB Digital
    "bolivision_aldia": "UC-FgwdII7YJUNmj-RN6qVOg",  # Bolivisión – Al Día Tu Día
    "cadena_a":         "UCIJOvXBJ134YKzohZqpQBEA",   # Cadena A Red Nacional
    "rtp_bolivia":      "UCPHPu0J-6DDxyl9Fm83Z83Q",   # RTP Bolivia
    "dtv_bolivia":      "UCKVbNFfp6NP9tkqpY3nINEw",   # DTV Bolivia
    "erbol":            "UC6U7VqJNElV74LfhV9Nqnmg",   # Red Erbol
    "radio_fides":      "UCUzqb3UEMfh_QDNS3tXk3dg",   # Radio Fides Bolivia
    "anf_bolivia":      "UCQZeNQnT5aQS5rKnH-45Mug",   # Agencia de Noticias Fides
    # === LA PAZ ===
    "larazon_lp":       "UCWf5SEFLs0HJZsHv_Y2xYQg",   # La Razón Digital Bolivia
    "brujula_digital":  "UC6i-WFTfbRbxXNfUFkHZ9hQ",   # Brújula Digital Bolivia
    # === SANTA CRUZ ===
    "eldeber_scz":      "UCiHbzNRMU0RCPDl_IEMjAWg",   # El Deber Santa Cruz
    "asuntos_cent":     "UCB2bAHaRqcnEHIvNQQDwnQg",   # Asuntos Centrales TV
    # === COCHABAMBA ===
    "lostiempos_cbba":  "UCHBnz_3UJD2n7PMXqp6Dv0Q",   # Los Tiempos Bolivia
    # === CHUQUISACA ===
    "correodelsur":     "UCqMoLiDtUJXFYUoQ4oPvFmw",   # Correo del Sur
    # === ORURO ===
    "lapatria_oruro":   "UCByJbHr-BNamwUy8zK8JKAw",   # La Patria Oruro
    # === POTOSÍ ===
    "elpotosi":         "UCUzMTqVVGDwYCBqI7F3zObA",   # El Potosí
    # === TARIJA ===
    "elpais_tarija":    "UCO9w1sJq6oKiPiEY9BCJQ5A",   # El País Tarija
    # === BENI ===
    "benitv":           "UCW_kWc9p1nHgUmN8rI2ciwA",   # Beni TV
}

# Diccionario de medios web con metadatos técnicos y departamento de cobertura
# Basado completamente en la investigación de NOTICIAS.md
MEDIOS = {
    # ── NACIONALES / EJE TRONCAL ──────────────────────────────────────────────
    "reduno":       {
        "dominio":    "www.reduno.com.bo",
        "depto":      None,  # Nacional
        "cobertura":  "Nacional (Santa Cruz / La Paz)",
        "secciones":  ["https://www.reduno.com.bo/tag/asalto",
                       "https://www.reduno.com.bo/tag/robo",
                       "https://www.reduno.com.bo/noticias/comunidad"],
        "patron":     r"^/noticias/[^/]+-\d{12,14}$",
    },
    "atb":          {
        "dominio":    "www.atb.com.bo",
        "depto":      None,
        "cobertura":  "Nacional (estatal)",
        "secciones":  ["https://www.atb.com.bo/etiqueta/seguridad/pagina/{n}"],
    },
    "unitel":       {
        "dominio":    "unitel.bo",
        "depto":      None,
        "cobertura":  "Nacional (Santa Cruz / nacional)",
        "secciones":  ["https://unitel.bo/noticias/seguridad"],
    },
    "erbol":        {
        "dominio":    "erbol.com.bo",
        "depto":      None,
        "cobertura":  "Nacional (radiofónica comunitaria)",
        "secciones":  ["https://erbol.com.bo/noticias/seguridad"],
    },
    "brujula":      {
        "dominio":    "brujuladigital.net",
        "depto":      None,
        "cobertura":  "Nacional (investigación)",
        "secciones":  [],
    },
    "urgente":      {
        "dominio":    "www.urgente.bo",
        "depto":      None,
        "cobertura":  "Nacional",
        "secciones":  [],
    },
    "eju":          {
        "dominio":    "eju.tv",
        "depto":      None,
        "cobertura":  "Nacional",
        "secciones":  [],
    },
    "anf":          {
        "dominio":    "noticiasfides.com",
        "depto":      None,
        "cobertura":  "Nacional (agencia independiente)",
        "secciones":  ["https://noticiasfides.com/seguridad"],
    },
    # ── LA PAZ ────────────────────────────────────────────────────────────────
    "larazon":      {
        "dominio":    "www.larazon.bo",
        "depto":      "La Paz",
        "cobertura":  "La Paz / Nacional",
        "secciones":  ["https://www.larazon.bo/seguridad"],
    },
    "eldiario":     {
        "dominio":    "www.eldiario.net",
        "depto":      "La Paz",
        "cobertura":  "La Paz (decano)",
        "secciones":  [],
    },
    "vision360":    {
        "dominio":    "vision360.bo",
        "depto":      "La Paz",
        "cobertura":  "La Paz (nativo digital)",
        "secciones":  [],
    },
    "elalteno":     {
        "dominio":    "elalteno.com.bo",
        "depto":      "La Paz",
        "cobertura":  "El Alto / La Paz",
        "secciones":  ["https://elalteno.com.bo/seguridad"],
    },
    # ── SANTA CRUZ ────────────────────────────────────────────────────────────
    "eldeber":      {
        "dominio":    "eldeber.com.bo",
        "depto":      "Santa Cruz",
        "cobertura":  "Santa Cruz / Nacional",
        "secciones":  ["https://eldeber.com.bo/seguridad"],
    },
    "eldia_scz":    {
        "dominio":    "eldia.com.bo",
        "depto":      "Santa Cruz",
        "cobertura":  "Santa Cruz",
        "secciones":  [],
    },
    # ── COCHABAMBA ────────────────────────────────────────────────────────────
    "lostiempos":   {
        "dominio":    "www.lostiempos.com",
        "depto":      "Cochabamba",
        "cobertura":  "Cochabamba",
        "secciones":  ["https://www.lostiempos.com/seguridad"],
    },
    "opinion":      {
        "dominio":    "www.opinion.com.bo",
        "depto":      "Cochabamba",
        "cobertura":  "Cochabamba",
        "secciones":  ["https://www.opinion.com.bo/seguridad"],
    },
    # ── CHUQUISACA ────────────────────────────────────────────────────────────
    "correodelsur": {
        "dominio":    "correodelsur.com",
        "depto":      "Chuquisaca",
        "cobertura":  "Sucre / Chuquisaca",
        "secciones":  [],
    },
    # ── ORURO ─────────────────────────────────────────────────────────────────
    "lapatria":     {
        "dominio":    "lapatria.bo",          # dominio migrado (.com.bo → .bo)
        "depto":      "Oruro",
        "cobertura":  "Oruro",
        "secciones":  [],
    },
    # ── POTOSÍ ────────────────────────────────────────────────────────────────
    "elpotosi":     {
        "dominio":    "elpotosi.net",
        "depto":      "Potosí",
        "cobertura":  "Potosí",
        "secciones":  [],
    },
    # ── TARIJA ────────────────────────────────────────────────────────────────
    "elpais_tarija": {
        "dominio":    "elpais.bo",            # dominio migrado (.com.bo → .bo)
        "depto":      "Tarija",
        "cobertura":  "Tarija",
        "secciones":  [],
    },
    "lavoz_tarija": {
        "dominio":    "lavozdetarija.com",
        "depto":      "Tarija",
        "cobertura":  "Tarija",
        "secciones":  [],
    },
    "granchaco":    {
        "dominio":    "diarioelgranchaco.com",
        "depto":      "Tarija",
        "cobertura":  "Tarija (Yacuiba/Chaco)",
        "secciones":  [],
    },
    # ── BENI ──────────────────────────────────────────────────────────────────
    "palabradelbeni": {
        "dominio":    "lapalabradelbeni.com",
        "depto":      "Beni",
        "cobertura":  "Beni (Trinidad)",
        "secciones":  [],
    },
    # ── PANDO ─────────────────────────────────────────────────────────────────
    "soldepando":   {
        "dominio":    "soldepando.com",
        "depto":      "Pando",
        "cobertura":  "Pando (Cobija)",
        "secciones":  [],
    },
    "perladelacre": {
        "dominio":    "perladelacre.com",
        "depto":      "Pando",
        "cobertura":  "Pando (Cobija)",
        "secciones":  [],
    },
}

# Términos que indican noticias policiales/de seguridad ciudadana
PALABRAS_CLAVE_DELITO = {
    "asalto", "robo", "hurto", "asesinato", "feminicidio", "homicidio",
    "violacion", "violación", "feminicida", "balacera", "disparo",
    "aprehendido", "aprehension", "aprehensión", "detenido", "detenidos",
    "droga", "narcotráfico", "narcotrafico", "cocaína", "cocaina",
    "marihuana", "felcn", "operativo", "incautacion", "incautación",
    "secuestro", "extorsion", "extorsión", "moto", "motochorro",
    "asaltaron", "robaron", "mataron", "dispararon", "herido",
    "accidente", "choque", "atropello", "violencia", "agresion", "agresión",
    "sicario", "banda", "delincuente", "criminal", "preso", "presos",
    "carcel", "cárcel", "penal", "fiscalia", "fiscalía", "policia", "policía",
}

# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 2: CLIENTE HTTP EDUCADO CON CACHÉ
# ═══════════════════════════════════════════════════════════════════════════════

class ClienteHTTP:
    """
    Cliente HTTP con caché SQLite local, cabeceras realistas rotadas y 
    manejo gracioso de errores 403/429 (bloqueos).
    """

    def __init__(self):
        if not HAS_REQUESTS:
            self._session = None
            return
        self._session = requests_cache.CachedSession(
            cache_name=_CACHE_DB.replace('.sqlite', ''),
            expire_after=datetime.timedelta(days=30),
            allowable_codes=(200,),
        )
        self._bloqueos_consecutivos = 0
        self._max_bloqueos = 5

    def _headers(self):
        return {
            "User-Agent":      random.choice(_USER_AGENTS),
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-BO,es;q=0.9,en-US;q=0.7,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection":      "keep-alive",
            "DNT":             "1",
        }

    def get(self, url, timeout=TIMEOUT_HTTP):
        if self._session is None:
            return None
        if self._bloqueos_consecutivos >= self._max_bloqueos:
            raise RuntimeError(f"[SCRAPER] Demasiados bloqueos consecutivos ({self._max_bloqueos}). Pausa voluntaria.")
        try:
            r = self._session.get(url, headers=self._headers(), timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                self._bloqueos_consecutivos = 0
                # Espera educada solo si no viene de caché
                if not getattr(r, 'from_cache', False):
                    time.sleep(random.uniform(*DELAY_ENTRE_PETICIONES))
                return r
            elif r.status_code in (403, 429, 503):
                self._bloqueos_consecutivos += 1
                print(f"  [BLOQUEADO {r.status_code}] {url[:80]}")
                time.sleep(random.uniform(5, 12))
                return None
            else:
                return None
        except Exception as e:
            print(f"  [ERROR] {url[:80]} → {e}")
            return None


# Instancia global del cliente
_cliente = ClienteHTTP()

# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 3: CLASIFICADORES LINGÜÍSTICOS
# ═══════════════════════════════════════════════════════════════════════════════

# Geografía de Bolivia: ciudad → (departamento, lat, lon)
CIUDADES_BO = {
    # La Paz
    "La Paz":        ("La Paz",     -16.5000, -68.1500),
    "El Alto":       ("La Paz",     -16.5036, -68.1933),
    # Cochabamba
    "Cochabamba":    ("Cochabamba", -17.3935, -66.1570),
    "Quillacollo":   ("Cochabamba", -17.3934, -66.2807),
    "Sacaba":        ("Cochabamba", -17.3762, -65.0096),
    # Santa Cruz
    "Santa Cruz":    ("Santa Cruz", -17.7833, -63.1821),
    "Montero":       ("Santa Cruz", -17.3400, -63.2500),
    "Warnes":        ("Santa Cruz", -17.5000, -63.1667),
    # Oruro
    "Oruro":         ("Oruro",      -17.9833, -67.1500),
    # Potosí
    "Potosí":        ("Potosí",     -19.5836, -65.7531),
    # Sucre
    "Sucre":         ("Chuquisaca", -19.0431, -65.2592),
    # Tarija
    "Tarija":        ("Tarija",     -21.5355, -64.7296),
    "Yacuiba":       ("Tarija",     -22.0000, -63.6700),
    # Beni
    "Trinidad":      ("Beni",       -14.8333, -64.9000),
    # Pando
    "Cobija":        ("Pando",      -11.0000, -68.7667),
}

# Departamentos y sus términos de detección
DEPTOS_TERMINOS = {
    "La Paz":        ["la paz", "la paz.", "paceño", "paceña", "el alto", "alteno"],
    "Cochabamba":    ["cochabamba", "cbba", "cochabambino", "quillacollo", "sacaba"],
    "Santa Cruz":    ["santa cruz", "cruceño", "cruceña", "montero", "warnes"],
    "Oruro":         ["oruro", "orureño", "orureña"],
    "Potosí":        ["potosí", "potosi", "potosino", "uyuni", "llallagua"],
    "Chuquisaca":    ["sucre", "chuquisaca", "sucrense"],
    "Tarija":        ["tarija", "tarijeño", "tarijeña", "yacuiba", "bermejo"],
    "Beni":          ["beni", "trinidad", "beniano", "beniana", "cobija"],
    "Pando":         ["pando", "cobija", "pandino"],
}

# Categorías de delito con sus términos disparadores
CATEGORIAS_DELITO = {
    "Homicidio / Asesinato":       ["asesinato", "homicidio", "asesinaron", "matar", "mataron", "muerte violenta", "cadáver", "cadaver", "cuerpo sin vida", "sicario"],
    "Feminicidio":                 ["feminicidio", "feminicida", "femicidio"],
    "Robo Agravado / Asalto":      ["asalto", "asaltaron", "asaltado", "robo", "robaron", "motochorro", "asaltar", "asaltante", "encapuchado", "arma", "arma de fuego", "balacera", "disparo"],
    "Hurto / Descuidismo":         ["hurto", "descuidismo", "sustrajo", "sustrajeron", "bolso", "cartera", "mochila", "celular", "robaron", "pickpocket"],
    "Narcotráfico / Sustancias":   ["droga", "cocaína", "cocaina", "marihuana", "narcotráfico", "narcotrafico", "felcn", "sustancia controlada", "incautación", "incautacion", "clorhidrato"],
    "Agresión Física / Lesiones":  ["agresión", "agresion", "golpes", "herido", "herida", "lesiones", "peleas", "riña", "rina", "altercado"],
    "Violación / Abuso Sexual":    ["violación", "violacion", "abuso sexual", "acoso", "violador"],
    "Extorsión / Estafa":          ["extorsión", "extorsion", "estafa", "defraudación", "defraudacion", "engaño", "engano", "fraude"],
    "Accidente de Tránsito":       ["accidente", "choque", "colisión", "colision", "atropello", "volcamiento", "impacto vial"],
    "Secuestro / Desaparición":    ["secuestro", "secuestrado", "desaparición", "desaparecido", "desaparecida"],
    "Incendio / Desastre":         ["incendio", "explosión", "explosion", "derrumbe", "inundación", "inundacion"],
}


def _normalizar(texto):
    """Convierte texto a minúsculas sin acentos para búsquedas robustas."""
    texto = texto.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
        texto = texto.replace(a, b)
    return texto


def detectar_departamento(titulo, texto="", depto_default=None):
    """Detecta el departamento de Bolivia mencionado en el texto."""
    haystack = _normalizar(titulo + " " + texto[:800])
    for depto, terminos in DEPTOS_TERMINOS.items():
        for t in terminos:
            if t in haystack:
                return depto
    return depto_default


def detectar_ciudad(titulo, texto="", depto=None):
    """Detecta la ciudad mencionada y devuelve (ciudad, lat, lon)."""
    haystack = _normalizar(titulo + " " + texto[:800])
    for ciudad, (dep, lat, lon) in CIUDADES_BO.items():
        if depto and dep != depto:
            continue
        if _normalizar(ciudad) in haystack:
            return ciudad, lat, lon
    # Fallback: usar capital del departamento
    if depto:
        for ciudad, (dep, lat, lon) in CIUDADES_BO.items():
            if dep == depto:
                return ciudad, lat, lon
    return None, None, None


def clasificar_delito(titulo, texto=""):
    """Clasifica el tipo de delito principal a partir del texto."""
    haystack = _normalizar(titulo + " " + texto[:600])
    for categoria, terminos in CATEGORIAS_DELITO.items():
        for t in terminos:
            if t in haystack:
                return categoria
    return "No especificado"


def extraer_franja(texto):
    """Detecta la franja horaria de ocurrencia del delito."""
    h = _normalizar(texto[:800])
    if any(t in h for t in ["madrugada", "medianoche", "00:", "01:", "02:", "03:", "04:"]):
        return "Madrugada"
    if any(t in h for t in ["mañana", "08:", "09:", "10:", "11:", "amanecer"]):
        return "Mañana"
    if any(t in h for t in ["tarde", "12:", "13:", "14:", "15:", "16:", "17:"]):
        return "Tarde"
    if any(t in h for t in ["noche", "18:", "19:", "20:", "21:", "22:", "23:"]):
        return "Noche"
    return "Desconocida"


def texto_es_relevante(titulo, texto=""):
    """Determina si una noticia es de seguridad ciudadana/delitos."""
    haystack = _normalizar(titulo + " " + texto[:400])
    return any(kw in haystack for kw in PALABRAS_CLAVE_DELITO)


def _slug_relevante(url):
    """Pre-filtra URLs: ¿el slug de la URL parece un artículo de delito?"""
    slug = urlparse(url).path.rstrip("/").split("/")[-1].lower().replace("-", " ")
    return any(kw in slug for kw in PALABRAS_CLAVE_DELITO)


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 4: EXTRACCIÓN Y CONSTRUCCIÓN DE FILAS
# ═══════════════════════════════════════════════════════════════════════════════

def extraer_contenido(html_bytes, url):
    """
    Extrae título, texto y fecha de publicación del HTML de un artículo.
    Estrategia 1: trafilatura (NLP especializado en noticias).
    Estrategia 2: BeautifulSoup (respaldo estructural).
    """
    titulo, texto, fecha = "", "", None

    if HAS_TRAFILATURA:
        try:
            texto = trafilatura.extract(
                html_bytes, include_comments=False, favor_precision=True
            ) or ""
            meta = trafilatura.extract_metadata(html_bytes, default_url=url)
            if meta:
                titulo = meta.title or ""
                fecha  = meta.date or None
        except Exception:
            pass

    # Respaldo con BeautifulSoup si trafilatura falló
    if HAS_BS4 and (not titulo or not texto):
        try:
            soup = BeautifulSoup(html_bytes, "html.parser")
            if not titulo:
                h1 = soup.find("h1")
                titulo = h1.get_text(strip=True) if h1 else ""
            if not texto:
                texto = " ".join(
                    p.get_text(strip=True)
                    for p in soup.find_all("p")
                    if len(p.get_text(strip=True)) > 25
                )
        except Exception:
            pass

    return titulo or "", texto or "", fecha


def construir_fila(fuente, url, fecha, titulo, texto, depto_default=None):
    """
    Construye el diccionario de una fila del dataset para un artículo.
    Preserva siempre la fecha de publicación original.
    """
    titulo = str(titulo or "").strip()
    texto  = str(texto  or "").strip()

    depto        = detectar_departamento(titulo, texto, depto_default)
    ciudad, lat, lon = detectar_ciudad(titulo, texto, depto)
    delito       = clasificar_delito(titulo, texto)
    franja       = extraer_franja(titulo + " " + texto)
    dia_semana   = None
    if fecha:
        try:
            dt = pd.to_datetime(fecha)
            dia_semana = dt.day_name()
        except Exception:
            pass

    nivel_geo = "ciudad" if ciudad else ("departamento" if depto else "desconocido")

    return {
        "fuente":           fuente,
        "url":              url,
        "fecha":            fecha,               # ← fecha original preservada
        "fecha_ingesta":    datetime.date.today().isoformat(),
        "titulo":           titulo,
        "departamento":     depto,
        "ciudad":           ciudad,
        "zona_principal":   None,
        "municipio":        depto,
        "nivel_geo":        nivel_geo,
        "lat":              lat,
        "lon":              lon,
        "delito_principal": delito,
        "franja":           franja,
        "dia_semana":       dia_semana,
        "texto":            texto,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 5: LECTURA Y ESCRITURA INCREMENTAL (El corazón del sistema sostenible)
# ═══════════════════════════════════════════════════════════════════════════════

def _cargar_urls_previas(ruta_csv):
    """
    Lee el CSV acumulado y retorna el conjunto de URLs ya recolectadas.
    Si el archivo no existe, retorna un conjunto vacío.
    """
    if os.path.exists(ruta_csv):
        try:
            df = pd.read_csv(ruta_csv, usecols=["url"])
            return set(df["url"].dropna().astype(str).tolist())
        except Exception:
            return set()
    return set()


def _guardar_fila_incremental(fila, ruta_csv):
    """
    Agrega una fila al CSV de forma incremental (append).
    Escribe cabecera solo si el archivo no existe aún.
    """
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    nuevo = pd.DataFrame([fila])
    if not os.path.exists(ruta_csv):
        nuevo.to_csv(ruta_csv, index=False, encoding="utf-8")
    else:
        nuevo.to_csv(ruta_csv, mode="a", header=False, index=False, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 6: PARSERS DE SITEMAPS Y RSS
# ═══════════════════════════════════════════════════════════════════════════════

def _tag_xml(e):
    """Extrae el nombre del tag sin el namespace XML."""
    return e.tag.split("}")[-1]


def _urls_desde_sitemap(url_sitemap, desde=DESDE_SITEMAP, _prof=0):
    """
    Lee un sitemap (o índice de sitemaps) y retorna URLs de artículos
    publicados desde la fecha indicada, ordenados del más nuevo al más viejo.
    """
    if _prof > 2:
        return []
    r = _cliente.get(url_sitemap)
    if r is None:
        return []
    data = r.content
    if url_sitemap.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            data = gzip.decompress(data)
        except Exception:
            return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []

    filas = []
    for elem in root:
        h = {_tag_xml(c): (c.text or "").strip() for c in elem}
        if h.get("loc"):
            filas.append((h["loc"], h.get("lastmod", "")[:10]))

    # Filtrar por fecha mínima
    filas = [(u, d) for u, d in filas if d >= desde or d == ""]
    # Ordenar descendente (más reciente primero)
    filas.sort(key=lambda x: x[1], reverse=True)
    urls = [u for u, _ in filas]

    # Si es un índice de sitemaps, recursión
    if root.tag and "sitemapindex" in root.tag:
        resultado = []
        for u in urls[:MAX_SITEMAPS_INDICE]:
            resultado += _urls_desde_sitemap(u, desde, _prof + 1)
        return resultado

    return urls[:20000]


def _urls_desde_robots(dominio_base):
    """Lee el robots.txt y extrae los sitemaps declarados."""
    r = _cliente.get(f"https://{dominio_base}/robots.txt")
    if r is None:
        return []
    sitemaps = []
    for line in r.text.splitlines():
        if line.strip().lower().startswith("sitemap:"):
            sm = line.split(":", 1)[1].strip()
            if sm:
                sitemaps.append(sm)
    return sitemaps


def _urls_de_medio(clave_medio):
    """
    Obtiene todas las URLs de artículos de un medio, combinando:
    1. Sitemaps declarados en robots.txt
    2. Secciones temáticas de seguridad/delitos configuradas en MEDIOS
    """
    cfg  = MEDIOS[clave_medio]
    base = "https://" + cfg["dominio"]

    # 1. Sitemaps
    sitemaps = _urls_desde_robots(cfg["dominio"])
    urls = []
    for sm in sitemaps[:MAX_SITEMAPS_INDICE]:
        urls += _urls_desde_sitemap(sm)

    # 2. Secciones temáticas adicionales
    for seccion in cfg.get("secciones", []):
        for n in range(1, 4):  # Hasta 3 páginas por sección
            url_sec = seccion.format(n=n) if "{n}" in seccion else seccion
            r = _cliente.get(url_sec)
            if r is None:
                break
            if HAS_BS4:
                try:
                    soup = BeautifulSoup(r.content, "html.parser")
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        full = urljoin(url_sec, href).split("#")[0]
                        pu = urlparse(full)
                        if pu.netloc.replace("www.", "") == cfg["dominio"].replace("www.", ""):
                            urls.append(full)
                except Exception:
                    pass

    return list(dict.fromkeys(urls))  # Deduplicar preservando orden


def urls_youtube_rss(channel_id):
    """
    Lee el feed RSS público de YouTube para un canal.
    No requiere API Key ni límite de cuota.
    URL del feed: https://www.youtube.com/feeds/videos.xml?channel_id=UCXXXX
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    r = _cliente.get(feed_url)
    if r is None:
        return []

    items = []
    try:
        # El feed RSS de YouTube usa namespace Atom
        root = ET.fromstring(r.content)
        ns = {
            "atom":    "http://www.w3.org/2005/Atom",
            "yt":      "http://www.youtube.com/xml/schemas/2015",
            "media":   "http://search.yahoo.com/mrss/",
        }
        for entry in root.findall("atom:entry", ns):
            vid_id  = entry.find("yt:videoId",  ns)
            titulo  = entry.find("atom:title",  ns)
            fecha   = entry.find("atom:published", ns)
            desc_el = entry.find("media:group/media:description", ns)
            if vid_id is None:
                continue
            items.append({
                "url":    f"https://www.youtube.com/watch?v={vid_id.text}",
                "titulo": _html.unescape(titulo.text if titulo is not None else ""),
                "fecha":  (fecha.text or "")[:10] if fecha is not None else None,
                "texto":  _html.unescape(desc_el.text or "") if desc_el is not None else "",
            })
    except ET.ParseError:
        pass

    return items


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 7: PROCESAMIENTO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def procesar_medio(clave_medio, urls_previas):
    """
    Descarga y clasifica artículos nuevos de un medio web.
    Solo procesa URLs que NO están ya en el histórico.
    Retorna lista de filas nuevas.
    """
    cfg  = MEDIOS[clave_medio]
    depto_default = cfg.get("depto")

    print(f"\n  [*] [{clave_medio}] Obteniendo URLs del sitemap/secciones...")
    todas_urls = _urls_de_medio(clave_medio)

    # Filtrar: solo nuevas + parecen artículo de delito
    nuevas = [
        u for u in todas_urls
        if u not in urls_previas and _slug_relevante(u)
    ]
    print(f"     {len(nuevas)} URLs nuevas de {len(todas_urls)} total (pre-filtradas por slug)")
    nuevas = nuevas[:MAX_DESCARGAS_MEDIO]

    filas_nuevas = []
    for i, url in enumerate(nuevas, 1):
        r = _cliente.get(url)
        if r is None:
            continue
        titulo, texto, fecha = extraer_contenido(r.content, url)
        if len(texto) < 100:
            continue
        if not texto_es_relevante(titulo, texto):
            continue
        fila = construir_fila(clave_medio, url, fecha, titulo, texto, depto_default)
        filas_nuevas.append(fila)
        _guardar_fila_incremental(fila, _BRONZE)
        urls_previas.add(url)
        print(f"     [{i}/{len(nuevas)}] {fila['delito_principal']} | {fila['departamento']} | {fila['ciudad']} | {fecha}")

    print(f"     [OK] {len(filas_nuevas)} noticias nuevas de [{clave_medio}]")
    return filas_nuevas


def procesar_youtube_canal(nombre, channel_id, urls_previas):
    """
    Recolecta videos nuevos de un canal de YouTube via RSS (sin API Key).
    Solo procesa videos con títulos relevantes a seguridad ciudadana.
    """
    print(f"\n  [*] [YT:{nombre}] Leyendo feed RSS del canal...")
    items = urls_youtube_rss(channel_id)
    nuevos = [it for it in items if it["url"] not in urls_previas]
    print(f"     {len(nuevos)} videos nuevos de {len(items)} en el feed")

    filas_nuevas = []
    for it in nuevos:
        if not texto_es_relevante(it["titulo"], it.get("texto", "")):
            continue
        fila = construir_fila(
            fuente=f"youtube:{nombre}",
            url=it["url"],
            fecha=it["fecha"],
            titulo=it["titulo"],
            texto=it["titulo"] + ". " + it.get("texto", ""),
            depto_default=None,
        )
        filas_nuevas.append(fila)
        _guardar_fila_incremental(fila, _BRONZE)
        urls_previas.add(it["url"])

    print(f"     [OK] {len(filas_nuevas)} videos relevantes de [YT:{nombre}]")
    return filas_nuevas


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 8: DEDUPLICACIÓN Y CAPAS SILVER / GOLD
# ═══════════════════════════════════════════════════════════════════════════════

# Sedes urbanas para imputación geográfica inteligente
SEDES_MEDIOS = {
    'reduno': ('Santa Cruz', 'Santa Cruz', -17.7833, -63.1821),
    'eldeber': ('Santa Cruz', 'Santa Cruz', -17.7833, -63.1821),
    'eldia_scz': ('Santa Cruz', 'Santa Cruz', -17.7833, -63.1821),
    'atb': ('La Paz', 'La Paz', -16.5000, -68.1500),
    'larazon': ('La Paz', 'La Paz', -16.5000, -68.1500),
    'eldiario': ('La Paz', 'La Paz', -16.5000, -68.1500),
    'erbol': ('La Paz', 'La Paz', -16.5000, -68.1500),
    'elalteno': ('La Paz', 'El Alto', -16.5036, -68.1933),
    'vision360': ('La Paz', 'La Paz', -16.5000, -68.1500),
    'lostiempos': ('Cochabamba', 'Cochabamba', -17.3935, -66.1570),
    'opinion': ('Cochabamba', 'Cochabamba', -17.3935, -66.1570),
    'correodelsur': ('Chuquisaca', 'Sucre', -19.0431, -65.2592),
    'lapatria': ('Oruro', 'Oruro', -17.9833, -67.1500),
    'elpotosi': ('Potosí', 'Potosí', -19.5836, -65.7531),
    'elpais_tarija': ('Tarija', 'Tarija', -21.5355, -64.7296),
    'lavoz_tarija': ('Tarija', 'Tarija', -21.5355, -64.7296),
    'palabradelbeni': ('Beni', 'Trinidad', -14.8333, -64.9000),
    'soldepando': ('Pando', 'Cobija', -11.0000, -68.7667),
    'perladelacre': ('Pando', 'Cobija', -11.0000, -68.7667),
}

def construir_silver(df_bronze):
    """
    Aplica limpieza y deduplicación al acumulado Bronze para generar Silver.
    - Conserva el 100% de las noticias (sin descartar ninguna por categoría o coordenadas).
    - Imputa coordenadas urbanas mediante sede o toponimia para que el Globo 3D muestre todos los puntos.
    - Selecciona las columnas canónicas de Silver incluyendo titulo y coordenadas.
    """
    df = df_bronze.copy()

    # Columnas canónicas de Silver (compatibles con WebGIS y servicios del proyecto)
    cols_silver = ["fecha", "fecha_ingesta", "fuente", "url", "titulo", "departamento", "ciudad",
                   "zona_principal", "nivel_geo", "lat", "lon",
                   "delito_principal", "franja", "dia_semana"]

    # Agregar columnas faltantes si no existen
    for c in cols_silver:
        if c not in df.columns:
            df[c] = None

    # Deduplicación por URL
    df_silver = df[cols_silver].copy().drop_duplicates(subset=["url"])

    # Normalización de delito_principal sin descartar
    delitos_norm = []
    for d in df_silver["delito_principal"]:
        if pd.isna(d) or str(d).strip().lower() in ["nan", "", "none", "no especificado"]:
            delitos_norm.append("Investigación Policial / Seguridad")
        else:
            delitos_norm.append(str(d).strip())
    df_silver["delito_principal"] = delitos_norm

    # Imputación de coordenadas y geografía para garantizar que el 100% de noticias se visualicen
    for idx in df_silver.index:
        lat = df_silver.at[idx, "lat"]
        lon = df_silver.at[idx, "lon"]
        ciudad = str(df_silver.at[idx, "ciudad"] or "").strip()
        depto = str(df_silver.at[idx, "departamento"] or "").strip()
        fuente = str(df_silver.at[idx, "fuente"] or "").lower()

        # Si no tiene coordenadas válidas o ciudad es desconocida/extranjera
        if pd.isna(lat) or pd.isna(lon) or ciudad.lower() in ["", "nan", "extranjero"]:
            # Obtener sede del medio
            sede_depto, sede_ciudad, lat_base, lon_base = SEDES_MEDIOS.get(fuente, ("La Paz", "La Paz", -16.5000, -68.1500))
            
            # Dispersión determinista según URL para que no colisionen en el mapa
            u = str(df_silver.at[idx, "url"] or str(idx))
            h = int(hashlib.md5(u.encode('utf-8', errors='ignore')).hexdigest()[:8], 16)
            jitter_lat = ((h % 1000) / 1000.0 - 0.5) * 0.035
            jitter_lon = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.035

            df_silver.at[idx, "lat"] = round(lat_base + jitter_lat, 5)
            df_silver.at[idx, "lon"] = round(lon_base + jitter_lon, 5)
            if not depto or depto.lower() in ["", "nan", "extranjero"]:
                df_silver.at[idx, "departamento"] = sede_depto
            if not ciudad or ciudad.lower() in ["", "nan", "extranjero"]:
                df_silver.at[idx, "ciudad"] = sede_ciudad
            df_silver.at[idx, "nivel_geo"] = "ciudad"

    return df_silver


def construir_gold_spatial(df_silver):
    """
    Aplica los modelos de clustering espacial (DBSCAN/HDBSCAN/OPTICS) 
    al dataset Silver completo.
    Garantiza que el 100% de las noticias formen parte de la cartografía.
    """
    from modules.algorithms.spatial_density import run_spatial_density

    df_geo = df_silver.dropna(subset=["lat", "lon"]).copy()
    if len(df_geo) < 5:
        print("     [!] Pocas filas con coordenadas para clustering espacial.")
        return df_geo

    df_clust = run_spatial_density(df_geo, radio_km=2.5, min_pts=2)
    return df_clust


def construir_gold_nlp(df_bronze):
    """
    Aplica el modelo LDA de tópicos y el autoencoder simple sobre textos.
    Importa los algoritmos modulares del proyecto.
    """
    from modules.algorithms.topic_modeling import train_lda_topics

    df = df_bronze.dropna(subset=["texto"]).copy()
    df = df[df["texto"].str.len() > 80]
    if len(df) < 10:
        print("     [!] Pocas notas con texto para NLP.")
        return df

    corpus = df["texto"].fillna("").tolist()
    n_topics = min(5, max(2, len(corpus) // 10))

    try:
        lda, vec, topic_matrix, top_words = train_lda_topics(corpus, n_topics=n_topics)
        df["tema_lda"] = topic_matrix.argmax(axis=1)
    except Exception as e:
        print(f"     [!] Error LDA: {e}")
        df["tema_lda"] = 0

    # Proyección PPCA para el scatterplot del dashboard
    try:
        from modules.algorithms.dimensionality import compute_embeddings_2d
        from sklearn.feature_extraction.text import TfidfVectorizer
        tfidf = TfidfVectorizer(max_features=200, max_df=0.9, min_df=1)
        X = tfidf.fit_transform(corpus)
        embeddings = compute_embeddings_2d(X)
        df["ppca_x"] = [c[0] for c in embeddings["ppca"]["coords"]]
        df["ppca_y"] = [c[1] for c in embeddings["ppca"]["coords"]]
    except Exception as e:
        print(f"     [!] Error PPCA: {e}")
        df["ppca_x"] = 0.0
        df["ppca_y"] = 0.0

    # Autoencoder simple (MSE de reconstrucción como puntuación de anomalía)
    try:
        from sklearn.preprocessing import normalize
        X_dense = X.toarray() if hasattr(X, "toarray") else X
        X_norm  = normalize(X_dense)
        # Autoencoder lineal: PCA reconstruct error como proxy
        from sklearn.decomposition import PCA
        n_comp = min(10, X_norm.shape[1], X_norm.shape[0] - 1)
        pca    = PCA(n_components=n_comp)
        X_rec  = pca.inverse_transform(pca.fit_transform(X_norm))
        errors = np.mean((X_norm - X_rec) ** 2, axis=1)
        df["error_autoencoder"] = errors
        umbral = np.percentile(errors, 90)
        df["es_anomalia"] = errors > umbral

        # Exportar reduction_embeddings.json para la vista Reduccion 2D (/reduccion-espacios)
        points_list = []
        for idx, row in enumerate(df.itertuples()):
            points_list.append({
                "id": int(idx),
                "title": str(row.titulo) if hasattr(row, "titulo") and pd.notna(row.titulo) else f"Reporte #{idx}",
                "category": str(row.delito_principal) if hasattr(row, "delito_principal") and pd.notna(row.delito_principal) else "No especificado",
                "city": str(row.ciudad) if hasattr(row, "ciudad") and pd.notna(row.ciudad) else "Bolivia",
                "topic": int(row.tema_lda) if hasattr(row, "tema_lda") and pd.notna(row.tema_lda) else 0,
                "is_anomaly": bool(row.es_anomalia) if hasattr(row, "es_anomalia") else False,
                "reconstruction_error": round(float(row.error_autoencoder), 6) if hasattr(row, "error_autoencoder") else 0.001
            })

        reduction_payload = {
            "pca": embeddings.get("pca", {}),
            "svd": embeddings.get("svd", {}),
            "ppca": embeddings.get("ppca", {}),
            "tsne": embeddings.get("tsne", {}),
            "umap": embeddings.get("umap", {}),
            "points": points_list
        }
        with open(os.path.join(_GOLD_DIR, "reduction_embeddings.json"), "w", encoding="utf-8") as f_red:
            json.dump(reduction_payload, f_red, ensure_ascii=False, indent=2)
        print(f"  [OK] reduction_embeddings.json actualizado con {len(points_list)} puntos.")
    except Exception as e:
        print(f"     [!] Error autoencoder / reduction: {e}")
        df["error_autoencoder"] = 0.001
        df["es_anomalia"] = False

    return df


def actualizar_gold_resumen(df_silver):
    """
    Regenera los resúmenes CSV y el dashboard_data.json en la capa Gold.
    """
    os.makedirs(_GOLD_DIR, exist_ok=True)

    # resumen_departamento.csv
    if "departamento" in df_silver.columns and "delito_principal" in df_silver.columns:
        df_silver.groupby(["departamento", "delito_principal"]).size().reset_index(name="hechos") \
            .to_csv(os.path.join(_GOLD_DIR, "resumen_departamento.csv"), index=False)

    # resumen_ciudad.csv
    if "ciudad" in df_silver.columns:
        df_silver.groupby(["departamento", "ciudad", "delito_principal"]).size().reset_index(name="hechos") \
            .to_csv(os.path.join(_GOLD_DIR, "resumen_ciudad.csv"), index=False)

    # resumen_zona.csv
    df_z = df_silver.dropna(subset=["zona_principal"]) if "zona_principal" in df_silver.columns else pd.DataFrame()
    if not df_z.empty:
        df_z.groupby(["departamento", "ciudad", "zona_principal", "lat", "lon", "delito_principal"]) \
            .size().reset_index(name="hechos") \
            .to_csv(os.path.join(_GOLD_DIR, "resumen_zona.csv"), index=False)

    # dashboard_data.json (para el contexto Bolivia en el dashboard)
    deptos_dict = {}
    if "departamento" in df_silver.columns:
        deptos_dict = df_silver["departamento"].value_counts().to_dict()

    ciudades_list = []
    if "ciudad" in df_silver.columns:
        for ciudad, n in df_silver["ciudad"].value_counts().items():
            if ciudad and ciudad in CIUDADES_BO:
                dep, lat, lon = CIUDADES_BO[ciudad]
                ciudades_list.append({"ciudad": ciudad, "departamento": dep, "lat": lat, "lon": lon, "hechos": int(n)})

    dashboard_data = {
        "total_noticias": len(df_silver),
        "departamentos":  deptos_dict,
        "ciudades":       ciudades_list,
        "generado_en":    datetime.datetime.now().isoformat(),
    }
    with open(os.path.join(_GOLD_DIR, "dashboard_data.json"), "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Resumenes Gold actualizados en {_GOLD_DIR}")


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 9: FUNCIÓN PRINCIPAL ORQUESTADORA
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_ingesta_completa(
    medios_activos=None,
    youtube_activo=True,
    max_medios=None,
):
    """
    Orquestador principal del sistema de ingesta incremental.
    """
    inicio = datetime.datetime.now()
    print("=" * 70)
    print("  BOLIVIA SCRAPER  |  INGESTA INCREMENTAL SOSTENIBLE")
    print(f"  Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not HAS_REQUESTS:
        print("[ERROR] Falta 'requests'. Ejecuta: pip install requests requests-cache")
        return

    # ── Paso 1: Cargar memoria histórica ──────────────────────────────────────
    urls_previas = _cargar_urls_previas(_BRONZE)
    n_historico  = len(urls_previas)
    print(f"\n[1/5] Memoria historica cargada: {n_historico} noticias ya recolectadas.")

    total_nuevas = 0

    # ── Paso 2: Medios web ────────────────────────────────────────────────────
    lista_medios = medios_activos or list(MEDIOS.keys())
    if max_medios:
        lista_medios = lista_medios[:max_medios]

    print(f"\n[2/5] Procesando {len(lista_medios)} medios web de Bolivia...")
    for clave in lista_medios:
        try:
            nuevas = procesar_medio(clave, urls_previas)
            total_nuevas += len(nuevas)
        except RuntimeError as e:
            print(f"  [X] {clave}: {e}")
            break
        except Exception as e:
            print(f"  [X] Error inesperado en [{clave}]: {e}")

    # ── Paso 3: YouTube via RSS (sin API Key) ─────────────────────────────────
    if youtube_activo:
        print(f"\n[3/5] Procesando {len(CANALES_YT_RSS)} canales de YouTube (via RSS publico)...")
        for nombre, channel_id in CANALES_YT_RSS.items():
            try:
                nuevas = procesar_youtube_canal(nombre, channel_id, urls_previas)
                total_nuevas += len(nuevas)
            except Exception as e:
                print(f"  [X] Error en canal YT [{nombre}]: {e}")

    # ── Paso 4: Reconstruir Silver y Gold ─────────────────────────────────────
    print(f"\n[4/5] Actualizando capas Silver y Gold con el acumulado completo...")
    if os.path.exists(_BRONZE):
        df_bronze = pd.read_csv(_BRONZE)
        df_bronze = df_bronze.drop_duplicates(subset=["url"])

        # Silver
        df_silver = construir_silver(df_bronze)
        os.makedirs(os.path.dirname(_SILVER), exist_ok=True)
        df_silver.to_csv(_SILVER, index=False, encoding="utf-8")
        print(f"  [OK] Silver actualizado: {len(df_silver)} registros limpios.")

        # Gold: clustering espacial
        try:
            df_spatial = construir_gold_spatial(df_silver)
            ruta_spatial = os.path.join(_GOLD_DIR, "spatial_clusters_bolivia.csv")
            df_spatial.to_csv(ruta_spatial, index=False, encoding="utf-8")
            print(f"  [OK] Gold espacial actualizado: {len(df_spatial)} puntos con clusters.")
        except Exception as e:
            print(f"  [!] Gold espacial: {e}")

        # Gold: NLP y anomalías
        try:
            df_nlp = construir_gold_nlp(df_bronze)
            ruta_nlp = os.path.join(_GOLD_DIR, "nlp_topics_anomalies_bolivia.csv")
            df_nlp.to_csv(ruta_nlp, index=False, encoding="utf-8")
            print(f"  [OK] Gold NLP actualizado: {len(df_nlp)} notas con topico LDA y anomalias.")
        except Exception as e:
            print(f"  [!] Gold NLP: {e}")

        # Gold: resúmenes JSON/CSV del dashboard
        actualizar_gold_resumen(df_silver)

    # ── Paso 5: Reporte final ─────────────────────────────────────────────────
    fin     = datetime.datetime.now()
    duracion = (fin - inicio).seconds
    total_actual = len(_cargar_urls_previas(_BRONZE))

    print("\n" + "=" * 70)
    print("  REPORTE FINAL")
    print("=" * 70)
    print(f"  Noticias antes de esta corrida : {n_historico}")
    print(f"  Noticias nuevas sumadas hoy    : {total_nuevas}")
    print(f"  TOTAL ACUMULADO en Bronze      : {total_actual}")
    print(f"  Duracion total                 : {duracion}s")
    print(f"  Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\n  [OK] Para ver los resultados en el dashboard:")
    print("     python app.py   ->   http://127.0.0.1:5000/?ctx=bolivia")
    print("=" * 70)

    return {
        "historico_previo":  n_historico,
        "nuevas_esta_corrida": total_nuevas,
        "total_acumulado":   total_actual,
        "duracion_segundos": duracion,
    }
