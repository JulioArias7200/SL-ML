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
        
    telemetry = DataService.get_dashboard_summary()["hardware_telemetry"]
    districts = SpatialDensityService.get_zones(ctx=ctx)
    
    # Parámetros calibrados según el dataset
    default_eps = 300 if ctx == 'chicago' else 1500
    default_min_pts = 25 if ctx == 'chicago' else 5
    hud_params = SpatialDensityService.calculate_haversine_hud(eps_meters=default_eps, min_pts=default_min_pts, ctx=ctx)
    
    # Datos analíticos de OPTICS, HDBSCAN, DBSCAN y Clustermap
    optics_data = SpatialDensityService.get_optics_data(ctx=ctx, xi=0.05, min_pts=default_min_pts)
    hdbscan_data = SpatialDensityService.get_hdbscan_data(ctx=ctx)
    dbscan_data = SpatialDensityService.get_dbscan_data(ctx=ctx)
    clustermap_data = SpatialDensityService.get_clustermap_data(ctx=ctx)
    
    return render_template(
        'views/espacial_densidad.html',
        telemetry=telemetry,
        districts=districts,
        hud_params=hud_params,
        optics_data=optics_data,
        hdbscan_data=hdbscan_data,
        dbscan_data=dbscan_data,
        clustermap_data=clustermap_data,
        active_page='espacial-densidad',
        current_context=ctx
    )
