import pytest
from modules.services.webgis_service import WebGISService
from modules.services.spatial_service import SpatialDensityService
from modules.services.bolivia_service import BoliviaService


def test_bolivia_unified_dataset_across_modules():
    """Verifica que el dataset de Bolivia sea idéntico en todos los módulos (Jerarquía y Densidad, WebGIS, Dashboard) con 137 crónicas."""
    # Reset caches if any
    SpatialDensityService._BOLIVIA_COORDS_CACHE = None
    WebGISService._df_cache = None
    BoliviaService._data_clusters = None

    # 1. Jerarquía y Densidad
    coords_spatial = SpatialDensityService._get_bolivia_coords_rad()
    assert len(coords_spatial) == 137, f"Jerarquía y Densidad debe tener 137 crónicas, tiene {len(coords_spatial)}"

    # 2. WebGIS / Globo 3D
    geo_webgis = WebGISService.get_geojson(ctx='bolivia')
    assert geo_webgis["total"] == 137, f"WebGIS debe tener 137 crónicas, tiene {geo_webgis['total']}"
    assert len(geo_webgis["features"]) == 137

    # 3. Bolivia Service (Dashboard General)
    df_bolivia = BoliviaService.get_clusters_data()
    assert len(df_bolivia) == 137, f"BoliviaService debe usar el mismo archivo de 137 crónicas, tiene {len(df_bolivia)}"

    # Mismos conteos de DBSCAN
    hotspots_spatial = set(df_bolivia["dbscan"].unique())
    assert -1 in hotspots_spatial
    assert {0, 1, 2, 3, 4, 5}.issubset(hotspots_spatial)


def test_chicago_unified_data_and_models():
    """Verifica que Chicago en WebGIS use el parquet silver curado (2024-2025) y tenga modelos reales."""
    geo_chi = WebGISService.get_geojson(ctx='chicago')
    assert geo_chi["total"] == 750
    assert len(geo_chi["features"]) == 750

    dbscan_labels = [f["properties"]["dbscan"] for f in geo_chi["features"]]
    hdbscan_labels = [f["properties"]["hdbscan"] for f in geo_chi["features"]]
    optics_labels = [f["properties"]["optics"] for f in geo_chi["features"]]

    # Los modelos no deben ser idénticos (no deben venir de un heurístico rígido distrital)
    assert dbscan_labels != hdbscan_labels
    assert hdbscan_labels != optics_labels

    # Verificar que los clusters sean reales
    n_dbscan_clusters = len(set(dbscan_labels) - {-1})
    assert n_dbscan_clusters >= 5


def test_webgis_metadata_consistency():
    """Verifica que la metadata de ambos contextos esté alineada."""
    meta_bol = WebGISService.get_metadata(ctx='bolivia')
    assert meta_bol["contexto"] == "bolivia"
    assert meta_bol["total_eventos"] == 137

    meta_chi = WebGISService.get_metadata(ctx='chicago')
    assert meta_chi["contexto"] == "chicago"
    assert meta_chi["total_eventos"] == 750
