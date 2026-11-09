from flask import Blueprint, render_template, request
from modules.services.spatial_service import SpatialDensityService
from modules.services.data_service import DataService

spatial_density_bp = Blueprint('spatial_density_bp', __name__)

@spatial_density_bp.route('/jerarquico-densidad')
@spatial_density_bp.route('/espacial-densidad')
def view():
    ctx = request.args.get('ctx', 'bolivia').lower()
    if ctx != 'chicago':
        ctx = 'bolivia'

    district_param = request.args.get('district')
    try:
        district = int(district_param) if district_param else 1
    except ValueError:
        district = 1
        
    telemetry = DataService.get_dashboard_summary()["hardware_telemetry"]
    districts = SpatialDensityService.get_zones(ctx=ctx)
    
    # Parámetros calibrados según el dataset y ámbito distrital
    if ctx == 'chicago':
        hud_params = SpatialDensityService.calculate_haversine_hud(ctx='chicago', district=district)
        optics_data = SpatialDensityService.get_optics_data(ctx='chicago', xi=0.05, min_pts=25)
        filter_options = SpatialDensityService.get_filter_options(ctx='chicago', district=district)
        model_comparison = SpatialDensityService.comparar_modelos(ctx='chicago', district=district)
        hallazgos = SpatialDensityService.generar_hallazgos(ctx='chicago', district=district)
    else:
        hud_params = SpatialDensityService.calculate_haversine_hud(eps_meters=2500, min_pts=2, ctx='bolivia')
        optics_data = SpatialDensityService.get_optics_data(ctx='bolivia', xi=0.05, min_pts=2)
        filter_options = SpatialDensityService.get_filter_options(ctx='bolivia')
        model_comparison = SpatialDensityService.comparar_modelos(ctx='bolivia')
        hallazgos = SpatialDensityService.generar_hallazgos(ctx='bolivia')
    
    # Datos analíticos de HDBSCAN, DBSCAN, Clustermap, Tabla de Zonas y Validación Metodológica
    hdbscan_data = SpatialDensityService.get_hdbscan_data(ctx=ctx)
    dbscan_data = SpatialDensityService.get_dbscan_data(ctx=ctx)
    clustermap_data = SpatialDensityService.get_clustermap_data(ctx=ctx)
    zones_table = SpatialDensityService.tabla_zonas(ctx=ctx)
    validation_data = SpatialDensityService.get_validation_data(ctx=ctx, district=district if ctx == 'chicago' else None)
    
    return render_template(
        'views/espacial_densidad.html',
        telemetry=telemetry,
        districts=districts,
        hud_params=hud_params,
        optics_data=optics_data,
        hdbscan_data=hdbscan_data,
        dbscan_data=dbscan_data,
        clustermap_data=clustermap_data,
        zones_table=zones_table,
        validation_data=validation_data,
        hallazgos=hallazgos,
        filter_options=filter_options,
        model_comparison=model_comparison,
        selected_district=district if ctx == 'chicago' else None,
        active_page='espacial-densidad',
        current_context=ctx
    )
